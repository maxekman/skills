---
name: backlog
argument-hint: "[status|next|groom|place|triage] [scope or id]"
allowed-tools: mcp__*, Read, Grep, Glob, Bash, Skill
description: Backlog grooming and planning for Linear and GitHub Issues — rank what to work on next, decide where a new issue belongs, and clean up statuses, priorities, milestones and stale relations across many issues at once. Use when the question spans the backlog rather than one ticket, including "what should I pick up next" in a repo that tracks work in GitHub Issues. For single-issue operations and starting work, /task is the counterpart.
---

# Backlog Grooming

Cross-issue view of a Linear or GitHub Issues backlog: what to work on next, where new work
belongs, and what is rotting. Handle: $ARGUMENTS

If no arguments, show the health snapshot (`status` below).

`/task` is the single-issue verb — create, update, implement one ticket. `/backlog` is the
plural one: it reads many issues, ranks them against each other, and proposes changes in a
batch. When grooming settles on an issue to actually work, hand off with `/task implement <id>`.

## Backend

Detect it the way `/task` does:

1. **Linear** — Linear MCP tools are in the session. They are named
   `mcp__linear-server__<action>`; if a session exposes a differently-named Linear server, fall
   back to matching `mcp__*<action>*` — the actions are stable. Never scrape `linear.app` over
   HTTP.
2. **GitHub Issues** — `gh repo view` succeeds. Use `gh issue` and `gh label` only, never
   `gh api`.

If both are available, use the one the project actively tracks work in. When uncertain, ask.

## Rank contract

**Neither backend has an ordering primitive you can reach.** Linear's MCP has no `sortOrder`,
`position`, or `boardOrder`; GitHub has no priority field, and Projects v2 board order is out of
reach from `gh`. Backlog order is therefore *derived*, never set. Say this plainly when someone
asks to move an issue up — then express the intent through the levers that do exist.

Rank key, highest first:

1. **priority** — Linear: `1` Urgent → `4` Low, with `0` (None) after Low. GitHub: only when
   the repo's labels already define a scheme (`P0`–`P3`, `priority:*`); otherwise skip this
   step and say so in the output.
2. **unblocked** — every blocker is finished (Linear `completed`/`canceled`, GitHub `CLOSED`).
   A blocked issue cannot be next no matter its priority; surface it as blocked instead.
3. **effective milestone** — the earliest of the issue's own milestone and those of every open
   issue it blocks, transitively. An issue that blocks M1 work is M1 work. Nearer first; no
   milestone sorts after any milestone.
4. **reach** — how many open issues it unblocks, transitively. Repos that lean on blocking
   edges express priority this way, and it splits issues a milestone cannot.
5. **age** — older `createdAt` first. Pure tiebreak; never promote on age alone.

Candidates are open leaf issues nobody has picked up. A parent with open sub-issues is tracked
through its children, so rank the children — a child with no milestone takes its parent's.
Anything already in flight (Linear `started`, GitHub assigned) is excluded: list your own on one
line above the ranking, and leave out everyone else's without comment.

To express "A should come before B":

| Situation | Move |
|---|---|
| Same priority tier and milestone | Add `blockedBy` on B pointing at A — a real dependency, and it ranks |
| Different milestones, and the order is genuinely wanted | Move A into the earlier milestone |
| Different priority tiers, and the order is genuinely wanted | Raise A's priority (GitHub: only with an existing label scheme), and state the reason |
| None is true | Say it cannot be expressed. Offer a milestone split, or tell the user to drag it in the Linear UI or Projects board |

Never invent a `sortOrder` argument or a priority label to make the last row go away.

## Commands

### Default / `status`
Health snapshot, no writes. Counts by state, work in progress, anything in flight without an
owner, blocked, and the stale count. GitHub has only open and closed, so there an assignee *is*
the in-progress signal. One screen — this is the "how bad is it" view, and `groom` is the one
that does something about it.

### `next [n] [scope]`
What to work on now, default 3. Apply the rank contract and show *why* each ranks where it
does — the reason line is the point, since a rank you cannot argue with is a rank you cannot
correct. Exclude anything blocked, and list blocked-but-otherwise-top issues separately with
the blocker named. A free-text scope ("the software side") maps onto labels, milestones or
projects that exist — state the mapping you used. Hand the chosen issue to
`/task implement <id>`.

### `groom [scope]`
The defect pass: read a slice of the backlog, find what is malformed, propose fixes, apply on
confirmation, verify. Scope to a project or team (Linear), or a milestone or label (GitHub) — a
whole-backlog groom is too big to review in one go. See `references/grooming.md`.

### `place <id-or-title>`
Where does this belong? Answers project (Linear only), milestone, labels, priority tier (named
against the neighbours it would sit among, not in the abstract; on GitHub only with a label
scheme), parent, and which `blockedBy` edges it needs.

Reach for it *before* `/task create` when the placement isn't obvious — several homes are
plausible, the work spans them, or it is the first of its kind. `/task` places the clear-cut case
itself. Either way it lands somewhere deliberate, which matters because neither tracker has an
"insert here": an issue created unplaced is exactly the one that turns up in a random spot later.

### `triage`
Linear: issues with `statusType: triage`, or missing priority or project. GitHub: issues with
the repo's triage label if it has one, otherwise open issues with no labels. For each, propose a
home — priority tier, project or labels, milestone — and confirm as a batch.

## When to Read References

- `references/linear.md` — backend is Linear, **before any write, always.** Carries the
  verified tool surface, the priority rubric, and the write contract that keeps a status change
  from silently vanishing. Also read it before a non-trivial read, so the `fields` and filter
  arguments are right first time.
- `references/github.md` — backend is GitHub, before the first `gh` read. The relation fields
  have a shape that breaks the obvious jq, and one call returns the whole graph if you ask for
  it right. Also carries the write surface and its read-back.
- `references/grooming.md` — args contain `groom` or `triage`.

## Safety

- Never write without showing the full proposal first and getting confirmation. The whole
  point of a batch is that it is reviewable before it lands.
- Never bulk-close. Closing is per-issue and always asks, even inside a confirmed batch.
- Never change an issue owned by someone else without calling that out in the proposal.
- Never create a label, milestone or project to make a proposal fit. Place within what exists.
- Verify every write by reading the result back. An unconfirmed write is a failed write —
  report it as such. See the write contract in the backend's reference.
- `status`, `next`, and `place` are read-only. Only `groom` and `triage` write, and only
  after confirmation.
