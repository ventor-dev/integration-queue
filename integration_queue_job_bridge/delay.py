# Copyright (c) 2026 VentorTech (https://ventor.tech)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

# Re-export the delayable API from OCA's queue_job so that connector code
# importing from integration_queue_job.delay continues to work without
# modification after the module is renamed.
#
# `chain` and `group` are what the connectors call directly; the classes below
# are re-exported because the fork exposes them at the same path and code that
# builds graphs by hand reaches for them.
from odoo.addons.queue_job.delay import (  # noqa: F401
    Delayable,
    DelayableChain,
    DelayableGraph,
    DelayableGroup,
    DelayableRecordset,
    Graph,
    chain,
    group,
)
