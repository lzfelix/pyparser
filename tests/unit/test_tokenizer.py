import pytest
from pyparser.errors import TokenizerError
from pyparser.lexer import tokenizer


def tokenize_values(expression: str) -> list[str]:
    return [str(token) for token in tokenizer.tokenize(expression)]


def test_single_number_is_valid():
    assert tokenize_values('327') == ['327']


def test_single_decimal_number_is_valid():
    assert tokenize_values('327.787') == ['327.787']


def test_single_negative_decimal_number_is_valid():
    assert tokenize_values('-327.787') == ['-', '327.787']


def test_single_positive_decimal_number_is_valid():
    assert tokenize_values('+327.787') == ['+', '327.787']


def test_decimals_should_contain_at_most_one_dot():
    with pytest.raises(TokenizerError):
        tokenize_values('3.14.15')


def test_decimal_should_not_start_with_leading_dot():
    with pytest.raises(TokenizerError):
        tokenize_values('.14')


def test_decimal_should_not_finish_with_trailing_dot():
    with pytest.raises(TokenizerError):
        tokenize_values('3.')


def test_spaced_expression():
    assert tokenize_values('3 + 2 * 10') == ['3', '+', '2', '*', '10']


def test_non_spaced_expression():
    assert tokenize_values('3+2*10') == ['3', '+', '2', '*', '10']


def test_decimal_expression():
    assert tokenize_values('3.14*2.7+1.333') == ['3.14', '*', '2.7', '+', '1.333']


def test_negative_expression():
    assert tokenize_values('-3 - -2 * -6 + 7') == ['-', '3', '-', '-', '2', '*', '-', '6', '+', '7']


def test_mixed_positive_negative_decimal_expression():
    assert (
        tokenize_values('-3 - +2 * +6.33 + -7.4') ==
        ['-', '3', '-', '+', '2', '*', '+', '6.33', '+', '-', '7.4']
    )


def test_empty_expression_should_raise():
    with pytest.raises(TokenizerError):
        tokenize_values('')


def test_mixed_signals_should_be_independent():
    assert tokenize_values('-+-3') == ['-', '+', '-', '3']


def test_parse_variable_name():
    assert tokenize_values('x + y + long_z_name + 2') == ['x', '+', 'y', '+', 'long_z_name', '+', '2']


def test_parse_function_call():
    assert tokenize_values('sin(x + 3)') == ['sin', '(', 'x', '+', '3', ')']


def test_positions_should_account_for_whitespace():
    positions = [token.position for token in tokenizer.tokenize('3 +  20')]
    assert positions == [0, 2, 5]


def test_whitespace_only_expression_should_raise():
    with pytest.raises(TokenizerError):
        tokenize_values('   ')


def test_whitespace_should_separate_numbers():
    assert tokenize_values('12 34') == ['12', '34']


def test_tokenize_unknown_symbol():
    with pytest.raises(TokenizerError):
        tokenize_values('2*3+4?7')


def test_should_accept_nonsensical_expressions():
    assert tokenize_values('+-*/)3(4') == ['+', '-', '*', '/', ')', '3', '(', '4']


def test_tokenize_function_call():
    assert tokenize_values('sin(x + 2)') == ['sin', '(', 'x', '+', '2', ')']
