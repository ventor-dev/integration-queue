# Copyright 2025 VentorTech
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

import re
import json
import html as html_lib

from odoo import api, fields, models, _


_LOG_RECORD_RE = re.compile(
    r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) '
    r'(DEBUG|INFO|WARNING|ERROR|CRITICAL) '
    r'([^:]+): (.*)$'
)

_LOG_LEVEL_COLORS = {
    'DEBUG': '#6c757d',
    'INFO': '#212529',
    'WARNING': '#b8860b',
    'ERROR': '#dc3545',
    'CRITICAL': '#b02a37',
}

_LOG_TIMESTAMP_COLOR = '#7c3aed'
_LOG_LOGGER_COLOR = '#0d6efd'


class QueueJobLogWizard(models.TransientModel):
    _name = 'queue.job.log.wizard'
    _description = 'Captured Job Log'

    job_id = fields.Many2one(
        comodel_name='queue.job',
        string='Job',
        required=True,
    )

    body = fields.Html(
        string='Captured Log',
        compute='_compute_body_from_job',
    )

    @api.depends('job_id.log_text')
    def _compute_body_from_job(self):
        for rec in self:
            rec.body = rec._format_captured_log_as_html(rec.job_id.log_text)

    def action_close(self):
        return {
            'type': 'ir.actions.act_window_close',
        }

    def download_log_txt(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/queue-job/log/export/{self.id}',
            'target': 'self',
        }

    @api.model
    def create_and_run(self, job_id: int) -> dict:
        wizard = self.create({'job_id': job_id})

        return {
            'type': 'ir.actions.act_window',
            'name': _('Captured Log'),
            'res_model': wizard._name,
            'res_id': wizard.id,
            'view_mode': 'form',
            'view_id': wizard.env.ref('integration_queue_job.queue_job_log_wizard_form').id,
            'target': 'new',
        }

    def prepare_log_content(self) -> str:
        self.ensure_one()

        job = self.job_id

        return json.dumps({
            'job_id': job.id,
            'uuid': job.uuid,
            'name': job.name,
            'channel': job.channel,
            'func_string': job.func_string,
            'state': job.state,
            'exc_name': job.exc_name,
            'exc_message': job.exc_message,
            'exc_info': job.exc_info,
            'identity_key': job.identity_key,
            'result': job.result,
            'exec_time': job.exec_time,
            'date_created': fields.Datetime.to_string(job.date_created),
            'date_started': fields.Datetime.to_string(job.date_started),
            'date_enqueued': fields.Datetime.to_string(job.date_enqueued),
            'date_done': fields.Datetime.to_string(job.date_done),
            'log_text': job.log_text,
        }, indent=4)

    @staticmethod
    def _format_captured_log_as_html(text: str) -> str:
        """Render captured job output as HTML for display in the wizard.

        Logger lines use the same format as capture._BufferHandler. All other
        lines (stdout/stderr) are shown as plain monospace text.
        """
        if not text:
            return '<p class="text-muted">No captured output.</p>'

        lines = []
        for line in text.splitlines():
            if not line:
                lines.append('<br/>')
                continue

            match = _LOG_RECORD_RE.match(line)
            if match:
                timestamp, level, logger_name, message = match.groups()
                color_ = _LOG_LEVEL_COLORS.get(level, _LOG_LEVEL_COLORS['INFO'])

                lines.append(
                    '<div style="margin:0;padding:2px 0;font-family:monospace;'
                    f'font-size:12px;white-space:pre-wrap;color:{color_};">'
                    f'<span style="color:{_LOG_TIMESTAMP_COLOR};">'
                    f'{html_lib.escape(timestamp)}</span> '
                    f'<strong>{html_lib.escape(level)}</strong> '
                    f'<span style="color:{_LOG_LOGGER_COLOR};">'
                    f'{html_lib.escape(logger_name)}</span>: '
                    f'<span>{html_lib.escape(message)}</span>'
                    '</div>'
                )
            else:
                lines.append(
                    '<div style="margin:0;padding:2px 0;font-family:monospace;'
                    'font-size:12px;white-space:pre-wrap;color:#212529;">'
                    f'{html_lib.escape(line)}</div>'
                )

        return (
            '<div class="multiline" style="max-height:70vh;overflow:auto;padding:12px;color:#212529;background:#fff;">'
            '%s'
            '</div>'
        ) % ''.join(lines)
