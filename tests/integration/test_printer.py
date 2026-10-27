import pytest

from pyparser.lexer import tokenizer
from pyparser.operations import printer
from pyparser.parser import parser


def _parse(expr: str):
    return parser.parse(tokenizer.tokenize(expr))


@pytest.mark.parametrize(
    ('expression', 'expected'),
    [
        pytest.param('3+2*5', '3 + 2 * 5', id='adds-spacing'),
        pytest.param('((3))', '3', id='drops-redundant-parens'),
        pytest.param('(1+2)*3', '(1 + 2) * 3', id='keeps-needed-parens'),
        pytest.param('(1-2)-3', '1 - 2 - 3', id='drops-parens-on-left-associative-side'),
        pytest.param('1-(2-3)', '1 - (2 - 3)', id='keeps-parens-against-left-associativity'),
        pytest.param('(a*b)/c', 'a * b / c', id='drops-parens-on-left-of-division'),
        pytest.param('a*(b/c)', 'a * (b / c)', id='keeps-parens-on-right-of-multiplication'),
        pytest.param('2^(3^2)', '2 ^ 3 ^ 2', id='drops-parens-on-right-associative-side'),
        pytest.param('(2^3)^2', '(2 ^ 3) ^ 2', id='keeps-parens-against-right-associativity'),
        pytest.param('-(2^2)', '-2 ^ 2', id='drops-parens-around-power-under-sign'),
        pytest.param('(-2)^2', '(-2) ^ 2', id='keeps-parens-around-signed-base'),
        pytest.param('2^(-1)', '2 ^ -1', id='drops-parens-around-signed-exponent'),
        pytest.param('-(x+y)', '-(x + y)', id='keeps-parens-around-sum-under-sign'),
        pytest.param('sin((x+1))', 'sin(x + 1)', id='drops-parens-inside-call'),
        pytest.param('(sin(x))^2+(cos(x))^2', 'sin(x) ^ 2 + cos(x) ^ 2', id='drops-parens-around-calls'),
        pytest.param('(x[0])*x[1]', 'x[0] * x[1]', id='drops-parens-around-indexed-variable'),
        pytest.param('2*pi', '2 * pi', id='keeps-constants-symbolic'),
        pytest.param('e^(-x^2)', 'e ^ -x ^ 2', id='keeps-constant-base-symbolic'),
    ],
)
def test_to_string(expression: str, expected: str):
    assert printer.to_string(_parse(expression)) == expected


@pytest.mark.parametrize(
    'expression',
    [
        '1 + 2 - 3 * 4 / 5',
        '1 - (2 - (3 - 4))',
        '((1 - 2) - 3) - 4',
        'a / (b / c) / d',
        '(a + b) / (c - d)',
        '2 ^ 3 ^ 4',
        '((2 ^ 3) ^ 4) ^ 5',
        '-2 ^ -3 ^ -4',
        '(-2) ^ (-3) ^ 2',
        '--+-x * -(y - z)',
        '2 * -3 + -(4 * 5)',
        'sin(x) ^ 2 + cos(-x ^ 2) * log(2 * (y + 1))',
        'x[0] * (x[1] - x[2]) ^ 2 / -x[3]',
        '3.14 * r ^ 2',
        'pi * r ^ 2 + e ^ (2 * x)',
        '(((a)))',
    ],
)
def test_round_trip(expression: str):
    tree = _parse(expression)

    assert _parse(printer.to_string(tree)) == tree
