# Copyright 2026 VentorTech (https://ventor.tech)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import SUPERUSER_ID, api

_XMLID = 'queue_job_comp_rule'


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    # `queue_job_comp_rule` moved from security/ir.access.csv to
    # security/security.xml (wrapped in <odoo noupdate="1">) so that admins
    # can customize its domain without a module upgrade wiping it out.
    #
    # <odoo noupdate="1"> only skips re-writing a record that ALREADY exists
    # -- it never retroactively flips an existing ir.model.data row's
    # `noupdate` from False to True. Every database that installed this
    # module before the CSV->XML move has that row sitting at noupdate=False,
    # so without this one-time flip the "protection" never actually engages.
    env['ir.model.data'].search([
        ('module', '=', 'integration_queue_job'),
        ('name', '=', _XMLID),
    ]).write({'noupdate': True})
