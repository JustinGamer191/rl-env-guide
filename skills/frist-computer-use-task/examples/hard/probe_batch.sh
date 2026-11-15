#!/bin/sh
# probe_batch.sh SLOT "T:att:model T:att:model ..."  runs attempts one after another on one slot; waits while 1-min load > 12
H=$(cd "$(dirname "$0")" && pwd); R="$H/../runs"; mkdir -p "$R/probe"
for job in $2; do
  T=${job%%:*}; rest=${job#*:}; A=${rest%%:*}; M=${rest#*:}
  while [ "$(uptime | sed 's/.*load averages*: *//' | awk '{print int($1)}')" -gt 12 ]; do sleep 20; done
  echo "$(date +%H:%M:%S) start $T a$A $M slot $1 load $(uptime | sed 's/.*load averages*: *//')"
  nice -n 15 python3 "$H/probe.py" "$T" "$A" "$1" "$M" > "$R/probe/${T}_a$A.out" 2>&1
  echo "$(date +%H:%M:%S) done $T a$A: $(tail -1 "$R/probe/${T}_a$A.out" | cut -c1-200)"
done
