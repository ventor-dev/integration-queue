# Copyright 2026
# License LGPL-3.0 or later
from odoo.tests import common

from odoo.addons.integration_queue_job.job import Job


class TestJobLogTextRoundTrip(common.TransactionCase):
    """Verify Job.log_text survives store() and _load_from_db_record()."""

    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({"name": "log-text-fixture"})

    def test_log_text_defaults_to_empty_string(self):
        delayed = self.partner.with_delay().write({"name": "renamed"})
        job_ = Job.load(self.env, delayed.uuid)
        self.assertEqual(job_.log_text, "")

    def test_log_text_round_trip(self):
        delayed = self.partner.with_delay().write({"name": "renamed"})
        job_ = Job.load(self.env, delayed.uuid)

        job_.log_text = "captured stdout line 1\nlogger line 2\n"
        job_.store()
        self.env.flush_all()

        db_record = delayed.db_record()
        db_record.invalidate_recordset()
        self.assertEqual(
            db_record.log_text, "captured stdout line 1\nlogger line 2\n"
        )

        reloaded = Job.load(self.env, delayed.uuid)
        self.assertEqual(
            reloaded.log_text, "captured stdout line 1\nlogger line 2\n"
        )

    def test_empty_log_text_stores_as_false(self):
        """Empty string must not leak as the literal '' in DB; mirror `result`."""
        delayed = self.partner.with_delay().write({"name": "renamed"})
        job_ = Job.load(self.env, delayed.uuid)
        job_.log_text = ""
        job_.store()
        self.env.flush_all()

        db_record = delayed.db_record()
        db_record.invalidate_recordset()
        self.assertFalse(db_record.log_text)
