"""reset -> agent -> verify for each (task, agent). Usage: run_checks.py [T1,T2..] [agent,agent..] [--slot N]"""
import json, os, sys, time, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from world import World, ROOT
from tasks import TASKS, COMMON_ADV

args = [a for a in sys.argv[1:] if not a.startswith("--")]
slot = int(sys.argv[sys.argv.index("--slot") + 1]) if "--slot" in sys.argv else 0
args = [a for a in args if not a.isdigit()]
task_ids = args[0].split(",") if args else list(TASKS)
results = []
for tid in task_ids:
    t = TASKS[tid]
    agents = {"oracle#1": t["oracle"], "oracle#2": t["oracle"], "oracle#3": t["oracle"], "alt": t["alt"], **COMMON_ADV, **t["adv"]}
    wanted = args[1].split(",") if len(args) > 1 else list(agents)
    for name in wanted:
        run_dir = os.path.join(ROOT, "runs", tid, name.replace("#", "_"))
        w = World(slot, run_dir, t.get("seed", "v2")); t0 = time.time(); err = None
        try: agents[name](w)
        except Exception as e: err = f"{type(e).__name__}: {e}"; traceback.print_exc()
        time.sleep(1.0)
        final, rep = w.final(), w.report()
        score, why = t["verify"](w.seed, final, rep)
        w.stop()
        row = {"task": tid, "agent": name, "score": score, "secs": round(time.time() - t0, 1), "why": why[:4], "error": err}
        results.append(row); print(json.dumps(row), flush=True)
        json.dump({"seed": w.seed, "final": final, "report": rep, **row}, open(os.path.join(run_dir, "result.json"), "w"), indent=1)
out = os.path.join(ROOT, "runs", f"results-{'-'.join(task_ids)}-{int(time.time())}.json")
json.dump(results, open(out, "w"), indent=1); print("saved", out)
