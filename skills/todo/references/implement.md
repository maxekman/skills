# `/todo implement` — gather local context, then carry the item to a PR

Steps 1–5 are read-only: they collect information to support planning and never modify files, so they are safe in plan mode. Step 6 runs once the item is built.

## Step 1 — Find the item

When the args lead with a TODO file (`@docs/SECURITY_TODO.md`, or any path ending in `TODO.md`), search only that file. A label-shaped token after it (`S9`, `B12`) picks the box whose bold key matches (`- [ ] **S9 …**`) before any substring match. A file with no label means its first open box, unless the file states its own order. A box marked `_decide_` waits on the user's decision rather than on work: show it and ask, never implement it.

Otherwise match by substring (same as `done`). If multiple match, show them and ask which. Note:

- The `##` section the item lives under.
- Whether the item carries a tracker ID — trailing `[ABC-123]` (Linear) or `[#42]` (GitHub Issues), or inside its label (`**S22 (DEV-377). …**`). If present, mention it but don't auto-fetch — the user can pull tracker context separately via `/task show <id>` if useful.

## Step 2 — Read detail lines

Capture indented lines beneath the matched item — these often contain requirements, deadlines, or file references. Stop at the next `- [` item or section header.

## Step 3 — Follow explicit references

If detail lines mention specific files (e.g., "See SPEC.md for column mapping", "details in docs/auth.md"), read the relevant section. For large files, grep for the task keywords and show the surrounding section (one `##` header to the next) rather than the whole file.

## Step 4 — Search for related docs

Extract 1-2 core keywords from the item text (main noun/concept, not filler). Search:

- Glob `**/SPEC.md` near the TODO.md's directory — grep within each for keywords.
- Grep `**/*.md` (excluding TODO.md itself) — up to 5 files with brief excerpts.
- Check `docs/` if present.

## Step 5 — Present the context

```
## Task
**[Section]** — [item text]
[detail lines, if any]
[If a tracker ID is present:]
**Tracker**: [ID] — for full tracker context, run `/task show <id>`.

## Documentation
[For each relevant doc: filename, line range, matching excerpt]

## Related Items
[Other open items in the same TODO.md section]
```

Keep excerpts focused — show the relevant section between `##` headers, not entire files. The goal is enough context to plan, not a wall of text.

## Step 6 — Deliver

When the item is built, run the gate. If every condition holds, invoke `/jj` and then `/skills:pr` without asking: starting `/todo implement` was the user's request to commit, push and open the PR, and they review at the PR.

**Gate — all must hold:**

- The item and its detail lines are done, not partly done.
- The project's formatter, linter, and fast tests pass. Find the targets in `Makefile`, `package.json`, `mix.exs`, or `.mise.toml`. If you cannot run them at all, that is a gate failure — say so rather than reporting green.
- The diff stays inside the item. Unrelated drive-by edits mean stop and ask, not a bigger PR.
- No debug leftovers, stubs, or new `FIXME`s from this work remain in the diff.

If any condition fails, stop and say which one and what is left.

**On a pass, hand off in order:**

1. `/jj` — commits, checking the item off in the same commit and carrying its tracker tag (`[ACME-407]`) into the message.
2. `/skills:pr` — its *Handed off from `implement`* section decides whether to push without confirming and sets the report's shape. The first item of a section opens the PR, and later items push to its bookmark, which updates it; the open items left in TODO.md show what is still to come. An item from another `##` section is separate work: say so rather than pushing it onto that PR, since it would land as a stack.
