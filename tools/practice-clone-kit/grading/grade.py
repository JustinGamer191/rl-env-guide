#!/usr/bin/env python3
"""Run hidden journeys against the original or a clone checkout. Fresh backend per journey.

  python3 grade.py original [--only a,b]
  python3 grade.py clone --dir <clone dir> --port 5660 [--only a,b] [--json out.json]
"""
import argparse, glob, json, os, signal, subprocess, sys, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from journeys import JOURNEYS  # noqa: E402

CLOCK = '2026-09-15T14:00:00Z'


def exe():
    hits = sorted(glob.glob(os.path.expanduser('~/Library/Caches/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell')))
    return hits[-1]


def wait_http(url, secs=90):
    t = time.time()
    while time.time() - t < secs:
        try:
            urllib.request.urlopen(url, timeout=2); return True
        except Exception:
            time.sleep(0.4)
    return False


def kill_ports(*ports):
    for p in ports:
        subprocess.run(f'lsof -ti tcp:{p} | xargs kill 2>/dev/null', shell=True)


class Original:
    base = 'http://localhost:5750'
    def start(self): subprocess.run([str(HERE.parent / 'run-original.sh')], check=True, capture_output=True)
    def reset(self): subprocess.run([str(HERE.parent / 'run-original.sh'), 'server'], check=True)
    def stop(self): subprocess.run([str(HERE.parent / 'run-original.sh'), 'stop'])


class Clone:
    def __init__(self, d, port):
        self.d, self.port, self.proc = d, port, None
        self.base = f'http://127.0.0.1:{port}'
    def start(self):
        kill_ports(self.port, self.port + 1)
        env = dict(os.environ, PORT=str(self.port), BACKEND_PORT=str(self.port + 1), CLOCK_FIXED_TIME=CLOCK)
        self.log = open(f'/tmp/grade-clone-{self.port}.log', 'w') if False else open(os.devnull, 'w')
        self.proc = subprocess.Popen(['nice', '-n', '15', 'bun', 'dev.mjs'], cwd=self.d, env=env, stdout=self.log, stderr=self.log, start_new_session=True)
        ok = wait_http(self.base + '/', 60) and wait_http(self.base + '/app', 30)
        if not ok and not getattr(self, '_retry', False):
            self._retry = True; self.stop(); ok = self.start(); self._retry = False
        time.sleep(1.5)
        return ok
    def reset(self):
        self.stop(); self.start()
    def stop(self):
        if self.proc:
            try: os.killpg(self.proc.pid, signal.SIGTERM)
            except Exception: pass
            self.proc.wait(timeout=10)
        kill_ports(self.port, self.port + 1)
        for _ in range(40):
            busy = subprocess.run(f'lsof -ti tcp:{self.port} -ti tcp:{self.port + 1}', shell=True, capture_output=True, text=True).stdout.strip()
            if not busy:
                break
            time.sleep(0.25)


def run(target, only=None):
    results = []
    (HERE / 'fails').mkdir(exist_ok=True)
    target.start()
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe())
        for name, fn in JOURNEYS:
            if only and name not in only:
                continue
            target.reset()
            ctx = b.new_context(viewport={'width': 1440, 'height': 900}); ctx.clock.install(time=CLOCK)
            page = ctx.new_page(); page.set_default_timeout(8000)
            t = time.time()
            try:
                fn(page, target.base); ok, err = True, ''
            except Exception as e:
                ok, err = False, (str(e).strip().splitlines() or [''])[0][:300]
                try: page.screenshot(path=str(HERE / 'fails' / f'{type(target).__name__}-{name}.png'))
                except Exception: pass
            ctx.close()
            results.append({'journey': name, 'pass': ok, 'error': err, 'secs': round(time.time() - t, 1)})
            print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else '  :: ' + err), flush=True)
        b.close()
    target.stop()
    return results


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('target', choices=['original', 'clone'])
    ap.add_argument('--dir'); ap.add_argument('--port', type=int, default=5760)
    ap.add_argument('--only'); ap.add_argument('--json')
    a = ap.parse_args()
    t = Original() if a.target == 'original' else Clone(a.dir, a.port)
    res = run(t, set(a.only.split(',')) if a.only else None)
    print(f"{sum(r['pass'] for r in res)}/{len(res)} passed")
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1))
