# Clone-ticket rehearsal evidence (Nov 14)

Why the merge and checker rules in `../SKILL.md` are what they are.

## Own-file layout plus immediate merge (recorded clone, 10 tickets, 2 workers at a time, checker before every merge)

- With the own-file layout, 46 of 47 conflict hunks resolved by the perl line, 1 hand fix (two tickets replacing adjacent drawer rows), about 1 minute of merging for all 10, build green at every step, 28/28 hidden journeys, no regressions.
- Without it, merging each branch at DONE and rebasing the in-flight one also reached 28/28, but 3 of 5 rebases needed hand edits on the same line (the context's one-line return list, the drawer's shared picker), merges queued behind checkers, and conflicts grow with every extra worker in flight. Use that only for a ticket that cannot follow the layout.
- A `merge=union` gitattribute was tried and rejected: it also keeps both sides of real edits (it duplicated a drawer row).

## Runtime contention, not git (Flowboard, 11 tickets, 4 workers)

Zero merge conflicts; two tickets editing the same component (Sidebar) auto-merged because the hunks were apart. The real contention was runtime: workers killing each other's dev servers with `pkill -f dev.mjs`, and a shared seed race. The worker prompt's shared-machine rules exist for that.

## DONE is a claim

A worker labeled an option "8 pts" when the ticket said "8"; its own smoke check found the control by a looser selector, and it reported DONE while the grader failed it. Hence the independent acceptance checker that sees only the ticket and locates controls by the ticket's exact words.

## Reuse the app's components

The only Round 1 grader failure was a rebuilt page whose stat tiles used fresh markup instead of the codebase's card component, so a grader selecting by that component class found nothing.

## Smoke check snippet (Playwright, headless)

Python Playwright is importable globally on this Mac (prep.md), so it works from any directory. A Node script in `/tmp` cannot `import 'playwright'` (ESM resolves from the script's folder, not the repo), so for Node put the script in an ignored path inside the worktree or use the repo's own e2e setup.

```bash
cat > /tmp/claude-501/smoke-<ID>.py <<'PY'
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path="<headless shell path from DISCOVERY.md>")
    p = b.new_page(viewport={"width": 1440, "height": 900})
    p.goto("http://127.0.0.1:<port>/<path>")
    p.get_by_role("button", name="<ticket label>", exact=True).click()
    print("PASS" if p.get_by_text("<expected text>", exact=True).count() == 1 else "FAIL", "<criterion>")
    p.screenshot(path="/tmp/claude-501/smoke-<ID>.png"); b.close()
PY
nice -n 15 python3 /tmp/claude-501/smoke-<ID>.py
```
