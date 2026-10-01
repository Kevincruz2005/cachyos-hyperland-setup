# SPDX-License-Identifier: MIT
"""Publication contract checks; no GitHub/network mutations."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PublicationTests(unittest.TestCase):
    def test_owner_visibility_respected_not_changed(self):
        source = (ROOT / "tools/publish.sh").read_text()
        self.assertIn('"$repo_name true") visibility=private', source)
        self.assertIn('"$repo_name false") visibility=public', source)
        for mutation in ("gh repo edit", "gh repo create", "--visibility", "push --force"):
            self.assertNotIn(mutation, source)


if __name__ == "__main__":
    unittest.main()
