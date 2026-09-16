# Linear (MCP)

The connected server is `linear-server` (Linear's official remote MCP). Its tools are named `mcp__linear-server__<action>`. If a session exposes a differently-named Linear server, fall back to matching `mcp__*<action>*` — the actions themselves are stable.

| Action           | Tool                                    | Allowlisted |
|------------------|-----------------------------------------|-------------|
| Current user     | `mcp__linear-server__get_user`          | yes         |
| List teams       | `mcp__linear-server__list_teams`        | yes         |
| Search / list    | `mcp__linear-server__list_issues`       | yes         |
| Get issue        | `mcp__linear-server__get_issue`         | yes         |
| Create / update  | `mcp__linear-server__save_issue`        | yes         |
| Read comments    | `mcp__linear-server__list_comments`     | yes         |
| Add comment      | `mcp__linear-server__save_comment`      | yes         |
| Workflow states  | `mcp__linear-server__list_issue_statuses` | prompts   |
| Projects         | `mcp__linear-server__list_projects`     | prompts     |

`save_issue` is an upsert: omit `id` to create, pass `id` to update. Updating a long description takes `patch` (a list of `replace` / `prepend` / `append` ops) rather than resending the whole body. There is no separate create/update pair — `create_issue` and `update_issue` were folded into it, and `list_my_issues` is gone; use `list_issues` with `assigned:me`.

The "prompts" rows aren't in `settings.json` `permissions.allow`, so they interrupt for approval. Reading and writing issues and comments is on the critical path for `/task implement`, so those are allowlisted; the rest are rare enough that a prompt is the right cost.

## Identifiers

`get_issue` takes the human identifier (`ACME-407`), not just the UUID — pass what the user gave you. Uppercase it first; Linear URLs carry it uppercase but people type `acme-407`.

Full URLs are **not** accepted as an id. Parse `linear.app/<workspace>/issue/<ID>/<slug>` down to the ID first — see `implement.md` step 1, which also explains why the workspace and slug are worth keeping.

## Branch names

Linear generates a branch name per issue, exposed as `gitBranchName` on the issue. Prefer it verbatim: it honors the user's own branch-format setting and round-trips cleanly when a PR is reopened or rebased. Its default shape is `<user>/<id-lower>-<title-slug>`, and that title slug is the same one already sitting in the issue URL — so a pasted link gives you the branch name with no extra call. `/pr` step 3 consumes this.

## Query syntax

Linear filters support: `assigned:me`, `status:"In Progress"`, `priority:high`, `project:"Name"`, `updated:-3d`. Combine freely.

If the MCP server is unavailable or auth has expired, tell the user to check their Linear MCP connection — don't fall back to scraping `linear.app` over HTTP.
