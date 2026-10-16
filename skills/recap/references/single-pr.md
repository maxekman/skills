# Single-PR mode

Read when args are `#N` or a PR URL: the user wants one change explained, usually right after
it merged. The main skill's *Writing* rules still apply; this replaces its gather and shape.

## Gather

```bash
gh pr view N --json title,body,state,mergedAt,mergeCommit,baseRefName,closingIssuesReferences
```

Read the linked issue with `/skills:task show <id>` when there is one; its title usually says
why the change was wanted. Then decide where the change is, with the same proof the main skill
asks for:

- **Live** — a production deployment at or after `mergeCommit`, or a release or tag that
  contains it (`gh api 'repos/{owner}/{repo}/deployments?sha=<oid>'`, `gh release list`,
  `git tag --contains <oid>`).
- **Done, not live** — merged, with no such proof. Say where it runs if a staging deployment
  shows it.
- **Not merged** — say it is in review and not available yet.
- **Part of something bigger** — the linked issue is still open, or a TODO file still lists
  the feature → say this is one step toward it and what remains.

## Write

```
**Recap — <project>: <plain-language title>** (<live | merged, not live yet> · <date>)

- <What changed, in the reader's terms.>
- <Who notices, and how.>
- <What they need to do, if anything.>
```

At most three short bullets and about 80 words. This usually lands in a chat message, where a
dense paragraph gets skipped and three short lines get read.
