#!/usr/bin/env python3
"""Record a running web app the way Frist's pipeline does: per-step screenshot,
DOM snapshot, API traffic (HAR + simplified JSON) and the action taken.

The output bundle (recordings/) is the ONLY thing a generator agent may see.

Usage:
  python3 record.py                      # record every journey in journeys_spec.py
  python3 record.py --only 03-open-issue # record one journey
  python3 record.py --probe /app/board   # dump visible buttons/inputs for a URL (authoring help)

Reusing for another app: edit CONFIG below and journeys_spec.py. Each journey
starts from a fresh backend (CONFIG['reset_cmd']) with the browser clock frozen
at CONFIG['clock'] (time still flows from there).
"""
import argparse, glob, json, os, re, shutil, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
CONFIG = {
    'base': 'http://localhost:5750',
    'api_prefix': '/api/',
    'reset_cmd': [str(HERE / 'run-original.sh'), 'server'],
    'clock': '2026-09-15T14:00:00Z',
    'viewport': {'width': 1440, 'height': 900},
    'out': HERE / 'recordings',
    # host strings rewritten in everything the generator sees
    'redact': {'localhost:5750': 'app.local', 'localhost:5751': 'app.local', '127.0.0.1:5750': 'app.local'},
}


def chromium_exe():
    hits = sorted(glob.glob(os.path.expanduser('~/Library/Caches/ms-playwright/chromium_headless_shell-*/*/chrome-headless-shell')))
    return hits[-1] if hits else None


def redact(text):
    for a, b in CONFIG['redact'].items():
        text = text.replace(a, b)
    return text


def clean_dom(html):
    # keep markup and inline styles; drop scripts (the generator never sees app JS)
    html = re.sub(r'<script\b[^>]*>.*?</script>', '', html, flags=re.S | re.I)
    html = re.sub(r'<link\b[^>]*modulepreload[^>]*>', '', html, flags=re.I)
    return redact(html)


class Recorder:
    def __init__(self, page, outdir):
        self.page, self.out, self.steps, self.api, self.n = page, outdir, [], [], 0
        page.on('response', self.on_response)

    def on_response(self, resp):
        url = resp.url
        if CONFIG['api_prefix'] not in url:
            return
        req = resp.request
        try:
            body = resp.json()
        except Exception:
            try:
                body = resp.text()[:4000]
            except Exception:
                body = None
        try:
            post = req.post_data_json
        except Exception:
            post = req.post_data
        self.api.append({'step': self.n, 'method': req.method, 'url': redact(url), 'status': resp.status,
                         'request_body': post, 'response_body': body})

    def snap(self, action, note=''):
        self.page.wait_for_timeout(700)
        self.n += 1
        tag = f'step-{self.n:02d}'
        self.page.screenshot(path=str(self.out / f'{tag}.png'))
        (self.out / f'{tag}-snapshot.html').write_text(clean_dom(self.page.content()))
        self.steps.append({'step': self.n, 'action': action, 'note': note, 'url': redact(self.page.url),
                           'title': self.page.title(), 'screenshot': f'{tag}.png', 'snapshot': f'{tag}-snapshot.html'})


def target(page, sel):
    """sel forms: 'text=Foo', 'role=button:Foo', 'placeholder=Foo', 'label=Foo', 'testid=x', or CSS."""
    if sel.startswith('role='):
        role, _, name = sel[5:].partition(':')
        return (page.get_by_role(role, name=name, exact=True) if name else page.get_by_role(role)).locator('visible=true').first
    if sel.startswith('placeholder='):
        return page.get_by_placeholder(sel[12:]).first
    if sel.startswith('label='):
        return page.get_by_label(sel[6:]).first
    if sel.startswith('text='):
        return page.get_by_text(sel[5:], exact=True).locator('visible=true').first
    if sel.startswith('testid='):
        return page.get_by_test_id(sel[7:]).first
    return page.locator(sel).first


