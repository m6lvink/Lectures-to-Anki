import os
import sys
import tempfile
import types
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

sys.modules.setdefault("file_parser", types.SimpleNamespace(
    extractPdfText=lambda path: "",
    extractPptxText=lambda path: "",
    extractTxtText=lambda path: "",
))
sys.modules.setdefault("api_handler", types.SimpleNamespace(
    estimateTokensFromText=lambda text: (0, 0),
    estimateCost=lambda total_in, total_out, thinking: 0.0,
    generateAnkiCards=lambda chunk, card_type, use_thinking, client: (True, ""),
))
sys.modules.setdefault("progress_bar", types.SimpleNamespace(
    startProgressBar=lambda total: (lambda current: None, types.SimpleNamespace(set=lambda: None), types.SimpleNamespace(join=lambda: None)),
))
sys.modules.setdefault("ui_utils", types.SimpleNamespace(
    selectCardType=lambda: "Cloze",
    selectThinkingMode=lambda: False,
    selectOutputMode=lambda: "separate",
))
sys.modules.setdefault("config_utils", types.SimpleNamespace(loadApiKey=lambda: None))

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
