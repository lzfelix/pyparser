# pyparser

A small arithmetic expression parser, evaluator, pretty-printer and symbolic differentiator written in pure Python.

Expressions are tokenized and parsed into a tree, which can then be evaluated, printed or differentiated:

```
                                                      ┌─ evaluate(variables) ─▶  8.5
"2 * x + y"  ─ tokenize ─▶  list[Token]  ─ parse ─▶  AST ── to_string ─▶  "2 * x + y"
                                                      └─ differentiate(x) ─▶  AST of "0 * x + 2 * 1 + 0"
```

## Supported operations

| Operation      | Syntax          | Example          | Result  |
|----------------|-----------------|------------------|---------|
| Integers       | `42`            | `42`             | `42`    |
| Decimals       | `3.14`          | `3.14 * 2`       | `6.28`  |
| Variables      | `x`, `long_name`| `2 * x` (x = 3)  | `6`     |
| Constants      | `e`, `pi`       | `cos(pi)`        | `-1.0`  |
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
- `e` and `pi` are reserved for the [built-in constants](#constants): they can't be bound as variables or indexed, while `E` and `PI` are ordinary variables.
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

### Constants

| Constant | Value                        |
|----------|------------------------------|
| `e`      | Euler's number, `2.718281...` |
| `pi`     | *π*, `3.141592...`            |

Constants are written like variables and only replaced by their value when evaluating, so trees keep them symbolic: `2*pi` prints as `2 * pi`, and differentiating them gives `0`, as for any other name that isn't `var`.
See [ADR 0003](docs/decisions/0003-constants-are-resolved-at-evaluation-time.md) for the reasoning.
Exponentials are written as powers of `e`: `e ^ x`, `e ^ (-x ^ 2)`.

Binding a constant's name raises `EvaluationError`, even if the expression doesn't use it:

```python
evaluator.evaluate(parser.parse(tokenizer.tokenize('2 * pi * r')), {'r': 1})   # 6.283185307179586
evaluator.evaluate(parser.parse(tokenizer.tokenize('x + 1')), {'x': 1, 'e': 2})  # EvaluationError
```

Calling a constant (`e(2)`) is an unknown function, and indexing one (`pi[0]`) is an error.

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
from pyparser.operations import evaluator

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

### Pretty-printing

`printer.to_string` turns a tree back into text, normalizing spacing and keeping only the parentheses needed to parse it back into the same tree:

```python
from pyparser.operations import printer

printer.to_string(parser.parse(tokenizer.tokenize('((1-2))-(3-4)')))  # '1 - 2 - (3 - 4)'
printer.to_string(parser.parse(tokenizer.tokenize('(2^3)^(2^1)')))    # '(2 ^ 3) ^ 2 ^ 1'
```

Parsing the printed text always gives back an equal tree. Parentheses are kept even when the result wouldn't change (`1 + (2 + 3)`), since dropping them would change the tree's shape.
Floats that Python prints in scientific notation (e.g. `1e-07`) can't be tokenized back.

### Differentiation

`differentiate(tree, var)` builds the derivative of a tree with respect to a variable, as a new tree that can be printed, evaluated or differentiated again:

```python
from pyparser.operations.differentiator import differentiate
from pyparser.parser import ast

tree = parser.parse(tokenizer.tokenize('x * sin(x)'))
derivative = differentiate(tree, ast.VariableNode('x'))

printer.to_string(derivative)               # '1 * sin(x) + x * (cos(x) * 1)'
evaluator.evaluate(derivative, {'x': 0})    # 0.0
```

Results are correct but not simplified: `2 * x + y` differentiates to `0 * x + 2 * 1 + 0`.

Variables other than `var` are treated as constants, so this computes partial derivatives. Indexed variables are separate variables, so `x`, `x[0]` and `x[1]` are all independent:

```python
differentiate(parser.parse(tokenizer.tokenize('x * y ^ 2')), ast.VariableNode('y'))
# printed: 0 * y ^ 2 + x * (2 * y ^ (2 - 1) * 1)

differentiate(parser.parse(tokenizer.tokenize('x[0] * x[1]')), ast.IndexedVariableNode('x', 1))
# printed: 0 * x[1] + x[0] * 1
```

`differentiate` never modifies its input, so the same tree can be differentiated any number of times: once per variable to build a **gradient** that can then be evaluated at any point, or repeatedly for **higher-order derivatives**:

```python
tree = parser.parse(tokenizer.tokenize('x * y ^ 2 + sin(x)'))
gradient = [differentiate(tree, ast.VariableNode(name)) for name in ['x', 'y']]

[evaluator.evaluate(partial, {'x': 1, 'y': 2}) for partial in gradient]    # [4.5403..., 4]  (y ^ 2 + cos(x), 2 * x * y)
[evaluator.evaluate(partial, {'x': 0, 'y': -1}) for partial in gradient]   # [2.0, 0]

x = ast.VariableNode('x')
second = differentiate(differentiate(parser.parse(tokenizer.tokenize('x ^ 3')), x), x)
evaluator.evaluate(second, {'x': 2})    # 12  (6 * x)
```

Without simplification, each repeated differentiation makes the tree noticeably larger.

Exponentials follow the constant-base rule below. `log(e)` isn't simplified away, but evaluates to `1`, so the derivative of `e ^ x` evaluates to `e ^ x`:

```python
derivative = differentiate(parser.parse(tokenizer.tokenize('e ^ x')), ast.VariableNode('x'))

printer.to_string(derivative)               # 'e ^ x * log(e) * 1'
evaluator.evaluate(derivative, {'x': 1})    # 2.718281828459045
```

Constants can't be differentiated by: `differentiate(tree, ast.VariableNode('pi'))` raises `DifferentiationError`.

Rules applied, where `u` and `v` are subtrees and `'` marks their derivative:

| Expression | Derivative |
|------------|------------|
| anything without `var` | `0` |
| `var` | `1` |
| `±u` | `±u'` |
| `u ± v` | `u' ± v'` |
| `u * v` | `u' * v + u * v'` |
| `u / v` | `(u' * v - u * v') / v ^ 2` |
| `u ^ 0` | `0` |
| `u ^ n` (`n` without `var`) | `n * u ^ (n - 1) * u'` |
| `a ^ v` (`a` without `var`) | `a ^ v * log(a) * v'` |
| `e ^ v` | `e ^ v * log(e) * v'`, which evaluates to `e ^ v * v'` |
| `u ^ v` (both with `var`) | `u ^ v * (v' * log(u) + v * (u' / u))` |
| `sin(u)` | `cos(u) * u'` |
| `cos(u)` | `-sin(u) * u'` |
| `tan(u)` | `1 / cos(u) ^ 2 * u'` |
| `log(u)` | `1 / u * u'` |

## Errors

All errors subclass `pyparser.errors.PyParserError`, which has a `message` and, when known, the `position` in the input:

| Error             | Raised when |
|-------------------|-------------|
| `TokenizerError`  | Invalid character, malformed number (`3.`, `1.2.3`), or empty input |
| `ParserError`     | Unexpected token, unclosed parenthesis, or incomplete expression |
| `EvaluationError` | Undefined variable or function, a function outside its domain (`log(0)`), an index out of range, indexing a single value or using a sequence without an index, binding or indexing a constant (`e`, `pi`), or an unsupported operator or AST node |
| `DifferentiationError` | Differentiating with respect to a constant, or an unknown function or unsupported operator in a subtree that depends on the variable |

## Development

Requires Python 3.14+ and [uv](https://docs.astral.sh/uv/).

```sh
uv run pytest
```
