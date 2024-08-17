"""
Translate text, markup content, BeautifulSoup objects and files using the `translators` package.
"""

import functools
import sys
from typing import Callable, Dict, Generator, List, Optional, Tuple, IO, Any, Union
import time
import random
from translators.server import TranslatorsServer, tss, Tse
import simple_file_handler as sfh
import itertools
from asgiref.sync import sync_to_async
import asyncio
import textwrap

from .exceptions import TranslationError, UnsupportedLanguageError


__all__ = ["Translator", "add_translatable_html_tag"]

_translatable_tags = (
    "h1",
    "u",
    "s",
    "abbr",
    "del",
    "pre",
    "h5",
    "sub",
    "kbd",
    "li",
    "dd",
    "textarea",
    "dt",
    "input",
    "em",
    "sup",
    "label",
    "button",
    "h6",
    "title",
    "dfn",
    "th",
    "acronym",
    "cite",
    "samp",
    "td",
    "p",
    "ins",
    "big",
    "caption",
    "bdo",
    "var",
    "h3",
    "tt",
    "address",
    "h4",
    "legend",
    "i",
    "small",
    "b",
    "q",
    "option",
    "code",
    "h2",
    "a",
    "strong",
    "span",
)


def add_translatable_html_tag(tag: str) -> None:
    """Add a new HTML tag name to the global list of translatable HTML elements"""
    global _translatable_tags
    if tag in _translatable_tags:
        return
    _translatable_tags = (tag, *_translatable_tags)
    return None


