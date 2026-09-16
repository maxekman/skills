# Resolving `#N` arguments

When `/pr` arguments contain `#N` (e.g. `/pr #26`), determine whether it's an existing PR or an issue.

## 1. Try PR first

```bash
gh pr view N --json number,headRefName,title,url,body
```

Success → existing PR; follow the update-PR flow in the main skill.

## 2. Then try issue

```bash
gh issue view N --json number,title,body,labels
```

Success → create a **new PR** seeded from the issue:

- Derive the PR title from the issue title (apply normal title-format rules).
- Derive the branch name from the issue title (apply normal branch-naming rules).
- Include `Closes #N` in the PR description.
- Use the issue body as context when writing the description.

## 3. Neither

Stop and tell the user — `#N` doesn't resolve to a PR or issue.
