# `/task implement <description>` — resolve prose to an issue

`implement` accepts either a tracker reference or a plain description of the work. This file covers
the description form: it turns prose into an issue — adopted or created — and hands back to
`implement.md`, which owns everything from there.

This path is built for short, one-off work that should still have a ticket. Planning several issues
at once, or anything epic-shaped, is `/backlog`.

The split that matters: **searching is read-only, writing is not.** Steps 1-2 are safe inside plan
mode. Step 3 writes to the tracker and must not run until the plan is approved.

## Step 1 — Search before creating

An issue that already exists is nearly always the one you want, and a duplicate costs far more to
untangle later than the search costs now.

- **Linear**: `list_issues` with `query` set to the description verbatim, `limit: 10`, and
  `fields: ["id", "title", "description", "status", "statusType", "assignee", "url",
  "gitBranchName", "updatedAt"]`. `query` is free-text semantic search, so prose is exactly what it
  wants — don't reshape it into keywords. Scope with `team` when the repo maps to one.
- **GitHub**: `gh issue list --search "<description>" --state all --limit 10 --json
  number,title,body,state,url,assignees`.

Don't filter out closed or completed issues. One describing this exact work is a signal worth
seeing, not noise to hide — it usually means the work was already done, or deliberately dropped.

## Step 2 — Judge the matches

The question is never "is this related?" Semantic search will hand you three issues from the same
area every time. It is whether this is the **same deliverable**.

**The test: could one PR close both the existing issue and the description you were given?** If
shipping the description would leave the issue only partly done, or the issue is broader and the
description is one slice of it, that is the same *area*, not the same *deliverable*.

- **Passes** → adopt it. Name the issue you adopted and carry on; don't ask.
- **Fails, but something is close** → `AskUserQuestion` with the candidates (ID, title, status) and
  a "create a new issue instead" option. This is where the judgement is genuinely the user's.
- **Nothing close** → step 3.

Two cases always ask, whatever the test says:

- `statusType in (completed, canceled)` — reopening finished work is a decision, not an inference.
- Assigned to someone else **and** `statusType == started` — adopting silently means taking over
  work that is in flight. Every other wrong adoption is cheap to undo; this one isn't.

**When adopting**, use the issue body and the description together as context for the rest of the
flow — the description usually adds scope the ticket lacks. Offer to post that extra detail as a
comment, since a comment is additive and can't fail the way a `patch` can, but don't write it
unprompted.

If the description plainly covers several distinct deliverables, create the single issue asked for
and say once that `/backlog place` would split it. Don't block: the verb was chosen deliberately.

## Step 3 — Create the issue

**Not while the plan is still being written.** In plan mode this step goes *into* the plan as its
first action. A plan you reject should leave nothing behind in the tracker.

The binding deadline is the first commit. `/pr` needs the tracker ID to attach the PR, so an issue
that doesn't exist by then has already failed — step 8's gate checks for it. Approval is the moment
to do this; the first commit is the point of no return.

Order matters. `references/linear.md` carries the full write contract; each step here is shaped by
a way it has already failed:

1. `get_user` → the assignee.
2. Resolve the team — `list_teams`, or infer it from the project in context.
3. `list_issue_statuses` for that team → the state whose `statusType` is `started`. Resolve it;
   never send `"In Progress"` on faith, because team state names are not portable.
4. `save_issue` with no `id`: `title`, `description`, `team`, `assignee`, `state`, `priority`.
   Priority 3 (Medium) unless the description argues otherwise — that is the documented default for
   a new issue. Sending `state` on a create is safe: the contract's rule against bundling exists
   because a stale `patch` swallows the state change with it, and a create carries no `patch`.
5. Read `status` and `assignee` back off the response. A mismatch, a missing `status`, an
   `{"error": …}` object or an `Error:` string all mean the write failed — say so and quote what
   came back. If the issue exists but the state didn't take, retry as a bare `id` + `state` call
   rather than creating a second issue.
6. Capture `id`, `url` and `gitBranchName`. These feed the branch name.

Write the issue in the house style from `SKILL.md`: an imperative title of 3-7 words, and a
description that states problem plus context in one or two sentences. The prose you were handed is
raw material, not the issue body.

Then plant the bookmark, so the issue survives outside this session's memory:

```bash
jj bookmark create <gitBranchName> --revision @
```

`jj bc` bakes in `-r` and errors if you pass it again, so this needs the full form. Creating it on
an empty working copy warns *"Target revision is empty"* and is still correct: the bookmark stays
on that change, and the change becomes your first commit once you describe it. The tracker ID then
lives in the bookmark name, where `/pr` finds it without any help from the transcript. If the work
is abandoned, `jj bookmark delete <name>` cleans up.

**GitHub**: `gh issue create --title "<title>" --body "<body>" --assignee @me`, then read the number
from the returned URL. GitHub Issues has no in-progress state — the only analogue is a project
board, which `gh issue` cannot drive. Apply an in-progress label if `gh label list` shows one;
otherwise say plainly that there is no status to move, and continue. Don't narrate a state change
the tracker can't make.

## Step 4 — Hand back to `implement.md`

There is an issue now, so the rest is the existing pipeline. Rejoin at **step 3** and pin the branch
name exactly as step 2 there specifies, `gitBranchName` first. That pinned line is what `/pr`
consumes.

A freshly created issue has no comments, no linked issues, and a description written moments ago, so
the full step 6 block would be mostly empty headings. Present the condensed form:

```
## Task
[ID] — [title]  ([url])

## Codebase
[what step 5's search found: path, line range, excerpt]

## Delivery plan
**Deliverable**: [one line]
**Branch**: [pinned]
**PR title**: [ID] / [title, sentence case]
**Done when**:
- [acceptance criterion]

## Open Questions
[step 7, or "No open questions."]
```

Skip step 4 — a sentence you just typed references nothing — along with the Comments and Linked
Issues sections. Keep step 5: searching the codebase is what turns a one-line description into a
grounded plan, and it is the step that earns its cost here. Keep step 7, because on a one-liner the
ambiguities are the whole risk.

An **adopted** issue is the opposite case. It has history worth reading, so run the full step 6
block for it.

## Working memory

If the repo already has a `TODO.md` and the breakdown runs to more than one step, add the steps
under a section header carrying the ID:

```markdown
## ACME-407 — Add rate limiting to the public API
- [ ] Add a token bucket to the middleware
```

The ID belongs in the **header**, not on the items. A trailing `[ACME-407]` on an item claims *this
item is that issue*, which is why `/todo prune tracked` removes such items as redundant. A header
claims the items belong to the issue — the opposite. When the gate passes, prune the section again.

Don't create a `TODO.md` where none exists. That puts a tracked file in the diff and ships your
working notes inside the PR.
