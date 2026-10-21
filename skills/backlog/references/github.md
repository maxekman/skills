# GitHub Issues (`gh` CLI) — verified surface, the graph read, and the write contract

Everything below was checked against `gh` 2.102 on a live repo. Use `gh issue` and `gh label`;
never `gh api`.

## One read for the whole backlog

`gh issue list` returns relations for every issue in the same call — there is no reason to loop
`gh issue view` per issue:

```
gh issue list --state open --limit 300 --json \
  number,title,labels,milestone,assignees,createdAt,updatedAt,blockedBy,blocking,parent,subIssuesSummary
```

If the result has exactly `--limit` rows, say so and rank what came back rather than silently
truncating. Narrow server-side with `--search` when the scope allows (`label:area:ui`,
`milestone:"M1 First deck"`).

**Never request `projectItems` or `projectCards`.** They need the `read:project` scope, and
without it the *whole* call fails, not just those fields.

## Field shapes

The relation fields are connections, not arrays. Reading them as arrays is the usual jq error
(`expected an object but got: array`).

| Field | Shape |
|---|---|
| `blockedBy`, `blocking`, `subIssues` | `{"nodes": [{id, number, state, title, url}], "totalCount": N}` |
| `parent` | `{id, number, state, title, url}` or `null` |
| `subIssuesSummary` | `{completed, total, percentCompleted}` |
| `milestone` | `{number, title, description, dueOn}` or `null` |
| `assignees`, `labels` | arrays of `{login}` / `{name}` |

Node `state` is `OPEN` or `CLOSED` and carries no close reason. When the reason matters, ask
for the not-planned set once — `gh issue list --state closed --search 'reason:"not planned"'
--json number` — and intersect.

A tab-separated working table for ranking:

```
--jq '.[] | [.number, (.milestone.number // "-"), ([.assignees[].login] | join(",")),
  ([.blockedBy.nodes[] | select(.state == "OPEN") | .number] | join(",")),
  ([.blocking.nodes[]  | select(.state == "OPEN") | .number] | join(",")),
  (.parent.number // "-"), "\(.subIssuesSummary.completed)/\(.subIssuesSummary.total)",
  .createdAt[0:10], ([.labels[].name] | join(",")), .title] | @tsv'
```

## Mapping the rank contract

- **priority** — run `gh label list --limit 200 --json name` once. A scheme exists if labels
  like `P0`–`P3`, `priority:high`/`priority: low`, or `urgent` are present *and applied*. Map
  the highest to Linear's Urgent, and so on down. No scheme: skip the step and say "no priority
  labels — ranking on milestone, blockers and reach."
- **unblocked** — no `blockedBy` node is `OPEN`. The search `-is:blocked` agrees: GitHub's
  `is:blocked` matches only issues with an *open* blocker, so closed blockers are history.
- **milestone order** — by `dueOn`; when milestones have none, by `number` (creation order),
  and say which you used.
- **effective milestone and reach** — walk the `blocking` nodes from the one read: an issue's
  reach is the set of open issues reachable through `blocking`; its effective milestone is the
  earliest milestone in that set and its own. A node whose `url` points at another repo counts
  by its state only — don't fetch it.
- **leaf and in flight** — skip issues whose `subIssuesSummary.completed < total`, and issues
  with any assignee. `gh issue list --assignee @me` names yours for the in-flight line.

Useful search qualifiers: `-is:blocked`, `no:assignee`, `no:milestone`, `no:label`,
`sort:created-asc`, `label:"…"`, `milestone:"…"`, `reason:"not planned"`.

## Write surface

| Change | Command |
|---|---|
| Add / remove a blocker | `gh issue edit <n> --add-blocked-by <m>` / `--remove-blocked-by <m>` |
| Set / clear milestone | `gh issue edit <n> --milestone "<title>"` / `--remove-milestone` |
| Labels | `gh issue edit <n> --add-label "<l>"` / `--remove-label "<l>"` |
| Re-parent / un-parent | `gh issue edit <n> --parent <p>` / `--remove-parent` |
| Assign | `gh issue edit <n> --add-assignee <login>` |
| Close as stale | `gh issue close <n> --reason "not planned" --comment "<why>"` |
| Close as duplicate | `gh issue close <n> --duplicate-of <m>` |

Only use labels and milestones that already exist (`gh label list`, and the milestones seen in
the read). A typo'd name fails the call; an invented one is somebody else's cleanup.

## The write contract

**1. One `gh issue edit` per issue**, carrying only the fields this batch changes.

**2. Exit 0 is not verification.** `gh issue edit` prints the URL and nothing about what changed.
Read the changed fields back — `gh issue view <n> --json milestone,labels,blockedBy,parent` —
and compare to what was asked. A mismatch is a failed write; report it as one, with what the
read-back actually said.
