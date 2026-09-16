# `/task implement` — gather context, then carry the work to a PR

Two phases:

- **Phase 1 — context (steps 1-7).** Read-only. Fetches, reads, greps, presents. Never creates, updates, or comments — safe inside Claude Code plan mode.
- **Phase 2 — delivery (step 8).** Runs after the work is actually done. This is where `/jj` and `/pr` get invoked.

Phase 2 lives in this file rather than in a lazily-read reference on purpose: by the time the implementation is finished, nothing will prompt you to go read another file. It has to already be in context, so keep it here.

## Accepted inputs

Linear's "Copy link" and copy-as-markdown produce several shapes. Normalize before parsing:

- Strip wrapping `<`/`>` or backticks some clients add.
- Markdown link — `[ACME-407 Spike: verify SSO sandbox](https://linear.app/...)` — take the URL inside `(...)`; the link text is the real title, keep it.
- Drop `?query` and `#fragment` **from URLs only** — match the bare-reference patterns first. A bare `#42` is a GitHub issue, and treating its `#` as a fragment delimiter leaves an empty string. A `#comment-<id>` fragment on a Linear URL is worth keeping hold of: the user is pointing at that specific comment, so lead with it in the summary.

| Input | Example |
|---|---|
| Linear URL with slug | `https://linear.app/acme/issue/ACME-407/spike-verify-sso-sandbox-reservation-creation` |
| Linear URL, no slug | `https://linear.app/acme/issue/ACME-407` |
| Bare Linear ID | `ACME-407` or `acme-407` |
| GitHub URL | `https://github.com/<owner>/<repo>/issues/42` |
| Bare GitHub ref | `#42` or `42` (repo inferred from cwd) |

## Step 1 — Parse the reference

Linear issue URLs are `linear.app/<workspace>/issue/<ID>/<slug>`. Keep all three parts — each earns its place later:

- **workspace** (`acme`) — disambiguates when several Linear workspaces are connected, and rebuilds the canonical link for the PR body.
- **ID** (`ACME-407`) — uppercase it; the tracker matches on this regex and `/pr` puts it in the title slot.
- **slug** (`spike-verify-sso-sandbox-reservation-creation`) — this is Linear's own title slug, byte-identical to the tail of the branch name it generates. It gives you a usable branch name before any network call.

Then dispatch:

