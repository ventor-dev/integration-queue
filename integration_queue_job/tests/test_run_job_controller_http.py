# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from unittest import mock

from odoo import SUPERUSER_ID
from odoo.tests.common import HttpCase, tagged

from ..controllers.main import RunJobController


@tagged("-at_install", "post_install")
class TestRunJobHttp(HttpCase):
    """End-to-end tests for the ``/queue_job/runjob`` endpoint.

    ``runjob`` is declared ``auth="none"``, so ``_auth_method_none`` pins
    ``transaction.default_env`` to an env with ``uid=None``. The controller
    must additionally repoint ``default_env`` to a superuser env, otherwise
    any flush during ``job.perform()`` that goes through
    ``Transaction.flush() -> default_env.flush_all()`` recomputes stored
    fields with ``self.env.user`` as an empty recordset.
    See https://github.com/OCA/queue/pull/923
    """

    def test_runjob_pins_default_env_to_superuser(self):
        job_ = self.env["res.partner"].with_delay().create({"name": "test"})
        job_.set_enqueued()
        job_.store()
        self.env.flush_all()

        captured = {}

        def spy(self_, env, job):
            # Replaces the real execution, which commits (forbidden in tests)
            captured["job_uuid"] = job.uuid
            captured["default_env_uid"] = env.transaction.default_env.uid

        with mock.patch.object(RunJobController, "_try_perform_job", spy):
            response = self.url_open(
                f"/queue_job/runjob?db={self.env.cr.dbname}&job_uuid={job_.uuid}"
            )
            response.raise_for_status()

        self.assertEqual(captured.get("job_uuid"), job_.uuid)
        self.assertEqual(captured.get("default_env_uid"), SUPERUSER_ID)
