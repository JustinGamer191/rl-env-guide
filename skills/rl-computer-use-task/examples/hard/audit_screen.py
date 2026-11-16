"""Audit a screenshot-only probe: every tool call must be Bash running cu.py or Read of a PNG under work/shots.
Also counts permission denials (attempts the gate blocked). Usage: audit_screen.py T_aN  (runs/screen layout)"""
import json, os, re, sys
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.realpath(os.path.join(H, "..", "runs", "screen"))
run = sys.argv[1]
res = json.load(open(os.path.join(R, "private", run, "result.json")))
work = os.path.join(R, "solver", run, "work")
slug = re.sub(r"[^A-Za-z0-9]", "-", work)
tr = os.path.expanduser(f"~/.claude/projects/{slug}/{res['session_id']}.jsonl")
ok_bash = re.compile(r"^\s*python3 (\S*/)?cu\.py( |$)")
calls, bad, denied = 0, [], 0
for line in open(tr):
    try: m = json.loads(line)
    except Exception: continue
    content = (m.get("message") or {}).get("content")
    if not isinstance(content, list): continue
    for c in content:
        if c.get("type") == "tool_result" and "permission" in json.dumps(c.get("content", "")).lower() and c.get("is_error"): denied += 1
        if c.get("type") != "tool_use": continue
        calls += 1; inp = c.get("input", {}); name = c.get("name")
        if name == "Bash":
            cmd = re.sub(r'"(?:[^"\\]|\\.)*"', '""', inp.get("command", "").strip())  # quoted text (report messages) cannot hide commands from the split
            parts = re.split(r"\s*(?:&&|;|\|\||\n)\s*", cmd)
            if not all(ok_bash.match(p) or p.rstrip("/") in ("cd " + work, "cd .") for p in parts if p): bad.append(f"Bash: {inp.get('command','')[:200]}")
        elif name == "Read":
            fp = os.path.realpath(inp.get("file_path", ""))
            if not (fp.startswith(os.path.join(work, "shots")) and fp.endswith(".png")): bad.append(f"Read: {fp}")
        else: bad.append(f"{name}: {json.dumps(inp)[:200]}")
print(f"{run}: {calls} tool calls, {denied} denied by the gate, {len(bad)} non-cu calls")
for b in bad[:30]: print("  ", b)
