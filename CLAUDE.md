# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A Claude Code **plugin marketplace**, not an application. It ships six skills that chain into a
ticket-to-PR loop: `/backlog` → `/task` → `/todo` → `/grill-me` → `/jj` → `/pr`.

Everything here is markdown plus two JSON manifests. There is no build or test step — CI only
checks that the manifests agree with the tree and that the skills validate, then releases.
"Correct" means the frontmatter is valid, the prose is tight, and the manifests agree with the
tree. Editing skills *is* the work in this repo.

## Always use skill-creator

Before creating or editing **any** `SKILL.md`, reference file, or description — including
one-line fixes — invoke the skill-creator skill:

```
Skill(skill: "example-skills:skill-creator")
```

The prefix follows whichever plugin provides it; it may also appear under
`claude-plugins-official`. It carries the current frontmatter spec, the description-writing
rules, and the eval tooling. Don't hand-author skill content from memory — the spec moves, and
the defaults below are a summary of it, not a replacement for it.

## Architecture

```
.claude-plugin/
  marketplace.json    marketplace "maxekman" → lists the `skills` plugin
  plugin.json         the plugin itself → enumerates every skill path
skills/<name>/
  SKILL.md            frontmatter + body
  references/*.md     detail, loaded on demand
.github/
  workflows/          PR checks; release on push to main
  scripts/            next-version.sh, check-manifest.sh
CLAUDE.global-example.md   template for the *user's* ~/.claude/CLAUDE.md, not repo memory
```

**`plugin.json` enumerates skills explicitly.** A new `skills/<name>/` directory is inert until
its path is added to that array — the easiest thing in this repo to get wrong, because nothing
errors, the skill simply never loads. Current order: `jj`, `pr`, `task`, `backlog`, `todo`,
`grill-me`.

No skill has `scripts/` or `assets/` yet; all six are prose plus references.

## How a change here goes live

The installed plugin is a **separate clone of the GitHub remote** at
`~/.claude/plugins/marketplaces/maxekman`, not this working tree. Edits here do nothing for a
running session until they are pushed and the marketplace updates
(`/plugin marketplace update maxekman`), followed by a session restart.

Corollary: this repo's own skills are loaded while you work in it. Editing `skills/jj/SKILL.md`
changes a skill that may be active in the same session — what you have loaded is the old copy.

## Releases are automatic, and your commit type decides them

Pushing is not enough either. The installer caches an extracted plugin under its manifest
version and skips any update reporting a version it already has, so a change that lands without
a version bump reaches the marketplace and stops there — invisible to everyone who already
installed the plugin. That is too easy to forget, so CI owns it.

`.github/workflows/release.yml` runs on every push to `main`: it reads the conventional-commit
types since the last `skills--v*` tag, writes the next version into `plugin.json`, commits it
back as `chore(release): …`, tags, and publishes a GitHub Release. Merges here are **rebase
only**, so the commit messages you write are exactly what CI reads — the PR title never lands.
Your commit message *is* the release control.

**Don't hand-edit `version` in `plugin.json`.** Not because it breaks anything — because it does
nothing. Once a tag exists, the next version is computed from the tag, so a hand-edit is
silently overwritten by the next release and leaves a confusing diff in the meantime. The
`chore(plugin): bump version to 0.2.0` commit in this history is the last hand-written bump.
(Hand-*tagging* is the one that fails loudly: `next-version.sh` refuses when the version it
computed is already tagged.)

`marketplace.json` deliberately carries no `version` field. If it had one it would win over
`plugin.json`, and there would be two sources of truth for the one value that matters.

| What you changed | Type | Bump |
|---|---|---|
| A skill got something wrong and now does the right thing | `fix(<skill>)` | patch |
| A `description` — repairing triggering that was meant to work | `fix(<skill>)` | patch |
| Prose tightened or a reference clarified, no behaviour change | `docs(<skill>)` | none |
| A new `skills/<name>/`, plus its entry in the skills array | `feat(<name>)` | minor |
| A new verb or reference on an existing skill | `feat(<skill>)` | minor |
| A `description` — claiming prompts it used to ignore | `feat(<skill>)` | minor |
| A skill removed or renamed | `feat(<name>)!` + `BREAKING CHANGE:` footer | major |
| A verb the description advertises, removed or renamed | `feat(<skill>)!` | major |
| A `description` narrowed so the skill stops firing where it did | `feat(<skill>)!` | major |
| Manifest only — keywords, author, category | `chore(plugin)` | none |
| `README.md`, this file, `CLAUDE.global-example.md` | `docs` | none |
| The workflows or their scripts | `ci` | none |

Scope is the skill directory name, or `plugin` for manifest changes.

