# Recapping more than one repo

Read when args name another repo path, a client or company, or "everything".

## Resolve the repo set

- **Paths** → use them as given. Each must be a jj or git root; skip and name any that isn't.
- **A client, company, or "everything"** → this needs a map from names to directories. Use a
  workspace-map skill if one is installed (one that says which client owns which repo, such as
  a personal `dev-atlas`); otherwise ask for the paths. Guessing from directory names is how
  one client's work ends up in another's recap.
- **"Everything"** → keep only repos with commits in the window, so the recap isn't a list of
  quiet projects. With jj, `jj log -r '::trunk() & committer_date(after:"START")' --limit 1`
  per repo; with git, `git log --since=START -1 --format=%h BASE`.

Respect whatever the map marks off-limits — secrets, archives, third-party code. A recap needs
only commit metadata and PR text, never a recursive search.

## Run per repo

Run step 2 of the main workflow inside each repo: `cd` there, or pass `-R owner/repo` to every
`gh` call (and `-R <path>` to `jj`, `-C <path>` to `git`). Mixing flagged and unflagged calls
reads the wrong repo the moment one falls back to the current directory.

## Group

- **Different clients → separate recaps**, one per client, each with its own header. They are
  going to different readers, and one client's work isn't another's business. Never merge them
  to save space.
- **One client, several repos → one recap.** Cluster by outcome across repos — the reader
  doesn't know or care that the API and the app live apart. Name a repo only where the reader
  knows it as a product.
- **The user's own overview** ("what did I do this week", for themselves) → one recap with a
  short section per client is fine, since the reader is the user. Say so in the header.
