"""Exercise user-visible status and device selection without contacting a UPS."""
import contextlib
import datetime
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / 'usvwatch/usvwatch.py'
SPEC = importlib.util.spec_from_file_location('usvwatch_status_app', SOURCE)
app = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(app)


class StatusTests(unittest.TestCase):
    def test_replace_battery_and_charging_have_distinct_meanings(self):
        for language, replacement, charging in (
            ('de', 'Batterie ersetzen', 'Batterie lädt'),
            ('en', 'Replace battery', 'Charging'),
        ):
            with self.subTest(language=language):
                rendered = app.build_html(
                    lang=language, event_label='test', now=datetime.datetime(2026, 1, 1),
                    host='test-host', ups_name='test-ups', ups_desc='test device',
                    vars_={'ups.status': 'OL RB CHRG'}, include_all_vars=True,
                    include_status_legend=True, add_human_status_field=True,
                    all_vars_include_regex='', all_vars_exclude_regex='',
                )
                self.assertIn(replacement + ' (RB)', rendered)
                self.assertIn(charging + ' (CHRG)', rendered)
                self.assertNotIn('recharging', rendered)
                self.assertNotIn('wieder geladen', rendered)


class DeviceSelectionTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.dict('os.environ', {}, clear=True))
        self.stack.enter_context(patch('socket.create_connection', side_effect=AssertionError('Unexpected network')))
        self.stack.enter_context(patch.object(app, 'load_env_file'))
        client_class = self.stack.enter_context(patch.object(app, 'NutClient'))
        self.client = client_class.return_value.__enter__.return_value
        self.client.list_ups.return_value = [('first', 'First UPS'), ('second', 'Second UPS')]

    def test_explicit_name_selects_matching_device(self):
        with patch.dict('os.environ', {'NUT_UPS_NAME': 'second'}):
            self.assertEqual(app.nut_select_ups(), ('second', 'Second UPS'))

    def test_empty_name_preserves_automatic_first_device_selection(self):
        self.assertEqual(app.nut_select_ups(), ('first', 'First UPS'))

    def test_missing_explicit_name_stops_before_read_or_write_commands(self):
        for arguments in (['--print-status'], ['--list-commands'], ['--run-cmd', 'beeper.mute']):
            with self.subTest(arguments=arguments), \
                    patch.dict('os.environ', {'NUT_UPS_NAME': 'missing'}), \
                    patch('sys.argv', ['usvwatch.py'] + arguments), \
                    patch.object(app, 'nut_get_vars', return_value={}) as get_vars, \
                    patch.object(app, 'nut_list_cmds', return_value=[]) as list_cmds, \
                    patch.object(app, 'nut_run_cmd', return_value='OK') as run_cmd, \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(app.main(), 1)
                self.assertIn('error', json.loads(output.getvalue()))
                get_vars.assert_not_called()
                list_cmds.assert_not_called()
                run_cmd.assert_not_called()

    def test_empty_server_list_still_fails(self):
        self.client.list_ups.return_value = []
        with self.assertRaises(app.NutClientError):
            app.nut_select_ups()


if __name__ == '__main__':
    unittest.main()