class Translator(object):
    """
    Wraps around the `TranslatorServer` class from the `translators` package by UlionTse,
    providing a simpler interface for translation.

    Read more about the `translators` package here:
    https://pypi.org/project/translators/
    """

    _server = tss

    def __init__(self, engine: str = "bing"):
        """
        Create a Translator instance.

        :param engine (str): Name of translation engine to be used. Defaults to "bing"
        as it has been tested to be the most reliable.

        #### Call `Translator.engines` to get a list of supported translation engines.
        """
        if engine not in type(self).engines():
            raise ValueError(f"Invalid translation engine: {engine}")
        self.engine_name = engine
        return None

    @property
    def server(self) -> TranslatorsServer:
        """The translation server used by the Translator instance"""
        if not isinstance(self._server, TranslatorsServer):
            raise TypeError("Invalid type for `_server`")
        return self._server

    @property
    def engine(self) -> Tse:
        """The translation engine (Tse) used by the Translator instance"""
        return getattr(self.server, f"_{self.engine_name}")

    @property
    def engine_api(self) -> Callable:
        """API used by the translation engine to carryout translations"""
        return getattr(self.server, f"{self.engine_name}")

    @property
    def input_limit(self) -> Optional[int]:
        """
        The maximum number of characters that can be translated at once.
        This is dependent on the translation engine being used.
        """
        try:
            return self.engine.input_limit
        except Exception:
            return None

    @functools.cached_property
    def language_map(self) -> Dict:
        """
        A dictionary containing a mapping of source language codes
        to a list of target language codes that the translation engine can translate to.
        """
        try:
            return self.server.get_languages(self.engine_name)
        except BaseException:
            return {}

    @property
    def supported_languages(self) -> List:
        """
        Returns a list of language codes for source
        languages supported by the translator's engine.
        """
        return sorted(self.language_map.keys())

    @classmethod
    def engines(cls) -> List[str]:
        """Returns a list of supported translation engines"""
        return cls._server.translators_pool

    @classmethod
    def detect_language(cls, text: str) -> Dict:
        """
        Detects the language of the specified text.

        :param text (str): The text to detect the language of.
        :return: A dictionary containing the language code and confidence score.

        Bing is the preferred translation engine for this method as it works well for
        this purpose. However, it is not guaranteed to work always.

        Usage Example:
        ```python
        import tranzlate

        text = "Yoruba is a language spoken in West Africa, most prominently Southwestern Nigeria."
        language = tranzlate.Translator.detect_language(text)
        print(language)

        # Output: {'language': 'en', 'score': 1.0}
        ```
        """
        if not isinstance(text, str):
            raise TypeError("Invalid type for `text`")
        if not text:
            raise ValueError("`text` cannot be empty")
        try:
            result: Dict[str, Any] = cls._server.translate_text(
                query_text=text, translator="bing", is_detail_result=True
            )
            return result.get("detectedLanguage", {})
        except Exception as exc:
            sys.stderr.write(f"Error detecting language: {exc}\n")
            return {}

    def supports_language(self, lang_code: str) -> bool:
        """
        Check if the source language with the specified
        language code is supported by the translator's engine.

        :param lang_code (str): The language code for the language to check.
        :return: True if the language is supported, False otherwise.
        """
        if not isinstance(lang_code, str):
            raise TypeError("Invalid type for `lang_code`")

        lang_code = lang_code.strip().lower()
        return lang_code in self.supported_languages

    def get_supported_target_languages(self, src_lang: str) -> List:
        """
        Returns a list of language codes for target languages
        supported by the translation engine for the specified source language.

        :param src_lang (str): The source language for which to get supported target languages.
        """
        if not isinstance(src_lang, str):
            raise TypeError("Invalid type for `src_lang`")

        return self.language_map.get(src_lang, [])

    def supports_pair(self, src_lang: str, target_lang: str) -> bool:
        """
        Check if the source language and target language
        pair is supported by the translation engine.

        :param src_lang (str): The source language.
        :param target_lang (str): The target language.
        :return: True if the pair is supported, False otherwise.
        """
        return (
            src_lang != target_lang
            and target_lang in self.get_supported_target_languages(src_lang)
        )

    def check_languages(self, src_lang: str, target_lang: str) -> Tuple[str, str]:
        """
        Performs necessary 'compatibility' checks on the source and target language.
        Raises any of  `TypeError`, `ValueError` or `UnsupportedLanguageError`, if there is any issue
        """
        if not isinstance(src_lang, str):
            raise TypeError("Invalid type for `src_lang`")
        if not isinstance(target_lang, str):
            raise TypeError("Invalid type for `target_lang`")
        if not src_lang:
            raise ValueError("A source language must be provided")
        if not target_lang:
            raise ValueError("A target language must be provided")

        if src_lang == target_lang:
            raise ValueError("Source language and target language cannot be the same.")

        if src_lang != "auto" and not self.supports_language(src_lang):
            raise UnsupportedLanguageError(
                message=f"Unsupported source language using translation engine, '{self.engine_name}'",
                code=src_lang,
                engine=self.engine_name,
                code_type="source",
            )
        if (
            src_lang != "auto"
            and target_lang not in self.get_supported_target_languages(src_lang)
        ):
            raise UnsupportedLanguageError(
                message=f"Unsupported target language for source language, '{src_lang}', using translation engine, '{self.engine_name}'",
                code=target_lang,
                engine=self.engine_name,
                code_type="target",
            )
        return src_lang, target_lang

    def translate(
        self,
        content: Union[str, bytes],
        src_lang: str = "auto",
        target_lang: str = "en",
        *,
        is_markup: bool = False,
        encoding: str = "utf-8",
        **kwargs,
    ) -> Union[str, bytes]:
        """
        Translate content from source language to target language.

        :param content (str | bytes): Content to be translated
        :param src_lang (str, optional): Source language. Defaults to "auto".
        It is advisable to provide a source language to get more accurate translations.
        :param target_lang (str, optional): Target language. Defaults to "en".
        :param is_markup (bool, optional): Whether `content` is markup. Defaults to False.
        :param encoding (str, optional): The encoding of the content (for bytes content only). Defaults to "utf-8".
        :param **kwargs: Keyword arguments to be passed to the translation server.
            :kwarg timeout: float, default None.
            :kwarg proxies: dict, default None.
        :return: Translated content.

        Usage Example:
        ```python
        import tranzlate

        bing = tranzlate.Translator("bing")
        text = "Yoruba is a language spoken in West Africa, most prominently Southwestern Nigeria."
        translation = bing.translate(text, "en", "yo")
        print(translation)

        # Output: "Yorùbá jẹ́ èdè tí ó ń ṣe àwọn èdè ní ìlà oòrùn Áfríkà, tí ó wà ní orílẹ̀-èdè Gúúsù Áfríkà."
        """
        is_bytes = isinstance(content, bytes)
        if is_markup:
            return self.translate_markup(
                markup=content,
                src_lang=src_lang,
                target_lang=target_lang,
                encoding=encoding,
                **kwargs,
            )

        translation = self.translate_text(
            text=content.decode(encoding) if is_bytes else content,
            src_lang=src_lang,
            target_lang=target_lang,
            **kwargs,
        )
        return translation.encode(encoding) if is_bytes else translation

    def translate_text(
        self, text: str, src_lang: str = "auto", target_lang: str = "en", **kwargs
    ) -> str:
        """
        Translate text from `src_lang` to `target_lang`.

        :param text (str): Text to be translated
        :param src_lang (str, optional): Source language. Defaults to "auto".
        It is advisable to provide a source language to get more accurate translations.
        :param target_lang (str, optional): Target language. Defaults to "en".
        :param **kwargs: Keyword arguments to be passed to the translation server.
            :kwarg timeout: float, default None.
            :kwarg proxies: dict, default None.
        :return: Translated text.
        """
        if not isinstance(text, str):
            raise TypeError("Invalid type for `text`")
        if not text:
            return text

        src_lang, target_lang = self.check_languages(src_lang, target_lang)
        kwargs.pop("is_detail_result", None)
        kwds = {**kwargs, "if_ignore_empty_query": True}

        def translate(text: str) -> str:
            """Translate text using translation engine"""
            return self.engine_api(
                query_text=text, to_language=target_lang, from_language=src_lang, **kwds
            )

        async_translate = sync_to_async(translate)

        def translate_in_chunks(text: str, chunksize: int) -> str:
            tasks = list(map(async_translate, chunks(text, chunksize)))

            async def execute_tasks() -> List[str]:
                return await asyncio.gather(*tasks)

            translated_chunks = asyncio.run(execute_tasks())
            return "".join(translated_chunks)

        try:
            input_limit = self.input_limit or 1000
            if len(text) > input_limit:
                return translate_in_chunks(text, input_limit)
            return translate(text)
        except Exception as exc:
            raise TranslationError(str(exc)) from exc

    def translate_file(
        self, filepath: str, src_lang: str = "auto", target_lang: str = "en", **kwargs
    ) -> IO:
        """
        Translates file from `src_lang` to `target_lang`.
        This method replaces the file content the translation.
        You may need to translate a duplicate if you do not want to modify
        the original file.

        Supported file types include: .txt, .csv, .doc, .docx, .pdf, .md..., mostly files with text content.

        :param filepath (str): path to the file to be translated. If the file is empty, it is returned as is.
        :param src_lang (str, optional): Source language. Defaults to "auto".
        It is advisable to provide a source language to get more accurate translations.
        :param target_lang (str, optional): Target language. Defaults to "en".
        :param **kwargs: Keyword arguments to be passed to the translation server.
            :kwarg timeout: float, default None.
            :kwarg proxies: dict, default None.
        :return: Translated file.
        """
        src_lang, target_lang = self.check_languages(src_lang, target_lang)
        kwds = {"if_ignore_empty_query": True}
        kwargs.pop("is_detail_result", None)
        kwds.update(kwargs)

        try:
            with sfh.FileHandler(
                filepath, exists_ok=True, not_found_ok=False
            ) as file_handler:
                content = file_handler.file_content
                if not content:
                    return file_handler.file

                if file_handler.filetype in ("xhtml", "htm", "shtml", "html", "xml"):
                    translation = self.translate_markup(
                        content, src_lang, target_lang, **kwds
                    )
                else:
                    translation = self.translate_text(
                        content, src_lang, target_lang, **kwds
                    )

                file_handler.write_to_file(translation, write_mode="w+")
                return file_handler.file
        except Exception as exc:
            raise TranslationError("File cannot be translated.") from exc

    def translate_tag(
        self, tag, src_lang: str = "auto", target_lang: str = "en", **kwargs
    ):
        """
        Translates the text of a `bs4.element.Tag` object 'in place'.

        :param element (`bs4.element.Tag`): The tag whose text content is to be translated.
        :param src_lang (str, optional): Source language. Defaults to "auto".
        :param target_lang (str, optional): Target language. Defaults to "en".
        :return: The translated `bs4.element.Tag`
        """
        from bs4.element import Tag

        if not isinstance(tag, Tag):
            raise TypeError("Invalid type for `tag`")

        if not (tag.string and tag.string.strip()):
            return tag

        translation = self.translate_text(
            text=tag.string, src_lang=src_lang, target_lang=target_lang, **kwargs
        )
        tag.string.replace_with(translation)
        return tag

    def translate_soup(
        self, soup, src_lang: str = "auto", target_lang: str = "en", **kwargs
    ):
        """
        Translates the text of a `BeautifulSoup` object.

        :param soup (`BeautifulSoup`): The `BeautifulSoup` object whose text is to be translated.
        :param src_lang (str, optional): Source language. Defaults to "auto".
        It is advisable to provide a source language to get more accurate translations.
        :param target_lang (str, optional): The target language for translation. Defaults to "en".
        :return: The translated `BeautifulSoup` object.
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError(
                '"bs4" is required to translate soup. Run `pip install beautifulsoup4` in your terminal to install it'
            )

        if not isinstance(soup, BeautifulSoup):
            raise TypeError("Invalid type for `soup`")

        src_lang, target_lang = self.check_languages(src_lang, target_lang)
        tags = soup.find_all(_translatable_tags)
        tags = [tag for tag in tags if tag.string]

        def safe_translate_tag(*args, **kwargs):
            """Ignores any exception that occurs during translation"""
            try:
                return self.translate_tag(*args, **kwargs)
            except BaseException:
                pass

        kwds = {**kwargs, "src_lang": src_lang, "target_lang": target_lang}
        translate_tag = functools.partial(safe_translate_tag, **kwds)
        async_translate_tag = sync_to_async(translate_tag)
        # Translate tags in batches to avoid making excessive requests to translation server at once
        for batch in itertools.batched(tags, 50):
            tasks = list(map(async_translate_tag, batch))

            async def execute_tasks() -> List[str]:
                return await asyncio.gather(*tasks)

            asyncio.run(execute_tasks())
            time.sleep(random.randint(1, 3))
        return soup

    def translate_markup(
        self,
        markup: Union[str, bytes],
        src_lang: str = "auto",
        target_lang: str = "en",
        *,
        markup_parser: str = "lxml",
        encoding: str = "utf-8",
        **kwargs,
    ) -> Union[str, bytes]:
        """
        Translates markup (html, xml, etc.)

        :param markup (str | bytes): markup content to be translated
        :param src_lang (str, optional): Source language. Defaults to "auto".
        It is advisable to provide a source language to get more accurate translations.
        :param target_lang (str, optional): Target language. Defaults to "en".
        :param markup_parser (str, optional): The (beautifulsoup) markup parser to use. Defaults to "lxml".
        :param encoding (str, optional): The encoding of the markup (for bytes markup only). Defaults to "utf-8".
        :param kwargs: Keyword arguments to be passed to the translation server.
            :kwarg timeout: float, default None.
            :kwarg proxies: dict, default None.
        :return: Translated markup.
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError(
                '"bs4" is required to translate soup. Run `pip install beautifulsoup4` in your terminal to install it'
            )

        if not isinstance(markup, (str, bytes)):
            raise TypeError("Invalid type for `markup`")
        if not markup:
            return markup

        is_bytes = isinstance(markup, bytes)
        kwargs.pop("is_detail_result", None)
        soup = BeautifulSoup(
            markup, markup_parser, from_encoding=encoding if is_bytes else None
        )
        translated_markup = self.translate_soup(
            soup, src_lang, target_lang, **kwargs
        ).prettify()
        return translated_markup.encode(encoding) if is_bytes else translated_markup


def chunks(text: str, size: int) -> Generator[str, Any, None]:
    """Yields a chunk of the text on each iteration, respecting word boundaries."""
    wrapper = textwrap.TextWrapper(
        width=size, break_long_words=False, replace_whitespace=False
    )
    for chunk in wrapper.wrap(text):
        yield chunk
