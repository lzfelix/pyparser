class PyParserError(Exception):
    def __init__(self, message: str, position: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.position = position


class TokenizerError(PyParserError):
    pass


class ParserError(PyParserError):
    pass


class EvaluationError(PyParserError):
    pass


class DifferentiationError(PyParserError):
    pass
