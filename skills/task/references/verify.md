# `/task verify` — check an issue against the code

Answers one question: does the code do what the issue asks? It is read-only. It reads and greps,
never runs anything, and never writes to the tracker without a yes, so it is safe inside plan mode.

The **criteria check** below is also the definition of "satisfied" that `implement`'s step-9 gate
applies to its **Done when** list. That gate keeps its own process checks (format, lint, tests, scope,
leftovers); this file owns only the question of whether each criterion is met.

## Step 1 — Resolve the issue

A reference, optionally followed by guidance, parses exactly as `implement.md` "Accepted inputs" and
step 1 describe. Guidance narrows what gets checked (`#42 just the API half`). It never adds criteria
the issue doesn't have.

With no argument, take the first of these that resolves:

1. The issue this session is already implementing or discussing.
2. A tracker ID in the local stack: bookmark names and commit messages in `jj log -r 'trunk()..@'`
   (`max/acme-407-…`, `[ACME-407]`, `#42`).
3. Neither → ask. Never guess between two candidates.

There is no description search. Verify judges an issue that exists, so prose that matches nothing
points to `/skills:task implement`, not to a tracker search.

Fetch as in `implement.md` step 2, with `includeRelations: true` on Linear and the same `--json`
fields on GitHub. Sub-issues and comments both matter here. Skip branch pinning; nothing is pushed.

## Step 2 — Collect the criteria

Take the first source that applies:

1. **This session's Done when list** from `implement` step 6, used verbatim. The user already
   approved it, including any guidance that narrowed it.
2. **Stated criteria**: checklists, an "Acceptance criteria" section, numbered requirements. Then
   apply the comments in order: a later comment that adds, drops, or changes a requirement wins over
   the description. Note which comment changed what.
3. **Inferred**: when nothing is stated, write what done means from the description and comments,
   and mark every such line *(inferred)*. The verdict on an inferred line is only as good as the
   inference, so the reader needs to see which lines are which.

Name the deliverable shape with `implement.md` step 3's signals. The shape decides where each
criterion is checked:

| Shape | Where to check it |
|---|---|
| Code, Document | the working copy |
| Follow-up issues | the tracker: sub-issues exist and together cover the scope the issue asked to split |
| Findings | the issue's comments: one that answers the question, cited by author and date |

## Step 3 — The criteria check

Judge each criterion against the **working copy**: trunk, plus the local stack, plus uncommitted
changes. That is the code the user is actually looking at.

| Verdict | Means | Must show |
|---|---|---|
| **met** | the code does it | `file:line`, plus the test that covers it if one exists |
| **partial** | some of it | what is there (cited) and what is missing |
| **unmet** | no evidence | where you looked: paths and grep terms, so the absence is credible |
| **can't tell statically** | depends on runtime, config, data, or an external system | the check that would settle it (a test to run, an endpoint to hit, a setting to read) |

Every verdict cites something. A verdict without a citation can't be checked, which defeats the
point of verifying. A missing test does not make a criterion unmet. Note it, because tests are the
gate's concern, not this check's.

Tag each `met` and `partial` citation **landed** or **unlanded**. Unlanded means the cited file
appears in `jj diff --from 'trunk()' --to @ --name-only` and the cited lines fall inside that diff's
hunks. "Built but not merged" and "shipped" call for different next steps. The tag compares
against the local `trunk()` as of the last fetch. Don't fetch to refresh it, because a fetch moves
local state.

## Step 4 — Sub-issues

List every sub-issue with its tracker status. Don't verify them; an epic's cost would grow with
every child. Any sub-issue still open makes the overall verdict **Incomplete**, whatever the
parent's own criteria say. Offer `/skills:task verify <child>` for the ones worth checking.

## Step 5 — Report

```
## Verify — [ID] [title]
**Verdict**: Incomplete | Complete, unlanded | Complete, landed
[If any line is can't-tell: N criteria need a runtime check — listed below.]
[If guidance narrowed the check: **Checked only**: [guidance]]

## Criteria
- ✅ [criterion] — `path/file.ex:42` (landed) · test `path/file_test.exs:88`
- 🟡 [criterion] — has X at `path:12` (unlanded); missing Y
- ❌ [criterion] — no match for `foo`, `bar` in `lib/`, `config/`
- ❔ [criterion] *(inferred)* — settle with: [check]

## Sub-issues
[ID — title — status, one per line. Omit if none.]

## Next
[one pointer, below]
```

The verdict is **Incomplete** if any criterion is partial or unmet, or any sub-issue is open.
Otherwise it is **Complete**, qualified *unlanded* if any citation is. Can't-tell lines don't decide
the verdict, but they do sit on the verdict line, so "Complete" never hides an unchecked runtime
behaviour.

End with exactly one pointer:

- Incomplete → `/skills:task implement <id> <the unmet and partial lines, condensed>`
- Complete, unlanded → `/skills:pr`
- Complete, landed, issue still open → `/skills:wrapup`
- Complete, landed, issue closed → nothing to do; say so

These are pointers only. Verify doesn't start any of them.

## Step 6 — Offer once

Offer to post the report as a comment on the issue, and post only on a yes. Never change the
status, close the issue, or tick its checklist. Closing belongs to the PR merge and `/wrapup`, and
the description is a body other people edit too.

When `implement`'s gate runs the criteria check, stop after step 3. The gate turns the verdicts into
pass or fail, so there is no report, pointer, or offer.
