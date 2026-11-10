---
name: overview
argument-hint: "[init|status]"
allowed-tools: Bash(/usr/bin/python3 ${CLAUDE_SKILL_DIR}/scripts/snapshot.py *), Bash(gh *), Bash(jj *), Bash(rex split *), Bash(rex block ls *), Read, Write, Edit, Skill, Monitor, ListAgents, SendMessage, PushNotification
description: Live guide for an umbrella folder of parallel, hand-run Claude sessions — watches every jj or git workspace under it, which issue each session is on, whether it is busy, idle or waiting on the user, and the PRs and tracker issues behind them, then says what needs attention - a session waiting on input, red checks or requested changes, a stalled session, a merge whose issue did not close. Suggests the next item for an idle free workspace and proposes the tracker follow-up after a merge, acting only on a yes. Use whenever the user wants an overview, orchestrator, dashboard or status of their agents or workspaces, asks where things stand, what the sessions are doing or which workspace is free, or starts Claude in a client or project umbrella folder rather than inside a repo, even without the word overview. Ranking work inside one repo is /backlog; post-merge cleanup inside a workspace is /wrapup.
---

# Umbrella Overview

A monitor that follows along while the user runs every worker session by hand. It runs from
the umbrella folder (the non-repo parent of a project's repos and their `-N` workspaces), keeps
a board of what each workspace is doing, and interrupts only when something needs the user. The
user picks up work in the sessions themselves. When a session starts on something, that is the
normal flow: record it on the board, without commentary. It never drives a session or touches a
working copy. It ranks with `/backlog`
and leaves each workspace's post-merge cleanup to `/wrapup`, run in that workspace.

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
(`prompt_ids`). It finds the umbrella by walking up from the cwd, so a drifting shell is fine. For
each live Claude session, taken from Claude Code's session registry (`~/.claude/sessions/`), it
gives `name` (the `SendMessage` address), `status`, `waiting_long`, `stalled`, `prompt_head` and
`asked` (idle, and its last message since the user's last prompt ended on a question).
Per repo it gives PRs by the user (or by anyone, with `"prs": "all"` in the config) that are
open or closed in the last 12 hours, with checks and review state. It also gives `trunk`: the
current result of each workflow on the default branch, which catches a deploy or release run
that went red after a merge. Last, it gives GitHub issue states for the IDs it found. `gh`
results are cached for 90 seconds in `.overview/cache/`. Linear issues are not in it: fetch those through the Linear MCP.

`warnings` comes first in the output. A registry-format warning means Claude Code changed the
file, and session data is missing until the script is fixed. The board shows it at the top;
say it in chat once.

## Commands

### `init`

Run once per umbrella. Creating `.overview/` is the opt-in. Read `references/init.md`.

### Default: the guide

1. **Catch up.** Read `.overview/config.json`, `notes.json` and `state.md`, run the snapshot,
   and fetch the state and title of each Linear issue a workspace is on.
2. **Reconcile.** Derive each workspace's state and act on every transition, as
   `references/lifecycle.md` describes. Read it on the first wake of a session.
3. **Write `notes.json`** (below) in one `Write`, only when something in it changed.
4. **Open the board pane** above the guide, so its prompt stays at the bottom, once, unless a block labelled `overview-board` already exists in
   `rex block ls -s "$REX_SESSION"`:
   ```bash
   rex split -s "$REX_SESSION" -b "$REX_BLOCK" --split=above --ratio 40 --focus=false \
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

Between wakes, answer the user's questions from the latest snapshot: where things stand, what
a workspace is on, or what to pick up next.

### `status`

Print `--board` once and stop. No monitor, no writes. It works from any session under the
umbrella, including one in a workspace.

## The board

`snapshot.py --board` draws it, and with `--watch` redraws it every 5 seconds, at no token
cost:

```
opendecks · 13:51

opendecks    #418  Choose the browse row size in settings  working    idle 6m
opendecks-2  #680  Give the QSPI lines room round U3       working    ⚠ waiting 8m
opendecks-3                                                free       idle 3m     next up: #63 (P1)
opendecks-4  #266  Bring up the DAC2 Pro on the bench Pi   in review  no session  PR #677 draft ✓
site               Publish the press kit                   merged     no session  PR #31 merged · needs wrapup

CI on trunk
  ✗ opendecks main: Deploy (dev) (1h ago)

Offers
  close #61? PR #70 merged without "Closes"
```

The script works out the facts. What only the guide can judge goes into
`.overview/notes.json`, and the board draws it in:

```json
{
  "overrides": {"opendecks-2": "#680"},
  "workspaces": {"opendecks-3": {"next": "#63 (P1, unblocks #64)"},
                 "site": {"note": "needs wrapup"}},
  "titles": {"DEV-88": "Cache the venue list offline"},
  "offers": ["close #61? PR #70 merged without \"Closes\""],
  "notes": ["#442 is the last open sub-issue of #440"]
}
```

- **overrides**: what the user said a workspace is on. It beats every derived source.
- **workspaces**: per workspace, `next` (shown only while it is free) and a short `note`.
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

`status` reads neither.

## Safety

- Never write in a workspace: no `jj` or `git` command that changes anything, and no file
  edits. Every working copy belongs to the session in it. The only files the guide writes are
  in `.overview/`.
- Every tracker write goes through an offer first and happens on the user's yes, because a
  wrong tracker change shows up on the public timeline. `SendMessage` to a worker happens only
  when the user asks for it: they drive the sessions, and a message that lands mid-task makes
  the session lose its thread.
- Keep repos apart. Next items for a workspace come from its own repo's tracker. A tracker write
  stays in its own tracker and never names another repo, its issues or its paths. Links between
  repos go in `notes.json` and `state.md` only, because an umbrella can hold a private repo
  whose name must never appear in a public one.
- Before any write, re-read the issue. A restart halfway through a merge sequence must not
  close the wrong issue or promote twice.
- Never close an issue that has no merged PR, and never close more than one per offer.
