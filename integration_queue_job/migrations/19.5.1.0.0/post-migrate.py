# Copyright 2026 VentorTech (https://ventor.tech)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

_OBSOLETE_SECURITY_XMLIDS = (
    'access_queue_job_manager',
    'access_queue_job_function_manager',
    'access_queue_job_channel_manager',
    'access_queue_requeue_job',
    'access_queue_jobs_to_done',
    'access_queue_jobs_to_cancelled',
    'queue_job_comp_rule',
)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    # `ir.model.access` and `ir.rule` are gone from the Odoo 20 registry -- they
    # were replaced by `ir.access`. Reaching for either through `env[...]` raises
    # KeyError, and it would raise on exactly the databases this script is for:
    # the ones upgrading from 19, where the rows it looks for still exist. Only
    # the models still present are worth walking.
    legacy_models = [model for model in ('ir.model.access', 'ir.rule') if model in env]

    if not legacy_models:
        return

    IrModelData = env['ir.model.data']
    for xmlid_name in _OBSOLETE_SECURITY_XMLIDS:
        metadata = IrModelData.search([
            ('module', '=', 'integration_queue_job'),
            ('name', '=', xmlid_name),
            ('model', 'in', legacy_models),
        ])
        for row in metadata:
            record = env[row.model].browse(row.res_id).exists()
            if record:
                _logger.info(
                    'Removing obsolete %s (%s) for ir.access migration',
                    row.model,
                    xmlid_name,
                )
                record.unlink()
