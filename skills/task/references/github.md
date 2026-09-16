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
| Add labels     | `gh issue edit <number> --add-label "<label>"`       |
| Assign         | `gh issue edit <number> --add-assignee "<user>"`     |

## Filter flags

`--state open|closed|all`, `--label "<label>"`, `--milestone "<name>"`, `--search "<GitHub search query>"`.

## Subtasks

GitHub Issues has no native parent-child. Create separate issues and reference the parent with "Part of #<number>" in the body.
