# pyparser

A small arithmetic expression parser, evaluator, pretty-printer and symbolic differentiator written in pure Python.

Expressions are tokenized and parsed into a tree, which can then be evaluated, printed or differentiated:

```
                                                      ┌─ evaluate(variables) ─▶  8.5
"2 * x + y"  ─ tokenize ─▶  list[Token]  ─ parse ─▶  AST ── to_string ─▶  "2 * x + y"
                                                      └─ differentiate(x) ─▶  AST of "0 * x + 2 * 1 + 0"
```

`Expression` wraps these steps in a single object; see [Usage](#usage).

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
| `sqrt(a)` | Square root, `a` non-negative |

A function outside its domain, such as `log(0)` or `sqrt(-1)`, raises `EvaluationError`.

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

### Expressions

`Expression` takes the source text and parses it once. Its variables are the ones the source uses, sorted by name:

```python
from pyparser import Expression

f = Expression('x * sin(x) + y')

str(f)                          # 'x * sin(x) + y'
f.variables                     # ('x', 'y')
f.evaluate({'x': 0, 'y': 2})    # 2.0
f.evaluate({'x': 1, 'y': 0})    # 0.8414..., same expression, new values
```

`evaluate` takes a mapping with a value for every variable, and nothing else; a missing or unknown name raises `ExpressionError`.
Names are passed in a mapping rather than as keyword arguments because names such as `if` or `class` are valid variables in an expression.
Indexed uses such as `x[0]` and `x[1]` belong to the variable `x`, which is bound to a sequence:

```python
g = Expression('x[0] * x[1] + y')
g.variables                          # ('x', 'y')
g.evaluate({'x': [2, 3], 'y': 1})    # 7
```

Built-in constants aren't variables: they need no value, and can't be indexed or differentiated by:

```python
area = Expression('pi * r ^ 2')
area.variables             # ('r',)
area.evaluate({'r': 2})    # 12.566...
```

`differentiate(var, order=1)` returns the partial derivative as another `Expression`, so it can be printed, evaluated, or differentiated again. `var` must be a variable of the expression, plain (`'x'`) or indexed (`'x[1]'`); anything else raises `ExpressionError`.
A derivative keeps the variables of the expression it came from, even ones it no longer uses, so every derivative of a function is evaluated at the same points:

```python
df = f.differentiate('x')
str(df)                          # '1 * sin(x) + x * (cos(x) * 1) + 0'
df.variables                     # ('x', 'y')
df.evaluate({'x': 0, 'y': 5})    # 0.0, y must still be given

g.differentiate('x[1]')          # Expression('0 * x[1] + x[0] * 1 + 0')
g.differentiate('x[2]')          # ExpressionError: x[2] is not a variable of the expression
```

`order` gives higher-order derivatives, the same as differentiating repeatedly. Order `0` returns the expression itself; a negative or non-integer order raises `ExpressionError`:

```python
cube = Expression('x ^ 3')

cube.differentiate('x', 2).evaluate({'x': 2})                     # 12  (6 * x)
cube.differentiate('x').differentiate('x').evaluate({'x': 2})     # 12, same derivative
Expression('e ^ x').differentiate('x', order=3).evaluate({'x': 1})    # 2.718..., e ^ x
```

`gradient()` differentiates with respect to every variable, indexed ones included, sorted by name and then by index, matching `variables`: `g.gradient()` gives the partials for `x[0]`, `x[1]` and `y`, in that order. For example, gradient descent:

```python
f = Expression('(x - 3) ^ 2 + 2 * (y + 1) ^ 2')
gradient = f.gradient()

point = {'x': 0.0, 'y': 0.0}
for _ in range(50):
    slopes = [partial.evaluate(point) for partial in gradient]
    point = {name: point[name] - 0.1 * slope for name, slope in zip(f.variables, slopes)}

point    # {'x': 2.99995..., 'y': -0.99999...}
```

Expressions are immutable. The parsed tree is available as `f.tree` for use with the lower-level functions below.

#### Comparing expressions

Expressions support `==` and can be hashed, so they work as set members and dictionary keys. Two expressions are equal when they have the same tree and the same variables, regardless of spacing or redundant parentheses in the source:

```python
Expression('x+1') == Expression('(x) + 1')    # True

cube = Expression('x ^ 3')
cube.differentiate('x', 2) == cube.differentiate('x').differentiate('x')    # True

{Expression('x+1'), Expression('x + 1'), Expression('x + 2')}    # 2 distinct expressions
```

Equality compares structure, not mathematical meaning: `x + y` and `y + x` are different trees, and so are `x * 2` and `2 * x`, so they aren't equal.
A derivative also keeps the variables of the expression it came from, so `Expression('x + y').differentiate('x')` prints as `1 + 0` but isn't equal to `Expression('1 + 0')`, which has no variables.
Expressions can't be ordered: `<` and `>` raise `TypeError`.

### Lower-level functions

`Expression` is a thin wrapper over plain functions that tokenize, parse, and operate on trees. They can be used directly:

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

#### Pretty-printing

`printer.to_string` turns a tree back into text, normalizing spacing and keeping only the parentheses needed to parse it back into the same tree:

```python
from pyparser.operations import printer

printer.to_string(parser.parse(tokenizer.tokenize('((1-2))-(3-4)')))  # '1 - 2 - (3 - 4)'
printer.to_string(parser.parse(tokenizer.tokenize('(2^3)^(2^1)')))    # '(2 ^ 3) ^ 2 ^ 1'
```

Parsing the printed text always gives back an equal tree. Parentheses are kept even when the result wouldn't change (`1 + (2 + 3)`), since dropping them would change the tree's shape.
Floats that Python prints in scientific notation (e.g. `1e-07`) can't be tokenized back.

#### Differentiation

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
| `sqrt(u)` | `1 / (2 * sqrt(u)) * u'` |

The derivative of `sqrt(u)` can't be evaluated where `u` is `0` (it divides by zero), matching its infinite slope there.

## Errors

All errors subclass `pyparser.errors.PyParserError`, which has a `message` and, when known, the `position` in the input:

| Error             | Raised when |
|-------------------|-------------|
| `TokenizerError`  | Invalid character, malformed number (`3.`, `1.2.3`), or empty input |
| `ParserError`     | Unexpected token, unclosed parenthesis, or incomplete expression |
| `EvaluationError` | Undefined variable or function, a function outside its domain (`log(0)`), an index out of range, indexing a single value or using a sequence without an index, binding or indexing a constant (`e`, `pi`), or an unsupported operator or AST node |
| `DifferentiationError` | Differentiating with respect to a constant, or an unknown function or unsupported operator in a subtree that depends on the variable |
| `ExpressionError` | `Expression` misuse: indexing a constant in the source (with its position), missing or unknown values in `evaluate`, or differentiating with respect to something that isn't a variable of the expression, or with an invalid order |

## Development

Requires Python 3.14+ and [uv](https://docs.astral.sh/uv/).

```sh
uv run pytest
```
