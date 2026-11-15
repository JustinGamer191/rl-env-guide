#!/bin/bash
# Ground-truth original on 5750 (UI, vite preview of the prod build) / 5751 (API), fresh DB, fixed clock.
# Usage: run-original.sh            start both (fresh DB)
#        run-original.sh build      rebuild client then start both
#        run-original.sh server     restart only the API with a fresh DB (fast reset between journeys)
#        run-original.sh stop
D="$(cd "$(dirname "$0")" && pwd)/original"
kill_port(){ lsof -ti tcp:$1 | xargs kill 2>/dev/null; }
start_server(){
  kill_port 5751; sleep 0.5
  cd "$D/server" && rm -f prisma/dev.db prisma/dev.db-journal && npx prisma db push --skip-generate >/dev/null 2>&1
  CLOCK_FIXED_TIME=2026-09-15T14:00:00Z nohup nice -n 15 node --import ./fakeclock.mjs src/index.js > "$D/server.log" 2>&1 &
  for i in $(seq 40); do curl -sf localhost:5751/api/health >/dev/null && break; sleep 0.25; done
}
case "$1" in
  stop) kill_port 5750; kill_port 5751; exit 0;;
  server) start_server; exit 0;;
esac
kill_port 5750
start_server
cd "$D/client"; [ "$1" = build ] && npx vite build > "$D/build.log" 2>&1
nohup nice -n 15 npx vite preview --port 5750 --strictPort > "$D/client.log" 2>&1 &
for i in $(seq 40); do curl -sf localhost:5750 >/dev/null && break; sleep 0.25; done
curl -s localhost:5751/api/health; echo
