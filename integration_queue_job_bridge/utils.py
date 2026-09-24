# Copyright (c) 2026 VentorTech (https://ventor.tech)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

# Re-export the inline-execution helper from OCA's queue_job so that connector
# code importing from integration_queue_job.utils continues to work without
# modification after the module is renamed.
#
# Both sides read the same context key, `queue_job__no_delay`, so a connector
# that sets it keeps running its jobs inline under either implementation.
from odoo.addons.queue_job.utils import must_run_without_delay  # noqa: F401
