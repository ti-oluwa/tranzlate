
class TranslationError(Exception):
    """Error encountered during translation"""
    message = "Error occurred during translation"

    def __init__(self, message: str = None) -> None:
        if message:
            self.message = message 

    def __str__(self):
        return self.message if self.message else self.__doc__


class UnsupportedLanguageError(TranslationError):
    """Language cannot be translated by translation engine"""
    message = 'Language cannot be translated by translation engine'

    def __init__(
            self, 
            message: str = None, 
            code: str = None,
            engine: str = None,
            code_type: str = "source"
        ):
        """
        Unsupported language error

        :param message: Error message
        :param code: Language code
        :param code_type: Type of code (source or target)
        :param engine: Translation engine name
        """
        msg = ''
        preposition = "from" if code_type == "source" else "to"

        if code and engine:
            msg = f"Translation {preposition} '{code}' is not supported by {engine}"
        elif code and not engine:
            msg = f"Translation {preposition} '{code}' is not supported by translation engine"
        elif not code and engine:
            msg = f"Language cannot be translated by {engine}"

        message = f"{message}. {msg}" if msg else message
        return super().__init__(message)
