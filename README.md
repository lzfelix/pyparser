# pyparser

A small arithmetic expression parser and evaluator written in pure Python.

Expressions go through three stages:

```
"2 * x + y"  ─ tokenize ─▶  list[Token]  ─ parse ─▶  AST  ─ evaluate(variables) ─▶  8.5
```

## Supported operations

| Operation      | Syntax          | Example          | Result  |
|----------------|-----------------|------------------|---------|
| Integers       | `42`            | `42`             | `42`    |
| Decimals       | `3.14`          | `3.14 * 2`       | `6.28`  |
| Variables      | `x`, `long_name`| `2 * x` (x = 3)  | `6`     |
| Addition       | `a + b`         | `3 + 2`          | `5`     |
| Subtraction    | `a - b`         | `3 - 5`          | `-2`    |
| Multiplication | `a * b`         | `3 * 4`          | `12`    |
| Division       | `a / b`         | `7 / 2`          | `3.5`   |
| Unary sign     | `+a`, `-a`      | `-+--+-3`        | `3`     |
| Grouping       | `( ... )`       | `2 * (-7 + 5)`   | `-4`    |

- `*` and `/` bind tighter than `+` and `-`; binary operators are left-associative.
- Division always returns a float; dividing by zero raises `ZeroDivisionError`.
- Variable names use letters and `_`, and are case-sensitive.
- Whitespace is ignored.

Not supported yet: exponentiation (`^`) is tokenized, but not parsed.

## Grammar

```
expr    := term (('+' | '-') term)*
term    := unary (('*' | '/') unary)*
unary   := ('+' | '-') unary | primary
primary := NUMBER | VARIABLE | '(' expr ')'
```

## Usage

```python
from pyparser.lexer import tokenizer
from pyparser.parser import parser
from pyparser.evaluators import evaluator

tree = parser.parse(tokenizer.tokenize('2 * x + y'))

evaluator.evaluate(tree, {'x': 3, 'y': 2.5})  # 8.5
evaluator.evaluate(tree, {'x': 1, 'y': 0})    # 2, same tree, new values
```

Variables are only bound at evaluation time, so a parsed tree can be evaluated any number of times with different values.
Expressions without variables can omit the mapping: `evaluator.evaluate(tree)`.

## Errors

All errors subclass `pyparser.errors.PyParserError`, which has a `message` and, when known, the `position` in the input:

| Error             | Raised when                                                         |
|-------------------|---------------------------------------------------------------------|
| `TokenizerError`  | Invalid character, malformed number (`3.`, `1.2.3`), or empty input |
| `ParserError`     | Unexpected token, unclosed parenthesis, or incomplete expression    |
| `EvaluationError` | Undefined variable, or unsupported operator or AST node             |

## Development

Requires Python 3.14+ and [uv](https://docs.astral.sh/uv/).

```sh
uv run pytest
```
