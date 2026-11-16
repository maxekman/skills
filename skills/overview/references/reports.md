# Reports

An umbrella can name project-specific reports in `config.json`, such as a repo's own
"what to do today" skill:

```json
"reports": {
  "today": {"skill": "<repo>/.claude/skills/<name>/SKILL.md",
            "run": ["daily", "request"],
            "digest": "the verdict and the one thing to do first"}
}
```

Project skills only load in sessions started in their repo, so run a report by reading its
`SKILL.md` and following it, with the commands run from that repo's folder. Give the report's
reads and commands calls of their own, never chained with reads of this skill or another repo:
a private repo's report trips guard hooks that block any one command naming both a private
and a public repo. `run` says when:

- `daily`: on the first wake of a day. The 30-minute heartbeat catches the date change. Log
  each run in `state.md` so a restart doesn't repeat it.
- `request`: when the user asks for the report by name, or for "the report" or "status".

Print the report in chat when it runs, then put its `digest` (two lines at most) into
`notes.json` `notes`, replacing the previous one. Its output stays in the chat and in
`.overview/`, like everything else: a report about a private repo never goes into a tracker.
