---
name: frist-clone-tickets
description: Fastest reliable loop for finishing the tickets on a Frist app clone (10 pts per ticket, 100 pts when the whole clone is complete) using parallel subagent workers in git worktrees. Use this whenever the Frist hackathon is underway and there is a clone repo with tickets, issues, TODOs or a feature checklist to finish, when Justin says "do the tickets", "finish the clone", "what tickets are left", or names a ticket ID, and before declaring any clone done. Works for any stack because it starts by discovering the repo's conventions.
---

# Frist clone tickets

Goal: every ticket on the clone done, nothing that worked before broken, clone accepted as 100% as early as possible (target 13:00). A finished clone is worth 100 points and is the gate to 500-point coding tasks, but a ticket that breaks another feature can cost the whole clone.

The main session orchestrates (frist-hackathon-playbook); workers implement; a separate checker verifies each ticket before merge. Rehearsal evidence behind every rule here: `references/rehearsal-evidence.md`. Frist's published clone conventions and the generator bugs to expect: `references/frist-clone-conventions.md` (read it during discovery).

## 1. Discover (orchestrator, 10 to 15 minutes, once per clone)

Clone into `~/Hackathons-local/frist/<repo>` (never `~/Documents` or `~/Desktop`). If the clone has no `.git`, `git init && git add -A && git commit -qm base` first. If git complains about the Xcode license, prefix `DEVELOPER_DIR=/Library/Developer/CommandLineTools`.

Do not guess the stack. Read README and docs, the ticket source (file, `gh issue list`, portal, `TODO(TICKET-` comments), manifests, CI config, tests, docker compose, seed scripts. Then actually install, start the app, run the full suite, lint and build. Record in `~/Hackathons-local/frist/DISCOVERY.md`:
- Exact commands: install, dev server (and ports, and the env vars that change them), test (whole suite and one test), lint, typecheck, build.
- Baseline: which tests pass, which fail, which fail because their ticket is unfinished. That list is the progress meter.
- Tickets: ID, title, acceptance criteria, how "done" is judged (tests, checklist, staff demo).
- Shared hot files: lockfiles, migrations, route tables, schema, nav, the domain context (`BookingContext`, `WorkspaceContext`, ...), `useWindowAPIs`, the backend route file, the big shared component.
- Worktree bootstrap: the one command that makes a fresh worktree runnable (`cp -cR <main>/node_modules <wt>/` is an instant APFS clone; never a networked install per worker). Confirm with `git check-ignore -v node_modules` that it is ignored even as a symlink (`node_modules/` with a slash does NOT match a symlink, so `git add -A` would commit it; add a bare `node_modules` line).
- Offline browser tooling: which Playwright (Python or Node) imports and which Chromium binary it launches (`npx playwright` downloads and fails offline). Write the working launch line.
- Env quirks (seed races, slow first load, overlays that eat clicks).

If install or the baseline fails for reasons unrelated to tickets, fix that first in one worker, merge, then fan out.

## 2. Triage (orchestrator)

On BOARD.md per ticket: size (S under 15 min, M under 45, L more), likely files, dependencies, hot-file flag. Order: tickets others depend on, then S, then M, then L. Group tickets that edit the same component into one worker. A ticket needing a migration or new dependency goes to one serialized integrator worker. Apply the generator-bug fix order from `references/frist-clone-conventions.md` (blocking modal first).

## 3. Dispatch (orchestrator)

Launch 3 to 5 workers at once (playbook "Machine limits": load under 12, `nice -n 15`, drop to 2 if load climbs), one ticket or same-file group each, with the worker prompt below. `isolation: "worktree"` only works when the session's cwd is the clone repo; otherwise create worktrees yourself (`git worktree add ../wt/<ID> -b <ID>` from the repo, so they land in `~/Hackathons-local/frist/wt/`), run the bootstrap command, and put the absolute path in the prompt. Each worker gets its own port pair (3101/3102, 3111/3112, ...).

