import unittest

from validator import OutputValidator


class OutputValidatorTests(unittest.TestCase):
    def setUp(self):
        self.validator = OutputValidator()

    def test_valid_agent_output_passes(self):
        graph = {
            field: 7
            for field in self.validator.REQUIRED_GRAPH_FIELDS
        }
        output = {
            "dashboard_view": {
                "status": "מתאים מאוד",
                "match_percent": 7,
            },
            "interview_details": {"graph": graph},
        }

        self.assertEqual([], self.validator.validate(output))

    def test_out_of_range_scores_are_reported(self):
        output = {
            "dashboard_view": {
                "status": "לא ידוע",
                "match_percent": 12,
            },
            "interview_details": {"graph": {"communication": -1}},
        }

        errors = self.validator.validate(output)

        self.assertTrue(any("סטטוס לא חוקי" in error for error in errors))
        self.assertTrue(any("match_percent" in error for error in errors))
        self.assertTrue(any("חורג מהטווח" in error for error in errors))
