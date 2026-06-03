# Copyright 2026
# License LGPL-3.0 or later
import logging
from contextlib import contextmanager
from unittest import mock

from odoo.tests import common

from odoo.addons.integration_queue_job.controllers.main import RunJobController
from odoo.addons.integration_queue_job.jobrunner import queue_job_config
from odoo.addons.integration_queue_job.job import Job


_logger = logging.getLogger(__name__)


@contextmanager
def _patched_partner_write(env, marker, raise_exc=False):
    """Replace res.partner.write with a wrapper that prints / logs `marker`.

    Patches the unbound method on the class so the job's `self.func` (which
    is `getattr(recordset, 'write')`) resolves to the wrapped version.
    Optionally raises ValueError after printing/logging to exercise the
    failure path.
    """
    Partner = type(env["res.partner"])
    original_write = Partner.write

    def wrapped(self, vals):
        print(marker)
        _logger.info(marker)
        if raise_exc:
            raise ValueError(f"boom: {marker}")
        return original_write(self, vals)

    with mock.patch.object(Partner, "write", wrapped):
        yield


class TestCaptureController(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({"name": "capture-fixture"})
        self.controller = RunJobController()

    def _delay_a_job(self):
        return self.partner.with_delay().write({"name": "renamed"})

    def test_success_path_persists_log(self):
        delayed = self._delay_a_job()
        job_ = Job.load(self.env, delayed.uuid)

        with _patched_partner_write(self.env, "STDOUT_SUCCESS_MARKER"):
            self.controller._try_perform_job(self.env, job_)

        self.env.flush_all()
        delayed.invalidate_recordset()

        self.assertEqual(delayed.state, "done")
        self.assertIn("STDOUT_SUCCESS_MARKER", delayed.log_text or "")

    def test_failure_path_attaches_log_to_job_for_caller(self):
        """In-memory contract: job.log_text is set before the exception escapes."""
        delayed = self._delay_a_job()
        job_ = Job.load(self.env, delayed.uuid)

        with _patched_partner_write(
            self.env, "STDOUT_BEFORE_BOOM", raise_exc=True
        ):
            with self.assertRaises(ValueError):
                self.controller._try_perform_job(self.env, job_)

        self.assertIn("STDOUT_BEFORE_BOOM", job_.log_text)

    def test_failure_path_persists_log_on_fresh_cursor(self):
        """Same path as runjob: rollback, then _persist_failed_job stores log_text."""
        delayed = self._delay_a_job()
        job_ = Job.load(self.env, delayed.uuid)

        with _patched_partner_write(
            self.env, "STDOUT_BEFORE_BOOM", raise_exc=True
        ):
            with self.assertRaises(ValueError):
                self.controller._try_perform_job(self.env, job_)

        self.env.cr.rollback()
        self.controller._persist_failed_job(
            job_,
            "(simulated traceback)",
            ValueError("boom: STDOUT_BEFORE_BOOM"),
        )
        self.env.flush_all()
        delayed.invalidate_recordset()

        self.assertEqual(delayed.state, "failed")
        self.assertIn("STDOUT_BEFORE_BOOM", delayed.log_text or "")
        self.assertIn("(simulated traceback)", delayed.exc_info or "")

    def test_capture_disabled_leaves_log_empty(self):
        delayed = self._delay_a_job()
        job_ = Job.load(self.env, delayed.uuid)

        with mock.patch.dict(queue_job_config, {"capture_output": False}), \
                _patched_partner_write(self.env, "STDOUT_SHOULD_NOT_BE_CAPTURED"):
            self.controller._try_perform_job(self.env, job_)

        self.env.flush_all()
        delayed.invalidate_recordset()

        self.assertEqual(delayed.state, "done")
        self.assertFalse(delayed.log_text)
