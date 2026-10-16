---
name: wrapup
argument-hint: "[#N, PR url, or bookmark]"
allowed-tools: Bash(jj *), Bash(gh *), Bash(curl *), Read, Grep, Glob, Skill
description: Post-merge wrap-up for a GitHub PR. Fetches and moves onto a fresh change on trunk when nothing else is in flight, confirms the merge actually reached dev or staging (the deploy and smoke runs it triggered, plus a read-only health probe), and lists the work the PR left behind - unresolved review threads, unchecked PR-body items, tracker issues that did not close, open TODO.md items, new TODO/FIXME lines. Use whenever the user says a PR merged, landed, or went in, asks to wrap up or clean up after a merge, asks what is left from #N, or wants to know whether staging picked up the change, even without the words "wrap up". Opening or updating a PR, and rebasing a stack after its parent merged, belong to /skills:pr; choosing what to work on next belongs to /backlog.
---

# Post-merge Wrap-up

The step after a PR merges: get the local repo off the dead stack, confirm the change is live
where it auto-deploys, and surface what the PR left undone. It never opens PRs (`/skills:pr`)
or picks the next issue (`/backlog`) — it ends by pointing at the latter.

Handle: $ARGUMENTS

## Context

- `jj status`: !`jj status 2>/dev/null || echo "not a jj repo"`
- Local stack: !`jj log -r 'trunk()..@' 2>/dev/null || echo "no trunk() resolvable"`
- Bookmarks: !`jj bookmark list 2>/dev/null || echo "none"`
- Repo info: !`gh repo view --json nameWithOwner,defaultBranchRef 2>/dev/null || jj git remote list 2>/dev/null || echo "no remote detected"`
- Recently merged by me: !`gh pr list --author @me --state merged --limit 3 --json number,title,headRefName,mergedAt 2>/dev/null || echo "gh unavailable"`

## Workflow

Resolve the PR before fetching: fetch can drop the merged bookmark, and with it the easiest
way to tell which PR this stack belonged to.

### 1. Resolve the PR

First that fires:

1. **Argument** — `#N`, a number, or a PR URL → that PR. A bookmark name →
   `gh pr list --head <name> --state all`.
2. **Local stack** — a bookmark in the `Local stack` above → `gh pr list --head <bookmark> --state all`.
3. **Recently merged by me** — the newest entry. If several merged within the same hour and
   nothing local disambiguates, ask which.

```bash
gh pr view <N> --json number,title,url,state,mergedAt,mergeCommit,commits,body,headRefName,autoMergeRequest,closingIssuesReferences
```

Then branch on `state`:

- **MERGED** → continue.
- **OPEN** with `autoMergeRequest` set, or the user said "once it lands" → the merge is minutes
  away, so wait rather than send them back later. Poll `state` every 60s for up to 15 minutes;
  still open after that → report `gh pr checks <N>` and stop.
- **OPEN** otherwise, or **CLOSED** unmerged → report state, `reviewDecision`, and checks, then
  stop. Nothing below means anything until it merges.

### 2. Sync

```bash
jj git fetch
```

Fetch often finishes the job itself: once it sees the PR's commits landed, it abandons the local
copies and rebases `@` onto trunk. If `jj log -r '@- & trunk()'` lists a commit, `@` is already
where it belongs — skip the move and go straight to the leftover check below. Moving anyway
just stacks a second empty change.

Otherwise, move only when it can't strand anything: `@` has no changes, **and** every commit in
`trunk()..@-` is one of the PR's `commits[].oid` (an empty set qualifies). Commits are signed at
push time, so local ids equal the pushed ones and the comparison is exact.

```bash
jj log --no-graph -r 'trunk()..@-' -T 'commit_id ++ "\n"'
```

- **Safe** → `jj new trunk()`.
- **Not safe** → leave `@` where it is and name what blocked it (working-copy changes, or the
  unrelated commits by title). Read `references/sync.md` — the blocker is often a stacked
  child PR.

Either way, check that no merged commits are still visible:
`jj log -r '::visible_heads() & (commit_id(<oid1>) | commit_id(<oid2>))'` — anything listed is
a leftover; `references/sync.md` covers abandoning exactly those.

