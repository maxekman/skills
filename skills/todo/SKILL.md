---
name: todo
argument-hint: "[add|done|list|prune|implement] [@file] [label or details]"
allowed-tools: Read, Edit, Write, Glob, Grep, Skill
description: Lightweight TODO.md task management for local, in-progress work — break a feature into implementation steps, track progress as you build, and check items off as they're done. Use TODO.md as working memory for multi-step tasks. For external issue trackers (Linear, GitHub Issues), use /task.
---

# TODO.md Manager

Manage lightweight TODO.md checklists for local, multi-step work — typically the implementation breakdown of a feature you're actively building. Distinct from external issue trackers (use `/task` for those).

If the work originates from a Linear or GitHub Issues ticket, the TODO.md is your local breakdown of that ticket — `/task` knows about the bigger thing, `/todo` knows about the steps you're walking through right now. The coordination between them is deliberately thin: `/task implement` may seed a section headed with the tracker ID (`## ACME-407 — …`) into a TODO.md you already have, and never creates one. Otherwise the TODO is just your working memory.

Handle: $ARGUMENTS

## File Discovery

```
**/*TODO.md
```

The leading `*` matters: it catches area queues like `docs/SECURITY_TODO.md` beside plain `TODO.md`, and a repo that splits its TODOs that way keeps most of its open work in them. Skip vendored and build directories (`node_modules/`, `deps/`, `_build/`, `vendor/`).

If none exist and the user wants to add items, create `TODO.md` at the project root.

When multiple TODO files exist, scope to the one closest to the user's working directory or context. If ambiguous, show what exists and ask. A file that states its own rules (when an item counts as done, who may tick it) wins over the defaults here.

## Format

Standard markdown checkboxes — one line per item, grouped under `##` section headers when useful.

```markdown
# TODO

## Networking
- [ ] Add retry logic to API client
- [x] Switch to connection pooling

## Docs
- [ ] Update README with new CLI flags
```

Single line per item where possible. For more context, indent detail lines beneath:

```markdown
- [ ] Migrate user table to new schema
  Needs coordination with the auth team. Target: after v2.1 release.
  See SPEC.md for column mapping.
```

Preserve whatever structure and conventions the file already uses — task IDs, numbering, spec references, etc. Don't impose a new scheme on existing files.

Area queues often label their boxes — `- [ ] **S22 (DEV-377). Protect main.** …` — so a box can be named by its key, `S22`. Keep the labels as the file writes them. A tracker ID inside the label makes the box that issue, the same as a trailing `[DEV-377]`.

## Commands

### Default (no args)
Show open (unchecked) items across all TODO files. Group by file if multiple. Include the section header for context.

### `add <text>`
Append `- [ ] <text>`. If a section is specified ("add X to Networking"), put it under that `##` header — create the section if absent. Otherwise append to the end (or last section).

### `done <text or pattern>`
Find a matching open item, change `- [ ]` to `- [x]`. Substring match. If multiple match, show them and ask which.

### `undo <text or pattern>`
Reverse of `done` — `- [x]` back to `- [ ]`.

### `list` or `show`
All items (open and completed). Filters:

- `/todo list open` — only unchecked (same as no-args default).
- `/todo list done` — only checked.
- `/todo list <section>` — items under a specific section.
- `/todo show <file>` — items from a specific file.

### `prune [done|tracked|all]`
Clean up items that no longer need to be in TODO.md.

- `/todo prune done` — remove completed (`- [x]`) items.
- `/todo prune tracked` — remove items with a trailing tracker ID like `[ABC-123]` or `[#42]`. Those live in the tracker now; the local copy isn't pulling its weight.
- `/todo prune` or `/todo prune all` — both.

When removing an item, also remove its indented detail lines (everything indented beneath until the next `- [` or section header).

Show what will be removed grouped by category, confirm before editing. Clean up empty sections — if removing items leaves a `##` header with no items, remove the header too.

### `implement [@<file>] <label, text or pattern>`
A leading TODO file (`@docs/SECURITY_TODO.md`) scopes the search to that file, and a label (`S9`) picks its box; the file alone means its first open box. Arguments that start with a TODO file and name no verb — `/todo @docs/SECURITY_TODO.md S9` — mean `implement`, since that is what someone typing them wants.

Gather context for a local item, then carry the built item to a PR. Gathering is read-only, so it is safe in plan mode. Once the item is built and its gate passes, `/jj` commits it and `/skills:pr` opens the PR — or updates the one an earlier item opened — without asking. Read `references/implement.md` whole: its delivery step has to be in context when the build finishes.

## Safety

- Never delete or overwrite a TODO.md without showing the user what changes.
- For `prune`, always confirm before removing items.
- Preserve file structure, existing IDs, formatting, and comments.
