from pyparser.lexer import tokenizer
from pyparser.parser import parser
from pyparser.parser import ast
from pyparser.lexer import tokens


def test_parse_simple_expression():
    actual = parser.parse(tokenizer.tokenize('3+2-5'))

    expected = ast.BinaryNode(
        ast.BinaryNode(
            ast.TerminalNode(tokens.IntToken(3, 0)),
            tokens.OperatorToken('+', 1),
            ast.TerminalNode(tokens.IntToken(2, 2)),
        ),
        tokens.OperatorToken('-', 3),
        ast.TerminalNode(tokens.IntToken(5, 4))
    )

    assert actual == expected


def test_subtraction_with_unary_operator():
    # 3/3/-3 -> 3 / 3 / (-3)
    actual = parser.parse(tokenizer.tokenize("3/3/-3"))

    expected = ast.BinaryNode(
        ast.BinaryNode(
            ast.TerminalNode(tokens.IntToken(3, 0)),
            tokens.OperatorToken("/", 1),
            ast.TerminalNode(tokens.IntToken(3, 2)),
        ),
        tokens.OperatorToken("/", 3),
        ast.UnaryNode(
            tokens.OperatorToken("-", 4),
            ast.TerminalNode(tokens.IntToken(3, 5)),
        ),
    )

    assert actual == expected
