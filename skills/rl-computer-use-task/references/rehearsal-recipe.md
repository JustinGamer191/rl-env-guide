# CU task recipe, tested end to end (rehearsal Nov 14 2026)

Rehearsed on a generated app clone (Quillstack, a Linear-like tracker: `bun dev.mjs`, fresh SQLite per boot, `window.__app`). Five tasks (property-targeted edit, near-twin trap, read-then-act create, infeasible, multi-record end state), 35 adversarial runs (all 0), oracle 3x plus an alternate UI path per task (all 1), 55 resets with one identical normalized seed, and 2 real Opus solver agents per task plus 2 Haiku probes. The working harness is in `../examples/quillstack-harness/` (copy it, change the snapshot mapping and the task file).

## 1. Reset = fresh boot, seed captured live

- Generated clones often boot with a fresh temp DB per `dev.mjs` run, so reset is "kill the process group, boot again" (about 1 s here). Start with `start_new_session=True` and kill with `os.killpg`, or Vite and the backend outlive the parent.
- Snapshot the seed from the DB right after each boot instead of trusting a stored file: ids are random cuids per boot and seed timestamps drift by milliseconds when the clock "flows forward" from `CLOCK_FIXED_TIME`.
- Chromium refuses some ports (6000, 6665-6669, 6697 are "unsafe"). Pick others.

## 2. Verifier = whole-state snapshot diff (expected = seed + intended change)

