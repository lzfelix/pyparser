import string

_NUMBERS_ALPHABET = set(str(i) for i in range(10))
_SIGNS_ALPHABET = {'+', '-'}
_OPEN_PAR = '('
_CLOSE_PAR = ')'
_OPERATORS = {'+', '-', '*', '/', '^'}
_STR_ALPHABET = set(string.ascii_letters) | {'_'}


def _parse_number(expr: str, idx: int) -> (int, str):
    expr_len = len(expr)
    found_dot = False
    current_token = []

    start_idx = idx
    while idx < expr_len and (expr[idx] in _NUMBERS_ALPHABET or expr[idx] == '.'):
        if expr[idx] == '.':
            if found_dot:
                raise ValueError(f'Numbers must contain a single dot in {"".join(current_token)}.')
            elif idx == start_idx:
                raise ValueError(f'Numbers cannot start with leading dot in {"".join(current_token)}.')
            else:
                found_dot = True
        current_token.append(expr[idx])
        idx += 1

    if current_token and current_token[-1] == '.':
        raise ValueError(f'Numbers cannot end with trailing dot in {"".join(current_token)}')
    return idx, ''.join(current_token)


def _parse_string_value(expr: str, idx: int) -> (int, str):
    expr_len = len(expr)

    token_size = 0
    start_idx = idx
    while idx < expr_len and expr[idx] in _STR_ALPHABET:
        token_size += 1
        idx += 1

    return idx, expr[start_idx:start_idx+token_size]


def tokenize(expr: str) -> list[str]:
    idx = 0
    expr = expr.replace(' ', '')
    expr_len = len(expr)

    parsed_tokens = []
    while idx < expr_len:
        current_char = expr[idx]

        if current_char in _NUMBERS_ALPHABET:
            idx, new_token = _parse_number(expr, idx)
            parsed_tokens.append(new_token)
        elif current_char in _STR_ALPHABET:
            idx, new_token = _parse_string_value(expr, idx)
            parsed_tokens.append(new_token)
        elif current_char in _SIGNS_ALPHABET:
            parsed_tokens.append(current_char)
            idx += 1
        elif current_char == _OPEN_PAR:
            parsed_tokens.append('(')
            idx += 1
        elif current_char == _CLOSE_PAR:
            parsed_tokens.append(')')
            idx += 1
        elif current_char in _OPERATORS:
            parsed_tokens.append(current_char)
            idx += 1
        else:
            raise ValueError('Unexpected token')

    if not parsed_tokens:
        raise ValueError('Empty expression')

    return parsed_tokens
