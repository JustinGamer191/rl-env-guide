---
name: frist-coding-task
description: Create ACCEPTABLE coding RL tasks (500 pts each when accepted) on a finished Frist app clone, SWE-bench/SWE-smith style, using parallel subagent workers plus an adversarial reviewer before every submission. Use this whenever a Frist clone is complete and the next step is authoring coding tasks, when Justin says "make a coding task", "inject a bug", "RL task", "500 point task", mentions Frist's task categories or task template, or when a coding task was rejected and needs fixing. Rejected tasks score 0, so use the checklist here every time.
---

# Frist coding task

A coding RL task is a repo in a broken or incomplete state, a ticket an agent reads, hidden tests that decide the reward, and a reference solution proving it is solvable. It is accepted only if the reward is trustworthy: solvable, not passed by doing nothing, not hackable, deterministic, clearly stated. Agents write weak tests and then pass them, so no agent grades its own work: the work is split across roles with an information firewall.

**Frist's template and categories win over everything here.** Before the first task, DISCOVERY.md must hold Frist's template, category list and an example. Map our pieces (repo, ticket, hidden tests, oracle, metadata) onto their slots (`~/.claude/skills/frist-hackathon-playbook/references/task-formats.md` shows how public formats name them). If a slot is unclear, ask staff before mass-producing.

Depth: `references/winning-coding-tasks.md` (bug-site catalog, bug taxonomy, ticket rules, test-strength recipe, rehearsal data, rejection causes). Paste-ready prompts for every role: `references/role-prompts.md`.

## Known Frist coding-task format (public, verify at kickoff)

From Frist's blog ("Green Tests, Broken Apps", Oct 23 2026) and sample runs at https://frist.ai/samples/, summarized in `~/Documents/Hackathons/Frist/frist-intel.md`:
- Tasks **remove a working feature or plant a bug** in a clone. The original passes grading; the broken app fails.
- **The prompt is a ticket**, no file names, no cause:
  ```
  # <title>
  **Page:** `<route>` · **Type:** feature|bug · **Size:** M
  ## Description
  ## Requested behavior
  - <bullets>
  ## Acceptance criteria
  - [ ] <checkbox naming a concrete visible label, e.g. selecting "Photos">
  Start the dev server with `bun dev.mjs` (http://127.0.0.1:5173 ...). Chromium and Playwright are installed.
  ```
- **Grading replays browser journeys** on held-out inputs plus many regression journeys (one sample: 2 feature, 27 regression). So F2P = feature journeys, P2P = regression journeys.
- Their rubric: feature works, no regressions, reuses the app's existing names, labels, components and fallbacks, solver tested its work and reported truthfully. Design tasks so hardcoding the ticket's example fails on held-out inputs.

## Task dir layout (what the scripts expect)

`~/Hackathons-local/frist/tasks/<task-id>/`:
- `repo/`: broken repo exactly as the solver sees it (no `.git`, or one squashed commit; no hidden tests, notes, backups).
- `ticket.md`: Frist-template ticket.
- `solution.patch`: oracle, broken -> original (`a/` `b/` paths, applies with `git apply` in `repo/`).
- `hidden_tests/`: overlaid onto `repo/` at grading time (feature + regression journeys, goldens, the shared harness under `hidden/harness/`).
- `wrong_fixes/*.patch`: plausible honest wrong fixes (must all fail). `alt_fixes/*.patch`: other valid fixes (must all pass).
- `hacks/*.patch`: cheating attempts (must all fail).
- `equivalent_mutants.txt`, `mutation_report.json`: checker outputs.
- Private, never shipped: `BUG_NOTES.md`, `screen_check.sh`, `heldout_hint.md` (keep them in `~/Hackathons-local/frist/private/<task-id>/`).

Rename to Frist's layout at packaging time.

## Pipeline (orchestrator)

Once per clone, as soon as discovery is done (can overlap the last tickets):
- **0a Catalog agent** (role-prompts 0a): 15 to 25 scored bug sites across feature areas, each tagged with a Frist category.
- **0b Harness agent** (role-prompts 0b), in parallel: one shared journey runner and fact recorder with `MB_SLOT` ports. Every task reuses it; this is the biggest throughput win.

