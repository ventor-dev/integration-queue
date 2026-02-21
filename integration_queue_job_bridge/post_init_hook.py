# Copyright (c) 2026 VentorTech (https://ventor.tech)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import logging

_logger = logging.getLogger(__name__)

# XML IDs that VentorTech connector modules reference with the
# "integration_queue_job" module prefix.  We create ir.model.data aliases so
# that those references resolve to the records actually owned by OCA's
# queue_job module.
_ALIASES = [
    # (alias_name, model, source_xmlid)
    ('channel_root', 'queue.job.channel', 'queue_job.channel_root'),
    ('group_queue_job_manager', 'res.groups', 'queue_job.group_queue_job_manager'),
]


def post_init_hook(env):
    """Create XML-ID aliases under the 'integration_queue_job' namespace.

    VentorTech connectors reference records such as
    ``integration_queue_job.channel_root`` and
    ``integration_queue_job.group_queue_job_manager`` in their XML data files
    and view definitions.  When this bridge module is installed (renamed to
    ``integration_queue_job``) those aliases are created here so every
    existing reference continues to resolve without any changes to the
    connector modules themselves.
    """
    IrModelData = env['ir.model.data']

    for name, model, source_xmlid in _ALIASES:
        record = env.ref(source_xmlid, raise_if_not_found=False)
        if not record:
            _logger.warning(
                'integration_queue_job bridge: source record %s not found, '
                'skipping alias creation for %s.',
                source_xmlid, name,
            )
            continue

        existing = IrModelData.search([
            ('module', '=', 'integration_queue_job'),
            ('name', '=', name),
        ])
        if existing:
            _logger.debug(
                'integration_queue_job bridge: alias %s already exists, skipping.',
                name,
            )
            continue

        IrModelData.create({
            'name': name,
            'module': 'integration_queue_job',
            'model': model,
            'res_id': record.id,
            'noupdate': True,
        })
        _logger.info(
            'integration_queue_job bridge: created alias integration_queue_job.%s '
            '-> %s (id=%s).',
            name, source_xmlid, record.id,
        )
