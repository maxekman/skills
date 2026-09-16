# Secondary jj workspaces (no `.git`)

Secondary jj workspaces (created with `jj workspace add`) have no `.git` in their tree — the git store lives in the primary workspace. `gh` auto-detects the repo via `git`, so without `.git` every unqualified `gh` call fails with `fatal: not a git repository`.

## Detection

The `Repo info` line in the context block is the signal:

- **JSON object** → primary workspace, `gh` auto-detection works, no `-R` needed.
- **`origin <url>` line** → secondary workspace. Extract the slug and pass `-R owner/repo` to every `gh` call.
- **`no remote detected`** → no usable remote; `gh` will fail.

## Slug extraction

Strip the host prefix and `.git` suffix from the URL — no need to shell out:

```bash
# Context shows: origin git@github.com:acme/app.git  →  extract acme/app
REPO="acme/app"
gh -R "$REPO" pr list --author @me --json number,headRefName,title,url
gh -R "$REPO" pr create --head <branch> --title "..." --body "..."
gh -R "$REPO" pr comment <pr-number> --body "..."
```

Use `-R "$REPO"` consistently — mixing flagged and unflagged `gh` calls fails the moment one hits auto-detection.