**Own-file layout.** Paste this block into every worker prompt where marked, with the repo's real file names filled in:
```
Merge rules (other workers edit the same shared files in parallel; follow exactly):
- New state, effects and actions go in a NEW file src/actions/<ID>.ts exporting one hook use<ID>(core) that takes what it needs (updateX, setX, toast, record, ...) as its argument.
- In <context file> add exactly two lines: one import after the last import, and `...use<ID>({ ... }),` as the LAST entry of the returned object. Change nothing else there; if an existing action must behave differently, do it in your own file.
- In <window-API file> add at most one line at the end of `actions` and one at the end of getState().
- New backend routes go in a NEW file backend/routes/<ID>.mjs exporting `register(route, deps)`; in <server file> add one import line and one call line right after the last route(...) call. Schema: only new lines, or a new model at the end.
- New UI goes in a NEW component file; in the existing component add only its import and render it in place of the dead control.
```
Every merge still conflicts textually (everyone appends at the same spot), but the hunks are insert/insert with an empty base, which the perl line in section 4 resolves. Never use a `merge=union` gitattribute.

## 4. Check, then merge at once (orchestrator)

A worker's DONE is a claim, not evidence. For each DONE:
1. **Acceptance checker.** Launch a fresh checker subagent (prompt below) that gets only the ticket text, the branch or worktree path and a port pair: never the worker's report or diff. Run checkers one browser at a time. Any FAIL goes back to the worker with the checker's output.
2. **Quick diff review** on PASS: scope creep, deleted or skipped tests, unexplained snapshot changes, files outside the own-file layout.
3. **Merge right away** (never batch; new workers then branch from a main that has their neighbours' labels), from the main checkout:
   ```bash
   if ! git -c merge.conflictStyle=diff3 merge --no-edit <branch>; then
     F=$(git diff --name-only --diff-filter=U)
     perl -0pi -e 's/^<<<<<<< [^\n]*\n((?:(?!^[<|=>]{7}).)*?)^\|{7} [^\n]*\n=======\n((?:(?!^[<|=>]{7}).)*?)^>>>>>>> [^\n]*\n/$1$2/gms' $F
     if grep -n '^<<<<<<< \|^>>>>>>> ' $F; then echo "REAL CONFLICT: fix by hand, typecheck, git add, commit"
     else git add $F && git commit -q --no-edit; fi
   fi
   ```
   The perl line keeps both sides of every hunk whose base is empty and leaves real conflicts marked.
4. Typecheck, full suite, lint and build on main; mark the ticket MERGED. If main goes red, stop dispatching, fix or revert, then continue.

Never rebase in-flight workers; their branch merges the same way when its checker passes.

## 5. Final pass (before claiming the clone)

A fresh subagent that wrote no tickets: re-checks every ticket's acceptance criteria against the running app on a fresh server, runs suite, lint, typecheck and build from a clean install, clicks through the main pre-existing flows for regressions, and lists anything missing. Only then report the clone done and follow Frist's completion process.

## Worker rules (why each exists)

- **Read the spec literally.** Graders check the ticket's stated behavior, including every "Requested behavior" bullet, on held-out inputs.
- **Smallest change** that satisfies the ticket; extra refactors create conflicts and regressions.
- **Never delete, skip or loosen existing tests.** Report a test that seems wrong.
- **Reuse the app's components, classes and label style.** Frist's journeys "expect the app's existing components and labels".
- **Use the ticket's labels character for character** as visible control text; graders find controls by exact label.
- **Commit per ticket** with the ID first: `TICKET-12: add sort by date to inbox`.
- **Hot files only via the own-file layout**; a new dependency or migration means stop and report NEEDS-DEP.

## Worker prompt template (paste and fill)

```
You are a worker finishing ONE ticket on a Frist app clone. You are in your own git worktree <path>; other workers are editing other tickets in parallel on the same machine.
Read ~/Hackathons-local/frist/DISCOVERY.md first (stack, commands, ports, hot files).
Ticket: <ID> <title>
Spec / acceptance criteria (verbatim): <paste>
Files likely involved: <list>. Do NOT edit: <shared hot files>, except as the merge rules below allow.
Use ports <port>/<backend port> for the dev server.
<own-file layout block from frist-clone-tickets section 3>

How you are graded: hidden browser journeys replay this ticket on a fresh database with inputs you have not seen (other records and values than the ticket's examples), select elements by the app's existing labels, roles and component classes, and also replay journeys over the rest of the app. Every "Requested behavior" bullet is checked, not just the acceptance criteria. An independent checker will re-test your branch from the ticket alone before it merges.

Do:
1. Read the relevant code first. Find the closest existing feature (page, card, menu, picker, list row, API route) and copy its structure, components, CSS classes, helpers and label style. If design/ has a screenshot of this screen, match it. If the bug is in one list item, sibling or route, grep for the same pattern elsewhere.
2. Implement the smallest change that meets every Requested behavior bullet and acceptance criterion literally (labels, texts, formats, colours, ordering, limits, error messages, status codes). Use the ticket's labels and values character for character as visible text (if it says pick "8", the option reads "8", not "8 pts"). If another control in the same panel already has your label, say so in NOTES. If the ticket needs a hot file the merge rules do not cover, stop and report NEEDS-DEP.
3. Add or update tests if the repo has tests for that layer.
4. Verify and paste the tail of each output (N/A for steps the repo lacks): a. tests for this area, b. full suite, c. lint (no new errors), d. typecheck, e. build, f. smoke check on a FRESHLY started dev server on your ports after your final commit: a headless Playwright script that checks each criterion and bullet, printing PASS/FAIL per line with the text seen. Find every control by the ticket's own words with exact matching (get_by_role("option", name="8", exact=True), get_by_text("None", exact=True)), never by your own class, test id or a looser match. If the exact string does not find it, that line is FAIL and you are not DONE. Try at least one input that is not the ticket's example. Then load two unrelated pages and one neighbouring feature and confirm they still work.
5. Commit "<ID>: <short summary>". Leave git status clean: smoke scripts, screenshots and logs go in /tmp/claude-501/.
Never delete, skip or weaken existing tests. Use every resource that helps: web search, docs, the real product's public site for exact wording and behavior, the repo, design/. Do not add dependencies yourself. Prefer tools already in node_modules/.bin over npx downloads.

Shared-machine rules:
- Start servers only on your ports; stop them by port (lsof -ti tcp:<port> | xargs kill). NEVER pkill -f or killall by name.
- If the server dies or the page is blank, read its log first; another worker may have killed it. Restart once.
- One browser at a time against a fresh server; wait for the app to finish loading before asserting.
- Prefix installs, builds and test runs with nice -n 15.

Report exactly:
STATUS: DONE | BLOCKED | NEEDS-DEP
BRANCH: <branch> COMMITS: <shas>
FILES CHANGED: <list>
VERIFICATION: <a-f pass/fail with short output; f lists every criterion>
NOTES: <ambiguities and the reading you chose, files outside the list and why>
```

## Acceptance checker prompt (paste and fill)

```
You are an ACCEPTANCE CHECKER for one Frist clone ticket. You did not write the code and you get no report from whoever did. Do not edit the repo.
Read ~/Hackathons-local/frist/DISCOVERY.md (commands, offline Playwright launch line).
Ticket (verbatim): <paste>
Code to check: worktree <path> (branch <branch>). Ports: <port>/<backend port>. Write scripts and logs only in /tmp/claude-501/check-<ID>/.
1. Start the app freshly from that worktree on your ports.
2. Write your own headless Playwright checks: one per acceptance criterion and one per Requested behavior bullet. Locate every control and text by the ticket's exact words with exact matching (role + exact name, or exact text). A control the exact words do not find is FAIL. Add one input that is not the ticket's example.
3. Load two unrelated existing pages and one neighbouring feature on the same screen; they must still work.
4. Stop your servers by port. Close every browser.
Return exactly:
CHECK: PASS | FAIL
LINES: <one line per criterion/bullet/regression: PASS|FAIL, the exact text or value seen>
NOTES: <anything ambiguous in the ticket>
```

## When stuck

- Spec ambiguous: pick the reading most consistent with the rest of the app, note it; the orchestrator asks staff if it could cost the clone.
- Ticket needs something outside the repo (keys, external service): BLOCKED, ask staff, move on.
- A ticket fights a worker for over 45 minutes: park it, finish the rest, retry with a fresh worker that gets the previous notes.
