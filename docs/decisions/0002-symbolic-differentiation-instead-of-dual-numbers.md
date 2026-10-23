# 0002. Symbolic differentiation instead of dual numbers

- **Status:** Accepted
- **Date:** 2026-10-23

## Context

We want to differentiate expressions: given `x * sin(x)` and the variable `x`, produce `sin(x) + x * cos(x)` (or an equivalent tree). The result must be an expression that can be printed, simplified, evaluated with any variable values, and differentiated again.

Two broad approaches exist:

- **Symbolic differentiation:** walk the AST and build a new tree by applying derivative rules (sum, product, quotient, power and chain rules).
- **Automatic differentiation with dual numbers** (forward mode): evaluate the expression on pairs `(value, slope)` whose arithmetic follows the derivative rules, since `(a + a'ε)(b + b'ε) = ab + (a'b + ab')ε` when `ε² = 0`. To differentiate at `x = 2`, `x` is bound to the dual number `2 + 1ε`, written `(2, 1)`: the `2` is the point, and the `1` is the *seed* marking `x` as the variable being differentiated by (`dx/dx = 1`; other variables get slope `0`). Evaluating then returns `(f(2), f'(2))`.

## Decision

Implement symbolic differentiation as an operation that returns a new tree: `differentiate(root, var) -> ast.Node`, under `operations/`.

Built-in functions provide their own derivative as a tree builder (`functions.Function.derivative`), and the differentiator applies the chain rule.

## Consequences

- **The derivative is an expression.** It can be printed with `printer.to_string`, evaluated at any point, simplified, and differentiated again for higher-order derivatives.
- **Results grow and need simplifying.** Applying the rules mechanically produces correct but verbose trees (`d/dx (3 * x)` gives `0 * x + 3 * 1`). A simplifier is a separate, planned operation; the differentiator only applies rules.
- **Verification is approximate.** The differentiator is tested with exact tree comparisons for individual rules, and with finite differences (`(f(x + h) - f(x - h)) / 2h`) for combinations, which need a tolerance.

## Alternatives considered

### Dual numbers (forward-mode automatic differentiation)

- **For:**
  - Exact derivative values, with no approximation error and no tolerance.
  - Cost is roughly one evaluation regardless of expression size, with no growth in intermediate expressions.
  - Mostly reuses the evaluator, which already computes with Python operators: binding a variable to a `Dual` class that overloads them nearly suffices. Function calls and the evaluator's `numbers.Number` check would need small hooks.
- **Against:**
  - **It never produces the derivative expression, only its value at one point.** A new point needs a new evaluation, and there is nothing to print, simplify or differentiate again. This doesn't meet the goal.

Rejected as the way to differentiate.

## Future option

Dual numbers remain a good fit for two things, and may be added later as a separate operation (e.g. `derivative_at(tree, wrt, point, variables)`):

- **An exact test oracle** for the symbolic differentiator, replacing finite differences.
- **Cheap point derivatives** when the expression itself isn't needed.

Implementation notes for that case:

- Function derivatives can reuse `Function.derivative` by evaluating the derivative tree at the dual's value, keeping a single source of truth.
- The general dual rule for `a ^ b` uses `log(a)`, which fails for negative bases; when the exponent's slope is zero, use `n * a^(n-1)` instead.
