import unittest
from unittest.mock import patch

from fastapi import HTTPException

import security


class AccessControlTests(unittest.TestCase):
    def test_analysis_is_open_when_no_key_is_configured(self):
        with patch.object(security, "ANALYSIS_ACCESS_KEY", ""):
            security.require_analysis_access(None)

    def test_analysis_rejects_an_invalid_configured_key(self):
        with patch.object(security, "ANALYSIS_ACCESS_KEY", "expected"):
            with self.assertRaises(HTTPException) as context:
                security.require_analysis_access("wrong")

        self.assertEqual(401, context.exception.status_code)

    def test_analysis_accepts_the_configured_key(self):
        with patch.object(security, "ANALYSIS_ACCESS_KEY", "expected"):
            security.require_analysis_access("expected")

    def test_candidate_dashboard_requires_configuration(self):
        with patch.object(security, "CANDIDATES_ADMIN_KEY", ""):
            with self.assertRaises(HTTPException) as context:
                security.require_candidates_admin(None)

        self.assertEqual(503, context.exception.status_code)

    def test_candidate_dashboard_rejects_an_invalid_key(self):
        with patch.object(security, "CANDIDATES_ADMIN_KEY", "expected"):
            with self.assertRaises(HTTPException) as context:
                security.require_candidates_admin("wrong")

        self.assertEqual(401, context.exception.status_code)
