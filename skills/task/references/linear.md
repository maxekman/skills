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
| Workflow states  | `mcp__linear-server__list_issue_statuses` | allowlist it |
| Projects         | `mcp__linear-server__list_projects`     | allowlist it |
| Labels           | `mcp__linear-server__list_issue_labels`  | allowlist it |

`save_issue` is an upsert: omit `id` to create, pass `id` to update. Updating a long description takes `patch` (a list of `replace` / `prepend` / `append` ops) rather than resending the whole body. There is no separate create/update pair — `create_issue` and `update_issue` were folded into it, and `list_my_issues` is gone; use `list_issues` and filter to the current user from `get_user`.

Whether a tool prompts depends on your own `settings.json` `permissions.allow`. Reading and writing issues and comments is on the critical path for `/task implement`, so allowlist those. **`list_issue_statuses` belongs on that list too** — the write contract below calls it before every status change, and an approval prompt on that path is the thing that tempts you into guessing a state name instead. All four marked "allowlist it" are read-only lookups.

## Identifiers

`get_issue` takes the human identifier (`ACME-407`), not just the UUID — pass what the user gave you. Uppercase it first; Linear URLs carry it uppercase but people type `acme-407`.

Full URLs are **not** accepted as an id. Parse `linear.app/<workspace>/issue/<ID>/<slug>` down to the ID first — see `implement.md` step 1, which also explains why the workspace and slug are worth keeping.

## Branch names

Linear generates a branch name per issue, exposed as `gitBranchName` on the issue. Prefer it verbatim: it honors the user's own branch-format setting and round-trips cleanly when a PR is reopened or rebased. Its default shape is `<user>/<id-lower>-<title-slug>`, and that title slug is the same one already sitting in the issue URL — so a pasted link gives you the branch name with no extra call. `/pr` step 3 consumes this.

## Querying

`list_issues` takes structured arguments — `state`, `project`, `team`, `parentId`, `createdAt`, `includeArchived`, `orderBy`, `limit`, `fields` — and filters on those. Its `query` argument is **free-text semantic search**, not a filter language: use it to find issues *about* something, not to express `assigned:me`.

`fields` is a strict enum and an unknown value fails the whole call. The useful ones here: `id`, `title`, `description`, `status`, `statusType`, `priority`, `assignee`, `labels`, `project`, `projectMilestone`, `parentId`, `url`, `gitBranchName`, `createdAt`, `updatedAt`.

There is no label or assignee filter. To find issues carrying a label, ask for `labels` in
`fields` and narrow the result client-side — `query` will not do it, and neither will a filter
argument that does not exist.

Branch logic on **`statusType`** — Linear's fixed category (`triage`, `backlog`, `unstarted`, `started`, `completed`, `canceled`) — and show `status`, the team's own name, to the user. `status` is not portable: one team's "In Progress" is another's "Doing". "Is it finished?" is `statusType in (completed, canceled)`, never `status == "Done"`.

If the MCP server is unavailable or auth has expired, tell the user to check their Linear MCP connection — don't fall back to scraping `linear.app` over HTTP.

## Placement and classification

`save_issue` accepts considerably more than the create path in `find-or-create.md` sends. Observed
arguments, grouped:

| Group | Arguments |
|---|---|
| Placement | `project`, `milestone`, `parentId`, `team`, `priority` |
| Classification | `addLabels` (adds), `labels` (replaces), `assignee`, `state` |

`labels` replaces the whole set; `addLabels` adds to it. Use `labels` only on a create, where there
is nothing to clobber — on an existing issue it strips every label it doesn't mention.

**Never settable here**: `estimate`, `cycle`, `dueDate`, `sortOrder`. All four read back through
`list_issues` `fields`, which makes it easy to assume they round-trip — they don't. If the user
wants an estimate or a cycle set, say it has to happen in the Linear UI rather than narrating a
write that never left.

Deciding *which* project and labels is `placement.md`; this is only what the call accepts.

## Write contract

Inline rather than in a lazily-read reference, for the same reason `implement.md` keeps its delivery phase inline: by the time a status write happens, nothing will prompt you to go read another file. Each rule is here because it has already failed in practice.

**1. Resolve the state before writing it.** Call `list_issue_statuses` for the team and match the requested state against the real list — on `statusType` first, then name. No match means stop and report the available states; it does not mean send the guess anyway. Guessed state names are the largest single cause of a status change that never happened.

**2. Never bundle `patch` with `state`.** `save_issue` is atomic: a `replace` op whose `old_string` no longer matches returns *"Patch failed, nothing was saved"* and **the state change dies with it**. Send two calls — patch first, state second. A status write should be the smallest call you can make: `id` and `state`, nothing else.

**3. Read the status back.** `save_issue` returns the saved issue with its `status` field, so verification costs no extra call. Matches what you asked → report it. Differs, or no `status` in the response, or the response is an `{"error": …}` object or an `Error:` string → **the write failed**: say so, name the issue, and quote what came back. Never narrate a status change you did not confirm.

**4. Mind the preconditions.** `Duplicate` returns HTTP 400 — *"Issues can only be moved to a duplicate state when a duplicate issue relation exists"* — unless `duplicateOf` was set in an **earlier** call. Set the relation, confirm it, then move the state.

## Beyond one issue

This file covers single-issue operations. Ranking a backlog, deciding where a new issue belongs, or cleaning up priorities and stale relations across many issues is `/backlog` — it carries the priority rubric and the rank contract that stand in for Linear's missing `sortOrder`.
