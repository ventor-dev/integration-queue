# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from unittest import mock

from odoo import SUPERUSER_ID, http
from odoo.tests.common import HttpCase, tagged

from ..controllers.main import RunJobController


@tagged("-at_install", "post_install")
class TestRunJobHttp(HttpCase):
    """End-to-end tests for the ``/queue_job/runjob`` endpoint.

    ``runjob`` is declared ``auth="none"``, so ``_auth_method_none`` pins
    ``transaction.default_env`` to an env with ``uid=None``. The controller
    must repoint ``default_env`` to a superuser env, otherwise any flush
    during ``job.perform()`` that goes through
    ``Transaction.flush() -> default_env.flush_all()`` (every flushing
    ``cr.savepoint()`` and ``cr.commit()``) recomputes stored fields with an
    empty ``env.user`` and ``env.company.id == False``. Port of OCA/queue#923.
    """

    def _enqueued_job(self):
        delayed = self.env["queue.job"].with_delay()._test_job()
        job = delayed.db_record()
        job.with_context(_job_edit_sentinel=job.EDIT_SENTINEL).write(
            {"state": "enqueued"}
        )
        self.env.flush_all()
        return job

    def _capture_default_env_at_perform(self):
        """Hit ``/queue_job/runjob`` and observe ``transaction.default_env``
        at the moment the job would be performed.

        ``_try_perform_job`` is patched so the job is neither performed nor
        committed (commits are forbidden inside tests); nothing between the
        start of ``runjob`` and this call touches ``default_env``, so the
        state seen here is what ``job.perform()`` would see.
        """
        job = self._enqueued_job()
        captured = {}

        def spy(controller, env, job):
            default_env = env.transaction.default_env
            captured["uid"] = default_env.uid
            captured["company_id"] = default_env.company.id

        with mock.patch.object(RunJobController, "_try_perform_job", spy):
            # same request shape as jobrunner/runner.py (db via header)
            response = self.url_open(
                f"/queue_job/runjob?job_uuid={job.uuid}",
                headers={"X-Odoo-Database": self.env.cr.dbname},
            )
            response.raise_for_status()

        self.assertTrue(captured, "runjob did not reach _try_perform_job")
        return captured

    def test_runjob_pins_default_env_to_superuser(self):
        """Mid-job flushes must run with a real user and company."""
        captured = self._capture_default_env_at_perform()
        self.assertEqual(captured["uid"], SUPERUSER_ID)
        self.assertTrue(captured["company_id"])

    def test_runjob_without_updating_default_env_leaves_uid_none(self):
        """``update_env`` is the load-bearing call: without it the default
        env keeps the ``uid=None`` / no-company state from ``auth="none"``
        (the behavior of ``env = http.request.env(user=SUPERUSER_ID)``).
        """

        def no_op_update_env(self_, user=None, context=None, su=None):
            """Simulate a runjob that never updates the request env."""

        with mock.patch.object(http.Request, "update_env", no_op_update_env):
            captured = self._capture_default_env_at_perform()

        self.assertIsNone(captured["uid"])
        self.assertFalse(captured["company_id"])
