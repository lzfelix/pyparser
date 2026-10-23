from pyparser.lexer import tokenizer
from pyparser.parser import parser
from pyparser.parser import nodes
from pyparser.lexer import tokens


def test_parse_simple_expression():
    actual = parser.parse(tokenizer.tokenize('3+2-5'))

    expected = nodes.BinaryNode(
        nodes.BinaryNode(
            nodes.TerminalNode(tokens.IntToken(3, 0)),
            tokens.OperatorToken('+', 1),
            nodes.TerminalNode(tokens.IntToken(2, 2)),
        ),
        tokens.OperatorToken('-', 3),
        nodes.TerminalNode(tokens.IntToken(5, 4))
    )

    assert actual == expected


def test_subtraction_with_unary_operator():
    # 3/3/-3 -> 3 / 3 / (-3)
    actual = parser.parse(tokenizer.tokenize("3/3/-3"))

    expected = nodes.BinaryNode(
        nodes.BinaryNode(
            nodes.TerminalNode(tokens.IntToken(3, 0)),
            tokens.OperatorToken("/", 1),
            nodes.TerminalNode(tokens.IntToken(3, 2)),
        ),
        tokens.OperatorToken("/", 3),
        nodes.UnaryNode(
            tokens.OperatorToken("-", 4),
            nodes.TerminalNode(tokens.IntToken(3, 5)),
        ),
    )

    assert actual == expected
