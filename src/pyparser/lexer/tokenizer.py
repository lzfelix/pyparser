import string
from pyparser.errors import TokenizerError
from pyparser.lexer import tokens


_NUMBERS_ALPHABET = set(str(i) for i in range(10))
_SIGNS_ALPHABET = {'+', '-'}
_OPEN_PAR = '('
_CLOSE_PAR = ')'
_OPEN_BRACKET = '['
_CLOSE_BRACKET = ']'
_OPERATORS = {'+', '-', '*', '/', '^'}
_STR_ALPHABET = set(string.ascii_letters) | {'_'}


def _parse_number(expr: str, idx: int) -> (int, tokens.FloatToken | tokens.IntToken):
    expr_len = len(expr)
    found_dot = False
    current_token = []

    start_idx = idx
    while idx < expr_len and (expr[idx] in _NUMBERS_ALPHABET or expr[idx] == '.'):
        if expr[idx] == '.':
            if found_dot:
                raise TokenizerError(f'Numbers must contain a single dot in {"".join(current_token)}.', position=idx)
            elif idx == start_idx:
                raise TokenizerError(f'Numbers cannot start with leading dot in {"".join(current_token)}.', position=idx)
            else:
                found_dot = True
        current_token.append(expr[idx])
        idx += 1

    if current_token and current_token[-1] == '.':
        raise TokenizerError(f'Numbers cannot end with trailing dot in {"".join(current_token)}', position=idx - 1)

    number_as_str = ''.join(current_token)
    if found_dot:
        token = tokens.FloatToken(position=start_idx, value=float(number_as_str))
    else:
        token = tokens.IntToken(position=start_idx, value=int(number_as_str))

    return idx, token


def _parse_string_value(expr: str, idx: int) -> (int, tokens.StringToken):
    expr_len = len(expr)

    token_size = 0
    start_idx = idx
    while idx < expr_len and expr[idx] in _STR_ALPHABET:
        token_size += 1
        idx += 1

    return idx, tokens.StringToken(position=start_idx, value=expr[start_idx:start_idx+token_size])


def tokenize(expr: str) -> list[tokens.Token]:
    idx = 0
    expr_len = len(expr)

    parsed_tokens = []
    while idx < expr_len:
        current_char = expr[idx]

        if current_char.isspace():
            idx += 1
        elif current_char in _NUMBERS_ALPHABET:
            idx, new_token = _parse_number(expr, idx)
            parsed_tokens.append(new_token)
        elif current_char in _STR_ALPHABET:
            idx, new_token = _parse_string_value(expr, idx)
            parsed_tokens.append(new_token)
        elif current_char in _SIGNS_ALPHABET:
            parsed_tokens.append(tokens.OperatorToken(position=idx, value=current_char))
            idx += 1
        elif current_char == _OPEN_PAR:
            parsed_tokens.append(tokens.OpenParensToken(position=idx, value='('))
            idx += 1
        elif current_char == _CLOSE_PAR:
            parsed_tokens.append(tokens.CloseParensToken(position=idx, value=')'))
            idx += 1
        elif current_char == _OPEN_BRACKET:
            parsed_tokens.append(tokens.OpenBracketToken(position=idx, value='['))
            idx += 1
        elif current_char == _CLOSE_BRACKET:
            parsed_tokens.append(tokens.CloseBracketToken(position=idx, value=']'))
            idx += 1
        elif current_char in _OPERATORS:
            parsed_tokens.append(tokens.OperatorToken(position=idx, value=current_char))
            idx += 1
        else:
            raise TokenizerError(f'Unexpected character "{current_char}" at position {idx}.', position=idx)

    if not parsed_tokens:
        raise TokenizerError('Empty expression')

    return parsed_tokens
