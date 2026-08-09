import unittest

from pydantic import ValidationError

from models import CandidateRequest


class CandidateRequestTests(unittest.TestCase):
    def test_names_are_trimmed(self):
        candidate = CandidateRequest(
            first_name="  Noa ",
            last_name=" Binet  ",
            email=" noa@example.com ",
        )

        self.assertEqual("Noa", candidate.first_name)
        self.assertEqual("Binet", candidate.last_name)
        self.assertEqual("noa@example.com", candidate.email)

    def test_blank_name_is_rejected(self):
        with self.assertRaises(ValidationError):
            CandidateRequest(first_name="   ", last_name="Binet")
