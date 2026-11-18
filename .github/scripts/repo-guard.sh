#!/usr/bin/env bash
# Fails the build on the patterns used in the November 2026 compromise
# (commit 5ef261f): code hidden far to the right of a line, build config that
# downloads and runs code, and a committed .env. Cheap, and it would have
# stopped that commit at review.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
status=0

# 1. A committed .env (only *.example files belong in git).
if git ls-files | grep -E '(^|/)\.env(\..+)?$' | grep -v '\.example$'; then
  echo "::error::A .env file is committed. Remove it and rotate anything in it."
  status=1
fi

# 2. Code pushed off-screen: the payload sat behind ~600 spaces to the right
#    of an innocent-looking `init();`. Flag long runs of blanks inside a line,
#    and any line over 1000 characters (real code, even a long Tailwind class
#    list, stays well under that).
while IFS= read -r file; do
  if awk '/[^ \t][ \t]{80,}[^ \t]/ || length($0) > 1000 { print FILENAME ":" NR ": " length($0) " characters, possibly hiding code"; found=1 } END { exit found ? 1 : 0 }' "$file"; then
    :
  else
    echo "::error file=$file::Suspiciously long line. Scroll right and check what is hidden there."
    status=1
  fi
done < <(git ls-files '*.py' '*.ts' '*.tsx' '*.js' '*.mjs' '*.cjs' '*.json' '*.yml' '*.yaml' '*.sh' \
  | grep -v -E '(^|/)package-lock\.json$')

# Extensionless files are what `node init` ran; check any that look like scripts.
while IFS= read -r file; do
  if head -c 200 "$file" | grep -q -E "use strict|require\(|import "; then
    echo "::error file=$file::Extensionless script in the repo. Check what it does before allowing it."
    status=1
  fi
done < <(git ls-files | grep -v '/\.' | grep -v -E '\.[A-Za-z0-9]+$' | grep -v -E '(^|/)(Dockerfile|LICENSE|Makefile)$' || true)

# 3. Build configuration that fetches or evaluates code.
for file in frontend/vite.config.ts frontend/package.json; do
  if grep -n -E 'eval\(|new Function|atob\(|node-fetch|child_process|https?://[^"'\'' ]*(raw|gist|pastebin)' "$file"; then
    echo "::error file=$file::Build configuration fetches or evaluates code."
    status=1
  fi
done
if grep -n -E '"(pre|post)?(dev|build|install|prepare|start)"\s*:\s*"[^"]*node ' frontend/package.json; then
  echo "::error file=frontend/package.json::An npm script runs an extra node program. Check it."
  status=1
fi

exit $status
