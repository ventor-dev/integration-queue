# Copyright (c) 2026 VentorTech (https://ventor.tech)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

# Re-export all exception classes from OCA's queue_job so that connector code
# importing from integration_queue_job.exception continues to work without
# modification after the module is renamed.
from odoo.addons.queue_job.exception import (  # noqa: F401
    BaseQueueJobError,
    ChannelNotFound,
    FailedJobError,
    JobError,
    NoSuchJobError,
    RetryableJobError,
)
