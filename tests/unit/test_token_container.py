import pytest
from pyparser.errors import ParserError
from pyparser.lexer import tokens
from pyparser.parser.token_container import TokenContainer


def test_next_should_return_tokens_in_order():
    container = TokenContainer([tokens.IntToken(3, 0), tokens.OperatorToken('+', 1)])

    assert container.next() == tokens.IntToken(3, 0)
    assert container.next() == tokens.OperatorToken('+', 1)


def test_peek_should_not_consume_token():
    container = TokenContainer([tokens.IntToken(3, 0)])

    assert container.peek() == tokens.IntToken(3, 0)
    assert container.next() == tokens.IntToken(3, 0)


def test_is_exhausted_after_consuming_all_tokens():
    container = TokenContainer([tokens.IntToken(3, 0)])

    assert not container.is_exhausted()
    container.next()
    assert container.is_exhausted()


def test_next_past_end_should_raise():
    container = TokenContainer([])

    with pytest.raises(ParserError):
        container.next()


def test_peek_past_end_should_raise():
    container = TokenContainer([])

    with pytest.raises(ParserError):
        container.peek()
