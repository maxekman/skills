---
name: todo
argument-hint: "[add|done|list|prune|implement] [details]"
allowed-tools: Read, Edit, Write, Glob, Grep
description: Lightweight TODO.md task management for local, in-progress work — break a feature into implementation steps, track progress as you build, and check items off as they're done. Use TODO.md as working memory for multi-step tasks. For external issue trackers (Linear, GitHub Issues), use /task.
---

# TODO.md Manager

Manage lightweight TODO.md checklists for local, multi-step work — typically the implementation breakdown of a feature you're actively building. Distinct from external issue trackers (use `/task` for those).

If the work originates from a Linear or GitHub Issues ticket, the TODO.md is your local breakdown of that ticket — `/task` knows about the bigger thing, `/todo` knows about the steps you're walking through right now. The coordination between them is deliberately thin: `/task implement` may seed a section headed with the tracker ID (`## ACME-407 — …`) into a TODO.md you already have, and never creates one. Otherwise the TODO is just your working memory.

Handle: $ARGUMENTS

## File Discovery

```
**/TODO.md
```

If none exist and the user wants to add items, create `TODO.md` at the project root.

When multiple TODO.md files exist, scope to the one closest to the user's working directory or context. If ambiguous, show what exists and ask.

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

## Commands

### Default (no args)
Show open (unchecked) items across all TODO.md files. Group by file if multiple. Include the section header for context.

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

### `implement <text or pattern>`
Gather context for a local item before starting work. Read-only — never modifies files. See `references/implement.md` for the full flow.

## Safety

- Never delete or overwrite a TODO.md without showing the user what changes.
- For `prune`, always confirm before removing items.
- Preserve file structure, existing IDs, formatting, and comments.
