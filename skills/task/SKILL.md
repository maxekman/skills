---
name: task
argument-hint: "[create|update|search|implement] [details]"
allowed-tools: mcp__*, Read, Grep, Glob, Bash, Edit, Skill
description: Issue management for Linear (MCP) and GitHub Issues (gh CLI) - handles creation, updates, search, and gathering context for implementation. `implement <id-or-url>` also carries finished work to a commit and PR via /jj and /pr. Use for tracker operations. For local multi-step implementation checklists tied to a feature, /todo is the working-memory counterpart.
---

# Issue Management

Handle issue/tracker management across Linear and GitHub Issues. Pick the backend, then fulfill: $ARGUMENTS

If no arguments, show issues assigned to the current user, grouped by status.

## Backend Detection

1. **Linear** — when `mcp__*` Linear tools are available in the session. Primary interface for Linear.
2. **GitHub Issues** — when the project is a GitHub repo (`gh repo view` confirms). Use the `gh` CLI exclusively, never raw API calls.

If both are available, prefer whichever the project actively uses. When uncertain, ask.

## Writing Style

- **Titles**: imperative, 3-7 words ("Fix login timeout on mobile").
- **Descriptions**: problem + context in 1-2 sentences max.

## Commands

### Default (no args)
Show issues assigned to the current user, grouped by status.

### Create
`/task create <title>` — new issue. Infer project/repo from context.

### Search / List / Show
- `/task list` or `/task mine` — your assigned issues.
- `/task search <query>` — free-form search.
- `/task show <id>` — detailed view of a single issue.

### Update
- `/task update <id> status <state>` — move through workflow.
- `/task comment <id> <text>` — add a comment.

### Break Down
`/task break down <id>` — read the issue, split into smaller subtasks. Each independently completable. Link parent-child where the backend supports it.

### Implement
`/task implement <id-or-url>` — carry an issue from tracker link to merged-ready PR. Two phases:

- **Context** — fetch, read, grep, present. Read-only, so it is safe inside plan mode. It also pins the branch name and PR title from the Linear slug, which is what lets `/pr` attach the PR to the issue later.
- **Delivery** — after you have built the thing, a quality gate runs. If it passes, `/jj` and `/pr` are invoked autonomously; if it fails, the work stops and reports what is unmet.

Accepts `ACME-407`, Linear URLs (including the copy-paste `linear.app/<ws>/issue/ACME-407/<slug>` form), `#42`, or GitHub URLs. See `references/implement.md` for the full flow — read it whole, since the delivery contract has to be in context by the time the work finishes.

Not every issue ends in code. Spikes, research, and scoping issues land findings, an ADR, or a set of follow-up issues instead — `implement.md` step 3 names the shape up front so the gate knows what done means.

If the work needs a multi-step local breakdown as you build, `/todo` is the local-task counterpart — `/task` knows about the tracker issue, `/todo` tracks the implementation steps.

## When to Read References

- `references/implement.md` — args contain `implement <id-or-url>`.
- `references/linear.md` — backend is Linear; covers MCP tool patterns and query syntax.
- `references/github.md` — backend is GitHub Issues; covers the full `gh issue` command table and filter flags.

The basic verbs (list/create/view/edit/comment/close) are predictable — go straight to the command. Read the backend reference when you need full query syntax or a less-common flag.

## Safety

- Never delete or close issues without explicit user confirmation.
- Never bulk-update without confirmation.
- Verify an issue exists before modifying it.
- Don't put secrets or sensitive data in issue bodies.
- `implement`'s context phase is read-only — never modifies files or mutates tracker state.
- `implement`'s delivery phase commits and opens PRs on its own once its gate passes, but still never writes to the tracker unprompted. Creating follow-up issues or posting findings as a comment needs explicit confirmation.
