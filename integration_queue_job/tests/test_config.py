# Copyright 2026
# License LGPL-3.0 or later
import os
from unittest import TestCase, mock

from odoo.addons.integration_queue_job.jobrunner import _bool, queue_job_config


class TestBoolParser(TestCase):
    def test_none_returns_default_true(self):
        self.assertTrue(_bool(None, default=True))

    def test_none_returns_default_false(self):
        self.assertFalse(_bool(None, default=False))

    def test_bool_passthrough(self):
        self.assertTrue(_bool(True, default=False))
        self.assertFalse(_bool(False, default=True))

    def test_truthy_strings(self):
        for raw in ("1", "true", "TRUE", "True", "yes", "YES", "on", " on ", "On"):
            self.assertTrue(
                _bool(raw, default=False),
                msg=f"expected {raw!r} to be truthy",
            )

    def test_falsy_strings(self):
        for raw in ("0", "false", "no", "off", "", "anything else", "2"):
            self.assertFalse(
                _bool(raw, default=True),
                msg=f"expected {raw!r} to be falsy",
            )


class TestCaptureOutputDefault(TestCase):
    def test_default_is_true_when_env_unset(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("QUEUE_JOB__CAPTURE_OUTPUT", None)
            value = _bool(os.environ.get("QUEUE_JOB__CAPTURE_OUTPUT"), default=True)
        self.assertTrue(value)

    def test_env_zero_disables(self):
        with mock.patch.dict(os.environ, {"QUEUE_JOB__CAPTURE_OUTPUT": "0"}):
            value = _bool(os.environ.get("QUEUE_JOB__CAPTURE_OUTPUT"), default=True)
        self.assertFalse(value)

    def test_capture_output_in_queue_job_config_is_bool(self):
        self.assertIsInstance(queue_job_config["capture_output"], bool)
