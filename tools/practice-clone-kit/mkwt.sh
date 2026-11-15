#!/bin/bash
# mkwt.sh QS-1 -> creates gen-workspace/wt/QS-1 on branch qs-1 with a private CoW copy of node_modules
export DEVELOPER_DIR=/Library/Developer/CommandLineTools
R="$(cd "$(dirname "$0")" && pwd)/gen-workspace"
T=$1; B=$(echo $T | tr A-Z a-z)
cd "$R/clone" && git worktree add -q "$R/wt/$T" -b "$B" && cp -cR "$R/clone/node_modules.nosync" "$R/wt/$T/node_modules" && echo "$R/wt/$T ready"