- Host `linear.app` → Linear. Host `github.com` → GitHub, ID from `/issues/42`.
- `^[A-Za-z][A-Za-z0-9]+-\d+$` → Linear ID (uppercase it).
- `^#?\d+$` → GitHub issue in the current repo (`gh repo view` to confirm).
- A `linear.app` URL whose segment after the workspace is `project` or `document`, not `issue` — that is not an issue. Say so and offer the sensible alternative (list the project's issues, read the document).
- Genuinely ambiguous → fall back to standard backend detection and ask.

## Step 2 — Fetch the issue

- **Linear**: `mcp__linear-server__get_issue` with the identifier (`ACME-407`). Comments come from `mcp__linear-server__list_comments`. Capture title, state, assignee, labels, priority, description, comments, linked/related issues, parent, sub-issues — and **`gitBranchName` if the response carries it**.
- **GitHub**: `gh issue view <number> --json number,title,state,assignees,labels,body,comments,milestone`. If the URL named a different repo than cwd, pass `--repo <owner>/<repo>`.

**Pin the branch name now, while the issue data is in front of you.** `/pr` step 3 looks for exactly this and uses it verbatim, so it has to appear in your output:

1. `gitBranchName` from the Linear response, if present — it reflects the user's own Linear branch-format setting.
2. Otherwise `<git-user>/<id-lower>-<slug>`, where `<git-user>` is the local part of `jj config get user.email` (`max@looplab.se` → `max`) and `<slug>` is the URL slug verbatim. This reproduces Linear's default format; Linear links the PR off the ID regex anyway, so a near-miss slug still attaches.
3. No slug in the URL and no `gitBranchName` → kebab-case the issue title yourself.

If the issue is already closed, flag it prominently — the user may want context, not new work, and should confirm before planning.

## Step 3 — Read the deliverable shape

Not every issue ends in shipped code, and guessing wrong here wastes the whole session. Decide what this issue actually produces before planning how to do it. Signals: labels (`spike`, `research`, `discovery`, `chore`), title verbs (*Spike*, *Investigate*, *Verify*, *Evaluate*, *Research*, *Scope*, *Explore*, *Assess*, *POC*), and whether the description poses a **question** rather than describing a change.

| Shape | Looks like | Ends in |
|---|---|---|
| **Code** | describes a change to make | commit + PR — the default |
| **Document** | asks for an ADR, RFC, spec, runbook, migration plan | commit + PR (a docs PR is still a PR) |
| **Follow-up issues** | an epic, "break down X", "scope Y", a spike whose stated output is tickets | proposed issues — **ask before creating any** |
| **Findings** | verify/investigate/evaluate; the output is knowledge | a written answer — offer to post it to the tracker |

These combine routinely: a spike often lands findings *and* an ADR *and* a set of follow-up issues. Name every shape that applies rather than forcing one. Say the shape out loud in the Delivery plan so the end-of-work gate knows what "done" means.

## Step 4 — Follow explicit references

If the description or comments mention specific files (`See SPEC.md`, `lib/auth/session.ex`, `docs/uptime.md`), read the relevant sections. For large files, grep for keywords tied to the issue and show the surrounding section (one `##` header to the next) rather than the whole file.

## Step 5 — Search related project docs

Extract 1-2 core keywords from the issue title (the main noun/concept, not filler — from `spike-verify-sso-sandbox-reservation-creation` that is `sso` and `reservation`, not `spike` or `verify`). Search:

- Glob `**/SPEC.md` and grep within each for the keywords.
- Grep `**/*.md` — show up to 5 matching files with brief excerpts.
- Check `docs/` and any `docs/adr/` if present — for a document-shaped issue, existing ADRs establish the format to follow.

## Step 6 — Present the context

```
## Task
**[ID]** — [title]
**Status**: [state] | **Assignee**: [assignee] | **Priority**: [if set]
[If closed: ⚠ This issue is closed — confirm before planning new work.]

[Description, or distilled summary if very long]

## Comments
[Last 3-5, one-line summaries with author. Keep ones containing decisions or requirements.]

## Linked Issues
[Parent, sub-issues, "relates to" links with titles and statuses. Omit if none.]

## Documentation
[For each referenced or discovered doc: path, line range, matching excerpt]

## Delivery plan
**Deliverable**: [shape(s) from step 3]
**Branch**: [pinned in step 2]
**PR title**: [ID] / [issue title, sentence case]
**Done when**:
- [acceptance criterion]
- [acceptance criterion]

## Open Questions
[See step 7. If none: "No open questions — the issue is well-scoped."]
```

Keep excerpts focused — enough context to plan, not a wall of text.

Build the PR title from the **issue title**, not the slug — the slug has lost its capitalization, so `spike-verify-sso-sandbox-reservation-creation` round-trips as "Spike verify sso sandbox…" and mangles acronyms like SSO. Drop the branch and PR title lines when the deliverable is findings or follow-up issues only; add them back if code or docs end up changing after all.

Derive **Done when** from the issue's own acceptance criteria where it states them. Where it doesn't, write what you believe done means and mark the lines as your inference — that is exactly the kind of gap step 7 exists to catch.

## Step 7 — Surface ambiguities

Scan for genuine gaps:

- Missing acceptance criteria — how will we know this is done?
- Underspecified scope — e.g., "add monitoring" without saying which services.
- Multiple plausible technical approaches the issue doesn't pick between.
- Conflicting guidance across comments — a later one contradicts the description.

Resolve them with `AskUserQuestion` — multiple choice where possible, with an escape hatch. Don't ask about things the issue already answers. If nothing is ambiguous, say so explicitly so the user knows the check ran.

Getting these answered now is what makes step 8 able to run unattended: an unresolved question is a gate failure later, so it costs far less to settle it here.

## Step 8 — Deliver

Phase 1 ends here; the user plans and builds. **Don't draft the plan inside this skill** — that's the caller's job. But the delivery contract below is yours, and it applies when the work is finished.

When the implementation is complete, run the gate. If every condition holds, invoke `/jj` and then `/pr` **without asking** — that autonomy is the point, and the user reviews at the PR.

**Gate — all must hold:**

- Every **Done when** line is satisfied.
- The project's formatter, linter, and fast tests pass. Find the targets in `Makefile`, `package.json`, `mix.exs`, or `.mise.toml`. If you cannot run them at all, that is a gate failure — say so rather than reporting green.
- New behavior has the tests a reviewer would ask for, or the repo demonstrably doesn't test that area.
- The diff stays inside the issue's scope. Unrelated drive-by edits mean stop and ask, not a bigger PR.
- No question from step 7 is still open, and no debug leftovers, stubs, or new `FIXME`s from this work remain in the diff.

**Stop and report instead — do not auto-PR — when:**

- Any gate condition fails. Say precisely which one and what is left.
- The change touches secrets, credentials, DB migrations, infra/deploy config, or auth. These are cheap to review before a PR exists and expensive to unwind after.
- The deliverable was **findings** and no code or docs changed — present the findings and offer to post them to the tracker. Posting is outward-facing, so ask first.
- The deliverable was **follow-up issues** — list the issues you propose (title + one-line body each) and ask before creating any. `/task create` mutates the tracker; that stays a human decision.

**On a pass, hand off in order:**

1. `/jj` — it reads the diff, splits mixed changes, and writes the message. Don't pre-compose the commit yourself. If a `TODO.md` tracks this work, `/jj` checks the items off and carries the tracker tag (`[ACME-407]`-style) into the message.
2. `/pr` — pass the pinned branch name so the Linear slug survives verbatim: `/pr <branch-name>`. It builds the `<ID> / Title` PR title and attaches the tracker link.
3. Report the PR URL, plus anything you consciously left out of scope.

A document-shaped deliverable goes through the same gate — an ADR lands as a docs PR. Skip only the "tests for new behavior" condition, which has nothing to bite on.
