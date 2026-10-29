# 0004. An immutable `Expression` wrapper as the user-facing API

- **Status:** Accepted
- **Date:** 2026-10-27

## Context

Using the library meant chaining modules by hand: `parser.parse(tokenizer.tokenize(source))`, then `evaluator.evaluate(tree, values)`, and `differentiate(tree, ast.VariableNode('x'))`, which takes a node the user has to build. Higher-order derivatives and gradients repeated this plumbing.

We want users to give an expression as a string, evaluate it at any point, and differentiate it, getting back something they can evaluate or differentiate again with the same interface.

## Decision

Add `pyparser.Expression`, a class wrapping a parsed tree and the variables it uses:

```python
f = Expression('x ^ 2 * y')
f.variables                                     # ('x', 'y')
f.evaluate({'x': 3, 'y': 2})                    # 18
f.differentiate('x', order=2)                   # Expression('...')
f.differentiate('x').differentiate('y').evaluate({'x': 3, 'y': 2})
```

- **Variables come from the source.** The constructor tokenizes and parses the source once, and records the variables it uses, plain (`x`) or indexed (`x[1]`), sorted by name and then by index, as is usual in mathematics. `variables` lists their names; `x[0]` and `x[1]` both belong to `x`.
- **The gradient covers every variable.** `gradient()` takes no arguments and returns one partial derivative per variable, in the same sorted order, so it lines up with `variables`.
- **Values are a mapping.** `evaluate(values)` requires a value for every variable and rejects unknown names, so typos in keys fail before evaluation starts.
- **Only existing variables can be differentiated by.** `differentiate(var)` raises `ExpressionError` unless `var` is one of the recorded variables; for indexed variables the exact index must appear (`x[5]` is rejected when only `x[0]` and `x[1]` are used).
- **Derivatives are wrappers.** `differentiate(var, order)` parses `var` (`'x'` or `'x[1]'`) with the existing tokenizer and parser, applies `operations.differentiator.differentiate` `order` times, and wraps the resulting tree in a new `Expression` that keeps the original's variables, without re-parsing.
- **Immutable and comparable.** Instances can't be modified, and compare and hash by their tree and variables, so trees compare structurally as elsewhere.
- **No behaviour moves into the AST.** The class only delegates to the existing operation functions (see [0001](0001-operations-use-pattern-matching-instead-of-visitors.md)); the lower-level functions remain public.

Variables are collected with the `helpers.variable_uses` operation. Built-in constants (`e`, `pi`, see ADR 0003) are not variables: they need no value, and indexing one or differentiating with respect to one raises `ExpressionError`.

## Consequences

- **One import for common use.** Parsing, evaluating, printing and differentiating, including nth derivatives and gradients, go through one object.
- **Nothing to declare.** The source alone defines the variables, so there is no list to keep in sync with it.
- **Some typos surface later.** A misspelled variable in the source (`x * yy`) is only noticed when `evaluate` reports a missing value for `yy`, not at construction.
- **Derivatives keep every variable of the original**, even ones they no longer use (`d/dx (x + y)` is `1 + 0`), so they must still be given a value for `y`, and can still be differentiated by `y`. This keeps every derivative of an expression interchangeable, such as the partials of a gradient evaluated at the same point.
- **Two layers to document and maintain.** The wrapper must follow changes in the operations it delegates to.

## Alternatives considered

### Keyword arguments for values: `f.evaluate(x=3, y=2)`

- **For:** shorter to write.
- **Against:** variable names like `if`, `class` or `lambda` are valid in expressions but not as Python keyword arguments, and the mapping form is what the evaluator already takes, so a point can be passed around as one value.

Rejected.

### Returning trees from `differentiate`

- **For:** no new type; the tree is what the differentiator already produces.
- **Against:** the user drops back to the low-level functions after the first derivative, so the interface can't be used for nth derivatives or evaluating a derivative.

Rejected; the tree remains available as `Expression.tree`.

### Re-parsing the printed derivative

Build the derivative's `Expression` from `printer.to_string(derivative_tree)`, going through the public constructor.

- **For:** a single construction path.
- **Against:** printing and parsing again is wasted work, and floats that Python prints in scientific notation (`1e-07`) can't be tokenized back, so some derivatives would fail. Wrapping the tree with a private constructor avoids both, and the variables need no new check since differentiation introduces none.

Rejected.

### Declaring variables when constructing: `Expression(source, variables)`

- **For:** a misspelled variable fails at construction, with its position; the declared order could differ from alphabetical; a function can have variables it doesn't use (`f(x, y) = x ^ 2`).
- **Against:** it repeats what the source already says, while values must be passed to `evaluate` anyway. Misspellings are still caught when evaluating, as missing values; sorted names give a predictable order; and derivatives already keep variables they no longer use.

Rejected.

### Choosing the variables of `gradient(variables)`

- **For:** a custom order, or a gradient over a subset, such as a model's weights but not its data.
- **Against:** the gradient is the vector of partials with respect to every variable; a subset or another order is a list comprehension over `differentiate`.

Rejected.

### Ignoring unknown values in `evaluate`

- **For:** a single point with extra entries could be passed to any expression.
- **Against:** a misspelled key would be silently ignored. Since derivatives keep the original's variables, every partial of a gradient already accepts the same point.

Rejected.
