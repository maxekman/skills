#!/usr/bin/env bash
# The checks `claude plugin validate` does not do:
#   - every skills/<name>/ is listed in plugin.json (an unlisted one loads as nothing)
#   - every listed path actually has a SKILL.md
#   - marketplace.json declares no version, which would override plugin.json
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

plugin=".claude-plugin/plugin.json"
marketplace=".claude-plugin/marketplace.json"
fail=0

while IFS= read -r path; do
  if [ ! -f "$path/SKILL.md" ]; then
    echo "listed in plugin.json but has no SKILL.md: $path" >&2
    fail=1
  fi
done < <(jq -r '.skills[]' "$plugin")

for dir in skills/*/; do
  entry="./${dir%/}"
  if ! jq -e --arg p "$entry" 'any(.skills[]; . == $p)' "$plugin" >/dev/null; then
    echo "not listed in plugin.json, so it will never load: $entry" >&2
    fail=1
  fi
done

if jq -e 'any(.plugins[]; has("version"))' "$marketplace" >/dev/null; then
  echo "marketplace.json declares a version; it would override plugin.json" >&2
  fail=1
fi

exit $fail
