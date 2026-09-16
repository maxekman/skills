# Edge cases and recovery

## Parallel work in the working copy

**Parallel work is always expected.** Other agents or processes may be working in the same repo simultaneously. Changes you don't recognize belong to them — never restore, revert, or undo them.

Your scope is the set of files this session worked on, often spanning multiple directories (`lib/`, `test/`, `config/`, etc.). Identify by *what was modified during this session*, not by cwd.

- **User specifies scope** ("this folder", specific files) → use that.
- **No explicit scope, all changes look related** → proceed with `jj commit`.
- **Mixed scope** (your changes + foreign changes) → `jj split -m "..." <your-files>` to commit only yours, leaving the rest in the working copy.
- **Unsure what's yours** → show `jj diff --stat` and ask the user.

If your changes are fixups to earlier commits in your stack, prefer `jj absorb <files>` over split (see `rebasing.md`).

## Fileset quoting

Paths with colons, parens, or other special chars conflict with jj's fileset syntax. `foo:bar/` is parsed as fileset kind `foo:` with arg `bar/`, not as a path. Affects `jj split`, `jj diff`, `jj restore`, etc.

Fix with explicit pattern prefixes and quotes:

```bash
# WRONG: jj split -m "msg" audit:performance/    → "Invalid file pattern kind audit:"
# RIGHT (single):
jj split -m "msg" cwd:"audit:performance/"
# RIGHT (multiple):
jj split -m "msg" cwd:"audit:performance/" cwd:"audit:security/"
# BATCH (glob):
jj split -m "msg" glob:"audit:*/**" glob:"dev:*/**"
```

## .gitignore hygiene

When adding system files (`.DS_Store`, `*.tmp`, `node_modules/`) to `.gitignore`, also run `jj file untrack <path>` for any newly-ignored files that are already tracked.

## Workspaces

```bash
jj workspace add .jj-workspaces/<name> --name <name> -r <base>
jj workspace list
jj workspace forget <name>
jj workspace update-stale
```

**Critical**: never edit files outside the current workspace directory.

## Recovery

- `jj undo` — undo the most recent operation.
- `jj op log` — operation history. Check this before undoing to avoid undo cascades.
- `jj op undo <operation-id>` — undo a specific operation by ID.

After `jj absorb` or any rewriting operation, `jj op show -p` shows what changed.
