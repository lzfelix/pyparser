import pytest
from pyparser import tokenizer


def test_single_number_is_valid():
    assert tokenizer.tokenize('327') == ['327']


def test_single_decimal_number_is_valid():
    assert tokenizer.tokenize('327.787') == ['327.787']


def test_single_negative_decimal_number_is_valid():
    assert tokenizer.tokenize('-327.787') == ['-', '327.787']


def test_single_positive_decimal_number_is_valid():
    assert tokenizer.tokenize('+327.787') == ['+', '327.787']


def test_decimals_should_contain_at_most_one_dot():
    with pytest.raises(ValueError):
        tokenizer.tokenize('3.14.15')


def test_decimal_should_not_start_with_leading_dot():
    with pytest.raises(ValueError):
        tokenizer.tokenize('.14')


def test_decimal_should_not_finish_with_trailing_dot():
    with pytest.raises(ValueError):
        tokenizer.tokenize('3.')


def test_spaced_expression():
    assert tokenizer.tokenize('3 + 2 * 10') == ['3', '+', '2', '*', '10']


def test_non_spaced_expression():
    assert tokenizer.tokenize('3+2*10') == ['3', '+', '2', '*', '10']


def test_decimal_expression():
    assert tokenizer.tokenize('3.14*2.7+1.333') == ['3.14', '*', '2.7', '+', '1.333']


def test_negative_expression():
    assert tokenizer.tokenize('-3 - -2 * -6 + 7') == ['-', '3', '-', '-', '2', '*', '-', '6', '+', '7']


def test_mixed_positive_negative_decimal_expression():
    assert (
        tokenizer.tokenize('-3 - +2 * +6.33 + -7.4') ==
        ['-', '3', '-', '+', '2', '*', '+', '6.33', '+', '-', '7.4']
    )


def test_empty_expression_should_raise():
    with pytest.raises(ValueError):
        tokenizer.tokenize('')


def test_mixed_signals_should_be_independent():
    assert tokenizer.tokenize('-+-3') == ['-', '+', '-', '3']


def test_parse_variable_name():
    assert tokenizer.tokenize('x + y + long_z_name + 2') == ['x', '+', 'y', '+', 'long_z_name', '+', '2']


def test_parse_function_call():
    assert tokenizer.tokenize('sin(x + 3)') == ['sin', '(', 'x', '+', '3', ')']
