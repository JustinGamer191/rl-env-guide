#!/bin/sh
# audit_fable.sh T_aN : audit a headless fable probe transcript
R=$(cd "$(dirname "$0")/../runs" && pwd); W="$R/solver/$1/work"
SID=$(python3 -c "import json;print(json.load(open('$R/private/$1/result.json'))['session_id'])")
SLUG=$(echo "$W" | sed 's#[^A-Za-z0-9]#-#g')
python3 "$(dirname "$0")/audit.py" "$HOME/.claude/projects/$SLUG/$SID.jsonl" "$W"
