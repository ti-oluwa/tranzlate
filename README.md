## tranzlate

A wrapper around the translators package by UlionTse that enables multilingual translation of text, files, markup and BeautifulSoup objects.

## Installation

Perform a quick install with pip:

```bash
pip install tranzlate
```

## Usage

### Create a Translator

The `Translator` class is the main interface for the package. It can be used to translate text, files, markup and BeautifulSoup objects. To create an instance of the `Translator` class, simply import the `tranzlate` package and instantiate the `Translator` class:

```python
import tranzlate

translator = tranzlate.Translator()
```

### Use a Custom Translation Engine

By default, the `Translator` class uses Bing Translator as its translation engine. Based on test results, Bing is the most reliable translation engine. However, you can use any translation engine that is supported by the translators package by passing the name of the engine to the `Translator` class on instantiation:

In this example, we will use Google Translate as our translation engine:

```python
import tranzlate

translator = tranzlate.Translator('google')
```

To get a list of all supported translation engines:

```python
import tranzlate

print(tranzlate.Translator.engines())

# Output:
# ['bing', 'google', 'yandex', 'baidu', 'sogou', 'tencent', 'deepl', 'alibaba', ...]
```

### Detect Language

```python
import tranzlate

translator = tranzlate.Translator()
text = 'Good Morning!'
detected_lang = translator.detect_language(text)
print(detected_lang)

# Output: en
```

### Translate Text, Markup and BeautifulSoup Objects

To translate text, markup or a soup, you can use the `translate` method of the `Translator` class. The `translate` method is a general purpose method that can be used to translate text, markup and BeautifulSoup objects.

#### Translate Text

```python
import tranzlate

translator = tranzlate.Translator()

text = 'Good Morning!'
translation = translator.translate(text, target_lang='yo')
print(translation)

# Output: Eku ojumo!
```

#### Translate Markup

```python
import tranzlate

translator = tranzlate.Translator()

markup = '<p>Good Morning!</p>'
translated_markup = translator.translate(markup, target_lang='yo')
print(translated_markup)

# Output: <p>Eku ojumo!</p>
```

#### Translate BeautifulSoup Objects

```python
import tranzlate
from bs4 import BeautifulSoup

translator = tranzlate.Translator()

markup = '<p>Good Morning!</p>'
soup = BeautifulSoup(markup, 'html.parser')
translated_soup = translator.translate(soup, target_lang='yo')
```

However, there are specialized methods for translating text, markup and BeautifulSoup objects. These methods are `translate_text`, `translate_markup` and `translate_soup` respectively.

### Translate Files

To translate files, we use the `translate_file` method of the `Translator` class.

```python
import tranzlate

translator = tranzlate.Translator()
translated_file = translator.translate_file('path/to/file.txt', src_lang="en", target_lang='yo')
```

It is advisable to specify the source language when performing translations as it helps the translation engine to provide more accurate translations.

### Use a Proxy

To use a proxy, simply pass the proxy to the `Translator` class on instantiation:

```python
import tranzlate

translator = tranzlate.Translator()
text = 'Good Morning!'
translation = translator.translate(text, target_lang='yo', proxies={'https': 'https://<proxy>:<port>'})
print(translation)
```

### Other Methods

#### Get Supported Languages

To get a list of all supported (source) languages by the translator's engine:

```python
import tranzlate

translator = tranzlate.Translator()
print(translator.supported_languages)
```

#### Check if a Language is Supported

To check if a (source) language is supported by the translator's engine:

```python
import tranzlate

translator = tranzlate.Translator()
is_supported = translator.is_supported_language('yo')
print(is_supported)

# Output: True
```

#### Check if a Language Pair is Supported

To check if a language pair is supported by the translator's engine:

```python
import tranzlate

translator = tranzlate.Translator()
is_supported = translator.is_supported_pair(src_lang='en', target_lang='yo')
print(is_supported)

# Output: True
```

#### Get a List of Supported Target Languages for a Source Language

To get a list of supported target languages for a source language:

```python
import tranzlate

translator = tranzlate.Translator()
supported_target_languages = translator.get_supported_target_languages('en')
print(supported_target_languages)
```

### Testing

To run the tests, simply run the following command in the root directory of your cloned repository:

```bash
python -m unittest discover tests "test_*.py"
```

### Contributing

Contributions are welcome. Please open an issue or submit a pull request.
