---
name: jj
argument-hint: "[commit message or operation]"
allowed-tools: Bash(jj *), Bash(git submodule status *), Bash(git add *), Bash(git commit *), Read, Glob, Edit
description: Jujutsu (jj) version control operations - handles commit descriptions and workflow management
---

# Jujutsu (jj) Helper

Expert helper for the Jujutsu (jj) version control system. Handle the user's request using the appropriate jj commands.

## Context

Current repo state (already gathered — don't re-check):

- `jj status`: !`jj status`
- `jj diff`: !`jj diff`
- Recent commits: !`jj log --limit 10`
- Submodules: !`git submodule status 2>/dev/null || echo "No git submodules"`
- Repo root: !`jj root 2>/dev/null`
- Working dir: !`pwd`

## Task

Handle: $ARGUMENTS

If no arguments, commit the current working copy following the workflow below.

## Default Workflow

The happy path is short — read the diff, write a good message, commit:

1. **Look at the diff.** Assume the changes are yours. Only stop to investigate if something looks foreign (unfamiliar files, unexpected churn) — see `references/edge-cases.md` for the parallel-work playbook.
2. **Write a conventional-commit message** (`type(scope): title`, optional prose body). Format below.
3. **Before committing, ask: "Is this one conceptual change?"** A single conceptual change is one feature, one fix, one refactor, or one chore. If the diff contains two or more of those, split. Concretely, split when the working copy mixes any of:
   - product change + dev-tooling change (`.mise.toml`, editor config, lint config, scripts) — unless the tooling change *directly enables* the product change (e.g., bumping a dep to use a new API it adds).
   - two unrelated product changes (bug fix A + feature B).
   - your changes + formatter/linter/codegen churn on files you weren't otherwise touching.

   Default to splitting. Lumping is only correct when every hunk genuinely serves one intent.

4. **Commit:**
   - `jj split -m "..." <files>` for each separable piece — fileset is mandatory, never omit it. Order so the lower commit is the more foundational one (tooling/refactor first, feature on top). Splits cascade: after each split, the remainder stays at `@` ready for the next split or the final `jj commit -m`.
   - `jj commit -m "..."` once the working copy contains a single cohesive change.
   - `jj absorb` if the working copy is fixups for earlier commits in your stack (`trunk()..@`). See `references/rebasing.md`.

If earlier commits in `trunk()..@` are WIP (`wip:` prefix) and your changes belong with them, fold in with `jj squash --into <rev>` instead of creating a new commit. Never squash into a commit on `trunk()`.

**Formatter, linter, or codegen churn always gets its own commit.** If reformatted files are ones you were already meaningfully changing, those hunks can stay in the main commit; reformats on *other* files split out into `chore: formatting` (or `chore: lint`, `chore: codegen`). For a stack, `jj absorb` routes the hunks to the commits that own those lines instead.

### Bad lumping to avoid

These should always be two commits, not one:

- `feat(api): add /users endpoint` + `.mise.toml` node version bump → split tooling out as `chore(mise): bump node to 22`.
- `fix(auth): reject expired tokens` + reformatted 8 unrelated files → split reformats out as `chore: formatting`.
- `feat(ui): add settings page` + `fix(api): handle null user` → two product commits; they were just in the working copy together.

When in doubt, split. A reviewer reading `jj log` should see one intent per line.

If a `TODO.md` is in the diff and your change clearly resolves an open `- [ ]` item, check it off (`- [x]`) as part of the same commit. Don't glob the whole repo — only check items in files you're already touching. If a checked item has a tracker ID (`[ABC-123]`), include it in the message and suggest closing it via `/task update <id> status done`.

## Commit Message Format

- **Conventional commits**: `type(scope): description`. Common types: `feat`, `fix`, `chore`, `docs`, `ci`, `dev`, `test`, `refactor`. Check `jj log` for project-specific scopes.
- **50/72**: title ≤50 chars, body lines ≤72 chars.
- **Title**: imperative, describes the *outcome*, not the mechanism. No filenames or function names — the diff already shows those.
- **Body** (when needed): present-tense prose. Explain how the approach works conceptually and why it improves things. No bullet lists, no filenames, no function signatures. See `references/commit-style.md` for examples.

## Custom Aliases

The user's jj config defines these — prefer them over raw commands:

- `jj l` — log of working-copy bookmark vs `main`.
- `jj bc <name>` — create bookmark at latest non-empty ancestor.
- `jj lift` — rebase entire feature stack onto latest trunk (`jj rebase -s 'roots(trunk()..@)' -d trunk()`). Use after `jj git fetch`.
- `jj log-recent` — last 3 months of changes.
- `jj tug` — move closest bookmark forward to `@-`. **DANGER**: tug moves whatever bookmark is closest, **including `main`**. Before tug, run `jj log -r 'closest_bookmark(@-)'`. If it resolves to a protected bookmark (`main`, `master`, `develop`, `staging`, `prod`), do NOT tug — use `jj bc <feature-name>` instead.

## Critical Safety

- **NEVER** use `-i`/`--interactive`/`--tool` — they require a TTY and fail in non-interactive sessions.
- **NEVER** use `jj describe`, `jj commit`, or `jj split` without `-m` — they open `$EDITOR` and hang.
- **`jj split` additionally requires a fileset**: `jj split -m "msg" <files>`. Running `jj split -m "msg"` with no files opens the interactive diff picker and hangs. If you cannot split by file boundaries (e.g., mixed hunks inside one file), commit the file as-is and note the mixing rather than attempting an interactive split.
- **NEVER** modify protected bookmarks: `main`, `master`, `develop`, `staging`, `prod`.
- **NEVER** squash or rebase into commits on `trunk()`. Only `trunk()..@` is mutable. If a fix belongs in a landed commit, create a follow-up (`fix(scope): correct oversight from <hash>`).
- **ALWAYS** `jj git push --dry-run` first. Abort if a protected bookmark would be pushed. See `references/git-and-prs.md`.
- **ALWAYS** check `gh pr list --head <bookmark> --state merged` before pushing an existing bookmark — pushing to a merged PR's branch silently no-ops.
- **Submodules**: jj doesn't support them. After the jj commit, use `git add <path>` + `git commit`. See `references/git-and-prs.md`.
- **Never work around locked credentials.** If a push, fetch, or signed operation fails on an SSH agent / signing key error (1Password locked, `ssh-agent` unreachable, "no such identity", "agent refused operation"), do not switch to HTTPS, disable signing, alter `~/.ssh/config`, or otherwise route around it. Wait it out — see "Signing and a locked screen" below.

## Signing and a locked screen

Commits are signed lazily at push time (`signing.behavior = "drop"` plus `git.sign-on-push`), so a locked screen never blocks local work — commit, split, and squash freely. Two consequences follow:

- **Push is where signing happens**, so `jj git push` is the one command needing 1Password unlocked. If it fails with `Signing error` / `SSH sign failed` / `1Password:`, the user has stepped away from the desk. Nothing was pushed and the repo is fine, so wait rather than ask:
  ```bash
  for i in $(seq 1 10); do timeout 30 jj git push --bookmark <name> && break; sleep 30; done
  ```
  If that budget runs out, stop and leave the exact command ready to paste. Never route around the lock — no `--no-gpg-sign`, no editing `signing.*`, no `~/.ssh/config` edits. An unsigned commit outlives the coffee break and has to be rewritten later.
- **Signing rewrites the commits it signs**, so the hash that lands differs from the one `--dry-run` predicted and descendants get rebased. That is expected, not a sign something went wrong. The dry-run safety check reads bookmark *names*, which stay accurate.

## When to Read References

- `references/rebasing.md` — rebasing, squashing, absorb, splits, stack management.
- `references/git-and-prs.md` — submodules, feature bookmarks, push, PR creation, push safety details.
- `references/edge-cases.md` — parallel work, fileset quoting (paths with `:`/`(`/`)`), workspaces, recovery (`jj undo`, `op log`).
- `references/commit-style.md` — longer commit-message guidance with before/after examples.

## Output Format

After commit operations, output ONLY the commit message (title + body if present). No bullets, summaries, metadata, or attribution.
