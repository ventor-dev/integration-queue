# Copyright 2025 VentorTech
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from odoo.tests import tagged

from odoo.addons.integration_queue_job.tests.common import QueueJobCommon


@tagged('post_install', '-at_install')
class TestFormatCapturedLog(QueueJobCommon):

    def test_empty_log(self):
        html = self.env['queue.job.log.wizard']._format_captured_log_as_html('')
        self.assertIn('No captured output', html)

    def test_logger_line_highlighted(self):
        log_text = (
            '2024-01-01 12:00:00,123 INFO odoo.addons.test: hello world\n'
            'plain stdout line\n'
        )
        html = self.env['queue.job.log.wizard']._format_captured_log_as_html(log_text)
        self.assertIn('INFO', html)
        self.assertIn('odoo.addons.test', html)
        self.assertIn('hello world', html)
        self.assertIn('plain stdout line', html)
        self.assertIn('color:#212529', html)
        self.assertIn('multiline', html)

    def test_error_level_uses_red(self):
        log_text = '2024-01-01 12:00:00,123 ERROR odoo.addons.test: boom\n'
        html = self.env['queue.job.log.wizard']._format_captured_log_as_html(log_text)
        self.assertIn('#dc3545', html)
        self.assertIn('boom', html)

    def test_warning_level_uses_yellow(self):
        log_text = '2024-01-01 12:00:00,123 WARNING odoo.addons.test: careful\n'
        html = self.env['queue.job.log.wizard']._format_captured_log_as_html(log_text)
        self.assertIn('#b8860b', html)

    def test_debug_level_uses_gray(self):
        log_text = '2024-01-01 12:00:00,123 DEBUG odoo.addons.test: trace\n'
        html = self.env['queue.job.log.wizard']._format_captured_log_as_html(log_text)
        self.assertIn('#6c757d', html)
