#!/bin/bash
# merge-all.sh <repo> <tickets...> : merge qs-<n> in order; additive conflicts auto-resolved, typecheck after each
export DEVELOPER_DIR=/Library/Developer/CommandLineTools
M="$(cd "$(dirname "$0")" && pwd)"; cd "$1"; shift; git config merge.conflictStyle diff3
for t in "$@"; do
  s=$(date +%s)
  if git merge -q --no-edit qs-$t >/dev/null 2>&1; then r="clean"; else
    F=$(git diff --name-only --diff-filter=U); H=0; for f in $F; do H=$((H+$(grep -c '^<<<<<<< ' $f))); done
    if python3 $M/resolve-additive.py $F >/tmp/claude-501/ra.log; then git add $F && git commit -q --no-edit && r="conflict($H hunks/$(echo $F|wc -w|tr -d ' ') files: $(echo $F | xargs -n1 basename | tr '\n' ' '))auto-additive"
    else echo "qs-$t NEEDS HAND"; cat /tmp/claude-501/ra.log; exit 1; fi
  fi
  if nice -n 15 node_modules/.bin/tsc -p frontend --noEmit >/tmp/claude-501/tsc.log 2>&1; then tc=ok; else tc="FAIL"; fi
  echo "qs-$t $r tsc=$tc $(( $(date +%s)-s ))s"
  [ "$tc" != ok ] && { head -20 /tmp/claude-501/tsc.log; exit 2; }
done
