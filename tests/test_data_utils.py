import unittest

import data_utils


class TestDataUtils(unittest.TestCase):
    def test_parse_user_selection_mixed_formats(self):
        result = data_utils.parseUserSelection("1,3-5,2,5,99", 6)
        self.assertEqual(result, [0, 2, 3, 4, 1])

    def test_parse_user_selection_ignores_invalid_tokens(self):
        result = data_utils.parseUserSelection("a,-1,2-foo,4", 4)
        self.assertEqual(result, [3])

    def test_clean_card_lines_cloze_validation_and_dedup(self):
        content = "\n".join([
            "The {{c1::mitochondria}} is the powerhouse.",
            "The {{c1::mitochondria}} is the powerhouse.",
            "No cloze markers here",
        ])
        lines, stats = data_utils.cleanCardLines(content, "Cloze")
        self.assertEqual(len(lines), 1)
        self.assertEqual(stats["valid"], 1)
        self.assertEqual(stats["duplicates"], 1)
        self.assertEqual(stats["invalid"], 1)

    def test_clean_card_lines_basic_validation_and_dedup(self):
        content = "\n".join([
            "Question?\tAnswer",
            "Question?\tAnswer",
            "No tab separator",
            "Front only\t",
        ])
        lines, stats = data_utils.cleanCardLines(content, "Basic")
        self.assertEqual(len(lines), 1)
        self.assertEqual(stats["valid"], 1)
        self.assertEqual(stats["duplicates"], 1)
        self.assertEqual(stats["invalid"], 2)

    def test_chunk_text_preserves_paragraph_boundaries(self):
        text = "Heading A\n\nThis is paragraph one with several words.\n\nThis is paragraph two."
        chunks = data_utils.chunkText(text, maxWords=6)
        self.assertTrue(len(chunks) >= 2)
        self.assertIn("Heading A", chunks[0])

    def test_chunk_text_empty_input(self):
        chunks = data_utils.chunkText("", maxWords=50)
        self.assertEqual(chunks, [""])


if __name__ == "__main__":
    unittest.main()
