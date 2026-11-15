#!/bin/bash
# grade-worker.sh <worktree dir> <ticket journey> : ticket journey + all regression journeys that passed at baseline
H="$(cd "$(dirname "$0")" && pwd)"
REG=dashboard_counters,board_columns,drawer_details,drawer_status_heldout,drawer_priority_heldout,comment_heldout,create_issue_heldout,list_view,list_inline_status_heldout,priority_filter_heldout,search_heldout,status_filter_heldout,inbox_page,cycles_page,command_menu_heldout,drag_heldout,dashboard_after_complete,project_breadcrumb
chmod 755 "$H/grading"
nice -n 15 python3 "$H/grading/grade.py" clone --dir "$1" --port 5760 --only "$2,$REG" --json "$H/results/$(basename $1).json"
chmod 000 "$H/grading"
