---
name: recap
argument-hint: "[period, since date/tag, #N, or repos/client]"
allowed-tools: Bash(jj *), Bash(git *), Bash(gh *), Bash(date *), Read, Grep, Glob, Skill
description: Plain-language recap of recent work for non-technical readers — clients, managers, product owners. Reads merged PRs, commits, changelogs, releases, docs and completed tracker issues over a period (default the last 7 days; also 14d, since 2026-10-01, since v0.5.0) or a single PR (#N), and writes a short paste-ready update - what is live, what is done, what is in progress, and anything to watch. Use whenever the user asks what got done, wants a weekly or status update, a stakeholder or client summary of a repo's work, or needs to explain a merged PR to someone non-technical, even without the word "recap". Customer-facing release notes and CHANGELOG entries are a different genre and not this; post-merge housekeeping belongs to /wrapup.
---

# Recap

Turns a repo's technical trail into a short update a non-engineer can read in thirty seconds.
It reports progress; it does not write release notes, CHANGELOG entries, or anything that gets
posted. The text ends up in chat for the user to paste wherever it goes.

Handle: $ARGUMENTS

## Context

- Today: !`date +%F 2>/dev/null || echo "unknown — use the session date"`
- jj root: !`jj root 2>/dev/null || echo "not a jj repo"`
- git root: !`git rev-parse --show-toplevel 2>/dev/null || echo "not a git repo"`
- Repo info: !`gh repo view --json nameWithOwner,description,defaultBranchRef 2>/dev/null || echo "gh unavailable — commits and files only"`

## Workflow

### 1. Resolve what to cover

- **Window** — nothing → the last 7 days, ending today. `14d`, `2w`, `last month`,
  `since 2026-10-01` → the obvious reading, rolling rather than calendar unless the user says
  otherwise. `since <tag>` → from that tag's commit date (`jj log --no-graph -r '<tag>' -T
  'committer.timestamp().format("%F")'`, or `git log -1 --format=%cs <tag>`).
- **Single PR** — `#N` or a PR URL → read `references/single-pr.md`, which replaces steps 2–3.
- **Repos** — the current one, unless args name other paths, a client, or "everything" → read
  `references/multi-repo.md` first.

Write the resolved range down now. It goes in the header, because "last week" read on a
Tuesday is not the week the reader assumes.

### 2. Gather

Run the independent reads in parallel. `START` is the window's first day, `BASE` the default
branch from `Repo info`.

```bash
gh pr list --state merged --base BASE --search "merged:>=START" --limit 100 \
  --json number,title,body,author,labels,closingIssuesReferences
gh pr list --state open --json title,body,isDraft,updatedAt,author --limit 30
gh run list --branch BASE --created ">=START" --json workflowName,conclusion,createdAt
```

`--base` keeps out stacked PRs that merged into a parent branch.

Commits on trunk fill the gaps — direct pushes, and the whole story when `gh` is unavailable:

```bash
jj log --no-graph -r '::trunk() & committer_date(after:"START")' \
  -T 'description.first_line() ++ "\n"'                         # jj
git log --since=START --format=%s BASE                          # git
```

**Where it landed** — the evidence step 3 needs before anything may be called shipped:

```bash
gh api 'repos/{owner}/{repo}/deployments?per_page=100' \
  --jq '.[] | [.environment, .created_at, .sha] | @tsv'
gh release list --limit 20 --json tagName,name,publishedAt
jj tag list                                  # or: git tag --sort=-creatordate
```

**What is still open** — TODO files (`**/TODO.md`, `**/*_TODO.md`) and, via `/skills:task
search`, open and recently completed tracker issues. Issue titles carry the business framing a
PR title lacks. No tracker connected, or `/task` not installed → skip it without comment.

Then the written sources, which often already say *why*: CHANGELOG and release bodies dated in
the window, and docs changed in the range. Read a doc's diff only when it explains a change the
PRs leave vague.

### 3. Shape

- **Done means nothing left.** Before calling an outcome done, check what is still open: an
  unchecked TODO item or an open issue for the same feature makes it *in progress*, however many
  PRs merged toward it. Write it as progress — what works now, what remains before anyone can
  use it. Don't carve a finished-sounding piece out of an unfinished effort to fill Done: a part
  that exists only to serve that effort belongs inside its In progress line.
- **Shipped needs proof it reached users**: a production deployment, a release or tag that
  contains the change, or a dated CHANGELOG release. Merged only, or deployed only to staging or
  a test server, is *done, not live*. No deploy signal at all is not proof either. The reader
  hears "shipped" as "customers have it", and an overstatement costs more than a weaker word.
- **Cluster by outcome, not by commit.** Five PRs toward one goal are one bullet. The linked
  issue, a shared scope, or the PR bodies usually name the goal.
- **Rank by what the reader feels**: things users can now do or no longer suffer, then
  reliability and security, then internal work.
- **Maintenance collapses.** Bot authors (`[bot]`), release commits, dependency bumps, CI and
  refactors become at most one line ("Routine upkeep: dependency updates and build fixes"), and
  nothing at all when there is real news.
- **In progress** — unfinished features from the first rule, open non-draft PRs, and started
  issues touched in the window. Anything untouched for the whole window is stale, not progress.
- **Heads-up** — risks only, the things the reader would be upset to learn later: breaking
  changes (`!` or `BREAKING CHANGE:`), reverts of shipped work, a red run on `BASE` with no
  green after it, a blocked issue. A revert inside the window cancels its original; mention
  neither. How to upgrade or try something is not a risk — a closing line, if the reader must act.

## Writing

```
**Recap — <project>, <Oct 9–16>**

<One sentence: the headline of the period, in plain words.>

**Shipped**
- <Outcome first.> <Why it matters, when the sources say so.>

**Done** (<where it runs>, not live yet)
- <Same shape.>

**In progress**
- <What works now; what is left.>

**Heads-up**
- <One line each.>
```

`<project>` is what the reader calls it — the product name from the README or repo
description, not the `owner/repo` slug. Omit an empty section rather than writing "none"; a
repo that deploys only to staging has no Shipped section at all.

- **120–250 words, at most seven bullets across Shipped and Done.** Past that, cluster harder;
  a long recap gets skimmed and the important line gets lost.
- **Plain words only.** No hashes, file paths, PR or issue numbers, branch names, function
  names, or tool names (CI, jj, MCP) — unless that thing is the product the reader knows. That
  includes illustrative ones: a sample command with a made-up ticket number is still jargon.
- **Never invent impact.** If no source says why a change matters, say what changed and stop.
  A reader who acts on a made-up benefit is worse off than one told less.
- **No filler adjectives** — "robust", "significantly", "seamless" add length, not meaning.
- **A quiet period gets one honest sentence**, not padding.
- English unless the user asks for another language.

| Source says | Recap says |
|---|---|
| `fix(api): handle null tz in /orders export (#412)` | Fixed order exports failing for accounts without a time zone set. |
| `refactor(auth): move sessions to Redis, add TTL` | Moved login sessions to new storage; idle sessions now expire on their own. *(not "faster, more secure logins" — nothing said so)* |
| 14 commits `chore(deps): bump …` | Routine upkeep: dependency updates. |
| 6 merged PRs toward invites, TODO still lists "send email" | In progress — invites: links can be created and accepted; sending them by email is next. |

## When to Read References

- `references/single-pr.md` — args are `#N` or a PR URL.
- `references/multi-repo.md` — args name a second repo path, a client or company, or ask for
  "everything" across repos. A recap of the current repo never reads it.

## Safety

- Read-only. Never post, send, comment, or publish — the user decides where the recap goes and
  who sees it. Write it to a file only when asked.
- Don't fetch. `gh` already reads the remote, and `jj git fetch` moves bookmarks and rebases
  the working copy of every workspace on the repo — including ones another session is using.
  If local trunk looks stale next to the merged PRs, trust the PRs and say so.
- One reader, one client. Never mix two clients' work in one recap; other clients' work isn't
  theirs to see. `references/multi-repo.md` covers grouping.
- Leave out credentials, internal hostnames, and customer or personal data that turn up in PR
  bodies or logs — the recap travels further than the repo does.
- Only merged work on `BASE` counts as done, and only work with proof it is live counts as
  shipped. An open or stacked PR is in progress, however finished it looks.
