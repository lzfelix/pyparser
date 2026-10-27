# 0003. Constants are resolved at evaluation time

- **Status:** Accepted
- **Date:** 2026-10-27

## Context

We want built-in constants, starting with `e` and `pi`, so users can write `2 * pi * r` without passing `pi` themselves. The main motivation is exponentials: with `e` available, `e ^ x` works, and so does its derivative, through the existing constant-base power rule.

Constants are spelled like variables (`pi`, `e`), so something has to tell them apart. That could happen at any stage of the pipeline: the tokenizer, the parser, or the operations that walk the tree.

## Decision

Constants live in their own read-only mapping, `pyparser.constants.CONSTANTS`, separate from the built-in functions in `pyparser.functions`.

The tokenizer and parser don't know about them: `pi` is parsed into a `VariableNode('pi')` like any other name. Each operation decides what a constant means to it:

- **Evaluator:** a `VariableNode` named after a constant evaluates to its value. Binding a constant's name in `variables` raises `EvaluationError` up front, even when the expression doesn't use it, and indexing a constant (`pi[0]`) raises too.
- **Printer:** unchanged; `2 * pi` prints as `2 * pi`.
- **Differentiator:** constants need no special case, since `depends_on` already treats any name other than `var` as constant, so their derivative is `0`. Differentiating *with respect to* a constant raises `DifferentiationError`.

Names are case-sensitive, so `E` and `PI` remain ordinary variables.

`e ^ x` differentiates to `e ^ x * log(e) * 1` through the constant-base rule, which evaluates to `e ^ x`. No `exp` function is added.

## Consequences

- **Trees stay symbolic.** Printed expressions and derivatives keep `pi` and `e` instead of `3.141592653589793`, so results remain readable and can be parsed back into the same tree.
- **No grammar change.** The tokenizer, parser and AST are untouched; only the evaluator and differentiator know about constants.
- **Constant names are reserved.** A caller who passes `{'pi': 3}` gets an error instead of a value that is silently used or silently ignored. Callers that used `e` or `pi` as ordinary variables before must rename them.
- **Derivatives are unsimplified.** `d/dx e ^ x` contains `log(e)`, which only becomes `1` when evaluated. Folding it is left to the planned simplifier.
- **Calling a constant (`e(2)`) is still an unknown-function error**, since function calls are looked up in `BUILTINS` only.

## Alternatives considered

### Resolve constants in the parser to `NumberNode`

The parser (or tokenizer) would replace `pi` with `NumberNode(math.pi)`.

- **For:** the evaluator and differentiator would need no changes at all.
- **Against:** the symbol is lost as soon as the expression is parsed. `2 * pi` would print as `2 * 3.141592653589793`, and `d/dx e ^ x` as `2.718281828459045 ^ x * log(2.718281828459045) * 1`. It also mixes evaluation concerns into the parser.

Rejected.

### Let users override constants through `variables`

Passing `{'e': 2}` would make `e` evaluate to `2`, with constants acting as default values.

- **For:** no reserved names; existing callers that already use a variable called `e` keep working.
- **Against:** the same tree would mean different things depending on the bindings, and a tree containing `e ^ x` would be differentiated as an exponential while possibly being evaluated as `2 ^ x`. It would also silently change results for callers who forgot a variable was shadowing a constant.

Rejected as ambiguous: binding a constant's name raises instead.
