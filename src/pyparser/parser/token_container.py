from pyparser.errors import ParserError
from pyparser.lexer import tokens


class TokenContainer:
    def __init__(self, expression: list[tokens.Token]) -> None:
        self._tokens = expression
        self._idx = 0

    def peek(self) -> tokens.Token:
        if self.is_exhausted():
            raise ParserError('Unexpected end of expression.')
        return self._tokens[self._idx]

    def next(self) -> tokens.Token:
        token = self.peek()
        self._idx += 1
        return token

    def is_exhausted(self) -> bool:
        return self._idx >= len(self._tokens)
