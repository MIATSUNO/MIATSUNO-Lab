import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import lookay


class LookayTests(unittest.TestCase):
    def test_parse_veristante_first_book(self):
        source = r'''<script>var FIRST_BOOK={id:"book-1",title:"Noite de cobre",author:"Kaye Bird",synopsis:"Uma história em duas partes.\nCom estrelas."};var books=[FIRST_BOOK];</script>'''
        works = lookay.parse_catalog(source)
        self.assertEqual(len(works), 1)
        self.assertEqual(works[0]["title"], "Noite de cobre")
        self.assertEqual(works[0]["author"], "Kaye Bird")
        self.assertEqual(works[0]["synopsis"], "Uma história em duas partes.\nCom estrelas.")

    def test_parse_catalog_ignores_incomplete_object(self):
        source = r'''var FIRST_BOOK={title:"Só título"};'''
        self.assertEqual(lookay.parse_catalog(source), [])

    def test_canonical_url_normalizes_and_removes_fragment(self):
        self.assertEqual(
            lookay.canonical_url("HTTPS://Example.COM/page?q=1#section"),
            "https://example.com/page?q=1",
        )

    def test_canonical_url_rejects_credentials_and_non_http(self):
        with self.assertRaises(ValueError):
            lookay.canonical_url("https://user:secret@example.com/")
        with self.assertRaises(ValueError):
            lookay.canonical_url("file:///etc/passwd")

    def test_count_words(self):
        self.assertEqual(lookay.count_words("  uma   obra\ncom três palavras "), 5)
        self.assertEqual(lookay.count_words("  "), 0)

    def test_write_creates_importable_kayepad_book_json(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "obra.json"
            args = Namespace(output=str(output))
            with patch.object(lookay, "get_session", return_value={"token": "test-token"}), \
                 patch.object(lookay, "api_json", return_value={"user": {"username": "kaye", "display_name": "Kaye Bird"}}), \
                 patch.object(lookay, "prompt_required", side_effect=["Noite de cobre", "Kaye Bird"]), \
                 patch.object(lookay, "prompt_optional", side_effect=["Sinopse teste", ""]), \
                 patch("builtins.input", side_effect=["Abertura", ""]), \
                 patch.object(lookay, "editor_text", return_value="Texto do capítulo"):
                lookay.command_escrever(args)
            book = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(book["type"], "BOOK")
        self.assertEqual(book["title"], "Noite de cobre")
        self.assertEqual(book["author"], "Kaye Bird")
        self.assertEqual(book["synopsis"], "Sinopse teste")
        self.assertEqual(book["chapters"][0]["title"], "Abertura")
        self.assertEqual(book["chapters"][0]["content"], "Texto do capítulo")
        self.assertEqual(book["chapters"][0]["wordCount"], 3)
        self.assertEqual(book["chapters"][0]["history"], [])


if __name__ == "__main__":
    unittest.main()
