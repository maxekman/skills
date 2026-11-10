# init

Set up `.overview/` in the umbrella. Run it from the umbrella folder itself, not from a
workspace inside it.

## 1. Discover

```bash
/usr/bin/python3 ${CLAUDE_SKILL_DIR}/scripts/snapshot.py --discover
```

It lists every direct subfolder that has `.jj` or `.git`. jj workspaces of one repo are folded
under that repo (`opendecks-2` … `opendecks-4` under `opendecks`), and each repo gets its GitHub
`owner/repo` from `origin`. A repo with no GitHub remote gets `"watch": false`.

`nested` lists folders that hold repos one level further down, such as a `labs/` with its own
`CLAUDE.md`. Those repos are not watched from here. Tell the user that such a folder can get
its own guide (`init` run inside it), and leave `nested` out of the config.

## 2. Settle each repo's tracker

`tracker` is `"github"` (that repo's issues), `"linear:<TEAM>"` (a Linear team key such as
`DEV`), or `null` (no tracker; the board still shows its workspaces). `github` stays set for
Linear repos, because their PRs are on GitHub.

Choose Linear when the umbrella's or the repo's `CLAUDE.md` says the repo tracks work in Linear,
or when the repo's recent bookmarks or commits carry Linear IDs (`max/dev-35-…`, `DEV-35`).
Find the team key with the Linear MCP's team list. When neither settles it, ask.

## 3. Confirm, then write

Show the proposed config and ask about anything unusual, such as a repo the user may not want
watched. Then write `.overview/config.json`:

```json
{
  "repos": {
    "opendecks": {
      "github": "opendecks/opendecks",
      "tracker": "github",
      "workspaces": ["opendecks", "opendecks-2", "opendecks-3", "opendecks-4"],
      "watch": true
    }
  }
}
```

Two umbrella-level options, both off unless the user asks: `"auto_wrapup": true` sends
`/skills:wrapup` to a worker once its PR merged and it is idle, and `"reports"` names
project-specific reports (see `references/reports.md`). Mention both once; don't guess at reports.

`"prs": "all"` on a repo shows everyone's PRs, not only the user's. Offer it for repos where
teammates' PRs matter to the user's sessions; it makes the board longer.

`"watch": false` leaves a repo off the board and out of every `gh` call; use it for folders the
user doesn't work in through sessions, such as slides or an archive.

`workspaces` are folder names relative to the umbrella. A workspace added later
(`jj workspace add ../opendecks-5`) needs either a new entry here or `init` run again.
`init` merges into an existing config. It never drops a repo the user set to `"watch": false`.

Also create `.overview/notes.json` as `{}` and an empty `.overview/state.md`.

## 4. Permission rules for the guide session

Offer to merge these rules into the umbrella's `.claude/settings.local.json`. Show the diff
first, and keep the rules already there.

```json
{
  "permissions": {
    "allow": [
      "Bash(/usr/bin/python3 */skills/overview/scripts/snapshot.py*)",
      "Bash(gh pr list *)", "Bash(gh pr view *)",
      "Bash(gh issue list *)", "Bash(gh issue view *)",
      "Bash(gh issue close *)", "Bash(gh issue comment *)",
      "Bash(rex split *)", "Bash(rex block ls *)"
    ]
  }
}
```

For a Linear repo, add the Linear MCP read tools and `save_issue`, using the names the session
actually exposes (normally `mcp__linear-server__…`).

Why the umbrella folder: Claude Code reads `.claude/settings*.json` only from the folder a
session starts in, with no lookup in parent folders. So these rules reach the guide and never
the worker sessions. Why `.local`: allow rules in `settings.json` take effect only once the
folder is trusted, and `settings.local.json` rules do not wait for that. The snapshot rule uses
a wildcard path because the plugin's install path changes with every release.

The rules only spare the user a permission prompt for a write they already said yes to in
chat. The offer is still where the decision gets made.

## 5. Start the guide

If this session is interactive and started at the umbrella root, carry on as the guide here.
Otherwise, tell the user how to start the guide in its own Rex tab, in fish syntax:

```fish
rex window new -s $REX_SESSION Overview -c (pwd) --keep-open --focus=false -- claude "/skills:overview"
```

Without Rex, start `claude "/skills:overview"` in a terminal in the umbrella folder.
