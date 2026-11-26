# Agent configuration

AI agents run with the developer's credentials, read untrusted text (issues, web pages,
dependency READMEs), and act on it. A committed allowlist is a standing grant to every agent
session in the repo, so it gets the same care as CI permissions.

## Files to look at

`.claude/settings.json` (committed), `.claude/settings.local.json` (should be ignored: check with
`git check-ignore -v`), `.mcp.json`, `AGENTS.md`, `CLAUDE.md`, `.claude/rules/`, `.claude/hooks/`,
and the equivalents for other agents (`.cursor/`, `.github/copilot-instructions.md`).

## Permissions

Severities: an allow rule that reaches deploy, decrypt or production is high; a missing deny
list, auto-enabled or unpinned MCP servers and a CI agent without an author gate are medium;
missing instructions are low.

- **No allow rules that grant deploy, decrypt, production or write access**: `Bash(make:*)` when
  the Makefile has deploy or decrypt targets, `Bash(git:*)`, `Bash(gh api:*)`, cloud CLIs
  (`gcloud`, `aws`, `kubectl`, `terraform`) beyond read verbs, `chmod`, package installs, and
  MCP tools that run code or SQL. Narrow rules (`Bash(make test:*)`) are fine.
- **A deny list for secrets**: `.env*`, `secrets/`, key files and tfstate, so a session can't
  read them even when asked to.
- **Project MCP servers aren't all auto-enabled.** `enableAllProjectMcpServers: true` runs any
  server a future commit adds to `.mcp.json`.
- **Hooks that enforce the rules that matter**, such as running the project's precommit before a
  commit, or blocking a push that would skip CI. Rules that exist only as prose get skipped.

## MCP servers

- **Pinned**: `npx pkg@1.2.3` or `uvx pkg==1.2.3`, never a bare package name, which runs
  whatever the registry serves today.
- **No inline credentials**: every `env` value is a reference, not a literal. Check without
  printing a value: `jq '.mcpServers[] | .env // {} | map_values(startswith("${"))' .mcp.json`
  shows `false` for each literal.
- **Known hosts**: remote servers point at the vendor's documented endpoint.

## Instructions

`AGENTS.md` or `CLAUDE.md` names the repo's dangerous shortcuts explicitly, because an agent
can't infer them:
- which commands touch production, decrypt secrets or deploy, and that they need confirmation
- that a blocked permission means stop and ask, not find another route
- that secrets and customer data are never read into the session
- anything repo-specific that bypasses a control, such as a superuser token, a prod shell, or a
  `make` target that runs against the live database

## Agents in CI

Workflows that run an agent (`anthropics/claude-code-action`, other LLM actions) on issues,
comments or PRs:
- **gate on `author_association`**, so a stranger's comment can't drive the agent
- **grant the minimum**: no `id-token: write`, deploy secrets or write tokens beyond what the
  task needs
- **treat PR and issue text as untrusted input**: an agent with write access that reads a PR
  body is a prompt-injection path to that access
