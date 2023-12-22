"""
Translates text, markup content, BeautifulSoup objects and files using the `translators` package.
"""

import functools
import sys
from typing import Dict, List, Tuple
from array import array
import time
import copy
import random
from bs4 import BeautifulSoup
from bs4.element import Tag
from concurrent.futures import ThreadPoolExecutor
try:
    import translators as ts
    from translators.server import TranslatorsServer, tss, Tse
except Exception as exc:
    raise ConnectionError(f"Could not import `translators` module: {exc}")

from .file_handler import FileHandler
from .exceptions import TranslationError, UnsupportedLanguageError



@functools.cache
def get_translation_engines():
    return ts.translators_pool

_translatable_tags = (
    'h1', 'u', 's', 'abbr', 'del', 'pre', 'h5', 'sub', 'kbd', 'li', 
    'dd', 'textarea', 'dt', 'input', 'em', 'sup', 'label', 'button', 'h6', 
    'title', 'dfn', 'th', 'acronym', 'cite', 'samp', 'td', 'p', 'ins', 'big', 
    'caption', 'bdo', 'var', 'h3', 'tt', 'address', 'h4', 'legend', 'i', 
    'small', 'b', 'q', 'option', 'code', 'h2', 'a', 'strong', 'span',
)


def _slice_iterable(iter: List | str | Tuple | array, slice_size: int):
    '''
    Slices an iterable into smaller iterables of size `slice_size`

    Args:
        iter (Iterable): The iterable to slice.
        slice_size (int): The size of each slice
    '''
    if not isinstance(iter, (list, tuple, str, array)):
        raise TypeError('Invalid argument type for `iter`')
    if not isinstance(slice_size, int):
        raise TypeError('Invalid argument type for `slice_size`')
    if slice_size < 1:
        raise ValueError('`slice_size` should be greater than 0')

    return [ iter[ i : i + slice_size ] for i in range(0, len(iter), slice_size) ]



