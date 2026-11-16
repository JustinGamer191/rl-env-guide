"""Screenshot-only computer-use tool, to probe a task the way a pixel-only agent harness sees it.
One persistent Playwright browser per attempt, held by a tiny local server; the solver drives it only through this CLI.
The solver never gets DOM text: every action returns the path of a fresh PNG screenshot, which it views with its Read tool.

Server (started by the probe runner, not the solver):
  python3 cu_screen.py serve --port P --shots DIR --log ACTIONS.jsonl --start URL [--allow http://127.0.0.1:6400 ...]
       [--chrome PATH] [--width 1280 --height 800] [--report-file report.json]
Client (the solver; reads the port from cu.json next to this file, or CU_PORT):
  cu.py screenshot                 save a PNG of the viewport, print its path
  cu.py click X Y [--double|--right]
  cu.py move X Y | drag X1 Y1 X2 Y2
  cu.py type "text"                type into whatever has focus
  cu.py key Enter                  one key or chord (Tab, Escape, ArrowDown, ControlOrMeta+a, Shift+Tab ...)
  cu.py scroll DY [DX] [--at X Y]  mouse wheel at a point (default: viewport center); positive DY scrolls down
  cu.py goto URL                   only the allowed app origins, never /api paths or file:// URLs
  cu.py back | wait SECONDS
  cu.py report complete|infeasible "message"
Every action but report prints a screenshot path. The server logs each action (time, args) for counting and audit.
Fairness notes: coordinates are viewport CSS pixels at device scale 1, so screenshot pixel (x, y) is click (x, y).
Native <select> popups and date pickers are not drawn in headless screenshots; focus them by click and use keys.
alert/confirm/prompt dialogs are accepted automatically (a human would click OK) and their text is printed with the action's output."""
import json, os, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def client(argv):
    port = os.environ.get("CU_PORT") or json.load(open(os.path.join(HERE, "cu.json")))["port"]
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__.split("Client")[1].split("Every action")[0]); return 0
    req = urllib.request.Request(f"http://127.0.0.1:{port}/act", data=json.dumps({"argv": argv}).encode(), method="POST",
                                 headers={"content-type": "application/json"})
    try: r = json.load(urllib.request.urlopen(req, timeout=120))
    except Exception as e: print("cu error:", e); return 1
    print(r.get("out", "")); return 0 if r.get("ok") else 1


def serve(args):
    import argparse
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from playwright.sync_api import sync_playwright
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, required=True); ap.add_argument("--shots", required=True); ap.add_argument("--log", required=True)
    ap.add_argument("--start", required=True); ap.add_argument("--allow", nargs="*", default=[]); ap.add_argument("--chrome")
    ap.add_argument("--width", type=int, default=1280); ap.add_argument("--height", type=int, default=800)
    ap.add_argument("--report-file"); ap.add_argument("--settle", type=float, default=0.7)
    a = ap.parse_args(args)
    os.makedirs(a.shots, exist_ok=True)
    allow = [x.rstrip("/") for x in (a.allow or [a.start])]
    pw = sync_playwright().start()
    browser = pw.chromium.launch(**({"executable_path": a.chrome} if a.chrome else {}))
    ctx = browser.new_context(viewport={"width": a.width, "height": a.height}, device_scale_factor=1)
    state = {"page": ctx.new_page(), "n": 0}
    state["dialogs"] = []
    def on_dialog(d):  # headless screenshots cannot show alert/confirm/prompt; accept it (a human clicks OK) and say so
        state["dialogs"].append(f"[browser {d.type} dialog: {d.message!r} -> clicked OK]")
        try: d.accept()
        except Exception: pass
    def on_page(p):
        p.on("dialog", on_dialog); state["page"] = p  # a new tab becomes the current page, as a human would see it
    ctx.on("page", on_page)
    state["page"].on("dialog", on_dialog)
    state["page"].goto(a.start)
    logf = open(a.log, "a")

    def shot():
        time.sleep(a.settle)
        state["n"] += 1
        path = os.path.join(a.shots, f"{state['n']:04d}.png")
        try: state["page"].screenshot(path=path, timeout=15000)
        except Exception as e: return f"screenshot failed: {e}"
        return path

    def allowed(url):
        u = urllib.parse.urlparse(url)
        origin = f"{u.scheme}://{u.netloc}"
        return u.scheme in ("http", "https") and origin in allow and "/api" not in u.path

    def act(argv):
        cmd, rest = argv[0], argv[1:]
        p = state["page"]; m = p.mouse; k = p.keyboard
        num = lambda i: float(rest[i])
        if cmd == "screenshot": return True, shot()
        if cmd == "click":
            btn = "right" if "--right" in rest else "left"
            m.click(num(0), num(1), button=btn, click_count=2 if "--double" in rest else 1)
            return True, shot()
        if cmd == "move": m.move(num(0), num(1)); return True, shot()
        if cmd == "drag":
            m.move(num(0), num(1)); m.down(); m.move(num(2), num(3), steps=12); m.up(); return True, shot()
        if cmd == "type": k.type(" ".join(rest), delay=15); return True, shot()
        if cmd == "key": k.press(rest[0]); return True, shot()
        if cmd == "scroll":
            at = rest.index("--at") if "--at" in rest else None
            x, y = (float(rest[at + 1]), float(rest[at + 2])) if at is not None else (a.width / 2, a.height / 2)
            nums = [float(v) for v in (rest[:at] if at is not None else rest)]
            dy = nums[0] if nums else 400; dx = nums[1] if len(nums) > 1 else 0
            m.move(x, y); m.wheel(dx, dy); return True, shot()
        if cmd == "goto":
            if not rest or not allowed(rest[0]): return False, f"goto refused: only {', '.join(allow)} (no /api paths)"
            p.goto(rest[0]); return True, shot()
        if cmd == "back": p.go_back(); return True, shot()
        if cmd == "wait": time.sleep(min(10.0, num(0))); return True, shot()
        if cmd == "report":
            if not a.report_file or not rest or rest[0] not in ("complete", "infeasible"): return False, 'usage: report complete|infeasible "message"'
            json.dump({"status": rest[0], "text": " ".join(rest[1:])}, open(a.report_file, "w")); return True, "reported " + rest[0]
        return False, f"unknown command {cmd!r}; run with --help"

    class H(BaseHTTPRequestHandler):
        def log_message(self, *x): pass
        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))) or b"{}")
            argv = [str(x) for x in body.get("argv", [])]
            t = time.time()
            try: ok, out = act(argv) if argv else (False, "no command")
            except Exception as e: ok, out = False, f"{type(e).__name__}: {str(e).splitlines()[0][:300]}"
            if state["dialogs"]: out = "\n".join(state["dialogs"] + [out]); state["dialogs"].clear()
            logf.write(json.dumps({"t": round(t, 2), "argv": argv, "ok": ok, "out": out[:200]}) + "\n"); logf.flush()
            data = json.dumps({"ok": ok, "out": out}).encode()
            self.send_response(200); self.send_header("content-type", "application/json"); self.send_header("content-length", str(len(data)))
            self.end_headers(); self.wfile.write(data)

    srv = HTTPServer(("127.0.0.1", a.port), H)  # single-threaded: Playwright's sync API stays on this thread
    print("CU_READY", a.port, flush=True)
    try: srv.serve_forever()
    finally:
        for f in (ctx.close, browser.close, pw.stop):
            try: f()
            except Exception: pass


if __name__ == "__main__":
    if sys.argv[1:2] == ["serve"]: serve(sys.argv[2:])
    else: sys.exit(client(sys.argv[1:]))
