---
name: overview
argument-hint: "[init|status|find] [workspace, path or issue id]"
allowed-tools: Bash(/usr/bin/python3 ${CLAUDE_SKILL_DIR}/scripts/snapshot.py *), Bash(gh *), Bash(jj *), Bash(rex split *), Bash(rex block ls *), Read, Write, Edit, Skill, Agent, Monitor, ListAgents, SendMessage, PushNotification
description: Live guide for an umbrella folder of parallel, hand-run Claude sessions — watches every jj or git workspace under it, which issue each session is on, whether it is busy, idle or waiting on the user, and the PRs and tracker issues behind them, then says what needs attention - a session waiting on input, red checks or requested changes, a stalled session, a merge whose issue did not close. Suggests the next item for an idle free workspace and proposes the tracker follow-up after a merge, acting only on a yes. Use whenever the user wants an overview, orchestrator, dashboard or status of their agents or workspaces, asks where things stand, what the sessions are doing or which workspace is free, or starts Claude in a client or project umbrella folder rather than inside a repo, even without the word overview. Ranking work inside one repo is /backlog; post-merge cleanup inside a workspace is /wrapup.
---

# Umbrella Overview

A monitor that follows along while the user runs every worker session by hand. It runs from
the umbrella folder (the non-repo parent of a project's repos and their `-N` workspaces), keeps
a board of what each workspace is doing, and interrupts only when something needs the user. The
user picks up work in the sessions themselves. When a session starts on something, that is the
normal flow: record it on the board, without commentary. It never touches a working copy and
never picks what a session works on. It ranks with `/backlog` and leaves each workspace's
post-merge cleanup to `/wrapup`, run in that workspace: with `auto_wrapup` on, it sends that
to the one session that owns a merged PR.

Handle: $ARGUMENTS

## Context

- Umbrella: !`test -f .overview/config.json && echo "initialized: $(pwd)" || echo "not initialized: $(pwd)"`
- Notes: !`cat .overview/notes.json 2>/dev/null || echo "no notes.json yet"`

## The snapshot

Everything observable comes from one script. Run it with `/usr/bin/python3` (Python 3.9,
standard library only) so the umbrella's mise pins can't break it:

```bash
/usr/bin/python3 ${CLAUDE_SKILL_DIR}/scripts/snapshot.py              # JSON, the whole umbrella
/usr/bin/python3 ${CLAUDE_SKILL_DIR}/scripts/snapshot.py --watch      # a line per change, forever
/usr/bin/python3 ${CLAUDE_SKILL_DIR}/scripts/snapshot.py --discover   # proposed config.json
```

Per workspace it reports the `trunk()..@` stack (read with `--ignore-working-copy`, so it never
snapshots another session's files), bookmarks, `free`, and the tracker IDs found in commits and
bookmarks (`stack_ids`), `TODO.md` headers (`todo_ids`) and the latest prompt that named one
(`prompt_ids`), plus the TODO-queue items it is on (`queue_items`, below). It finds the umbrella by walking up from the cwd, so a drifting shell is fine. For
each live Claude session, taken from Claude Code's session registry (`~/.claude/sessions/`), it
gives `name` (the `SendMessage` address), `status`, `waiting_long`, `stalled`, `prompt_head` and
`asked` (idle, and its last message since the user's last prompt ended on a question).
Per repo it gives PRs by the user (or by anyone, with `"prs": "all"` in the config) that are
open or closed in the last 12 hours, with checks and review state. It also gives `queues`: each `*TODO.md` file
on trunk (narrowed by the repo's `"todos"` globs) with its open and done counts and `next`, its
first open box with that box's `label` (`S22`), `title`, `section` heading and tracker `ids`. A
workspace's `queue_items` are the open boxes it is on, `via` `stack` when a commit in its stack
ticks or edits the box, or `prompt` when the latest prompt naming work names the box's label or
its file. A box that carries a tracker ID is that issue, and goes by its ID. It also gives `trunk`: the
current result of each CI workflow on the default branch. Deploy and nightly workflows are
`lanes` instead, one per workflow and ref (a branch, or `tags`), so tag and release runs show
too. A lane is `pending`, `pass`, `fail`, `behind` (a deploy cancelled with no run after it,
so its target lags that branch) or `cancelled` (a tag run). `cut` lists the deploys a newer
merge cancelled, which went live with this run. The name says which workflows are lanes:
deploy, release, publish or promote, or nightly, scheduled or cron, or a `schedule` run seen
on trunk. `"lanes"` in a repo's config overrides it, and `"ci"` opts a workflow out. Last, it
gives GitHub issue states for the IDs it found. `gh` results are cached for 90 seconds in `.overview/cache/`. Linear issues are not in it: fetch those through the Linear MCP.

`warnings` comes first in the output. A registry-format warning means Claude Code changed the
file, and session data is missing until the script is fixed. The board shows it at the top;
say it in chat once.

## Commands

### `init`

Run once per umbrella. Creating `.overview/` is the opt-in. Read `references/init.md`.

### Default: the guide

1. **Catch up.** Read `.overview/config.json`, `notes.json` and `state.md`, run the snapshot,
   and fetch the state and title of each Linear issue a workspace is on. Refresh a Linear
   team's graph when `references/graph.md` says it is due.
2. **Reconcile.** Derive each workspace's state and act on every transition, as
   `references/lifecycle.md` describes. Read it on the first wake of a session.
3. **Write `notes.json`** (below) in one `Write`, only when something in it changed.
4. **Open the board pane** above the guide, so its prompt stays at the bottom, once, unless a block labelled `overview-board` already exists in
   `rex block ls -s "$REX_SESSION"`:
   ```bash
   rex split -s "$REX_SESSION" -b "$REX_BLOCK" --split=above --ratio 55 --focus=false \
     --label overview-board -- /usr/bin/python3 ${CLAUDE_SKILL_DIR}/scripts/snapshot.py --board --watch
   ```
   Outside Rex (`REX_BLOCK` unset), tell the user that command's last part instead, to run in
   any terminal.
5. **Arm the watcher.** Use `Monitor` with the `--watch` command, `timeout_ms: 1800000`, and a
   description naming the umbrella. Each line it prints is a hint that something changed. Do
   not act on the line itself: run the snapshot and reconcile again, because the snapshot is
   the truth and a line can be stale by the time it arrives. When the monitor expires after 30
   minutes, treat that as the heartbeat: reconcile and re-arm. If it exits with an error, report
   that and re-arm once. If it fails again, stop and say so, because a guide that is silently
   blind is worse than none.

**Be quiet.** The board pane shows the state, so the chat only carries what needs the user: a
push-worthy event, an offer, or a question, one line each. A wake that needs nothing from the
user ends the turn with no text at all. Never write "nothing needs you", "no change" or a
summary of what changed; the board already shows it. To read one workspace, use
`snapshot.py --workspace NAME`; otherwise `--board` or `jq`. Don't write throwaway scripts to
slice the snapshot.

In those lines, and in the `next` and `offers` you write to `notes.json`, name each issue and
PR with its title the first time it appears: `DEV-44 / Cache the venue list`,
`#63 / Add a CSV export endpoint`, `PR #70 / Publish the API reference`, and `app#123 / …` in
another repo of the same org, `org/repo#123 / …` across orgs. A one-line push gets read without
the board beside it, and a bare key leaves the user asking which issue it was. Keys inside a
command stay bare so the command still runs. Take titles from the snapshot or `titles`, fetch
the missing ones, and copy each as the tracker has it.

Between wakes, answer the user's questions from the latest snapshot: where things stand, what
a workspace is on, or what to pick up next.

### `status`

Print `--board` once and stop. No monitor, no writes. It works from any session under the
umbrella, including one in a workspace.

### `find <workspace | path | issue id>`

Name the live session to `SendMessage`, found by where it works rather than by its name. Other
sessions run this before messaging one: `ListAgents` shows only names, which are folder names
plus a suffix, and a near-match can be another project entirely.

Run the snapshot once. Match the argument against each workspace's name, each session's `cwd`
(at or below a given path, `elsewhere` included), and the issue IDs a workspace is on
(`stack_ids`, `todo_ids`, `prompt_ids`, each `queue_items` key, and `overrides` in the umbrella's
`.overview/notes.json`). Print each matching live session as
`name · cwd · status · prompt_head`, one per line:

```
app-3-37 · ~/Development/work/acme/app-3 · idle · /skills:task implement ACME-1588 now…
```

Zero matches: say so and print every live session under the umbrella instead, so the caller can
spot the one by what it is doing rather than by a similar name. Several: print them all. Never
pick one, since the caller is about to message whichever it gets. Read-only like `status`: no board, no monitor,
no writes, from any session under the umbrella.

## The board

`snapshot.py --board` draws it, and with `--watch` redraws it every 5 seconds, at no token
cost:

```
acme · 13:51

app    #418  Let users pick the list page size     working    idle 6m
app-2  #680  Retry failed webhook deliveries       working    ⚠ waiting 8m
app-3                                              free       idle 3m     next up: #63 / Add a CSV export endpoint (P1)
app-4  #266  Move image uploads to object storage  in review  no session  PR #677 draft ✓
site         Publish the pricing page              merged     no session  PR #31 merged · needs wrapup

Actions
  … app Deploy (dev): running d4e5f6a7 3m · carrying a1b2c3d4 (cut off)
  ✗ app Nightly e2e: 9f8e7d6c (6h ago)
  ✓ app Release · tags: v1.4.0 18m ago
  ✗ app main: CI (1h ago)

Offers
  close #61 / Ship the public API docs? PR #70 / Publish the API reference merged without "Closes"

Queues · app
  MIGRATION_TODO  4 open  ● M3 Backfill the invoices table  app-4
  SECURITY_TODO   2 open  ○ S1 Rotate the deploy key        = #75

Path to unblock · app
  M1 Public beta · 222/263
    #402 Harden the integrations · 3/9
      ● #680 Retry failed webhook deliveries      app-2 · unblocks 2
        └ #742 Alert on stuck webhooks
      ○ #63 Add a CSV export endpoint             → app-3 · unblocks 3
        └ #742 (also ← #680)
    ⛔ #71 Open the API to partners               waiting on #61 (Ship the public API docs)
```

**Actions** shows a deploy lane while it runs and for 2 hours after it passed, a nightly only
while it runs or is red, and plain CI only when red, so a quiet, green umbrella shows none.

**Queues** gives one line per TODO file with open boxes: the box a workspace is on (●), or else
the file's first open box (○), with `→ workspace` when a `next` hint names it and `= ID` when it
was filed in the tracker. `status` lists every open box under its heading.

**Path to unblock** is the board's guide to what comes next, drawn for each GitHub-tracked
repo from its open issues, and for each Linear team from the graph the guide keeps in
`.overview/graph-<TEAM>.json`, one tree for every repo on the team. Roots are the milestones or
projects of the issues the workspaces are on or hinted at, plus GitHub's open milestone due
soonest. Under each root, its epics (top-level parent issues)
hold blocker chains: each root is an issue that can start or is in flight, and its children are
what finishing it unblocks. ● a workspace is on it, ○ ready, ? blockers not read yet, ◐ someone
else has it, ⛔ waiting on an issue outside the epic. An issue with several blockers is drawn
under one, and named `(also ← …)` under the rest. In `--watch` the tree gets whatever lines the
pane has left: it cuts deep chains first, then extra ready issues and quiet epics, then folds
each epic and project nobody is on into one line naming its best pickup. It never cuts what a
workspace is on or hinted at. Only a pane too short even for that gets a ranked list of what to
pick up instead.
`status` shows it whole. It is on the board only, not in the JSON, which stays small enough to
read on every wake, so answer "what next" questions from `status`.

The script works out the facts. What only the guide can judge goes into
`.overview/notes.json`, and the board draws it in:

```json
{
  "overrides": {"app-2": "#680"},
  "workspaces": {"app-3": {"next": "#63 / Add a CSV export endpoint (P1, unblocks #64)"},
                 "site": {"note": "needs wrapup"}},
  "titles": {"DEV-88": "Cache the venue list offline"},
  "offers": ["close #61 / Ship the public API docs? PR #70 / Publish the API reference merged without \"Closes\""],
  "notes": ["#442 is the last open sub-issue of #440"]
}
```

- **overrides**: what the user said a workspace is on. It beats every derived source.
- **workspaces**: per workspace, `next` (shown only while it is free) and a short `note`.
  Put the issue's key first, then its title, then the reason: the board reads the key to tell
  which issues are already hinted. A queue box goes as file key, then label:
  `"SECURITY_TODO S9 / Two owners, then dedicated admin identities (P1)"`, or the file key alone
  for a box with no label.
- **titles**: the title of each Linear issue on the board. The script gets GitHub titles itself
  but can't reach Linear. Add a title whenever a workspace moves to a new Linear issue, and drop
  titles no row uses.
- **offers**: tracker writes waiting for a yes. Remove each one once it is answered.
- **notes**: at most three lines the user should keep in view.

A workspace shows `?` when no source names its issue. Ask about it once, then record the answer
as an override.

## state.md

The guide's log, appended to rather than rewritten: every tracker write and message sent, with
time and reason, and decisions the user made that `notes.json` has no field for. Keep the last
20 entries.

## When to Read References

- `references/init.md`: args are `init`, or there is no `.overview/config.json`.
- `references/lifecycle.md`: the first wake of a guide session, and any time a PR merged, a
  workspace became free, or a push is due.
- `references/reports.md`: `config.json` has `reports`, on the first wake of a day and when the
  user asks for a report.
- `references/graph.md`: a repo's tracker is `linear:…` and its graph file is missing, or it is
  the first wake, a PR in that team merged, a workspace moved onto an issue not in the file, or
  the heartbeat came.

`status` and `find` read none of them.

## Safety

- Never write in a workspace: no `jj` or `git` command that changes anything, and no file
  edits. Every working copy belongs to the session in it. The only files the guide writes are
  in `.overview/`.
- Every tracker write goes through an offer first and happens on the user's yes, because a
  wrong tracker change shows up on the public timeline.
- A message to a worker may only finish work that session already owns, such as the
  `auto_wrapup` send. Starting new work, even the `next` item, waits for the user to ask:
  choosing the work is theirs, and they do it in the session itself. Never send to a `busy`
  session, because a message that lands mid-task makes it lose its thread.
- Keep repos apart. Next items for a workspace come from its own repo's tracker. A tracker write
  stays in its own tracker and never names another repo, its issues or its paths. Links between
  repos go in `notes.json` and `state.md` only, because an umbrella can hold a private repo
  whose name must never appear in a public one.
- Before any write, re-read the issue. A restart halfway through a merge sequence must not
  close the wrong issue or promote twice.
- Never close an issue that has no merged PR, and never close more than one per offer.
