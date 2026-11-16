"""Screenshot-only difficulty probe (pixel-agent style): the solver sees pixels only, through cu.py (cu_screen.py client).
Boots a private world on slot SLOT (ports 6100+10*SLOT .. +2), a cu_screen server on port +5, then headless `claude -p`
with tools limited to Read plus Bash for cu.py only (permission mode dontAsk: anything else is denied, not prompted).
Verifies when report.json appears (plus 15 s grace) or at the cap, tears everything down, records actions and turns.
Usage: probe_screen.py TASK ATTEMPT SLOT MODEL [--cap-min 30]
Public: runs/screen/solver/<T>_a<N>/ (report.json, work/ with cu.py, cu.json, shots/). Private: runs/screen/private/<T>_a<N>/."""
import json, os, shutil, signal, socket, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from world import World, ROOT, CHROME, _sig_group
from tasks import TASKS

H = os.path.dirname(os.path.abspath(__file__))
tid, att, slot, model = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
PROMPT_OVERRIDE = os.environ.get("CU_PROMPT_OVERRIDE")
cap = 60 * float(sys.argv[sys.argv.index("--cap-min") + 1]) if "--cap-min" in sys.argv else 30 * 60
MODELS = {"fable": "claude-fable-5-2", "opus": "claude-opus-5-5", "haiku": "haiku"}
pub = os.path.realpath(os.path.join(ROOT, "runs", "screen", "solver", f"{tid}_a{att}"))
priv = os.path.realpath(os.path.join(ROOT, "runs", "screen", "private", f"{tid}_a{att}"))
for d in (pub, priv): shutil.rmtree(d, ignore_errors=True)  # fresh dirs: an old one leaks the last solver's shots
work = os.path.join(pub, "work"); os.makedirs(work); os.makedirs(priv)
cport = 6105 + slot * 10
with socket.socket() as so:
    if so.connect_ex(("127.0.0.1", cport)) == 0: raise SystemExit(f"port {cport} busy; pick another slot")

w = World(slot, pub, TASKS[tid].get("seed", "v2"))
for name in ("dev.log", "mail.log"):
    os.rename(os.path.join(pub, name), os.path.join(priv, name))
w.log = os.path.join(priv, "dev.log")
json.dump(w.seed, open(os.path.join(priv, "seed.json"), "w"))
t = TASKS[tid]
uses_mail = "quillmail" in t["apps"]
start = f"{w.mail_url}/" if uses_mail else f"{w.url}/app"
shutil.copy(os.path.join(H, "cu_screen.py"), os.path.join(work, "cu.py"))
json.dump({"port": cport}, open(os.path.join(work, "cu.json"), "w"))
rp = os.path.join(pub, "report.json")
cu = subprocess.Popen(["nice", "-n", "15", sys.executable, os.path.join(H, "cu_screen.py"), "serve", "--port", str(cport),
                       "--shots", os.path.join(work, "shots"), "--log", os.path.join(priv, "actions.jsonl"), "--start", start,
                       "--allow", w.url, w.mail_url, "--chrome", CHROME, "--report-file", rp],
                      stdout=open(os.path.join(priv, "cu.log"), "w"), stderr=subprocess.STDOUT, start_new_session=True)
for _ in range(60):
    time.sleep(0.5)
    if "CU_READY" in open(os.path.join(priv, "cu.log")).read(): break
else:
    w.stop(); _sig_group(cu.pid, signal.SIGKILL); raise SystemExit("cu server did not start: " + open(os.path.join(priv, "cu.log")).read()[-500:])