Two judgement calls hide in that table. A `description` edit splits by *intent*, not size:
repairing triggering that was always meant to work is a `fix`, while making a skill fire on
prompts it deliberately ignored is new behaviour for every installed client — ship that as
`docs` and nobody receives it. And a rename is breaking even though nothing is deleted: `/foo`
stops existing for anyone whose own `CLAUDE.md` names it, and their sessions will call a slash
command that no longer resolves.

Breaking changes bump the major even pre-1.0 — `0.2.0` → `1.0.0` — so a removed skill is as
loud as it is disruptive. That is one variable, `BREAKING_PRE_1_0` at the top of
`.github/scripts/next-version.sh`.

Run `.github/scripts/next-version.sh` before opening a PR to see what your commits will cut. A
docs-only PR releasing nothing is correct, not a bug.

## Frontmatter contract

Every field used here is officially supported by Claude Code:

| Field | Notes |
|---|---|
| `name` | kebab-case, ≤64 chars, matches the directory name |
| `description` | the trigger surface — see writing defaults below |
| `argument-hint` | autocomplete hint; Claude Code only, not in the portable spec |
| `allowed-tools` | keep it narrow — `pr` uses `Bash(gh *), Bash(jj *)`, never bare `Bash` |

`$ARGUMENTS` interpolation and `` !`cmd` `` pre-execution inside a `## Context` block are
supported, and used by `jj` and `pr`. Guard every `` !`cmd` `` with `2>/dev/null || echo "…"`
so a missing tool can't poison the context.

Limits: `description` ≤1024 chars with **no angle brackets** under the portable Agent Skills
spec. `task`'s description currently contains `<id-or-url>` — fine in Claude Code, but it would
fail a portable check, so don't copy that pattern into new skills.

**`skill-creator/scripts/quick_validate.py` validates against the portable spec**, so it flags
`argument-hint` as an "unexpected key" on five of six skills. That is a false positive here —
never strip `argument-hint` to satisfy it. It also requires PyYAML, which isn't installed.

## SKILL.md house shape

```
---
frontmatter
---

# Title

One or two lines: what this is, what it is not, and the sibling skill it hands off to.

Handle: $ARGUMENTS

## Context                    (optional; !`cmd` blocks)
## Commands                   (or ## Workflow, with ### per verb)
## When to Read References
## Safety
```

Budget: bodies here run 75–145 lines against a hard ceiling of 500; references sit one level
deep and run 24–157 lines. `grill-me` is the deliberate outlier — 10 lines, no references,
because the whole skill is one instruction. When a body outgrows ~150 lines, move detail into
`references/` rather than adding another level of nesting.

## Writing defaults

**Descriptions** are the only text always in context, and they compete with every other
installed skill for attention. Write intent rather than implementation, say when to use it, and
name the counterpart skill so the boundary is unambiguous — `todo`'s "For external issue
trackers (Linear, GitHub Issues), use /task" is the pattern to copy. Lean slightly pushy; skills
undertrigger far more often than they overtrigger.

**Reference routing names the firing signal, not the topic.** `pr` does this best: "args contain
`#N`", "…shows a non-empty parent bookmark", closing with "Most PRs trigger none of these." A
section that merely lists what each file covers gets read every time, which defeats the purpose.

**Explain why instead of shouting.** `**NEVER** use -i` is weaker than "`-i` requires a TTY and
hangs the agent". Where an existing rule already carries its reason, keep it.

Also: never duplicate content between a `SKILL.md` and its references — pick one home. No
`README.md`, `CHANGELOG.md`, or other scaffolding inside a skill directory. Prefer the
imperative.

## The cross-reference web

The skills name each other in both descriptions and bodies, so renaming a skill or changing its
verbs is never a one-file edit. Update together:

- `.claude-plugin/plugin.json` — the skills array
- `README.md` — both the skill table and the ASCII loop diagram
- `CLAUDE.global-example.md` — the trigger list
- every sibling `SKILL.md` that names it (`/task` ↔ `/todo` ↔ `/backlog` ↔ `/jj` ↔ `/pr`)
- the commit that does it — a rename is a breaking change, so it needs `!` and a
  `BREAKING CHANGE:` footer. See *Releases are automatic*.

## Evals (optional)

The repo has none today. For a new skill or a description rewrite — where triggering accuracy is
what actually matters — skill-creator's trigger-eval loop (`scripts/run_loop.py`) measures
whether a description fires on the right prompts. Negative cases should be near-misses, not
obvious non-matches. `package_skill.py` excludes `evals/` from the packaged artifact, so adding
them costs nothing downstream.

## Out of scope here

jj/commit conventions and general agent behavior live in the user's global `~/.claude/CLAUDE.md`
and are deliberately not repeated in this file.
