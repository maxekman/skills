# Placement — project, labels, and hierarchy

What an issue is *filed under*, decided while it is being created. Three questions: which project,
which labels, and whether it hangs off a parent.

This is the single-issue slice. Ranking a backlog, re-filing many issues at once, or setting a
milestone belongs to `/backlog` — the last section says when to stop and hand over.

## The discovery pass

Run once per session, before the first write, and keep the result in context. Re-fetching per
issue costs calls and buys nothing: a workspace's vocabulary does not change mid-session.

Three sources, most authoritative first. Stop as soon as the answer is unambiguous.

**1. What is already written.** Grep the project's `CLAUDE.md` and `AGENTS.md`, then
`~/.claude/CLAUDE.md`, for a tracker section. A convention someone wrote down beats one inferred
from data, because it encodes intent the tracker cannot show — "everything in this repo goes in
Platform" is a decision, not a pattern.

**2. The tracker's own vocabulary**, for whatever step 1 left open:

- `list_projects` — the names, and which are still active.
- `list_issue_labels` with `includeGroups: true`. The groups are the important half; see below.
- `list_teams`, only if the team is still unknown. Usually it is already resolved.

**3. The neighbours**, when the project is still unclear after both:

```
list_issues(team: "<team>", limit: 20, fields: ["title", "project", "labels"])
```

Where similar work landed is the strongest signal available, and the one that survives a workspace
whose conventions were never written down.

### Recording a convention

When the user confirms a rule that was not written anywhere — "yes, this repo is always API v2" —
offer to add it to a `CLAUDE.md` or `AGENTS.md` that **already exists**:

```markdown
## Tracker

- Linear team: `Platform` (PLAT)
- Default project: `API v2`
- Labels: always set an `area/*`; `type/*` comes from the template, don't override
```

Loose prose, not a schema — the next session reads it, and so does a human. Offer rather than
assume: this edits a tracked file and lands in someone's diff. Never create the file. A repo
without a `CLAUDE.md` has not asked for one.

## Labels

**The vocabulary is the allowlist.** Apply only labels `list_issue_labels` returned. A name that
is not on that list has unverified behaviour on `save_issue`: it may fail the whole call, taking
anything bundled with it down too (write contract rule 2 in `linear.md`), or quietly mint a
near-duplicate of a label the team curates. When the obviously-right label does not exist, propose
it and let the user create it.

**Label groups carry the semantics.** Linear groups are mutually exclusive — a `type` group holds
`bug`, `feature`, `chore`, and an issue takes at most one. Two consequences worth acting on:

- Send one label per group. Two from the same group is the case Linear rejects.
- A group is a question the workspace decided to always answer, so leaving one unfilled on a new
  issue is a gap worth naming. An ungrouped label is optional: apply it where it fits, skip it
  where it doesn't.

**`labels` on a create, `addLabels` on an update.** `labels` replaces the whole set. On a create
there is nothing to clobber, so it is the right call; on an existing issue it silently strips every
label it doesn't mention, which turns "add one label" into "remove the rest".

GitHub works the same shape with different names: `gh label list` to discover, `--label` on create
and `--add-label` on edit to write. It has no label groups, so the mutual-exclusion rule has
nothing to bite on there.

## Hierarchy

An epic is a parent issue with sub-issues — not a project, and not an initiative, for which the
MCP exposes no tool at all.

- **Linear**: `save_issue(parentId: "<parent>")` on each child. `parentId` is also a `list_issues`
  filter, so `list_issues(parentId: "<parent>")` reads the whole set back in one call. Do that
  after a breakdown rather than trusting six separate responses.
- **GitHub**: `gh issue create --parent <n>`, or `gh issue edit <parent> --add-sub-issue <n>` when
  the child already exists.

**Sub-issues inherit nothing.** A child created with only a `parentId` has no project and no
labels — precisely the unfiled issue `/backlog groom` flags as its second defect. Carry the
parent's project and labels down to each child unless that child genuinely belongs elsewhere.

## When to stop and hand over

**The two decisions have very different costs, so they get different bars.** A wrong label sits
visibly on the issue and one call removes it. A wrong project files the issue onto a board nobody
working on it reads, and nothing surfaces it again. Label generously; place carefully.

For the project the question is not *which candidate looks best* but *how many survive*. Candidates
come from three places, strongest first: a written convention naming this repo's project;
inheritance, from a parent issue or from the near-match that step 2 of `find-or-create.md` turned
up — rejected as the same deliverable says nothing about it being the wrong home; and
`list_projects` returning exactly one plausible match.

One survivor → apply it and say so in a line. Two or more, or none → that is the ambiguous case,
and taking the first is the failure this rule exists to prevent. List the candidates and hand to
`/backlog place`, which is read-only and answers project, milestone, labels, priority and blockers
together rather than one at a time.

Otherwise bias toward placing: state what you picked and why in one line, then move on. Stopping to
ask costs the uninterrupted run that `/task implement "<description>"` exists to protect. The
exception is filing into someone else's project — that one asks.
