"""Verify SMTP mode handling with local mocks and synthetic message data."""
import importlib.util
from pathlib import Path
import smtplib
import unittest
from unittest.mock import patch, sentinel


SOURCE = Path(__file__).resolve().parents[1] / 'usvwatch/usvwatch.py'
SPEC = importlib.util.spec_from_file_location('usvwatch_app', SOURCE)
app = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(app)


class SmtpModeTests(unittest.TestCase):
    def setUp(self):
        self.arguments = {
            'smtp_host': 'smtp.example.test',
            'smtp_port': 587,
            'smtp_user': 'test-user',
            'smtp_pass': 'test-password',
            'smtp_from': 'sender@example.test',
            'smtp_to': ['recipient@example.test'],
            'smtp_cc': [],
            'smtp_bcc': [],
            'smtp_timeout': 15,
            'tls_verify': True,
            'subject': 'USVWatch mode test',
            'html_body': '<p>Synthetic status</p>',
        }
        # A missed SMTP mock must fail instead of contacting any server.
        self.start_patch('socket.create_connection', side_effect=AssertionError('Unexpected network access'))
        self.smtp = self.start_patch('smtplib.SMTP')
        self.smtp_ssl = self.start_patch('smtplib.SMTP_SSL')
        self.context = self.start_patch('ssl.create_default_context', return_value=sentinel.verified_context)
        self.unverified = self.start_patch('ssl._create_unverified_context', return_value=sentinel.unverified_context)

    def start_patch(self, name, **kwargs):
        patcher = patch(name, **kwargs)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def send(self, mode):
        app.send_mail(smtp_tls=mode, **self.arguments)

    def test_starttls_upgrades_before_login_and_delivery(self):
        self.send(' STARTTLS ')
        self.smtp.assert_called_once_with('smtp.example.test', 587, timeout=15)
        self.smtp_ssl.assert_not_called()
        client = self.smtp.return_value.__enter__.return_value
        self.assertEqual([call[0] for call in client.method_calls],
                         ['ehlo', 'starttls', 'ehlo', 'login', 'send_message'])
        client.starttls.assert_called_once_with(context=sentinel.verified_context)
        client.login.assert_called_once_with('test-user', 'test-password')
        client.send_message.assert_called_once()

    def test_implicit_ssl_uses_verified_context(self):
        self.arguments['smtp_port'] = 465
        self.send('ssl')
        self.smtp_ssl.assert_called_once_with('smtp.example.test', 465, timeout=15,
                                             context=sentinel.verified_context)
        self.smtp.assert_not_called()
        client = self.smtp_ssl.return_value.__enter__.return_value
        client.starttls.assert_not_called()
        client.login.assert_called_once_with('test-user', 'test-password')
        client.send_message.assert_called_once()

    def test_explicit_none_preserves_unencrypted_optional_auth_mode(self):
        self.arguments['smtp_user'] = ''
        self.send('none')
        self.smtp.assert_called_once_with('smtp.example.test', 587, timeout=15)
        self.smtp_ssl.assert_not_called()
        client = self.smtp.return_value.__enter__.return_value
        client.starttls.assert_not_called()
        client.login.assert_not_called()
        client.send_message.assert_called_once()
        self.context.assert_not_called()

    def test_documented_certificate_verification_override_is_preserved(self):
        self.arguments['tls_verify'] = False
        self.send('ssl')
        self.smtp_ssl.assert_called_once_with('smtp.example.test', 587, timeout=15,
                                             context=sentinel.unverified_context)
        self.context.assert_not_called()

    def test_failed_starttls_never_authenticates_or_delivers(self):
        client = self.smtp.return_value.__enter__.return_value
        client.starttls.side_effect = smtplib.SMTPNotSupportedError('STARTTLS unavailable')
        with self.assertRaises(smtplib.SMTPNotSupportedError):
            self.send('starttls')
        client.login.assert_not_called()
        client.send_message.assert_not_called()
        self.smtp_ssl.assert_not_called()

    def test_invalid_mode_is_rejected_before_any_connection(self):
        for value in ('startls', 'tls', 'off', '', '   '):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, r'SMTP_TLS must be one of: starttls, ssl, none'):
                    self.send(value)
        self.smtp.assert_not_called()
        self.smtp_ssl.assert_not_called()
        self.context.assert_not_called()
        self.unverified.assert_not_called()


if __name__ == '__main__':
    unittest.main()