class Translator:
    """
    A Wrapper around the `TranslatorServer` class from the `translators` package by UlionTse.
    """
    _server = tss

    def __init__(self, engine: str = "bing"):
        """
        Create a Translator instance.

        :param engine (str): Name of translation engine to be used. Defaults to "bing"
        as it is proven to be the most reliable.

        #### Call `get_translation_engines()` to get a list of supported translation engines.
        """
        if not engine in get_translation_engines():
            raise ValueError(f"Invalid translation engine: {self.engine}")
        self.engine_name = engine
        self._cache = {}
        return None


    @property
    def server(self):
        """The translation server used by the Translator instance"""
        if not isinstance(self._server, TranslatorsServer):
            raise TypeError("Invalid type for `_server`")
        return self._server
    
    @property
    def engine(self) -> Tse | None:
        """The translation engine used by the Translator instance"""
        return getattr(self.server, f"_{self.engine_name}", None)
    
    @property
    def input_limit(self) -> int:
        """
        The maximum number of characters that can be translated at once.
        This is dependent on the translation engine being used.
        """
        return self.engine.input_limit

    @functools.cached_property
    def language_map(self) -> Dict:
        """
        A dictionary containing a mapping of source language codes 
        to a list of target language codes that the translation engine can translate to.
        """
        def _get_lang_map(text, src_lang, target_lang) -> Dict | None:
            supported_langs = []
            
            try:
                # Some translation engine require that you ping/test them 
                # before you can obtain their language map
                getattr(self.server, f"{self.engine_name}")(text, src_lang, target_lang)

            except Exception as exc:
                # If ping fails, usually because of wrong src and/or target lang codes, 
                # the exception string usually contains, a list of the language map keys.
                exc_str = str(exc)
                # Parse out the list from the exception string.
                try:
                    supported_langs_str = exc_str.split(" in ")[1].strip().strip(".")
                    supported_langs = list(eval(supported_langs_str))
                except:
                    pass

                if not supported_langs:
                    return None
                
                # Use the first two languages in the list as the src and target languages.
                if len(supported_langs) >= 2:
                    src_lang, target_lang = supported_langs[:2]
                else:
                    src_lang, target_lang = supported_langs[0], supported_langs[0]
                # Retry with the new src and target languages.
                return _get_lang_map(text, src_lang, target_lang)
            
            # If ping succeeds, get the language map.
            lang_map = self.engine.language_map
            if lang_map:
                for key, value in lang_map.items():
                    if isinstance(value, str):
                        lang_map[key] = [value]
                        continue
                    lang_map[key] = list(value)

            # If the language map is still empty, try to construct it from the list of supported languages.
            if not lang_map and len(supported_langs) >= 2:
                lang_map = { lang : supported_langs[index + 1 : index - 1] for index, lang in enumerate(supported_langs) }
            return lang_map
        
        return _get_lang_map("Hello World", "en", "fr") or {}
    
    @property
    def supported_languages(self):
        """
        Returns a list of language codes for source 
        languages supported by the translation engine.
        """
        return sorted(self.language_map.keys())
    

    def get_supported_target_languages(self, src_lang: str) -> List:
        """
        Returns a list of language codes for target languages 
        supported by the translation engine for the specified source language.

        :param src_lang (str): The source language for which to get supported target languages.
        """
        if not src_lang:
            raise ValueError("Invalid value for `src_lang`")
        return self.language_map.get(src_lang, [])
    

    @functools.lru_cache(maxsize=128)
    def is_supported_language(self, lang_code: str):
        '''
        Check if the source language with the specified 
        language code is supported by the translation engine.
        
        :param lang_code (str): The language code for the language to check.
        :return: True if the language is supported, False otherwise.
        '''
        lang_code = lang_code.strip().lower()
        if not lang_code:
            raise ValueError("`lang_code` cannot be empty")
        
        return lang_code in self.supported_languages
    

    def detect_language(self, _s: str) -> Dict:
        """
        Detects the language of the specified text.

        :param _s (str): The text to detect the language of.
        :return: A dictionary containing the language code and confidence score.

        bing is the preferred translation engine for this method as it works well for 
        this purpose. However, it is not guaranteed to work well always. 
        """
        try:
            result = self.server.translate_text(
                query_text=_s, 
                translator='bing', 
                is_detail_result=True
            )
            return result.get('detectedLanguage', {}) if result else {}
        except:
            return {}
        
    
    def _check_lang_codes(self, src_lang: str, target_lang: str) -> None:
        if not src_lang:
            raise ValueError("A source language must be provided")
        if not target_lang:
            raise ValueError("A target language must be provided")
        
        if src_lang == target_lang:
            raise TranslationError("Source language and target language cannot be the same.")

        if src_lang != 'auto' and not self.is_supported_language(src_lang):
            raise UnsupportedLanguageError(
                message=f"Unsupported source language using translation engine, '{self.engine}'", 
                code=src_lang, 
                engine=self.engine_name,
                code_type="source"
            )
        if src_lang != "auto" and target_lang not in self.get_supported_target_languages(src_lang):
            raise UnsupportedLanguageError(
                message=f"Unsupported target language for source language, '{src_lang}', using translation engine, '{self.engine}'", 
                code=target_lang, 
                engine=self.engine_name,
                code_type="target"
            )


    def translate(
            self, 
            content: str | bytes | BeautifulSoup,
            src_lang: str = "auto", 
            target_lang: str = "en", 
            is_markup: bool = False, 
            **kwargs
        ):
        '''
        Translate content from source language to target language.

        :param content (str | bytes | BeatifulSoup): Content to be translated
        :param src_lang (str, optional): Source language. Defaults to "auto".
        It is advisable to provide a source language to get more accurate translations.
        :param target_lang (str, optional): Target language. Defaults to "en".
        :param cache (bool, optional): Whether to cache translations. Defaults to True.
        :param is_markup (bool, optional): Whether `content` is markup. Defaults to False.
        :param **kwargs: Keyword arguments to be passed to required translation method.
        :return: Translated content.
        '''
        if is_markup:
            return self.translate_markup(content, src_lang, target_lang, **kwargs)
        elif isinstance(content, BeautifulSoup):
            return self.translate_soup(content, src_lang, target_lang, **kwargs)
        return self.translate_text(content, src_lang, target_lang, **kwargs)

    
    @functools.cache
    def translate_text(
            self, 
            text: str, 
            src_lang: str="auto", 
            target_lang: str="en", 
            **kwargs
        ) -> str | Dict:
        '''
        Translate text from `src_lang` to `target_lang`.

        :param text (str): Text to be translated
        :param src_lang (str, optional): Source language. Defaults to "auto".
        It is advisable to provide a source language to get more accurate translations.
        :param target_lang (str, optional): Target language. Defaults to "en".
        :param **kwargs: Keyword arguments to be passed to `server.translate_text`.
            :kwarg is_detail_result: boolean, default False.
            :kwarg professional_field: str, support baidu(), caiyun(), alibaba() only.
            :kwarg timeout: float, default None.
            :kwarg proxies: dict, default None.
            :kwarg sleep_seconds: float, default random.random().
            :kwarg update_session_after_seconds: float, default 1500.
            :kwarg if_use_cn_host: bool, default False.
            :kwarg reset_host_url: str, default None.
            :kwarg if_ignore_empty_query: boolean, default False.
            :kwarg if_ignore_limit_of_length: boolean, default False.
            :kwarg limit_of_length: int, default 5000.
            :kwarg if_show_time_stat: boolean, default False.
            :kwarg show_time_stat_precision: int, default 4.
            :kwarg lingvanex_model: str, default 'B2C'.
        :return: Translated text.
        '''
        self._check_lang_codes(src_lang, target_lang)
        kwargs_ = {'if_ignore_empty_query': True}
        kwargs_.update(kwargs)

        def _translate(text: str):
            return self.server.translate_text(
                query_text=text, 
                to_language=target_lang, 
                from_language=src_lang, 
                translator=self.engine_name, 
                **kwargs_
            )
        
        try:
            chunks = _slice_iterable(text, self.input_limit)
            translated_contents = list(map(_translate, chunks))
            translated_text = "".join(translated_contents)   
            return translated_text
        
        except Exception as exc:
            raise TranslationError(exc.__str__())


    def translate_file(
            self, 
            filepath: str, 
            src_lang: str="auto", 
            target_lang: str="en", 
            **kwargs
        ):
        '''
        Translates file from `src_lang` to `target_lang`.

        Supported file types include: .txt, .csv, .doc, .docx, .pdf, .md..., mostly files with text content.

        :param filepath (str): path to the file to be translated.
        :param src_lang (str, optional): Source language. Defaults to "auto".
        It is advisable to provide a source language to get more accurate translations.
        :param target_lang (str, optional): Target language. Defaults to "en".
        :param **kwargs: Keyword arguments to be passed to the `translate_text` method.
            :kwarg professional_field: str, support baidu(), caiyun(), alibaba() only.
            :kwarg timeout: float, default None.
            :kwarg proxies: dict, default None.
            :kwarg sleep_seconds: float, default random.random().
            :kwarg update_session_after_seconds: float, default 1500.
            :kwarg if_use_cn_host: bool, default False.
            :kwarg reset_host_url: str, default None.
            :kwarg if_ignore_empty_query: boolean, default False.
            :kwarg if_ignore_limit_of_length: boolean, default False.
            :kwarg limit_of_length: int, default 5000.
            :kwarg if_show_time_stat: boolean, default False.
            :kwarg show_time_stat_precision: int, default 4.
            :kwarg lingvanex_model: str, default 'B2C'.
        :return: Translated file.
        '''
        self._check_lang_codes(src_lang, target_lang)
        kwargs_ = {'if_ignore_empty_query': True}
        kwargs.pop('is_detail_result', None)

        kwargs_.update(kwargs)
        file_handler = FileHandler(filepath, not_found_ok=False)
        content = file_handler.file_content

        try:
            if file_handler.filetype in ['xhtml', 'htm', 'shtml', 'html', 'xml']:
                translated_content = self.translate_markup(content, src_lang, target_lang, **kwargs_)
            else:
                translated_content = self.translate_text(content, src_lang, target_lang, **kwargs_)

            file_handler.write_to_file(translated_content, write_mode='w+')
            file_handler.close_file()
            return file_handler.file
        except Exception as exc:
            raise TranslationError(f"File cannot be translated. {exc}")


    def _translate_soup_tag(
            self, 
            element: Tag, 
            src_lang: str = "auto", 
            target_lang: str = "en", 
            _ct: int = 0,
            **kwargs
        ):
        '''
        Translates the text of a bs4.element.Tag object in place.

        NOTE: 
        * This function is not meant to be called directly. Use `translate_soup` instead.
        * This function is recursive.
        * This function modifies the element in place.
        * Translations are cached by default to avoid repeated translations which can be costly.

        :param element (bs4.element.Tag): The element whose text is to be translated.
        :param src_lang (str, optional): Source language. Defaults to "auto".
        :param target_lang (str, optional): Target language. Defaults to "en".
        :param _ct (int, optional): The number of times the function has been called recursively. Defaults to 0.
        Do not pass this argument manually.
        '''
        if not isinstance(element, Tag):
            raise TypeError("Invalid type for `element`")
        if not isinstance(_ct, int):
            raise TypeError("Invalid type for `_ct`")

        if element.string and element.string.strip():
            initial_string = copy.copy(element.string)
            cached_translation = self._cache.get(element.string, None)
            if cached_translation:
                element.string.replace_with(cached_translation)
            else:
                try:
                    translation = self.translate_text(
                        text=element.string, 
                        src_lang=src_lang, 
                        target_lang=target_lang,
                        **kwargs
                    )
                    element.string.replace_with(translation)

                except Exception as exc:
                    error_ = TranslationError(f"Error translating element: {exc}")
                    sys.stderr.write(f"{error_}\n")
                    # try again
                    _ct += 1
                    # prevents the translation engine from blocking our IP address
                    time.sleep(random.random(2, 5) * _ct)
                    if _ct <= 3:
                        return self._translate_soup_tag(element, src_lang, target_lang, _ct, **kwargs)
                finally:
                    self._cache[initial_string] = translation
        return None


    def translate_soup(
            self, 
            soup: BeautifulSoup, 
            src_lang: str = "auto", 
            target_lang: str = "en", 
            thread: bool = True, 
            **kwargs
        ):
        '''
        Translates the text of a BeautifulSoup object.

        :param soup (BeautifulSoup): The BeautifulSoup object whose text is to be translated.
        :param src_lang (str, optional): Source language. Defaults to "auto".
        It is advisable to provide a source language to get more accurate translations.
        :param target_lang (str, optional): The target language for translation. Defaults to "en".
        :param thread (bool, optional): Whether to use multi-threading to translate the text. Defaults to True.
        :return: The translated BeautifulSoup object.
        '''
        if not isinstance(soup, BeautifulSoup):
            raise TypeError("Invalid type for `soup`")
        self._check_lang_codes(src_lang, target_lang)
        translatables = soup.find_all(_translatable_tags)
        translatables = list(filter(lambda el: bool(el.string), translatables))
        if thread:
            with ThreadPoolExecutor() as executor:
                for tag_list in utils.slice_iterable(translatables, 50):
                    _ = executor.map(
                        lambda tag: self._translate_soup_tag(tag, src_lang, target_lang, **kwargs), 
                        tag_list
                    )
                    time.sleep(random.randint(3, 5))
        else:
            for tag in translatables:
                self._translate_soup_tag(tag, src_lang, target_lang, **kwargs)
        return soup


    def translate_markup(
            self, 
            markup: str | bytes, 
            src_lang: str="auto", 
            target_lang: str="en", 
            **kwargs
        ):
        '''
        Translates markup.

        :param markup (str | bytes): markup content to be translated
        :param src_lang (str, optional): Source language. Defaults to "auto".
        It is advisable to provide a source language to get more accurate translations.
        :param target_lang (str, optional): Target language. Defaults to "en".
        :param **kwargs: Keyword arguments to be passed to the `translate_soup` method.
            :kwarg thread: bool, default True.
            :kwarg professional_field: str, support baidu(), caiyun(), alibaba() only.
            :kwarg timeout: float, default None.
            :kwarg proxies: dict, default None.
            :kwarg sleep_seconds: float, default random.random().
            :kwarg update_session_after_seconds: float, default 1500.
            :kwarg if_use_cn_host: bool, default False.
            :kwarg reset_host_url: str, default None.
            :kwarg if_ignore_empty_query: boolean, default False.
            :kwarg if_ignore_limit_of_length: boolean, default False.
            :kwarg limit_of_length: int, default 5000.
            :kwarg if_show_time_stat: boolean, default False.
            :kwarg show_time_stat_precision: int, default 4.
            :kwarg lingvanex_model: str, default 'B2C'.
        :return: Translated markup.
        '''
        if not isinstance(markup, (str, bytes)):
            raise TypeError("Invalid type for `markup`")
        is_bytes = isinstance(markup, bytes)
        kwargs.pop('is_detail_result', None)
        soup = BeautifulSoup(markup, 'lxml')
        translated_markup = self.translate_soup(soup, src_lang, target_lang, **kwargs).prettify()

        # re-encode the markup if the initial markup was in bytes
        if is_bytes:
            translated_markup = translated_markup.encode('utf-8')
        return translated_markup
