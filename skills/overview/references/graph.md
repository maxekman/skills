# The Linear graph

The board draws a Linear team's path to unblock from `.overview/graph-<TEAM>.json`, one file
per team, shared by every repo on that team. Only the guide can write it, because the script
can't reach Linear. It lives outside `notes.json` because the guide rewrites that file whole on
every change and loads it with the skill, and a hundred nodes would ride along each time.

## When to refresh

- The file is missing, or this is the first wake of a guide session.
- A PR merged in one of the team's repos. Refresh before `/skills:backlog next`, and fetch every
  open issue's relations (step 3), since the merge is when the graph's shape changes most.
- A workspace moved onto an issue that is not in the file.
- The 30-minute heartbeat.

Refresh on no other wake: each refresh costs Linear calls, and the board shows the file's age.

## Shape

```json
{
  "fetched_at": "2026-11-17T15:40:00Z",
  "projects": {"Offline mode": {"done": 4, "total": 11, "active": true}},
  "nodes": {
    "DEV-44": {"title": "Sync on reconnect", "state": "unstarted", "project": "Offline mode",
               "parent": "DEV-40", "blocked_by": ["DEV-41"], "priority": 2, "assignee": null,
               "subs": [0, 0], "updated_at": "2026-11-17T09:12:44Z"}
  }
}
```

- `fetched_at`: UTC in exactly this format, or the board can't show the age.
- `state`: the issue's `statusType`. The board hides `triage`, `completed` and `canceled`.
- `parent`: the parent's human ID. A top-level parent is the issue's epic on the board.
- `blocked_by`: blockers that are not `completed` or `canceled`. A blocker whose state is
  unknown stays in: a wrong "ready" sends someone to work that can't start.
- `priority`: 1–4, `null` for none. `assignee`: the name of someone other than the user, `null`
  when it is unassigned or the user's own, so the board can tell "someone else has it".
- `subs`: `[done, total]` sub-issues, for an issue that has any.
- `updated_at`: the issue's `updatedAt`, which the next refresh compares. The board ignores it.

## Fetch

1. **Roots.** `list_projects` for the team; mark the ones in progress `active`. Add the
   projects of the issues the workspaces are on and of the `next` hints.
2. **Issues.** One `list_issues` per root project, in every state, with
   `fields: id, title, statusType, priority, assignee, assigneeId, parentId, project, updatedAt`.
   From these rows, count each project's `done` (`completed` or `canceled`) and `total`, and each
   parent's `subs`. Keep every open row as a node, and each issue a workspace is on even once it
   closed, with its `parent`: the board keeps that epic in view until the workspace moves on.
3. **Relations.** `get_issue(id, includeRelations: true)` for each open node that is new or whose
   `updatedAt` changed, and for every open node after a merge. Carry the rest over from the
   old file.
4. **Write** the whole file in one `Write`. The board reads it every 5 seconds, and a file left
   half-written shows as a warning until the next refresh.

Find the user's own ID with `get_user` once per session.
