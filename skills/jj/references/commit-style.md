# Commit message style

The diff already shows *what* changed — filenames, functions, line counts. The commit message adds what the diff cannot: **how** the change works conceptually and **why** it makes things better.

## Title

Imperative verb describing the *outcome*, not the mechanism. Don't restate file or function names — those are in the diff. ≤50 chars.

## Body (when needed)

Present-tense prose. Explain how the approach works at a conceptual level and what it improves. Describe gains, tradeoffs resolved, problems eliminated. No bullet lists. No filenames. No function signatures. ≤72 chars per line.

## Example

**Before** (what-focused, mechanical):

```
feat(auth): add JWT validation middleware

- Added validateToken() in auth/middleware.ts
- Updated routes/index.ts to use new middleware
- Added RS256 key rotation support in config.ts
```

**After** (how/why-focused):

```
feat(auth): validate tokens at the edge

Incoming requests now prove identity before reaching
any handler, so downstream code no longer needs its
own auth checks. Key rotation happens transparently
on a schedule, removing a manual operational step.
```

The "after" version tells a reader *what changed about the system*, not *which lines moved where*.
