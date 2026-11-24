"""Run notification cycles against temporary state and a mocked mail transport."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / 'usvwatch/usvwatch.py'
SPEC = importlib.util.spec_from_file_location('usvwatch_retry_app', SOURCE)
app = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(app)


class NotificationRetryTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        state_dir = self.stack.enter_context(tempfile.TemporaryDirectory())
        self.state_file = Path(state_dir) / 'usvwatch_state.json'
        self.stack.enter_context(patch.dict('os.environ', {
            'STATE_DIR': state_dir, 'SMTP_HOST': 'smtp.example.test',
            'MAIL_FROM': 'sender@example.test', 'MAIL_TO': 'recipient@example.test',
            'USVWATCH_LANG': 'en', 'ALERT_CHARGE_LOW': '0', 'ALERT_RUNTIME_LOW': '0',
            'ENABLE_DAILY_REPORT': '0',
        }, clear=True))
        self.stack.enter_context(patch('socket.create_connection', side_effect=AssertionError('Unexpected network')))
        self.stack.enter_context(patch('sys.argv', ['usvwatch.py']))
        self.stack.enter_context(patch.object(app, 'load_env_file'))
        self.stack.enter_context(patch.object(app, 'nut_select_ups', return_value=('test-ups', 'Test UPS')))
        self.get_vars = self.stack.enter_context(patch.object(app, 'nut_get_vars'))
        self.send_mail = self.stack.enter_context(patch.object(app, 'send_mail'))
        self.stack.enter_context(contextlib.redirect_stderr(io.StringIO()))

    def read_state(self):
        return json.loads(self.state_file.read_text())

    def test_failed_transition_is_retried_then_success_is_not_duplicated(self):
        cases = (
            ('on_battery', {'prev_ob': False}, 'OB', 'prev_ob', True),
            ('back_online', {'prev_ob': True}, 'OL', 'prev_ob', False),
            ('low_battery', {'prev_lb': False}, 'OL LB', 'prev_lb', True),
            ('recovered', {'last_reachable': False}, 'OL', 'last_reachable', True),
        )
        for name, initial_state, status, key, after in cases:
            with self.subTest(event=name):
                self.state_file.write_text(json.dumps(initial_state))
                self.get_vars.return_value = {'ups.status': status}
                self.send_mail.reset_mock()
                self.send_mail.side_effect = OSError('Synthetic delivery failure')
                app.main()
                self.send_mail.assert_called_once()
                self.assertEqual(self.read_state()[key], after)

                self.send_mail.reset_mock()
                self.send_mail.side_effect = None
                app.main()
                self.send_mail.assert_called_once()
                self.assertEqual(self.read_state()[key], after)

                self.send_mail.reset_mock()
                app.main()
                self.send_mail.assert_not_called()

    def test_disabled_alert_records_state_without_sending(self):
        with patch.dict('os.environ', {'ALERT_ON_BATTERY': '0', 'ALERT_LOW_BATTERY': '0'}):
            self.get_vars.return_value = {'ups.status': 'OB LB'}
            app.main()
            state = self.read_state()
            self.assertTrue(state['prev_ob'])
            self.assertTrue(state['prev_lb'])
            self.send_mail.assert_not_called()

    def test_zero_repeat_interval_preserves_first_threshold_delivery(self):
        for setting, values in (
            ('ALERT_CHARGE_LOW', {'ups.status': 'OL', 'battery.charge': '5'}),
            ('ALERT_RUNTIME_LOW', {'ups.status': 'OL', 'battery.runtime': '60'}),
        ):
            with self.subTest(setting=setting), patch.dict('os.environ', {
                setting: '1', 'THRESHOLD_RESEND_MIN': '0',
            }):
                self.state_file.write_text('{}')
                self.get_vars.return_value = values
                self.send_mail.reset_mock()
                self.send_mail.side_effect = OSError('Synthetic delivery failure')
                app.main()
                self.send_mail.assert_called_once()
                self.send_mail.reset_mock()
                self.send_mail.side_effect = None
                app.main()
                self.send_mail.assert_called_once()
                self.send_mail.reset_mock()
                app.main()
                self.send_mail.assert_not_called()

    def test_zero_unreachable_repeat_retries_failed_first_delivery(self):
        with patch.dict('os.environ', {'UNREACHABLE_RESEND_MIN': '0'}):
            self.get_vars.side_effect = OSError('Synthetic unavailable UPS')
            self.send_mail.side_effect = OSError('Synthetic delivery failure')
            self.assertEqual(app.main(), 1)
            self.send_mail.assert_called_once()
            self.send_mail.reset_mock()
            self.send_mail.side_effect = None
            self.assertEqual(app.main(), 1)
            self.send_mail.assert_called_once()
            self.send_mail.reset_mock()
            self.assertEqual(app.main(), 1)
            self.send_mail.assert_not_called()

    def test_failed_outage_message_is_not_replayed_after_power_recovers(self):
        self.get_vars.return_value = {'ups.status': 'OB'}
        self.send_mail.side_effect = OSError('Synthetic delivery failure')
        app.main()
        self.send_mail.reset_mock()
        self.send_mail.side_effect = None
        self.get_vars.return_value = {'ups.status': 'OL'}
        app.main()
        self.send_mail.assert_called_once()
        self.assertEqual(self.send_mail.call_args.kwargs['subject'], app.I18N['en']['back_online_subject'])
        self.send_mail.reset_mock()
        app.main()
        self.send_mail.assert_not_called()

    def test_failed_recovery_mail_does_not_hide_a_new_unreachable_event(self):
        with patch.dict('os.environ', {'UNREACHABLE_RESEND_MIN': '0'}):
            self.get_vars.side_effect = OSError('Synthetic unavailable UPS')
            self.assertEqual(app.main(), 1)
            self.send_mail.assert_called_once()

            self.get_vars.side_effect = None
            self.get_vars.return_value = {'ups.status': 'OL'}
            self.send_mail.reset_mock()
            self.send_mail.side_effect = OSError('Synthetic delivery failure')
            app.main()
            self.send_mail.assert_called_once()

            self.get_vars.side_effect = OSError('New synthetic outage')
            self.send_mail.reset_mock()
            self.send_mail.side_effect = None
            self.assertEqual(app.main(), 1)
            self.send_mail.assert_called_once()
            self.assertEqual(self.send_mail.call_args.kwargs['subject'], app.I18N['en']['unreachable_subject'])

    def test_failed_mains_restoration_mail_does_not_hide_next_power_outage(self):
        self.get_vars.return_value = {'ups.status': 'OB'}
        app.main()
        self.send_mail.assert_called_once()
        self.get_vars.return_value = {'ups.status': 'OL'}
        self.send_mail.reset_mock()
        self.send_mail.side_effect = OSError('Synthetic delivery failure')
        app.main()
        self.send_mail.assert_called_once()
        self.get_vars.return_value = {'ups.status': 'OB'}
        self.send_mail.reset_mock()
        self.send_mail.side_effect = None
        app.main()
        self.send_mail.assert_called_once()
        self.assertEqual(self.send_mail.call_args.kwargs['subject'], app.I18N['en']['on_battery_subject'])

    def test_new_threshold_incident_after_valid_normal_reading_is_delivered(self):
        for setting, variable, low, normal in (
            ('ALERT_CHARGE_LOW', 'battery.charge', '5', '100'),
            ('ALERT_RUNTIME_LOW', 'battery.runtime', '60', '3600'),
        ):
            with self.subTest(setting=setting), patch.dict('os.environ', {
                setting: '1', 'THRESHOLD_RESEND_MIN': '0',
            }):
                self.state_file.write_text('{}')
                self.send_mail.reset_mock()
                self.get_vars.return_value = {'ups.status': 'OL', variable: low}
                app.main()
                self.send_mail.assert_called_once()
                self.send_mail.reset_mock()
                self.get_vars.return_value = {'ups.status': 'OL', variable: normal}
                app.main()
                self.send_mail.assert_not_called()
                self.get_vars.return_value = {'ups.status': 'OL', variable: low}
                app.main()
                self.send_mail.assert_called_once()

    def test_missing_reading_does_not_rearm_threshold_notification(self):
        for setting, variable in (
            ('ALERT_CHARGE_LOW', 'battery.charge'),
            ('ALERT_RUNTIME_LOW', 'battery.runtime'),
        ):
            with self.subTest(setting=setting), patch.dict('os.environ', {
                setting: '1', 'THRESHOLD_RESEND_MIN': '0',
            }):
                self.state_file.write_text('{}')
                self.send_mail.reset_mock()
                self.get_vars.return_value = {'ups.status': 'OL', variable: '5'}
                app.main()
                self.send_mail.assert_called_once()
                self.send_mail.reset_mock()
                self.get_vars.return_value = {'ups.status': 'OL'}
                app.main()
                self.get_vars.return_value = {'ups.status': 'OL', variable: '5'}
                app.main()
                self.send_mail.assert_not_called()


if __name__ == '__main__':
    unittest.main()
