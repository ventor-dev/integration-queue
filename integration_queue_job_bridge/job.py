# Copyright (c) 2026 VentorTech (https://ventor.tech)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

# Re-export the Job class and related symbols from OCA's queue_job so that
# connector code importing from integration_queue_job.job continues to work
# without modification after the module is renamed.
from odoo.addons.queue_job.job import (  # noqa: F401
    Job,
    identity_exact,
    CANCELLED,
    DEFAULT_MAX_RETRIES,
    DEFAULT_PRIORITY,
    DONE,
    ENQUEUED,
    FAILED,
    PENDING,
    RETRY_INTERVAL,
    STARTED,
    WAIT_DEPENDENCIES,
)
