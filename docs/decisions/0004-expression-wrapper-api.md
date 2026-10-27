# 0004. An immutable `Expression` wrapper as the user-facing API

- **Status:** Accepted
- **Date:** 2026-10-27

## Context

Using the library meant chaining modules by hand: `parser.parse(tokenizer.tokenize(source))`, then `evaluator.evaluate(tree, values)`, and `differentiate(tree, ast.VariableNode('x'))`, which takes a node the user has to build. Higher-order derivatives and gradients repeated this plumbing, and a typo in a variable name only surfaced at evaluation time, if that branch was ever evaluated.

We want users to give an expression as a string together with its variables, evaluate it at any point, and differentiate it, getting back something they can evaluate or differentiate again with the same interface.

## Decision

Add `pyparser.Expression`, a class wrapping a parsed tree and its declared variables:

```python
f = Expression('x ^ 2 * y', variables=['x', 'y'])
f.evaluate({'x': 3, 'y': 2})                    # 18
f.differentiate('x', order=2)                   # Expression('...', variables=('x', 'y'))
f.differentiate('x').differentiate('y').evaluate({'x': 3, 'y': 2})
```

- **Parse once, validate early.** The constructor tokenizes and parses the source, and raises `ExpressionError` with the position of the first use of an undeclared variable. Declaring `x` covers both `x` and `x[i]`; duplicate declarations are rejected, unused ones allowed.
- **Values are a mapping.** `evaluate(values)` requires exactly the declared variables.
- **Derivatives are wrappers.** `differentiate(var, order)` parses `var` (`'x'` or `'x[1]'`) with the existing tokenizer and parser, applies `operations.differentiator.differentiate` `order` times, and wraps the resulting tree in a new `Expression` with the same declared variables, without re-parsing.
- **Immutable and comparable.** Instances can't be modified, and compare and hash by `(tree, variables)`, so trees compare structurally as elsewhere.
- **No behaviour moves into the AST.** The class only delegates to the existing operation functions (see [0001](0001-operations-use-pattern-matching-instead-of-visitors.md)); the lower-level functions remain public.

The check for undeclared variables lives in one function, using the `helpers.variable_uses` operation, so names that need no declaration (such as built-in constants) can be skipped there.

## Consequences

- **One import for common use.** Parsing, evaluating, printing and differentiating, including nth derivatives and gradients, go through one object.
- **Errors move earlier.** Undeclared names fail at construction with a position, and missing or extra values fail before evaluation starts.
- **Derivatives keep every declared variable**, even ones they no longer use (`d/dx (x + y)` is `1 + 0`), so they must still be given a value for `y`. This keeps every derivative of an expression interchangeable, such as the partials of a gradient evaluated at the same point.
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

### Inferring variables from the source

- **For:** nothing to declare.
- **Against:** a typo becomes a new variable instead of an error, and the declared order, which gives the order of `gradient()` and of the user's values, would depend on where names first appear.

Rejected.
