# Copyright (c) 2026 VentorTech (https://ventor.tech)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from .post_init_hook import post_init_hook

# Re-export the symbols that VentorTech connectors import directly from
# this package, keeping the same public API as integration_queue_job.
from odoo.addons.queue_job.job import identity_exact  # noqa: F401