### 3. Live systems

Always report what the merge commit triggered — this is the cheapest signal there is, and a
red run on `main` is the most important thing the wrap-up can find:

```bash
gh run list --commit <mergeCommit.oid> --json databaseId,workflowName,event,status,conclusion,url
```

Then look for deployed environments: a repo-local skill whose name mentions verify or deploy
under `.claude/skills/`, `environment:` blocks in `.github/workflows/*`, and staging/dev
sections in `CLAUDE.md` or `AGENTS.md`. Found any → read `references/live-systems.md`. Found
none → report "No deployed environments detected" and move on.

### 4. Leftovers

Collect from every source; an empty source is omitted from the report, not listed as "none".

- **PR body** — unchecked `- [ ]` items in `body`.
- **Review threads** — unresolved ones. `gh pr view` has no field for this, so ask GraphQL:
  ```bash
  gh api graphql -F o=<owner> -F r=<repo> -F n=<N> -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){pullRequest(number:$n){reviewThreads(first:100){nodes{isResolved path line comments(first:1){nodes{author{login} body url}}}}}}}' \
    --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved | not)'
  ```
- **Tracker** — a tracker ID from `headRefName` or the title (`[A-Z]+-\d+`), or
  `closingIssuesReferences`. Read it with `/skills:task show <id>`: state, and any open
  sub-issues. An issue still open after its PR merged usually means the auto-close didn't fire.
- **TODO.md** — open items under a `## <ID> — …` header or tagged `[<ID>]`, in `**/TODO.md`.
- **Diff** — `TODO`, `FIXME`, `XXX`, `HACK` used as comment markers (`# TODO:`, `// FIXME`,
  `<!-- TODO`) on added lines in `gh pr diff <N>`. Only added lines, because pre-existing
  markers aren't this PR's leftovers. Only markers, because prose that merely mentions the word
  (docs about `TODO.md`, a sample report line) isn't a note anyone left for later.
- **Session** — anything `/task implement` reported as consciously left out of scope, if it ran
  in this session.

### 5. Report

```
## Wrap-up — #<N> <title>

Sync
  fetched; @ is a new change on main          (or: left in place — <reason>)

Live systems
  Release (push) ✓
  <one line per environment, when step 3 found any>

Remaining work
  Tracker   ACME-407 still "In Review" (did not auto-close)
  Review    2 unresolved threads — <links>
  PR body   - [ ] update runbook
  Diff      lib/foo.ex  # TODO: drop shim after v3
```

Then make **one** batched offer covering whichever apply: close the tracker issue (via
`/skills:task update <id> status done`), file follow-ups (via `/skills:task create`, one per
leftover the user picks), prune finished TODO items (`/todo prune done`). Act only on what the
user approves.

When the PR closed a tracker issue or went out in a release — a sign that someone outside the
team is waiting on it — add one line: `Explain it to stakeholders: /skills:recap #<N>`. Offer
it; don't run it, since who hears about the change is the user's call.

When sync succeeded, every run is green, and nothing remains, end with one line:
`Ready for the next one: /skills:backlog next`. Don't invoke it — picking the next task is the
user's call.

## When to Read References

- `references/live-systems.md` — step 3 found an environment, a deploy workflow, or a repo-local
  verify skill.
- `references/sync.md` — step 2 refused to move, matched commits survived the move, or
  `Repo info` shows `origin <url>`.

Most wrap-ups read only `live-systems.md`, and a repo with nothing deployed reads neither.

## Safety

- Never move `@` over working-copy changes or unrelated commits — `jj new trunk()` would park
  them on a side head where they are easy to lose track of.
- Abandon only commits whose ids are in the merged PR's commit list, never by title — an
  unrelated local commit can share a title, and only the ids prove which ones the PR carried.
- Never touch protected bookmarks (`main`, `master`, `develop`, `staging`, `prod`).
- Live checks are read-only. Never dispatch a deploy, re-run a workflow, write to an
  environment's data, or switch a kube context — the wrap-up observes what the merge did.
- Production is out of scope unless the merge itself auto-deployed there.
- No tracker, TODO.md, or issue writes without the user's yes — the same rule `/task` holds.
