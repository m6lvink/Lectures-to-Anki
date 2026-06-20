import os
import tempfile
import unittest

import main


class TestMain(unittest.TestCase):
    def test_get_valid_files_skips_directories_and_sorts_results(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.mkdir(os.path.join(tmpdir, "nested.pdf"))
            with open(os.path.join(tmpdir, "b.txt"), "w", encoding="utf-8") as handle:
                handle.write("b")
            with open(os.path.join(tmpdir, "a.PDF"), "w", encoding="utf-8") as handle:
                handle.write("a")
            with open(os.path.join(tmpdir, "ignore.md"), "w", encoding="utf-8") as handle:
                handle.write("x")

            self.assertEqual(main.getValidFiles(tmpdir), ["a.PDF", "b.txt"])


if __name__ == "__main__":
    unittest.main()
