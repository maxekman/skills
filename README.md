# skills

Claude Code skills for a [Jujutsu (jj)](https://jj-vcs.github.io/jj/) based delivery
workflow: describe a commit, split what should never have been one commit, open and stack
pull requests, and keep the tracker and the working checklist in step.

They are written to be invoked by the agent when the trigger fires, not only typed by hand.

## Install

```
/plugin marketplace add maxekman/skills
/plugin install skills@maxekman
```

To give a whole repository the same workflow, commit this to its `.claude/settings.json` —
everyone who clones it then gets the skills with no install step:

```json
{
  "extraKnownMarketplaces": {
    "maxekman": { "source": "github", "repo": "maxekman/skills" }
  },
  "enabledPlugins": { "skills@maxekman": true }
}
```

## The skills

| Skill | Use it for |
|---|---|
| `/jj` | Any commit, `jj describe`, rebase, split, absorb, or conflict resolution. Splits a working copy that mixes unrelated changes into separate commits |
| `/pr` | Opening or updating a GitHub PR. Handles bookmarks, push, stacked PRs with auto-detected parent bases, and rebasing after a parent merges |
| `/task` | Linear (MCP) or GitHub Issues (`gh`) operations — create, update, search, and `implement <id>`, which carries finished work through to a commit and PR |
| `/todo` | A local `TODO.md` as working memory for a multi-step change. The counterpart to `/task`: the tracker knows the goal, this knows the steps |
| `/grill-me` | Stress-testing a plan before executing it — one question at a time, each carrying a recommended answer, exploring the codebase instead of asking whenever the answer is already there |

They interlock. `/task implement` pins a branch name from the tracker slug; `/pr` reuses
that name verbatim so the tracker auto-attaches the PR; `/jj` keeps the commits underneath
it clean enough to stack.

## Requirements

- `jj` for `/jj` and `/pr`; `gh` for `/pr` and GitHub-backed `/task`
- A Linear MCP server for Linear-backed `/task` — it falls back to GitHub Issues
- `/todo` and `/grill-me` have no dependencies

## Credits

`/grill-me` began as a fork of the skill in
[mattpocock/skills](https://github.com/mattpocock/skills) and has since diverged: upstream
is now a shim that delegates to a `grilling` skill and sets `disable-model-invocation:
true`. This copy keeps the instructions inline and stays model-invocable, so a project rule
can require it automatically rather than waiting for someone to type it.

## License

Apache 2.0 — see [LICENSE](LICENSE).