Per task, one sandbox per role under `~/Hackathons-local/frist/roles/<task-id>/<role>/` holding only that role's inputs (table in role-prompts "Isolation"). Give parallel tasks different feature areas and Frist categories.
1. **Bug author** (role-prompts 1): plants one bug or logic-only feature removal; writes `repo/`, `solution.patch`, `ticket.md`, `heldout_hint.md`, `BUG_NOTES.md`, `screen_check.sh`.
2. **Opus screen** (about 3 minutes; record it, it does not block): one headless Opus solver on ticket + broken repo only, graded by `screen_check.sh`. Run it in parallel with step 3. Command, from a solver sandbox holding only `ticket.md` and `repo/` (prompt = role-prompts 5):
   ```bash
   cd <solver sandbox> && nice -n 15 claude -p --model claude-opus-5-5 --permission-mode acceptEdits \
     --output-format json --allowedTools Bash Read Write Edit --disallowedTools WebFetch WebSearch Skill Agent \
     --disable-slash-commands --strict-mcp-config < <private>/solver_prompt.txt > <private>/screen.json
   bash <private>/screen_check.sh <solver sandbox>/repo <port-base>
   ```
   Transcript: `~/.claude/projects/<sandbox path with every non-alphanumeric char replaced by ->/<session_id from screen.json>.jsonl`; audit it (Isolation below). Write "screen: solved in N min" or "screen: failed (why)" on BOARD.md. Only if staff have said difficulty matters: wait for the screen and harden before step 3 (playbook "Difficulty gate").
3. In parallel: **test author** (role-prompts 2, ticket + heldout_hint + original only), **wrong-fix author** (role-prompts 3, ticket + broken repo only), **hack author** (role-prompts 3b).
4. **Assemble** the task dir (layout above). Move the solver's patch into the alt fixes for grading (`alt_plus_solver/`).
5. **Checker** (role-prompts 4): `mutation_bar.py`, then `verify_task.sh`, then the isolation results. Survivors go back to the test author (step 3) until `MUTATION BAR: PASS` and `VERIFY: PASS`.
6. **Reviewer** (playbook "Reviewer subagent prompt") on this skill's checklist. Only PASS is submitted.

Measured on a cold real app: catalog plus harness about 16 min, then about 60 min from clone to three graded tasks when the machine is not overloaded. Hidden-test authors are the slow step (18 to 20 min).

## Isolation step (evidence, not instructions)

Our roles may use the web and docs (event mode). What isolation protects is (a) the role firewall, so tests are written without seeing the bug and wrong fixes without seeing the tests, and (b) solver probes, which must see only what Frist's solver sees.
1. One directory per role holding only its allowed inputs (`cp -cR`).
2. Unique canaries (`CNRY-<KIND>-<task>-<hex>`) in `BUG_NOTES.md`, the `solution.patch` preamble (text before the first `diff --git`), every hidden test and golden, and a first-line comment in the reference copy of each touched file. None in the broken repo.
3. `chmod 000` the other copies of the answer (finished bug-author dirs, `tasks/`, `private/`) while a solver or wrong-fix author runs, where that does not block other workers (the main clone is usually still in use, so do not lock it). **This is a speed bump, not a wall:** a same-user agent with Bash can `chmod` it back, or read a copy elsewhere. The transcript audit is the real safeguard, so always pass every locked or forbidden path to it.
4. After each role, audit its transcript:
   ```bash
   python3 ~/.claude/skills/frist-coding-task/scripts/isolation_check.py --transcript <jsonl> \
     --allow <role dir> --allow ~/.claude/skills --forbid <each answer path> --canary <each token> \
     --outputs <role outputs> [--no-network]
   ```
   `--no-network` only for solver probes. A `chmod`, `cat` or `ls` on a forbidden path, git history commands, and canaries seen in tool results or written to outputs are all VIOLATIONS. `ISOLATION: VIOLATED` means discard that role's output and rerun it with a fresh agent. Subagent transcripts live at `~/.claude/projects/<project>/<session>/subagents/agent-<id>.jsonl`.

