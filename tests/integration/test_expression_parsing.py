import pytest

from pyparser.errors import ParserError, TokenizerError
from pyparser.lexer import tokenizer
from pyparser.parser import parser
from pyparser.parser import ast


def test_parse_simple_expression():
    actual = parser.parse(tokenizer.tokenize('3+2-5'))

    expected = ast.BinaryNode(
        ast.BinaryNode(
            ast.NumberNode(3),
            '+',
            ast.NumberNode(2),
        ),
        '-',
        ast.NumberNode(5)
    )

    assert actual == expected


def test_subtraction_with_unary_operator():
    # 3/3/-3 -> 3 / 3 / (-3)
    actual = parser.parse(tokenizer.tokenize("3/3/-3"))

    expected = ast.BinaryNode(
        ast.BinaryNode(
            ast.NumberNode(3),
            '/',
            ast.NumberNode(3),
        ),
        '/',
        ast.UnaryNode(
            '-',
            ast.NumberNode(3),
        ),
    )

    assert actual == expected


@pytest.mark.parametrize(
    ('expression', 'expected_error'),
    [
        pytest.param('', TokenizerError, id='empty'),
        pytest.param('   ', TokenizerError, id='whitespace-only'),
        pytest.param('3.', TokenizerError, id='trailing-dot'),
        pytest.param('1.2.3', TokenizerError, id='multiple-dots'),
        pytest.param('.5', TokenizerError, id='leading-dot'),
        pytest.param('3 $ 2', TokenizerError, id='unknown-symbol'),
        pytest.param('3 +', ParserError, id='missing-right-operand'),
        pytest.param('* 3', ParserError, id='missing-left-operand'),
        pytest.param('3 + * 2', ParserError, id='consecutive-binary-operators'),
        pytest.param('3 / / 2', ParserError, id='repeated-binary-operator'),
        pytest.param('-', ParserError, id='lone-unary-sign'),
        pytest.param('(3 + 2', ParserError, id='unclosed-parens'),
        pytest.param('((1)', ParserError, id='unbalanced-nested-parens'),
        pytest.param('3 + 2)', ParserError, id='unopened-parens'),
        pytest.param('()', ParserError, id='empty-parens'),
        pytest.param('3 (2)', ParserError, id='implicit-multiplication'),
        pytest.param('12 34', ParserError, id='adjacent-numbers'),
        pytest.param('2 ^', ParserError, id='missing-exponent'),
        pytest.param('^ 2', ParserError, id='missing-base'),
        pytest.param('2 ^ ^ 3', ParserError, id='repeated-power-operator'),
        pytest.param('sin(0 1', ParserError, id='call-with-stray-token-instead-of-close-parens'),
        pytest.param('sin(0', ParserError, id='unclosed-call'),
        pytest.param('sin()', ParserError, id='call-without-argument'),
        pytest.param('x[-1]', ParserError, id='negative-index'),
        pytest.param('x[+1]', ParserError, id='signed-index'),
        pytest.param('x[1.5]', ParserError, id='float-index'),
        pytest.param('x[i]', ParserError, id='variable-index'),
        pytest.param('x[1 + 1]', ParserError, id='expression-index'),
        pytest.param('x[]', ParserError, id='empty-index'),
        pytest.param('x[1', ParserError, id='unclosed-bracket'),
        pytest.param('x[1)', ParserError, id='mismatched-bracket'),
        pytest.param('x 1]', ParserError, id='unopened-bracket'),
        pytest.param('[1]', ParserError, id='index-without-variable'),
        pytest.param('x[0][1]', ParserError, id='multiple-indices'),
        pytest.param('sin(x)[0]', ParserError, id='indexed-call'),
    ],
)
def test_malformed_expression_should_raise(expression: str, expected_error: type[Exception]):
    with pytest.raises(expected_error):
        parser.parse(tokenizer.tokenize(expression))
