#!/usr/bin/env bash
# Print the next plugin version implied by the conventional commits since the last
# release tag. Prints nothing when none of them are releasable.
#
#   .github/scripts/next-version.sh
#   BREAKING_PRE_1_0=minor .github/scripts/next-version.sh
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

manifest=".claude-plugin/plugin.json"
name="$(jq -r .name "$manifest")"

# What a breaking change does while the major version is still 0.
#   major -> promote to 1.0.0, so a removed skill is as loud as it is disruptive
#   minor -> stay on the 0.x line
: "${BREAKING_PRE_1_0:=major}"

last_tag="$(git describe --tags --abbrev=0 --match "$name--v*" 2>/dev/null || true)"
if [ -n "$last_tag" ]; then
  range="$last_tag..HEAD"
  base="${last_tag#"$name--v"}"
else
  # No release yet: every commit counts, and the manifest is the baseline.
  range="HEAD"
  base="$(jq -r .version "$manifest")"
fi

subjects="$(git log --no-merges --format=%s "$range")"
bodies="$(git log --no-merges --format=%b "$range")"

if printf '%s\n' "$subjects" | grep -qE '^[a-z]+(\([^)]*\))?!:' ||
   printf '%s\n' "$bodies"   | grep -qE '^BREAKING[ -]CHANGE:'; then
  bump=major
elif printf '%s\n' "$subjects" | grep -qE '^feat(\([^)]*\))?:'; then
  bump=minor
elif printf '%s\n' "$subjects" | grep -qE '^(fix|perf)(\([^)]*\))?:'; then
  bump=patch
else
  echo "no releasable commits in $range" >&2
  exit 0
fi

IFS=. read -r major minor patch <<<"$base"
case "$bump" in
  major)
    if [ "$major" -eq 0 ] && [ "$BREAKING_PRE_1_0" = minor ]; then
      minor=$((minor + 1)); patch=0
    else
      major=$((major + 1)); minor=0; patch=0
    fi ;;
  minor) minor=$((minor + 1)); patch=0 ;;
  patch) patch=$((patch + 1)) ;;
esac

next="$major.$minor.$patch"

# CI owns the version. A hand-edited bump lands on a version that is already tagged,
# so fail loudly here rather than quietly regress the series.
if git rev-parse -q --verify "refs/tags/$name--v$next" >/dev/null; then
  echo "refusing: $name--v$next is already tagged — was version hand-edited?" >&2
  exit 1
fi

echo "$next"