urls = f"Quillstack (issue tracker): {w.url}/app" + (f"\nQuillmail (email client): {w.mail_url}/" if uses_mail else "")
CU = "python3 cu.py"
prompt = f"""You are a computer-use agent operating web apps in a browser that you can only see through screenshots. Complete the task below.
TASK:
{t['goal']}

APPS (already open in the browser; you are the signed-in user "You"):
{urls}
The browser currently shows {start}

How you operate the browser (run these from your working directory {work}):
  {CU} screenshot                 saves a PNG of the 1280x800 screen and prints its path
  {CU} click X Y                  left click at pixel (X, Y) of the screenshot; add --double or --right if needed
  {CU} type "text"                types into the focused field
  {CU} key Enter                  presses a key or chord (Tab, Escape, Backspace, ArrowDown, ControlOrMeta+a ...)
  {CU} scroll 400                 mouse wheel (positive scrolls down); add --at X Y to scroll a panel under that point
  {CU} drag X1 Y1 X2 Y2 | move X Y | back | wait SECONDS
  {CU} goto URL                   open one of the app URLs above
Every command prints the path of a new screenshot of the result. Look at it with the Read tool before deciding the next step.
Native dropdown menus and date pickers do not open visibly in screenshots: click the control to focus it, then type the
option's first letters or use ArrowUp/ArrowDown (the closed control shows the chosen value; do not press Enter there, since
inside a form Enter submits it). Type dates as digits. Browser alert/confirm dialogs are accepted for you and their text is
printed with that command's output.
You have no other way to see or change the apps: no page text, no DOM, no scripts, no API, no files beyond your screenshots.
You have at most 30 minutes.
When finished, end with exactly one report:
  {CU} report complete "<what you did>"   or   {CU} report infeasible "<why>"
Then reply with one short paragraph: what you did and which report you made.
"""
if PROMPT_OVERRIDE: prompt = PROMPT_OVERRIDE.replace("WORK", work)
open(os.path.join(priv, "prompt.txt"), "w").write(prompt)
allowed = [f"Bash({CU}:*)", f"Bash(python3 {work}/cu.py:*)", f"Read(/{work}/**)", f"Read(/{work}/shots/**)"]
cmd = ["nice", "-n", "15", "claude", "-p", "--model", MODELS[model], "--permission-mode", "dontAsk", "--output-format", "json",
       "--tools", "Bash,Read", "--allowedTools", *allowed,
       "--disallowedTools", "WebFetch", "WebSearch", "Skill", "Agent", "Write", "Edit", "Glob", "Grep", "NotebookEdit",
       "--disable-slash-commands", "--strict-mcp-config"]
json.dump(cmd, open(os.path.join(priv, "cmd.json"), "w"))
t0 = time.time()
proc = subprocess.Popen(cmd, cwd=work, stdin=subprocess.PIPE, stdout=open(os.path.join(priv, "claude.json"), "w"),
                        stderr=subprocess.STDOUT, start_new_session=True, text=True)
proc.stdin.write(prompt); proc.stdin.close()
print("READY", w.url, w.mail_url, "cu", cport, flush=True)
reported_at = None; down = 0; world_died = None; last_chk = 0
while time.time() - t0 < cap and not os.path.exists(os.path.join(priv, "STOP")):
    if time.time() - last_chk > 10:  # watchdog: something outside the probe killing the world makes the attempt invalid
        last_chk = time.time()
        alive = World._ok(w.api + "/health") and World._ok(w.url + "/app") and (not uses_mail or World._ok(w.mail_url + "/health"))
        down = 0 if alive else down + 1
        if down >= 3: world_died = round((time.time() - t0) / 60, 1); break
    if os.path.exists(rp) and reported_at is None: reported_at = time.time()
    if reported_at and time.time() - reported_at > 15: break
    if proc.poll() is not None: time.sleep(3); break
    time.sleep(2)
elapsed = time.time() - t0
time.sleep(1); final, rep = w.final(), w.report()
score, why = t["verify"](w.seed, final, rep)
if world_died is None and not (World._ok(w.api + "/health") and World._ok(w.url + "/app")): world_died = round(elapsed / 60, 1)
for pr in (proc, cu):
    if pr.poll() is None:
        _sig_group(pr.pid, signal.SIGTERM); time.sleep(3); _sig_group(pr.pid, signal.SIGKILL)
w.stop()
acts = [json.loads(l) for l in open(os.path.join(priv, "actions.jsonl"))] if os.path.exists(os.path.join(priv, "actions.jsonl")) else []
kinds = {}
for a in acts: kinds[a["argv"][0] if a["argv"] else "?"] = kinds.get(a["argv"][0] if a["argv"] else "?", 0) + 1
res = {"task": tid, "attempt": att, "model": model, "score": score, "why": why[:12], "report": rep,
       "mins_to_report": round((os.path.getmtime(rp) - t0) / 60, 1) if os.path.exists(rp) else None,
       "mins_total": round(elapsed / 60, 1), "capped": elapsed >= cap - 5 and not os.path.exists(rp),
       "actions": len(acts), "action_kinds": kinds, "world_died_at_min": world_died, "valid": world_died is None}
try:
    j = json.load(open(os.path.join(priv, "claude.json")))
    res.update(session_id=j.get("session_id"), cost=j.get("total_cost_usd"), num_turns=j.get("num_turns"),
               models_used=sorted((j.get("modelUsage") or {}).keys()), denials=len(j.get("permission_denials") or []))
except Exception as e: res["claude_json_error"] = str(e)
json.dump({**res, "final": final}, open(os.path.join(priv, "result.json"), "w"), indent=1)
print(json.dumps(res), flush=True)
