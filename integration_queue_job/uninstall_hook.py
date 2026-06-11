# Copyright 2025 VentorTech OU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import logging

_logger = logging.getLogger(__name__)


def uninstall_hook(env):
    _logger.info("Drop register_queue_process_func postgres function")
    env.cr.execute("DROP FUNCTION IF EXISTS register_queue_process_func;")
    _logger.info("Drop active_integration_queue_job_runner table")
    env.cr.execute("DROP TABLE IF EXISTS active_integration_queue_job_runner;")
