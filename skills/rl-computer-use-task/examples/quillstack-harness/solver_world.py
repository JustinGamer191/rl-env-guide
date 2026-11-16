"""Boot a world for a real-agent attempt, wait for STOP file, verify, tear down.
Usage: solver_world.py TASK ATTEMPT SLOT. Solver sees only runs/solver/<T>_a<N>/ (report.py + work/); seed and verdict go to runs/private/."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from world import World, ROOT
from tasks import TASKS
tid, att, slot = sys.argv[1], sys.argv[2], int(sys.argv[3])
pub = os.path.join(ROOT, "runs", "solver", f"{tid}_a{att}"); priv = os.path.join(ROOT, "runs", "private", f"{tid}_a{att}")
os.makedirs(os.path.join(pub, "work"), exist_ok=True); os.makedirs(priv, exist_ok=True)
open(os.path.join(pub, "report.py"), "w").write(
    'import json,os,sys\nassert sys.argv[1] in ("complete","infeasible"), "usage: report.py complete|infeasible \\"message\\""\n'
    'json.dump({"status":sys.argv[1],"text":" ".join(sys.argv[2:])},open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"report.json"),"w"))\nprint("reported",sys.argv[1])\n')
w = World(slot, pub)
os.rename(w.log, os.path.join(priv, "dev.log")); w.log = os.path.join(priv, "dev.log")  # dev.log names the DB path; keep it private
t0 = time.time(); json.dump(w.seed, open(os.path.join(priv, "seed.json"), "w"))
open(os.path.join(priv, "READY"), "w").write(w.url); print("READY", w.url, flush=True)
stop = os.path.join(priv, "STOP")
while not os.path.exists(stop) and time.time() - t0 < 40 * 60: time.sleep(2)
time.sleep(1); final, rep = w.final(), w.report()
rp = os.path.join(pub, "report.json")
score, why = TASKS[tid]["verify"](w.seed, final, rep)
w.stop()
res = {"task": tid, "attempt": att, "score": score, "why": why, "report": rep,
       "secs_to_report": round(os.path.getmtime(rp) - t0) if os.path.exists(rp) else None}
json.dump({**res, "final": final}, open(os.path.join(priv, "result.json"), "w"), indent=1); print(json.dumps(res), flush=True)
