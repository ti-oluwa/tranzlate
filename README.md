## tranzlate

A wrapper around the [`translators`](https://pypi.org/project/translators/) package, providing a simpler interface for the translation of text, files, markup and BeautifulSoup.

## Installation

Perform a quick install with pip:

```bash
pip install tranzlate
```

## Usage

> Ensure you have `beautifulsoup4` installed if you want to translate markup or BeautifulSoup. Run `pip install beautifulsoup4` in your terminal.

### Create a translator

The `Translator` class is the main interface for the package. It can be used to translate text, bytes, files, markup and BeautifulSoup. To create an instance of the `Translator` class, simply import the `tranzlate` package and instantiate a `Translator`:

```python
import tranzlate

translator = tranzlate.Translator()
```

### Use a custom translation engine

By default, the `Translator` class uses Bing Translator as its translation engine. Based on test results, Bing is the most reliable translation engine. However, you can use any translation engine that is supported by the translators package by passing the name of the engine to the `Translator` class on instantiation:

In this example, we will use Google Translate as our translation engine:

```python
import tranzlate

google = tranzlate.Translator('google')
```

To get a list of all supported translation engines:

```python
import tranzlate

print(tranzlate.Translator.engines())

# Output:
# ['bing', 'google', 'yandex', 'baidu', 'sogou', 'tencent', 'deepl', 'alibaba', ...]
```

### Detect language

```python
import tranzlate

text = 'Good Morning!'
language = tranzlate.Translator.detect_language(text)
print(language)

# Output: en
```

### Translate text, bytes, markup and BeautifulSoup

Translate text, markup or a soup using the `translate` method of the `Translator` class. The `translate` method is a general purpose method that can be used to translate text, bytes and markup.

#### Translate text/bytes

```python
import tranzlate

bing = tranzlate.Translator("bing")
text = 'Good Morning!'
translation = bing.translate(text, target_lang='yo')
print(translation)

# Output: Eku ojumo!
```

#### Translate markup

```python
import tranzlate

bing = tranzlate.Translator("bing")

markup = '<p>Good Morning!</p>'
translated_markup = bing.translate(markup, target_lang='yo', is_markup=True)
print(translated_markup)

# Output: <p>Eku ojumo!</p>
```

#### Translate BeautifulSoup

```python
import tranzlate
from bs4 import BeautifulSoup

baidu = tranzlate.Translator("baidu")
markup = '<p>Good Morning!</p>'
soup = BeautifulSoup(markup, 'html.parser')
translated_soup = baidu.translate_soup(soup, target_lang='fr')
```

However, there are specialized methods for translating text, markup and BeautifulSoup objects. These methods are `translate_text`, `translate_markup` and `translate_soup` respectively.

### Translate files

To translate files, we use the `translate_file` method.

```python
import tranzlate

bing = tranzlate.Translator() # Bing is used by default
translated_file = bing.translate_file('path/to/file.txt', src_lang="en", target_lang='yo')
```

It is advisable to specify the source language when performing translations as it helps the translation engine to provide more accurate translations.

### Use a proxy

To use a proxy, simply pass your proxies on translation:

```python
import tranzlate

deepl = tranzlate.Translator("deepl")
text = 'Good Morning!'
translation = deepl.translate(text, target_lang='yo', proxies={'https': 'https://<proxy>:<port>'})
print(translation)
```

### Other methods

```python
import tranzlate

google = tranzlate.Translator("google")
bing = tranzlate.Translator("bing")
```

#### Get supported languages

Get a list of all supported (source) languages by the translator's engine:

```python
print(google.supported_languages)
```

#### Check if a language is supported

Check if a (source) language is supported by the translator's engine:

```python
is_supported = google.supports_language('yo')
print(is_supported)

# Output: True
```

#### Check if a language pair is supported

Check if a language pair is supported by the translator's engine:

```python
is_supported = bing.supports_pair(src_lang='en', target_lang='yo')
print(is_supported)

# Output: True
```

#### Get a list of supported target languages for a source language

Get a list of supported target languages for a source language:

```python
supported_target_languages = bing.get_supported_target_languages('en')
print(supported_target_languages)
```

### Testing

To run tests, simply run the following command in the root directory of your cloned repository:

```bash
python -m unittest discover tests "test_*.py"
```

### Contributing

Contributions are welcome. Please open an issue or submit a pull request.
