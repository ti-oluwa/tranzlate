import unittest
from translators.server import TranslatorsServer, Tse
from io import IOBase
from bs4 import BeautifulSoup

import tranzlate
from tranzlate.exceptions import TranslationError, UnsupportedLanguageError


class TestTranslator(unittest.TestCase):
    """Test case for the Translator class."""
    example_text = "Yoruba is a language spoken in West Africa, most prominently Southwestern Nigeria."

    def setUp(self):
        self.translator = tranzlate.Translator()
    
    def test_engines(self):
        engines = self.translator.engines()
        self.assertIsInstance(engines, list)
        self.assertTrue(len(engines) > 0)

    def test_invalid_engine(self):
        with self.assertRaises(ValueError):
            tranzlate.Translator("invalid_engine")

    def test_detect_language(self):
        result = self.translator.detect_language(self.example_text)
        self.assertIsInstance(result, dict)
        self.assertTrue(len(result) == 2)
        language = result.get("language")
        confidence = result.get("score")
        self.assertIsInstance(language, str)
        self.assertEqual(language, "en")
        self.assertIsInstance(confidence, float)
        self.assertTrue(confidence > 0.0 and confidence <= 1.0)
        with self.assertRaises(TypeError):
            self.translator.detect_language(None)

    def test_detect_language_with_empty_text(self):
        with self.assertRaises(ValueError):
            self.translator.detect_language("")

    def test_translate_on_auto(self):
        with self.assertRaises(TypeError):
            self.translator.translate(None)
        with self.assertRaises(ValueError):
            self.translator.translate("")
        translation = self.translator.translate(self.example_text, target_lang="yo")
        self.assertIsInstance(translation, str)
        self.assertNotEqual(translation, self.example_text)

    def test_translate_with_source_and_target_language(self):
        with self.assertRaises(TypeError):
            self.translator.translate(self.example_text, None, "yo")
        with self.assertRaises(TypeError):
            self.translator.translate(self.example_text, "en", 1)
        translation = self.translator.translate(self.example_text, "en", "yo")
        self.assertIsInstance(translation, str)
        self.assertNotEqual(translation, self.example_text)

    def test_translate_with_empty_source_language(self):
        with self.assertRaises(ValueError):
            self.translator.translate(self.example_text, "", "yo")

    def test_translate_with_empty_target_language(self):
        with self.assertRaises(ValueError):
            self.translator.translate(self.example_text, "en", "")

    def test_translate_with_unsupported_source_language(self):
        with self.assertRaises(UnsupportedLanguageError):
            self.translator.translate(self.example_text, "en-xy", "yo")

    def test_translate_with_unsupported_target_language(self):
        with self.assertRaises(UnsupportedLanguageError):
            self.translator.translate(self.example_text, "en", "yo-xy")

    def test_translate_with_the_same_source_and_target_language(self):
        with self.assertRaises(TranslationError):
            self.translator.translate(self.example_text, "en", "en")

    def test_is_supported_language(self):
        self.assertTrue(self.translator.is_supported_language("en"))
        self.assertFalse(self.translator.is_supported_language("en-xy"))
        with self.assertRaises(TypeError):
            self.translator.is_supported_language(None)
        with self.assertRaises(ValueError):
            self.translator.is_supported_language("")
        
    def test_get_supported_target_languages(self):
        self.assertIsInstance(self.translator.get_supported_target_languages("en"), list)
        self.assertTrue(len(self.translator.get_supported_target_languages("en")) > 0)
        self.assertIsInstance(self.translator.get_supported_target_languages("en-xy"), list)
        self.assertTrue(len(self.translator.get_supported_target_languages("en-xy")) == 0)
        with self.assertRaises(TypeError):
            self.translator.get_supported_target_languages(None)
        with self.assertRaises(ValueError):
            self.translator.get_supported_target_languages("")

    def test_properties(self):
        self.assertIsInstance(self.translator.server, TranslatorsServer)
        self.assertIsInstance(self.translator.engine, Tse)
        self.assertTrue(callable(self.translator.engine_api))
        self.assertIsInstance(self.translator.input_limit, int)
        self.assertIsInstance(self.translator.language_map, dict)
        self.assertIsInstance(self.translator.supported_languages, list)

    def test_translate_text(self):
        translation = self.translator.translate_text(self.example_text*1000, "en", "yo")
        self.assertIsInstance(translation, str)

    def test_translate_file(self):
        translated_file = self.translator.translate_file("tests/fixtures/test_file.txt", "en", "yo")
        self.assertIsInstance(translated_file, IOBase)

    def test_translate_markup(self):
        translated_markup = self.translator.translate_markup("<h1>Test</h1>", "en", "yo")
        self.assertIsInstance(translated_markup, str)
        translated_markup_bytes = self.translator.translate_markup(b"<h1>Test</h1>", "en", "yo")
        self.assertIsInstance(translated_markup_bytes, bytes)

    def test_translate_soup(self):
        soup = BeautifulSoup("<h1>Test</h1>", "html.parser")
        translated_beautifulsoup = self.translator.translate_soup(soup, "en", "yo")
        self.assertIsInstance(translated_beautifulsoup, BeautifulSoup)
        with self.assertRaises(TypeError):
            self.translator.translate_soup(None, "en", "yo")

 
        
if "__name__" == "__main__":
    unittest.main()

# RUN WITH 'python -m unittest discover tests "test_*.py"' from project directory
