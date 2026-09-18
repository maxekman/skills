---
name: backlog
argument-hint: "[status|next|groom|place|triage] [project or id]"
allowed-tools: mcp__*, Read, Grep, Glob, Bash, Skill
description: Backlog grooming and planning for Linear — rank what to work on next, decide where a new issue belongs, and clean up statuses, priorities and stale relations across many issues at once. Use when the question spans the backlog rather than one ticket. For single-issue operations and starting work, /task is the counterpart.
---

# Backlog Grooming

Cross-issue view of a Linear backlog: what to work on next, where new work belongs, and what
is rotting. Handle: $ARGUMENTS

If no arguments, show the health snapshot (`status` below).

`/task` is the single-issue verb — create, update, implement one ticket. `/backlog` is the
plural one: it reads many issues, ranks them against each other, and proposes changes in a
batch. When grooming settles on an issue to actually work, hand off with `/task implement <id>`.

## Backend

Linear via MCP only. The ordering and priority model below has no GitHub equivalent — GitHub
Issues has no priority field, and Projects v2 ordering is unreachable from the `gh` CLI. In a
GitHub-backed repo, say so and defer to `/task`.

Tools are named `mcp__linear-server__<action>`. If a session exposes a differently-named
Linear server, fall back to matching `mcp__*<action>*` — the actions are stable. If no Linear
server is connected, stop and say so; never scrape `linear.app` over HTTP.

## Rank contract

**Linear's MCP has no ordering primitive.** There is no `sortOrder`, `position`, or
`boardOrder` on `save_issue`, and no ordering field to read back. Backlog order is therefore
*derived*, never set. Say this plainly when someone asks to move an issue up — then express
the intent through the levers that do exist.

Rank key, highest first:

1. **priority** — `1` Urgent → `4` Low. `0` (None) sorts last, after Low.
2. **unblocked** — every `blockedBy` issue is `completed` or `canceled`. A blocked issue
   cannot be next no matter its priority; surface it as blocked instead.
3. **milestone** — nearer `projectMilestone` first. No milestone sorts after any milestone.
4. **age** — older `createdAt` first. Pure tiebreak; never promote on age alone.

To express "A should come before B":

| Situation | Move |
|---|---|
| Same priority tier | Add `blockedBy` on B pointing at A — a real dependency, and it ranks |
| Different tiers, and the order is genuinely wanted | Raise A's priority, and state the reason in the proposal |
| Neither is true | Say it cannot be expressed. Offer a milestone split, or tell the user to drag it in the Linear UI |

Never invent a `sortOrder` argument to make the third row go away.

## Commands

### Default / `status`
Health snapshot, no writes. Counts by `statusType`, work in progress, anything `started`
without an assignee, and the stale count. One screen — this is the "how bad is it" view, and
`groom` is the one that does something about it.

### `next [n]`
What to work on now, default 3. Apply the rank contract and show *why* each ranks where it
does — the reason line is the point, since a rank you cannot argue with is a rank you cannot
correct. Exclude anything blocked, and list blocked-but-otherwise-top issues separately with
the blocker named. Hand the chosen issue to `/task implement <id>`.

### `groom [project|team]`
The defect pass: read a slice of the backlog, find what is malformed, propose fixes, apply on
confirmation, verify. Scope to a project or team — a whole-workspace groom is too big to
review in one go. See `references/grooming.md`.

### `place <id-or-title>`
Where does this belong? Answers five things: project, milestone, labels, priority tier (named
against the neighbours it would sit among, not in the abstract), and which `blockedBy` edges it
needs.

Reach for it *before* `/task create` when the placement isn't obvious — several projects are
plausible, the work spans them, or it is the first of its kind. `/task` places the clear-cut case
itself. Either way it lands somewhere deliberate, which matters because Linear has no "insert
here": an issue created without a priority and project is exactly the one that turns up in a
random spot later.

### `triage`
Issues with `statusType: triage`, or missing priority or project. For each, propose a home —
priority tier, project, milestone — and confirm as a batch.

## When to Read References

- `references/linear.md` — **before any write, always.** Carries the verified tool surface,
  the priority rubric, and the write contract that keeps a status change from silently
  vanishing. Also read it before a non-trivial read, so the `fields` and filter arguments are
  right first time.
- `references/grooming.md` — args contain `groom` or `triage`.

## Safety

- Never write without showing the full proposal first and getting confirmation. The whole
  point of a batch is that it is reviewable before it lands.
- Never bulk-close. Closing is per-issue and always asks, even inside a confirmed batch.
- Never change an issue owned by someone else without calling that out in the proposal.
- Verify every write by reading the result back. An unconfirmed write is a failed write —
  report it as such. See the write contract in `references/linear.md`.
- `status`, `next`, and `place` are read-only. Only `groom` and `triage` write, and only
  after confirmation.