1. **Normalize the domain to stable keys**: issue number, project key, label name, user email, cycle number instead of ids; datetimes to UTC dates; lists sorted. Drop `updatedAt` and derived logs (activity, notifications) that viewing or harmless UI use can touch.
2. `expected = deepcopy(seed)`, apply exactly the intended change, then `diff(expected, final)` must be empty. Collateral damage, wrong entity, change-everything and partial all fall out of one diff with a readable reason ("/issues/12/assignee: null -> guest").
3. **Free-form additions** (a new record, a comment's text): find them in final, validate the required fields with normalization (case-fold, punctuation stripped, whitespace collapsed), copy the valid one into expected so its free fields (description, timestamps) do not count as diffs.
4. **Fail closed.** In the rehearsal the first verifiers scored 1 for "report complete, do nothing" on two of five tasks: when the new comment or new issue was absent, nothing was copied into expected, expected equaled seed equaled final, and the diff was empty. Every intended change must be an explicit REQUIRED assertion, not "accept if present". The null agent did not catch it, because null failed only on the missing report; answer-only and partial caught it.
5. Report check: `report_complete` for feasible tasks, `report_infeasible` for infeasible ones. The report status is required, its text is never evidence.
6. **Assert the seed preconditions inside the verifier** (target unique, trap twin still present, infeasible task still infeasible). If an integrator changes the shared seed, the verifier crashes loudly instead of silently grading a different task.

## 3. Agents

- **Oracle and alt path drive the UI** (Playwright). The alt path changes the entry point (List row vs Board card vs Cmd+K search vs the `c` shortcut), the order of edits, and the text format ("downgraded - customer deadline moved." vs "Downgraded: customer deadline moved"). For an infeasible task the alt path opens every candidate and then refuses, which proves viewing has no side effects.
- **Adversaries call the REST API directly.** They test the verifier, not the UI, so they take 1 s each and can do things the UI cannot (replace a label list, spam comments).
- Adversary set that found real bugs: null, answer-only (report complete, no action), change-everything, wrong twin, partial (one of N records, or one of N fields), replaced-instead-of-added (label list overwritten), duplicate (same comment twice), edit-an-existing-record-instead-of-creating, oracle plus one unrelated change. For infeasible tasks add: act on the near miss then report complete, make it feasible (add the missing label) then act, act partly then report infeasible.
- Each adversary's 0 must come from a STATE reason, not only from the missing report; read the `why` column.

## 4. Real-solver difficulty probe

- Boot a dedicated world per attempt (own port pair), give a fresh subagent only: the goal text, the URL, how to launch Playwright, a `report.py complete|infeasible "msg"` command, a work dir, and rules (UI actions only: no `page.evaluate`, no `window.__app`, no direct API calls, no files outside the work dir). Keep `dev.log` (it prints the DB path) and the seed snapshot out of that work dir.
- After it stops, touch a STOP file; the runner verifies and tears down. Audit the transcript JSONL (`audit.py transcript work_dir`) for `evaluate(`, `__app`, `/api/`, curl/fetch, sqlite, and paths outside the work dir.
- Interpretation: 0/2 means read the failure: a wrong-twin or partial failure is the intended difficulty; a misread of the goal means the goal is ambiguous and must be rewritten.
- Rehearsal result: Opus solved 10/10 (95 to 217 s each, no isolation breach; two benign flags, a dead-code `evaluate` and a scroll via `evaluate`). Haiku solved the infeasible task (772 s) but failed the multi-record task: it moved all three issues and never set an assignee, then reported complete. The verifier caught the false claim, the same failure published clone benchmarks report (84% of failed rounds claimed success).
- **Difficulty is the open risk, not verifier quality.** Our five tasks had 2 to 6 atomic checks; a published accounts-payable benchmark calls 8 or fewer "easy", 9 to 19 "medium", 20+ "hard", and their best agents score 36 to 59%. If difficulty matters: chain more records (one rule over 6 to 10 items), add a derived metric trap ("lowest monthly payment, not lowest price"), span two apps, or hide the deciding fact on a page the agent must open (cycle membership was visible only in the issue drawer, which is what slowed Haiku).

Solver prompt used (fill the brackets; nothing else from the task goes in):

```
You are a computer-use agent operating a web app (<kind>) through a browser. Complete the task below.
TASK:
<goal text>
APP URL: <url> (already running; you are the signed-in user "<name>")
How you operate the browser: write and run Python Playwright scripts (sync API). Launch Chromium with
  p.chromium.launch(executable_path="<headless shell path>") and a 1440x900 viewport. Each script starts a fresh
browser, but app data persists between scripts. Run scripts with `nice -n 15 python3 ...`. Look with page.screenshot
(view the PNG with Read) and page.inner_text / locators. Act only like a human user: click, type, press keys, select options.
Rules (you will be audited):
- Work only inside <work dir>. Do not read, list or search any other files or directories.
- No page.evaluate or other JavaScript to read or change app state, no window globals, no direct HTTP API calls,
  no local storage or databases. Only the UI.
- Do not start or stop any servers. Close every browser you open.
When finished, end with exactly one report:
  python3 <run dir>/report.py complete "<what you did>"   or   python3 <run dir>/report.py infeasible "<why>"
Then reply with one short paragraph: what you did and which report you made.
```

## 5. Leaks found

- **Vite dev server serves the app root over `/@fs/`**: `http://host:port/@fs/<app>/backend/prisma/seed-data.json` returned 200 from the browser. Keep goal answers, verifiers and expected values outside the app directory (a sibling dir returned 403) and check with curl before submitting.
- `window.__app.getState()` exposes everything the store holds to an agent that can run JS. Fine for a screenshot-and-click harness, but never put expected values or verifier hints into app state.
- The clone's own `dev.log` names the DB file; an agent with a shell can read the DB directly. For our probe this is a rule plus a transcript audit; for a hosted grader it is the harness's job.

## 6. Environment gotchas (this Mac)

- Python Playwright wanted `chromium_headless_shell-1223` but `~/Library/Caches/ms-playwright` had `-1243`; pass `executable_path=` to the installed headless shell instead of downloading.
- `bun` is a shell function wrapper here; call `~/.bun/bin/bun` from scripts.
- In the clone, the left nav is also an `<aside>`; scope drawer selectors (`aside.drawer-in`). Picker options contain avatar initials, so match the label span (`span:text-is('You')`), not the whole button text.

## Dry-run notes (Nov 15, Tidewell POS + Quillmail world)

A full CU task (cu-1, 14 checks, supplier emails with corrections and a look-alike product) passed the checklist: oracle 1.0 x3, alt path and API path 1.0, null, answer-only, change-everything, wrong-entity, partial, collateral and six extra traps all 0 for state reasons. Friction to avoid next time:
- examples/hard World is Quillstack-specific (slot ports 6100+10*slot, /health and /app readiness URLs). For another app, pass explicit ports and that app's real readiness checks (e.g. a seed line in dev.log, an API route, the login page).
- Quillmail's server.mjs joins MAIL_SEED to its own root, so pass a path relative to world/quillmail, not an absolute one.
- Reuse the small core of examples/hard/tasks.py (plan, expected = seed + plan, full diff, apply via API, the adversary table), not the whole 900-line file.
- Keep report.py at the task root; the probe copies it into each run dir.
- Normalize clone-specific viewing side effects: edit forms that save null as "", opening a mail setting `read`. Add "open the edit form and save without changes" as an alt-path check that must score 1.
- The world's own seed file can be reachable over Vite's /@fs (200). That is a world leak, not a task leak; keep answers out of it.
- The harness blocks `sleep N; cmd` chains; wait with Monitor or until-loops.
