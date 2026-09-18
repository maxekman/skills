# skills

My preferred way of working with Claude Code, packaged so it installs in one step.

This is less a toolbox than a loop. The skills are written to hand off to each other —
a ticket becomes a branch name, the branch name becomes a PR title, the PR attaches
itself back to the ticket — so that the boring connective work between "I picked up an
issue" and "the PR is open" stops needing a human in the middle.

They are written to be invoked by the agent when the trigger fires, not only typed by hand.
That distinction matters more than the skills themselves; see
[Making them operational](#making-them-operational).

## The loop

```
  /backlog next               what to work on, ranked — or `place` a new issue first
         │
  /task implement ABC-123     pick up the ticket; pins the branch name from its slug
  /task implement "<what>"    …or describe the work: finds the issue, or opens one
         │
  /todo                       break it into steps, as working memory while building
         │
  /grill-me                   before anything large: resolve the plan's open questions
         │
    …build…
         │
  /jj                         commit — split what should never have been one commit
         │
  /pr                         open or update the PR; the tracker re-attaches itself
```

Not every change needs the whole loop. A one-line fix is `/jj` and `/pr`. A vague feature
request is `/grill-me` first and possibly nothing else for a while. `/backlog` runs on its own
rhythm — before picking work up, and periodically over the pile you are not looking at.

## The skills

| Skill | Use it for |
|---|---|
| `/task` | Linear (MCP) or GitHub Issues (`gh`) — create, update, search, and `implement`, which takes an issue id *or* a plain description of the work, then carries the finished work through to a commit and PR. Given a description it searches the tracker first and opens an issue assigned to you only if nothing matches |
| `/backlog` | The plural counterpart to `/task`: rank what to work on next, decide where a new issue belongs, and groom statuses, priorities and stale relations in bulk. Linear only |
| `/todo` | A local `TODO.md` as working memory for a multi-step change. The counterpart to `/task`: the tracker holds the goal, this holds the steps |
| `/grill-me` | Stress-testing a plan before executing it — one question at a time, each carrying a recommended answer, exploring the codebase instead of asking whenever the answer is already there |
| `/jj` | Any commit, describe, rebase, split, absorb, or conflict resolution. Splits a working copy that mixes unrelated changes into separate commits |
| `/pr` | Opening or updating a GitHub PR. Handles branch naming, push, stacked PRs with auto-detected parent bases, and rebasing after a parent merges |

Not every change starts from a ticket. `/task implement "fix the flaky retry test"` searches the
tracker for that work, adopts it if it is already filed, and otherwise opens an issue assigned to
you and moved to in progress — but only once you approve the plan, so a rejected plan writes
nothing. For several issues at once, or anything epic-shaped, `/backlog` is the right tool.

Where they interlock: `/backlog next` picks the issue and `/task implement` pins a branch name
from the tracker's own slug, `/pr` reuses that name verbatim so the tracker auto-attaches the
PR, and `/jj` keeps the commits underneath clean enough to stack.

`/backlog` exists because Linear's MCP has no ordering primitive — no `sortOrder`, no
`position`. Backlog order is derived from priority, blocking edges and milestones, so it
carries an explicit rank contract and a priority rubric rather than pretending an issue can be
dragged. It also holds the write contract that stops a status change from silently vanishing:
resolve state names instead of guessing them, never send `state` in the same atomic call as a
`patch`, and read the result back before saying it worked.

## Install

```
/plugin marketplace add maxekman/skills
/plugin install skills@maxekman
```

To give a whole repository the same workflow, commit this to its `.claude/settings.json` —
everyone who clones it then gets the skills with no install step:

```json
{
  "extraKnownMarketplaces": {
    "maxekman": {
      "source": { "source": "github", "repo": "maxekman/skills" },
      "autoUpdate": true
    }
  },
  "enabledPlugins": { "skills@maxekman": true }
}
```

Note the doubled `source` key — the outer one holds the source *object*, and the inner
one names its type. A flat `{ "source": "github", "repo": ... }` fails settings validation.

> **A same-named skill in `~/.claude/skills/` silently overrides the plugin.** Precedence is
> enterprise > personal > project, so an old personal copy keeps winning with no error to
> tell you. If you have been carrying your own `jj` or `pr` skill, delete it after
> confirming the plugin loaded.

Releases are automatic. Every merge to `main` reads the conventional-commit types that landed
and bumps the plugin version accordingly — a fix is a patch, a new skill a minor, a removed or
renamed skill a major. Docs-only changes ship without a release. Each one is tagged
`skills--vX.Y.Z` and published to [Releases](https://github.com/maxekman/skills/releases).

That is what `autoUpdate` depends on: the installer caches the plugin under its manifest
version and skips any update reporting a version it already has, so a change only reaches you
once a release has gone out. Pre-1.0, expect breaking changes to arrive as major bumps rather
than as a stable `1.x` promise.

## Making them operational

Installing the skills is the easy half. A skill nobody invokes is inert, and in practice
you will not remember to type `/jj` every time — which means the workflow only becomes real
once the agent reaches for these on its own.

That is what a global `CLAUDE.md` is for. It is loaded into every session in every project,
and it is where you say *when* each skill fires and what the surrounding rules are:

```markdown
### Skills (slash commands)
Invoke autonomously when the trigger fires — do not improvise the workflows these encapsulate:
- `/jj [message]` — any commit, `jj describe`, rebasing stacks, `jj split`, `jj absorb`…
```

[**`CLAUDE.global-example.md`**](CLAUDE.global-example.md) is close to the file I actually
run. Copy it to `~/.claude/CLAUDE.md` and adapt it — the trigger lines are the part that
makes this repo work; the conventions and anti-patterns below them are mine, and you should
expect to disagree with some.

Two things it is worth keeping whatever else you change:

- **Trigger phrasing over description.** "Any commit, rebase, split, or conflict
  resolution" fires reliably; "use for version control" does not.
- **Keep it short.** It competes for context with the actual work, every session. Mine is
  40 lines. If a rule has never been violated and realistically never would be, cut it.

## Requirements

`jj` ([Jujutsu](https://jj-vcs.github.io/jj/)) is my version control of choice, and `/jj`
and `/pr` assume it — they speak bookmarks and revsets, not branches. If you are on plain
git those two will not be much use to you, though `/task`, `/todo` and `/grill-me` are
independent of your VCS entirely.

- `jj` for `/jj` and `/pr`; `gh` for `/pr` and GitHub-backed `/task`
- A Linear MCP server for Linear-backed `/task` — it falls back to GitHub Issues
- A Linear MCP server for `/backlog`, which has no GitHub fallback — GitHub Issues has no
  priority field, and Projects v2 ordering is unreachable from the `gh` CLI
- `/todo` and `/grill-me` have no dependencies

## Credits

`/grill-me` began as a fork of the skill in
[mattpocock/skills](https://github.com/mattpocock/skills) and has since diverged: upstream
is now a shim that delegates to a `grilling` skill and sets `disable-model-invocation:
true`. This copy keeps the instructions inline and stays model-invocable, so a project rule
can require it automatically rather than waiting for someone to type it.

## License

Apache 2.0 — see [LICENSE](LICENSE).
