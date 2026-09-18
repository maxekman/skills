# GitHub Issues (`gh` CLI)

Use `gh` subcommands — never raw API calls.

| Action         | Command                                              |
|----------------|------------------------------------------------------|
| List my issues | `gh issue list --assignee=@me`                       |
| Search         | `gh issue list --search "<query>"`                   |
| View           | `gh issue view <number>`                             |
| Create         | `gh issue create --title "<title>" --body "<body>"`  |
| Edit           | `gh issue edit <number> ...`                         |
| Comment        | `gh issue comment <number> --body "<text>"`          |
| Close          | `gh issue close <number>`                            |
| Reopen         | `gh issue reopen <number>`                           |
| List labels    | `gh label list --limit 100`                          |
| Add labels     | `gh issue edit <number> --add-label "<label>"`       |
| Create a child | `gh issue create --parent <number> ...`              |
| Adopt a child  | `gh issue edit <parent> --add-sub-issue <number>`    |
| Assign         | `gh issue edit <number> --add-assignee "<user>"`     |

## Filter flags

`--state open|closed|all`, `--label "<label>"`, `--milestone "<name>"`, `--search "<GitHub search query>"`.

There is no `--project` filter. `gh issue create --project` does exist, but it needs
`gh auth refresh -s project` and an issue filed into a project cannot be found again from the CLI —
labels and parents round-trip, projects don't. That asymmetry is why `/task` leaves projects alone
on the GitHub backend.

## Subtasks

GitHub Issues has native parent-child. Create the child with `--parent <number>`, or attach one that
already exists with `gh issue edit <parent> --add-sub-issue <number>`. Read them back with
`gh issue view <parent> --json parent,subIssues`.

Children inherit nothing — pass `--label` on each, the same as Linear. See `placement.md`.
