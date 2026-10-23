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
| Indexed variables | `x[i]`       | `x[0] + x[1]` (x = [1, 2]) | `3` |
| Addition       | `a + b`         | `3 + 2`          | `5`     |
| Subtraction    | `a - b`         | `3 - 5`          | `-2`    |
| Multiplication | `a * b`         | `3 * 4`          | `12`    |
| Division       | `a / b`         | `7 / 2`          | `3.5`   |
| Power          | `a ^ b`         | `2 ^ 3 ^ 2`      | `512`   |
| Unary sign     | `+a`, `-a`      | `-+--+-3`        | `3`     |
| Grouping       | `( ... )`       | `2 * (-7 + 5)`   | `-4`    |
| Function call  | `f(a)`          | `2 * cos(0) + 1` | `3`     |

- Precedence, from highest to lowest: function calls and parentheses, `^`, unary sign, `*` `/`, `+` `-`.
- `^` is right-associative (`2 ^ 3 ^ 2` is `2 ^ (3 ^ 2)`); the other binary operators are left-associative.
- A leading sign applies after the power, as in Python: `-2 ^ 2` is `-4`, while `(-2) ^ 2` is `4`.
- Division always returns a float; dividing by zero raises `ZeroDivisionError`.
- Variable names use letters and `_`, and are case-sensitive.
- Indexed variables take a single non-negative integer literal as index (`x[0]`); expressions, variables, negative numbers and multiple indices (`x[i]`, `x[-1]`, `x[0][1]`) are rejected by the parser.
- Whitespace is ignored.

### Functions

A name followed by `(` is a function call; otherwise it's a variable. Functions take a single argument:

| Function | Meaning                     |
|----------|-----------------------------|
| `sin(a)` | Sine, `a` in radians        |
| `cos(a)` | Cosine, `a` in radians      |
| `tan(a)` | Tangent, `a` in radians     |
| `log(a)` | Natural logarithm (base *e*) |

## Grammar

```
expr    := term (('+' | '-') term)*
term    := unary (('*' | '/') unary)*
unary   := ('+' | '-') unary | power
power   := primary ('^' unary)?
primary := NUMBER | VARIABLE | VARIABLE '[' INT ']' | FUN_NAME '(' expr ')' | '(' expr ')'
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

Indexed variables are bound to a sequence of numbers:

```python
tree = parser.parse(tokenizer.tokenize('x[0] * x[1] + y'))
evaluator.evaluate(tree, {'x': [2, 3], 'y': 1})  # 7
```

## Errors

All errors subclass `pyparser.errors.PyParserError`, which has a `message` and, when known, the `position` in the input:

| Error             | Raised when |
|-------------------|-------------|
| `TokenizerError`  | Invalid character, malformed number (`3.`, `1.2.3`), or empty input |
| `ParserError`     | Unexpected token, unclosed parenthesis, or incomplete expression |
| `EvaluationError` | Undefined variable or function, a function outside its domain (`log(0)`), an index out of range, indexing a single value or using a sequence without an index, or an unsupported operator or AST node |

## Development

Requires Python 3.14+ and [uv](https://docs.astral.sh/uv/).

```sh
uv run pytest
```