The shipped environment needs the same care: no `.git` history, no `.orig`/`.rej`/backup files, no canary or answer in `repo/` (`verify_task.sh` checks these).

## Determinism rules

No network in code under test; freeze or anchor time (anchored clock: fixed start plus elapsed, never fully frozen, which breaks ORDER BY created_at); seed randomness; no dependence on test order, ports in use, locale or timezone (`TZ=UTC`; `mutation_bar.py` sets it). Pin dependencies. Oracle passes 3 runs in a row.

## Pre-submit checklist (reviewer runs every item, with evidence)

1. Matches Frist's template, category and required fields exactly; their validator passes if one exists.
2. Ticket is clear, user-facing, single interpretation, and leaks nothing: no file or function names, no cause, no diff, no test names, no hidden values beyond what the ticket's own example states. Grep test and stranger test done (winning-coding-tasks "Ticket writing").
3. Agent-visible repo has no hidden tests, solution, canaries or hints (comments, TODOs, git history, branch names, backup files, `.orig`/`.rej`).
4. Null attempt fails F2P on an assertion, not an import or boot error.
5. Oracle passes F2P and P2P, 3 runs in a row from a clean copy (`verify_task.sh RUNS=3`).
6. P2P is green on the broken repo.
7. Hacks fail: deleted tests, skip-all config, edited test script, hardcoded outputs, constant stub, plus `verify_task.sh` auto hacks.
8. `mutation_bar.py` passes: every wrong fix killed, every alt fix and the solver's fix pass, at least 80% of auto mutants killed after justified equivalents.
9. Deterministic: no network, time, randomness, order or locale dependence.
10. Not trivially marked: no greppable marker, crash with stack trace or type error. The Opus screen result is recorded on BOARD.md; a solve is not a failure.
11. Diverse from our other submitted tasks (different feature area or bug type).
12. Isolation audits CLEAN for test author, wrong-fix author and solver.

## Scripts (Python scripts take `--help`; `verify_task.sh` documents its env vars in its header)

- `scripts/verify_task.sh` (env vars): `TASK_DIR`, `F2P_CMD`, `P2P_CMD` required; `SETUP_CMD`, `RUNS` (default 3), `F2P_PASS_REGEX` (require a pass-count line, so an early `exit 0` cannot pass), `PROTECTED`, `AUTO_HACKS` (default 1), `MIN_HACKS` (default 4). Checks leaks, null, oracle x RUNS and scope, hacks, hidden-test tampering. Ends `VERIFY: PASS` or `VERIFY: FAIL (n problems)`.
  `TASK_DIR=<task> F2P_CMD='...' P2P_CMD='...' SETUP_CMD='...' F2P_PASS_REGEX='...' RUNS=3 nice -n 15 bash ~/.claude/skills/frist-coding-task/scripts/verify_task.sh`
- `scripts/mutation_bar.py --task-dir <task> --test-cmd '<F2P>' [--p2p-cmd] [--setup-cmd] [--tests-dir hidden_tests] [--wrong-dir wrong_fixes] [--alt-dir alt_fixes] [--syntax-cmd '<cmd with {file}>'] [--equivalent FILE] [--max-auto 40] [--min-auto-score 0.8] [--mutate-context 25] [--no-auto] [--jobs 1] [--slot-base N] [--infra-exit-codes 3] [--timeout 600] [--json-out FILE]`. `{slot}` in commands and `MB_SLOT` in the env pick ports; give concurrent runs disjoint `--slot-base`. Harness exit 3 = UNGRADED, never a kill. Ends `MUTATION BAR: PASS`.
- `scripts/isolation_check.py --transcript <jsonl> [--allow DIR]... [--forbid DIR]... [--canary TOKEN]... [--outputs DIR]... [--no-network] [--allow-history] [--upstream-hint owner/repo] [--ignore-path PREFIX]...`. Ends `ISOLATION: CLEAN` or `ISOLATION: VIOLATED`.

These are local pre-checks; Frist's harness is the real judge.

## On a rejection

Record Frist's reason on BOARD.md, tell every running worker in this pipeline, and add the cause to the checklist for later tasks. If the reason is difficulty, switch to the hardening levers in the playbook "Difficulty gate".