def run_step(page, rec, step):
    kind = step[0]
    note = step[-1] if isinstance(step[-1], str) and step[-1].startswith('#') else ''
    if kind == 'goto':
        page.goto(CONFIG['base'] + step[1]); page.wait_for_load_state('networkidle')
        desc = f'navigate to {step[1]}'
    elif kind == 'click':
        target(page, step[1]).click(); desc = f'click {step[1]}'
    elif kind == 'fill':
        target(page, step[1]).fill(step[2]); desc = f'type "{step[2]}" into {step[1]}'
    elif kind == 'press':
        page.keyboard.press(step[1]); desc = f'press {step[1]}'
    elif kind == 'select':
        target(page, step[1]).select_option(label=step[2]); desc = f'select "{step[2]}" in {step[1]}'
    elif kind == 'hover':
        target(page, step[1]).hover(); desc = f'hover {step[1]}'
    elif kind == 'scroll':
        page.mouse.wheel(0, step[1]); desc = f'scroll {step[1]}px'
    elif kind == 'drag':
        src, dst = target(page, step[1]), target(page, step[2])
        src.drag_to(dst); desc = f'drag {step[1]} onto {step[2]}'
    elif kind == 'wait':
        page.wait_for_timeout(step[1]); desc = f'wait {step[1]}ms'
    else:
        raise ValueError(kind)
    rec.snap(desc, note.lstrip('# '))


def record(only=None):
    sys.path.insert(0, str(HERE))
    from journeys_spec import JOURNEYS
    out = CONFIG['out']
    out.mkdir(exist_ok=True)
    index = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_exe())
        for name, steps in JOURNEYS:
            if only and name != only:
                continue
            jdir = out / 'journeys' / name
            shutil.rmtree(jdir, ignore_errors=True); jdir.mkdir(parents=True)
            subprocess.run(CONFIG['reset_cmd'], check=True)
            ctx = browser.new_context(viewport=CONFIG['viewport'], record_har_path=str(jdir / 'network.har'),
                                      record_har_url_filter=re.compile(re.escape(CONFIG['api_prefix'])),
                                      record_har_content='embed')
            ctx.clock.install(time=CONFIG['clock'])
            page = ctx.new_page()
            rec = Recorder(page, jdir)
            status = 'ok'
            try:
                for s in steps:
                    run_step(page, rec, s)
            except Exception as e:
                status = f'failed at step {rec.n + 1}: {str(e).splitlines()[0]}'
                rec.snap('error state', status)
            ctx.close()
            (jdir / 'network.har').write_text(redact((jdir / 'network.har').read_text()))
            (jdir / 'steps.json').write_text(json.dumps(rec.steps, indent=1))
            (jdir / 'api.json').write_text(json.dumps(rec.api, indent=1))
            index.append({'journey': name, 'steps': len(rec.steps), 'status': status})
            print(name, status, flush=True)
        browser.close()
    # stylesheet once (an rrweb-style capture would include it)
    css = sorted(glob.glob(str(HERE / 'original/client/dist/assets/*.css')))
    if css:
        (out / 'styles').mkdir(exist_ok=True)
        shutil.copy(css[-1], out / 'styles' / 'captured.css')
    if not only:
        (out / 'index.json').write_text(json.dumps({'clock': CONFIG['clock'], 'viewport': CONFIG['viewport'],
                                                     'journeys': index}, indent=1))


def probe(path):
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=chromium_exe())
        ctx = b.new_context(viewport=CONFIG['viewport']); ctx.clock.install(time=CONFIG['clock'])
        pg = ctx.new_page(); pg.goto(CONFIG['base'] + path); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(800)
        for el in pg.query_selector_all('button, a, input, textarea, select, [role=button]'):
            if el.is_visible():
                print(el.evaluate('e => e.tagName'), repr((el.inner_text() or el.get_attribute('placeholder') or el.get_attribute('title') or el.get_attribute('aria-label') or '')[:60]))
        b.close()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--only'); ap.add_argument('--probe')
    a = ap.parse_args()
    probe(a.probe) if a.probe else record(a.only)
