#!/usr/bin/env bash
# Copy files that Claude delivered into OneDrive's _incoming/ folder into the git repo you run this from
# (same relative paths), then archive them under _incoming/_done/. Run from the repo root.
set -euo pipefail
OD="${OD:-/mnt/c/Users/krist/OneDrive/Documents/Projects/C_trachomatis_inclusivity_exclusivity}"
INC="$OD/_incoming"
[ -d .git ] || { echo "run this from the git repo root"; exit 1; }
[ -d "$INC" ] || { echo "nothing to pull ($INC missing)"; exit 0; }
n=0
while IFS= read -r f; do
  rel="${f#"$INC"/}"
  mkdir -p "$(dirname "$rel")"
  cp -v "$f" "$rel"
  mkdir -p "$INC/_done/$(dirname "$rel")"
  mv -f "$f" "$INC/_done/$rel"
  n=$((n + 1))
done < <(find "$INC" -type f ! -path "$INC/_done/*")
echo "pulled $n file(s) into $(pwd)"
