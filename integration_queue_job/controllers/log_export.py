# Copyright 2025 VentorTech
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from odoo import _
from odoo.http import Controller, content_disposition, request, route


class QueueJobLogExport(Controller):

    @route('/queue-job/log/export/<int:wizard_id>', type='http', auth='user')
    def export_log_txt(self, wizard_id):
        wizard = request.env['queue.job.log.wizard'].browse(wizard_id)

        if not wizard.exists():
            return request.not_found(
                _('Log wizard with ID "%s" not found.') % wizard_id
            )

        if not wizard.job_id:
            return request.not_found(_('No job linked to this log wizard.'))

        filename = wizard.prepare_log_filename()
        content = wizard.prepare_log_content()

        return request.make_response(
            content,
            headers=[
                ('Content-Type', 'application/json'),
                ('Content-Length', str(len(content))),
                ('Content-Disposition', content_disposition(filename)),
            ]
        )

