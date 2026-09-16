# `/todo implement` — gather local context for a TODO item

Read-only — collects information to support planning. Never modifies files.

## Step 1 — Find the item

Match by substring (same as `done`). If multiple match, show them and ask which. Note:

- The `##` section the item lives under.
- Whether the item line ends with a tracker ID — `[ABC-123]` (Linear) or `[#42]` (GitHub Issues). If present, mention it but don't auto-fetch — the user can pull tracker context separately via `/task show <id>` if useful.

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
