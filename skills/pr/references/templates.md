# PR description templates

## Project template detection

Check, in order:

1. `.github/PULL_REQUEST_TEMPLATE.md`
2. `.github/pull_request_template.md`
3. `pull_request_template.md`
4. `docs/pull_request_template.md`
5. `.github/PULL_REQUEST_TEMPLATE/` directory

If found, use it exactly — preserve all formatting and structure. Never add promotional content or AI attribution.

## Fallback (no project template)

```
## Summary
- <change 1>
- <change 2>

## Test plan
- [ ] Tests pass
- [ ] Manual verification
```

## Stacked PR notice

When a parent PR exists (see `stacked.md`), prepend before the template content:

```
> **Stack**: based on #<parent-pr-number> — review/merge that first.
```
