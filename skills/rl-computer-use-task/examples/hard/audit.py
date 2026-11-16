"""Audit a solver transcript (JSONL): list every tool call compactly and flag isolation breaches.
Usage: audit.py TRANSCRIPT.jsonl ALLOWED_DIR"""
import json, re, sys
path, allowed = sys.argv[1], sys.argv[2]
FLAGS = [r"\.evaluate\(", r"__app", r"/api/", r"\bcurl\b", r"\bfetch\(", r"requests\.", r"urllib", r"sqlite", r"localStorage",
         r"cu-rehearsal/(hard/)?(app|harness|mail|seedgen|runs/private)", r"/var/folders", r"quillstack-clone", r"quillmail-", r"state\.json", r"__mail", r"/api/", r"seed", r"verifier", r"add_init_script", r"route\("]
calls, flags = [], []
for line in open(path):
    try: m = json.loads(line)
    except Exception: continue
    msg = m.get("message") or {}
    for c in msg.get("content", []) if isinstance(msg.get("content"), list) else []:
        if c.get("type") != "tool_use": continue
        inp = c.get("input", {}); name = c.get("name")
        text = json.dumps(inp)
        calls.append(f"{name}: {(inp.get('command') or inp.get('file_path') or inp.get('pattern') or text)[:160]}")
        for f in FLAGS:
            if re.search(f, text, re.I): flags.append(f"{name} matched {f}: {text[:200]}")
        for p in re.findall(r"/(?:private/)?(?:tmp|var|Users)/[^\s\"']+", text):
            if not p.replace("/private", "").startswith(allowed.replace("/private", "")) and "ms-playwright" not in p and "report.py" not in p and p.rstrip("/.") not in ("/tmp", "/private/tmp"):
                flags.append(f"{name} path outside work dir: {p[:160]}")
print(f"{len(calls)} tool calls"); print("\n".join(calls[-60:]) if "-v" in sys.argv else "")
print("FLAGS:" if flags else "FLAGS: none"); print("\n".join(sorted(set(flags))[:40]))
