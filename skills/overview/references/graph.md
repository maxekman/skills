# The Linear graph

The board draws a Linear team's path to unblock from `.overview/graph-<TEAM>.json`, one file
per team, shared by every repo on that team. Only the guide can write it, because the script
can't reach Linear. It lives outside `notes.json` because the guide rewrites that file whole on
every change and loads it with the skill, and a hundred nodes would ride along each time.

Linear can't list blockers: they cost one `get_issue` per issue. A team with 400 open issues
would take hundreds of calls and many minutes, with the board blank all the while. So the file
is written as soon as the issues are listed, and blockers are read a batch at a time.

## When to refresh

- The file is missing, or this is the first wake of a guide session.
- A PR merged in one of the team's repos. Refresh before `/skills:backlog next`.
- A workspace moved onto an issue that is not in the file.
- The 30-minute heartbeat.

Refresh on no other wake. Run each refresh in a background `Agent` with this file's steps, the
team, the issue IDs the workspaces are on or hinted at, and the merged issue if any. Don't wait
for it: the board picks up each write by itself.

## Shape

```json
{
  "fetched_at": "2026-11-17T15:40:00Z",
  "projects": {"Offline mode": {"done": 4, "total": 11, "active": true}},
  "nodes": {
    "DEV-44": {"title": "Sync on reconnect", "state": "unstarted", "project": "Offline mode",
               "parent": "DEV-40", "blocked_by": ["DEV-41"], "priority": 2, "assignee": null,
               "subs": [0, 0], "updated_at": "2026-11-17T09:12:44Z",
               "read_at": "2026-11-17T15:41:02Z"}
  }
}
```

- `fetched_at`: UTC in exactly this format, or the board can't show the age.
- `state`: the issue's `statusType`. The board hides `triage`, `completed` and `canceled`.
- `parent`: the parent's human ID. A top-level parent is the issue's epic on the board.
- `blocked_by`: blockers that are not `completed` or `canceled`, or `null` until they are read.
  The board shows an unread issue as `?`, never as ready. A blocker whose state is unknown
  stays in: a wrong "ready" sends someone to work that can't start.
- `priority`: 1–4, `null` for none. `assignee`: the name of someone other than the user, `null`
  when it is unassigned or the user's own, so the board can tell "someone else has it".
- `subs`: `[done, total]` sub-issues, for an issue that has any.
- `updated_at`, `read_at`: the issue's `updatedAt`, and when its blockers were last read. The
  next refresh compares them. The board ignores both.

## Refresh

1. **Projects.** The projects of the issues the workspaces are on or hinted at. Only when that
   gives fewer than two, add projects in progress from `list_projects`, up to two in all: a busy
   team has dozens in progress, far more than a pane can show. Mark each one `active`.
2. **Issues.** One `list_issues` per project, in every state, with
   `fields: id, title, statusType, priority, assignee, assigneeId, parentId, project, updatedAt`;
   follow `cursor` until it runs out. Count each project's `done` (`completed` or `canceled`) and
   `total`, and each parent's `subs`. Keep every open row as a node, and each issue a workspace
   is on even once it closed, with its `parent`: the board keeps that epic in view.
   Carry `blocked_by` and `read_at` over from the old file. **Write the file now.**
3. **Blockers.** `get_issue(id, includeRelations: true)` for at most 30 open issues that aren't
   epics, in this order, each once:
   1. the issues the merged issue blocked, after a merge;
   2. the issues the workspaces are on or hinted at, and the rest of their epics;
   3. issues whose `updatedAt` is newer than their `read_at`;
   4. unread ones, highest priority first;
   5. the oldest `read_at`.

   **Write the file again** after every ten. Unread issues fill in over the next heartbeats.

Find the user's own ID with `get_user` once per session.
