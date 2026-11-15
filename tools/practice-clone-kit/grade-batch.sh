#!/bin/bash
# grade-batch.sh "agentId:QS-n:journey" ... ; audits transcript then grades sequentially (one grader at a time)
H="$(cd "$(dirname "$0")" && pwd)"
for spec in "$@"; do
  IFS=: read -r aid t j <<< "$spec"
  echo "== $t"
  python3 "$H/audit-transcript.py" "$aid" "$H/gen-workspace/wt/$t" "$H/gen-workspace/DISCOVERY.md" "$H/gen-workspace/recordings"
  "$H/grade-worker.sh" "$H/gen-workspace/wt/$t" "$j" 2>&1 | grep -v '^PASS'
done
