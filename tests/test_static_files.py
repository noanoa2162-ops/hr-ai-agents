import unittest

from main import STATIC_DIR, spa_catchall


class StaticFileSafetyTests(unittest.IsolatedAsyncioTestCase):
    async def test_path_traversal_falls_back_to_spa_index(self):
        response = await spa_catchall("../pyproject.toml")

        self.assertEqual(
            (STATIC_DIR / "index.html").resolve(),
            response.path.resolve(),
        )
