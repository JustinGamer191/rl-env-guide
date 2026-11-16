"""Difficulty probe for one attempt. Boots a private world, writes the solver prompt, and either runs a headless
`claude -p` solver (--model fable) (both models headless; --external waits for a solver launched elsewhere).
Verifies when report.json appears (plus a 15 s grace) or at the cap, tears the world down, audits the transcript.
Usage: probe.py TASK ATTEMPT SLOT MODEL [--cap-min 20]
Public dir (solver sees only this): runs/solver/<T>_a<N>/ with report.py and work/. Private: runs/private/<T>_a<N>/."""
import glob, json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from world import World, ROOT, CHROME
from tasks import TASKS

tid, att, slot, model = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
cap = 60 * float(sys.argv[sys.argv.index("--cap-min") + 1]) if "--cap-min" in sys.argv else 20 * 60
pub = os.path.join(ROOT, "runs", "solver", f"{tid}_a{att}"); priv = os.path.join(ROOT, "runs", "private", f"{tid}_a{att}")
work = os.path.join(pub, "work")
os.makedirs(work, exist_ok=True); os.makedirs(priv, exist_ok=True)
for f in ("report.json",):
    if os.path.exists(os.path.join(pub, f)): os.remove(os.path.join(pub, f))
open(os.path.join(pub, "report.py"), "w").write(
    'import json,os,sys\nassert sys.argv[1] in ("complete","infeasible"), "usage: report.py complete|infeasible \\"message\\""\n'
    'json.dump({"status":sys.argv[1],"text":" ".join(sys.argv[2:])},open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"report.json"),"w"))\nprint("reported",sys.argv[1])\n')
w = World(slot, pub, TASKS[tid].get("seed", "v2"))
for name in ("dev.log", "mail.log"):  # logs name the DB and state paths; keep them private
    os.rename(os.path.join(pub, name), os.path.join(priv, name))
w.log = os.path.join(priv, "dev.log")
json.dump(w.seed, open(os.path.join(priv, "seed.json"), "w"))

t = TASKS[tid]
urls = f"Quillstack (issue tracker): {w.url}/app" + (f"\nQuillmail (email client): {w.mail_url}/" if "quillmail" in t["apps"] else "")
prompt = f"""You are a computer-use agent operating web apps through a browser. Complete the task below.
TASK:
{t['goal']}

APPS (already running; you are the signed-in user "You"):
{urls}

How you operate the browser: write and run Python Playwright scripts (sync API). Launch Chromium with
  p.chromium.launch(executable_path="{CHROME}") and a 1440x900 viewport. Each script starts a fresh
browser, but app data persists between scripts. Run scripts with `nice -n 15 python3 ...`. Look with page.screenshot
(view the PNG with Read) and page.inner_text / locators. Act only like a human user: click, type, press keys, select options.
Rules (you will be audited):
- Work only inside {work}. Do not read, list or search any other files or directories.
- No page.evaluate or other JavaScript to read or change app state, no window globals, no direct HTTP API calls,
  no local storage or databases. Only the UI.
- Do not start or stop any servers. Close every browser you open.
- You have at most 20 minutes.
When finished, end with exactly one report:
  python3 {pub}/report.py complete "<what you did>"   or   python3 {pub}/report.py infeasible "<why>"
Then reply with one short paragraph: what you did and which report you made.
"""
open(os.path.join(priv, "prompt.txt"), "w").write(prompt)
t0 = time.time(); proc = None
MODELS = {"fable": "claude-fable-5-2", "opus": "claude-opus-5-5"}
headless = "--external" not in sys.argv
if headless:
    out = open(os.path.join(priv, "claude.json"), "w")
    proc = subprocess.Popen(["nice", "-n", "15", "claude", "-p", "--model", MODELS[model], "--permission-mode", "acceptEdits",
                             "--output-format", "json", "--allowedTools", "Bash", "Read", "Write", "Edit",
                             "--disallowedTools", "WebFetch", "WebSearch", "Skill", "Agent", "--disable-slash-commands", "--strict-mcp-config"],
                            cwd=work, stdin=subprocess.PIPE, stdout=out, stderr=subprocess.STDOUT, start_new_session=True, text=True)
    proc.stdin.write(prompt); proc.stdin.close()
open(os.path.join(priv, "READY"), "w").write(w.url); print("READY", w.url, w.mail_url, flush=True)
rp = os.path.join(pub, "report.json"); stop = os.path.join(priv, "STOP"); reported_at = None
while time.time() - t0 < cap and not os.path.exists(stop):
    if os.path.exists(rp) and reported_at is None: reported_at = time.time()
    if reported_at and time.time() - reported_at > 15: break
    if proc and proc.poll() is not None and not os.path.exists(rp): time.sleep(5); break
    time.sleep(2)
time.sleep(1); final, rep = w.final(), w.report()
score, why = t["verify"](w.seed, final, rep)
w.stop()
if proc and proc.poll() is None:
    import signal
    from world import _sig_group
    _sig_group(proc.pid, signal.SIGTERM)
    time.sleep(3)
res = {"task": tid, "attempt": att, "model": model, "score": score, "why": why[:12], "report": rep,
       "mins_to_report": round((os.path.getmtime(rp) - t0) / 60, 1) if os.path.exists(rp) else None,
       "capped": not os.path.exists(rp)}
if headless:
    try:
        j = json.load(open(os.path.join(priv, "claude.json"))); res["session_id"] = j.get("session_id"); res["cost"] = j.get("total_cost_usd")
        res["models_used"] = sorted((j.get("modelUsage") or {}).keys())
    except Exception as e: res["claude_json_error"] = str(e)
json.dump({**res, "final": final}, open(os.path.join(priv, "result.json"), "w"), indent=1)
print(json.dumps(res), flush=True)
