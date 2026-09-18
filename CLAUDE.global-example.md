<!--
  Example ~/.claude/CLAUDE.md — copy to that path and adapt.

  This is close to the file I actually run, generalized slightly: the skills
  section lists all six skills this repo ships, where mine had grown to mention
  only the three I reach for most. Everything else is as-is, opinions included.

  Keep your own version short. It loads into every session in every project, so
  it competes for the same context as the work.
-->

## Commands

### VCS — jj

- ALWAYS use `jj` instead of `git`.
- ALWAYS pass `-m "message"` to `jj describe`, `jj commit`, `jj split`, `jj squash`. Without `-m`, jj opens `$EDITOR` and blocks the agent indefinitely.
- NEVER use `-i`, `--interactive`, or `--tool` flags — they require a TTY and hang.
- Only commits in `trunk()..@` are mutable. Never squash/rebase into a commit on `trunk()`; never modify `main`/`master`/`develop`/`staging`/`prod`. If a fix belongs in a landed commit, create a follow-up.
- Run `jj git push --dry-run` before any real push; abort if a protected bookmark would move.
- Use conventional commits (feat/fix/chore/docs/ci/dev). Match the existing scope vocabulary from `jj log`.

### Skills (slash commands)

Invoke autonomously when the trigger fires — do not improvise the workflows these encapsulate:

- `/task <create|update|search|implement> …` — issue/tracker operations on Linear (MCP) or GitHub Issues (`gh`). Use whenever the task references a ticket or asks to file/update one.
- `/backlog <status|next|groom|place|triage> …` — any question of what to work on next, where a new issue belongs, or cleaning up issue statuses, priorities and ordering across many issues. Linear only.
- `/todo` — a local `TODO.md` as working memory for a multi-step change. The counterpart to `/task`: the tracker holds the goal, this holds the steps.
- `/grill-me` — stress-test a plan before executing it.
- `/jj [message]` — any commit, `jj describe`, rebasing stacks, `jj split`, `jj absorb`, fixing earlier commits, or resolving conflicts. Default for non-trivial jj work.
- `/pr [title]` — opening or updating a GitHub PR. Handles bookmarks, push, stacked PRs (auto-detects parent base), and rebasing after a parent merges.

### Build & test

- Before committing (or invoking `/jj`), run the project's formatter, linter, and fast tests. Check `Makefile`, `package.json`, `mix.exs`, or `.mise.toml` for targets. Fix failures — never commit code that breaks CI. Never bypass with `--no-verify`.
- Use `mise` for dev-tool versions — prefer project `.mise.toml`, fall back to global.

## Conventions

- No abstractions until 3+ concrete uses. Inline repetition is fine below that threshold.
- No new dependency for anything achievable in <20 lines of stdlib.
- Comments explain *why*, never *what*. No comments on obvious code.
- Only catch errors you can handle. Do not wrap calls in defensive try/catch for invariants the code already guarantees.

## Agent behavior

- Do only what is asked. No unrequested refactors, comments, annotations, or "while I'm here" cleanup.
- Prefer deleting code over adding code.
- Before adding a new function/type, check whether an existing one can be extended or reused.
- When fixing a bug, identify the root cause and explain it in the commit message.
- If a change touches >3 files, stop and propose a refactor plan first.
- Before executing a plan that touches >3 files, introduces new abstractions, or adds a dependency, invoke the `/grill-me` skill to stress-test it.
- Verify imported modules, methods, and CLI flags exist before using them — read source/docs or `--help` rather than guessing.
- When finishing work, update any `SPEC.md`/`TODO.md` whose claims your change invalidates.

## Anti-patterns

- Never add AI attribution to commits or code.
- If something is unused, delete it — no tombstone comments, no `// removed`, no compatibility shims, no `_unused` renames.
- Parallel work may be ongoing — never revert, discard, or undo changes you didn't make.
