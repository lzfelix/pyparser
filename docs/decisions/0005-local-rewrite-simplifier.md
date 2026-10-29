# 0005. A local-rewrite simplifier, without a normal form

- **Status:** Accepted
- **Date:** 2026-10-29

## Context

The differentiator applies its rules mechanically, so results are correct but full of terms that cancel: `d/dx (3 * x ^ 2 + 2 * x)` gives `0 * x ^ 2 + 3 * (2 * x ^ (2 - 1) * 1) + (0 * x + 2 * 1)`. Every order copies the previous order's noise, so higher-order derivatives grow fast: the third derivative of `x * sin(x)` printed to 281 characters.

Simplification can mean very different amounts of work. Removing `* 1` and `+ 0` is a handful of local rules; recognizing that `x * 2 + 3 * x` is `5 * x` needs a normal form, where sums and products are flattened, sorted and combined; and deciding whether two arbitrary expressions are equal is undecidable in general.

## Decision

Add `operations.simplifier.simplify(root)`, a plain function like the other operations (see [0001](0001-operations-use-pattern-matching-instead-of-visitors.md)). It rebuilds the tree bottom-up: each node's children are simplified first, then a fixed set of local rules is applied to the node itself.

- **Constant folding:** `+`, `-`, `*` and `^` between two numbers are computed, as are signs on numbers. Division isn't folded, so `1 / 3` stays exact instead of becoming `0.3333333333333333`.
- **Identities:** `u + 0`, `0 + u`, `u - 0`, `u * 1`, `1 * u`, `u / 1`, `u ^ 1` and `+u` become `u`; `0 - u` becomes `-u`; `u * 0`, `0 * u` and `0 / u` become `0`; `u ^ 0` and `1 ^ u` become `1`; and `-(-u)` becomes `u`.
- **Negative numbers are negations.** Folding `2 - 5` gives `-(3)`, a sign applied to a positive number, which is how the parser reads `-3`, so a simplified tree prints into text that parses back into the same tree.

Since every rule's result is already simplified, one pass reaches a fixed point: simplifying twice gives the same tree as simplifying once.

`Expression.differentiate` and `Expression.gradient` simplify after each order, so later orders start from a small tree, and `Expression.simplify()` is available for any expression. The expression built from a source is not simplified, and the lower-level `differentiate` still returns the raw tree.

## Consequences

- **Readable derivatives.** `d/dx (x * sin(x))` prints as `sin(x) + x * cos(x)`, and its third derivative shrinks from 281 to 45 characters.
- **Results are not canonical.** No rule reorders or combines terms. These are left as they are:
  - like terms: `x + x`, `x - x`, `x * x`, and the third derivative of `x * sin(x)`, which prints as `-sin(x) + (-sin(x) + (-sin(x) + x * -cos(x)))` instead of `-3 * sin(x) - x * cos(x)`;
  - coefficients separated by a variable: `3 * (2 * x)` and `2 * x * 3` don't become `6 * x`, while `x * (2 * 3)` does become `x * 6`;
  - signs: `x * -y` and `a + -b` keep the negation where the rules produced it.
- **Equal values don't mean equal expressions.** Equality stays structural, so `x + 1` and `1 + x` remain different even after simplifying.
- **Only arithmetic on numbers is folded.** Functions and constants stay symbolic, so `cos(0)` and `log(e)` are kept; the derivatives of `e ^ x` carry a factor of `log(e)` per order.
- **Some folds are skipped:**
  - divisions, such as `4 / 2`;
  - powers whose exponent is above 64 in absolute value, so that `9 ^ 9 ^ 9` doesn't take ages to compute;
  - operations that would fail or give no real finite number, such as `0 ^ -1`, `(-8) ^ 0.5` or overflowing to infinity, which are left for the evaluator to report.
- **Folding happens in floating point**, the same as evaluating would: `0.1 + 0.2` becomes `0.30000000000000004`. A folded float that Python prints in scientific notation, such as `1e+20`, can't be tokenized back.
- **Some errors are simplified away.** `0 * u`, `u ^ 0`, `1 ^ u` and `0 / u` don't look at `u`, so `0 * log(x)` evaluates to `0` even where `log(x)` would raise, and `0 / x` evaluates to `0` at `x = 0`. A simplified tree never gives a different number where the original gives one; it can only give a number where the original raised. `0 / 0` written with numbers is kept.
- **Integers and floats can swap.** `x / 1` simplifies to `x`, so it evaluates to `2` instead of `2.0` for `x = 2`; `x * 0.0` simplifies to `0`.

## Alternatives considered

### A normal form

Flatten sums and products into lists, sort their terms, combine coefficients and like terms, and print back.

- **For:** results like `6 * x` and `-3 * sin(x) - x * cos(x)`, and equal results for mathematically equal polynomials.
- **Against:** much more code, and a design of its own: an ordering for every kind of term, rules for powers and products of sums, and a way to print the normal form back without it looking alien.

Deferred. The local rules already remove most of the noise from derivatives, and a normal form can be added later as another pass.

### Simplifying inside the differentiator

Build `u' * v` only when neither factor is `0` or `1`, and so on, while differentiating.

- **For:** no intermediate garbage.
- **Against:** every rule in the differentiator would grow special cases, mixing two concerns that are easier to test apart, and the simplifier wouldn't be available for expressions that aren't derivatives.

Rejected.

### Folding functions and constants

Evaluate `cos(0)`, `log(e)` or `2 * pi` while simplifying.

- **For:** fewer leftover terms, notably `log(e)`.
- **Against:** most results are irrational, so `log(2)` would become `0.6931471805599453`, losing the symbolic form [0003](0003-constants-are-resolved-at-evaluation-time.md) keeps on purpose. Exact cases such as `log(e)` or `cos(0)` would need rules of their own.

Rejected for now.
