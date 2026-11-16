---
name: rl-env-playbook
description: Top-level strategy and orchestrator loop for building reinforcement-learning environments and graded tasks with a fleet of Claude subagents. Covers what an RL task is (prompt, initial state, reset, hidden grader, reference solution), the split-role pipeline so nobody grades their own work, controls (empty change scores 0, reference scores 1), reward-hacking defenses, difficulty probes aimed at a mixed frontier pass rate, and machine-load limits. Use it whenever the user wants to build an RL environment, make a training or eval task, author coding tasks with hidden tests, computer-use tasks with a state verifier, finish an app clone for training, harden a task that models solve too easily, check a grader for reward hacking, or asks "what should we do next" while running that kind of pipeline. It routes to rl-clone-tickets, rl-coding-task and rl-computer-use-task.
---

# RL environment playbook

An RL task is five things: a **prompt** the agent reads, an **initial state** (a repo, an app with seeded data, a world of several apps) with a **reset**, a **grader** the agent cannot see that turns the final state into a reward, a **reference solution** that proves the task is solvable, and **metadata** (category, difficulty). A task is worth something only if its reward is trustworthy: the reference scores 1, doing nothing scores 0, cheating scores 0, every valid solution scores 1, and the result is the same every run.

This skill is the orchestrator's playbook. Three worker skills do the building:
- `rl-clone-tickets`: finish an app or app clone so tasks can be built on it (tickets, checker, merge loop).
- `rl-coding-task`: a broken or incomplete repo, a ticket, hidden tests, a reference fix, wrong fixes the tests must reject.
- `rl-computer-use-task`: a seeded app world, a goal, a fail-closed state verifier, an oracle, adversarial agents that must score 0.

## The lessons that matter most

1. **Split roles; nobody grades their own work.** Agents write weak tests and then pass them. One agent plants the bug or builds the feature, a second writes tests from the ticket and the working original only, a third writes plausible wrong fixes without seeing the tests, and a checker requires the tests to reject every wrong fix. Ticket workers get a fresh acceptance checker that sees only the ticket. In our tests the split raised wrong fixes caught from 13/24 to 23/24 on a real app.
2. **A mutation bar, one mutation per acceptance criterion.** For every criterion in the ticket there is at least one wrong fix or mutant that breaks only that criterion, and the hidden tests must catch it. Add auto operator mutants near the fix and require 80% or more killed after justified equivalents (`rl-coding-task/scripts/mutation_bar.py`).
3. **Controls.** The empty change (the broken repo as shipped, or a do-nothing agent) scores 0, and the reference scores 1, three runs in a row from a clean copy (`verify_task.sh`). The empty change must fail on an assertion, not an import or boot error.
4. **Tests check only what the ticket states.** Every tested behavior is stated or clearly implied in the ticket, and every stated behavior is tested. A test that checks a fact the solver had to guess is an ambiguity bug, not difficulty. Run a fairness audit on terse tickets (`rl-coding-task/references/building-coding-tasks.md`, "Terse ticket round").
5. **Hidden tests and answers cannot be reached.** No hidden tests, reference, canaries or answers in the shipped repo, its git history, backup files, served paths (Vite `/@fs/`), logs or seed data. Hidden tests are overlaid only at grading time.
6. **Shortcut and reward-hack attempts score 0.** A hack author writes cheats (delete tests, skip-all config, hardcode the example, constant stub, fake runner) and every one must fail. Expect any serious grading pipeline to run its own shortcut attempt too.
7. **Isolated difficulty probes, aimed at a mixed pass rate.** A probe solver sees only what the real solver sees, its transcript is audited, and the target is a mixed frontier result (about 1 of 3 attempts passes). What made tasks hard and what did not is in `references/making-tasks-hard.md` and the "Difficulty" section below.
8. **Computer-use verifiers fail closed.** Every intended change is a required assertion, the verifier diffs the whole relevant state against seed plus the intended change, and the report message is never evidence.
9. **Orchestrator plus workers plus checkers, within machine limits.** See the loop below.

## Roles

You are the **orchestrator**. The main session does not write feature code or tasks itself. It discovers, plans, dispatches subagent workers, merges, runs checkers and reviewers, keeps the board, and talks to the user. Workers do the work in isolated worktrees or sandboxes. This keeps the main context small over a long session and lets 3 to 5 things progress at once.

## Workspace and discovery

Pick one workspace root per project outside any iCloud-synced folder (for example `~/rl-work/<project>/`; written `<ws>` below), with one subfolder per app (`<ws>/<app>/` holds the repo, `wt/`, `tasks/`, `private/`, `DISCOVERY.md` and `BOARD.md`). iCloud-synced folders like `~/Documents` break `node_modules` (on one Mac the shell turned it into a `.nosync` symlink, which blanked Vite and slipped past `node_modules/` gitignore rules). Exclude the workspace from Spotlight (`touch <ws>/.metadata_never_index`); indexing `node_modules` copies pushed load to 12 to 19 in one test.

Run one discovery subagent that writes `<ws>/<app>/DISCOVERY.md`:
- Everything in `rl-clone-tickets` section 1 (commands, baseline, tickets, hot files, worktree bootstrap, offline Playwright, env quirks), plus one clean install in a scratch clone to catch setup gaps.
- The target task format: directory layout, required files, schema fields, categories, any validator, one example copied verbatim. If no format is given, use a public one from `references/task-formats.md`.
- World composition for computer-use tasks (apps, ports, seed and reset, verifier API).
- Answers from whoever defines acceptance (a platform's docs, a reviewer, the user).

Every worker prompt starts with "Read DISCOVERY.md first". Never invent a platform convention; discover it or ask.

## The orchestrator loop

1. **Plan.** Turn tickets or task ideas into `BOARD.md` rows with a files-touched guess and a shared-file flag.
2. **Dispatch.** One `Agent` subagent per independent row, launched together in one message so they run concurrently. Omit `model` so workers inherit the session default; use a second model family only as an extra solver on difficulty probes.
3. **Machine limits (10-core laptop).** At most **3 to 5 concurrent workers**, counting every agent that boots a dev server, a browser or a mutation bar. Check `uptime` before each batch and keep the 1-minute load **under 12**. Prefix installs, builds, test runs, probes and `mutation_bar.py` with `nice -n 15`, and **drop to 2 workers if load climbs**. In our tests, 4 workers plus graders hit 19, and 9 helpers plus 4 mutation bars hit 60 to 100 and nearly crashed the machine. Use a real charger: a 15 W USB brick drained the battery while "charging".
4. **Serialize shared files.** No two concurrent workers on package.json or lockfiles, migrations, schema, route registries or seed fixtures; one integrator worker owns those. New dependencies are reported (NEEDS-DEP), never installed in parallel. Clone tickets avoid most contention with the own-file layout (`rl-clone-tickets` section 3).
5. **Never kill by name.** Workers stop servers by port or PID. `pkill -f dev.mjs` takes down every other worker's server; a headless solver told only that "other engineers share the machine" still did it.
6. **Verify, then merge.** A worker's DONE or READY is a claim. Tickets: a fresh acceptance checker that sees only the ticket, then merge right away. Tasks: the checker pipeline in the task skill. If main breaks, stop dispatching, fix or revert.
7. **Review (tasks only).** A **fresh** reviewer subagent (prompt below) that did not author the task. Only PASS goes out; FAIL goes back with reasons.
8. **Ship and record.** Mark SHIPPED, then ACCEPTED or REJECTED with the reason. Read every rejection at once; a pattern in rejections changes the prompts for every running worker.
9. **Repeat.** Workers run in the background and notify you when done. Do not poll and do not predict their results.

## Open resources vs isolation

Your own agents (orchestrator, ticket workers, checkers, bug and test authors, wrong-fix authors, reviewers) may use every resource that helps: web search, docs, the real product's public site, any file in the repo. Isolation rules (no web, canaries, locked folders, transcript audits) apply to exactly two things:
- **Difficulty probes.** A solver probe sees only what the real solver will see (the ticket or goal plus the broken repo or running app), or its result means nothing.
- **The environment you ship.** Hidden tests, verifier code, seed answers and reference fixes must be unreachable from inside the task (no `/@fs` exposure, no DB path in logs, no answers in git history).

Separately, the coding pipeline's **role firewall** (test author never sees the bug, wrong-fix author never sees tests or the reference) is about test strength, not secrecy; it is always on.

## Difficulty

Training tasks are most useful in the **learnable band**: a strong model passes some attempts and fails others. A common target is the top models passing about 1 of 3 attempts. Too easy teaches nothing; never solved usually means the task is broken or ambiguous.

How to probe:
- One isolated probe per candidate by default (coding: `rl-coding-task` "Pipeline" step 2; computer use: `rl-computer-use-task` step 7). Record the result on BOARD.md.
- When difficulty gates acceptance: 3 attempts on the strongest model, plus a second model family if available, and aim for a mixed result.
- A 0-solve result means read the failures first: ambiguity or over-fit tests get fixed before calling it hard.
- Probe the way the real solver works: if the real harness is pixel-only, probe with screenshot-only control (`rl-computer-use-task` "Probe with screenshots only").

What did and did not raise difficulty in our tests, measured with headless Opus 5.5 probes (Nov 2026):

| Lever | Result |
|---|---|
| Small app (about 4,000 lines): linked causes, shared SQL helper, removed logic with about 15 rules, 20-check two-app CU tasks | all solved, 1 to 4 min |
| 160k-line app, 3 bugs (runtime pagination, 4-file fallback, shared recursion) | solved 1.8 to 3.7 min |
| Removed 8-step dependent chain in the API layer | solved 4.2 min, 561/561 tests |
| Removed 7-step client-state chain, browser-only checks | solved 6.8 min, 40/40 journeys |
| Tempting template page for another record | solved 3.7 min |
| Terse ticket with a fair grader | solved about 5 min; "failures" were only unguessable facts |
| CU tasks with screenshot-only control | 6/6 valid runs solved, 3 to 6 min |
| CU combinatorial optimum, 768 options, every number in a few emails | 2/2 solved, 3.5 min |
| Concurrency task whose ticket hinted the mechanism | 3/3 solved, about 13 min |

Why: with fair tickets (every checked rule stated), strong models turn the rule list into code in one pass, then verify with fast tests or one scripted Playwright walk. What still has room, from published data and the levers above: many independent decisions that compound (14 decisions at 95% each pass 49% of the time), state spread across services with no fast in-process test path, outcome-only tickets that do not name the mechanism, invariants that must hold across every write path (concurrency, ordering, deadlock order), and exploration problems where the deciding facts are spread across many pages. Ranked recipes with evidence: `references/making-tasks-hard.md`.

To harden a concurrency or invariant task whose probe solved it: state outcomes only (never the mechanism), widen the invariant across every write path, and add a lock-ordering case.

Never make a task hard through vagueness, clunky UI, flaky timing or facts the solver must guess. Reviewers reject those, and they do not teach anything.

## Prefer task shapes you can check end to end locally

Browser-lane and visual tasks depend on the grading pipeline's own browser image and screenshot handling. In our tests a visual task passed every local check (base 0/16, reference 16/16) and was still graded inverted twice by a remote pipeline whose image had no Chromium. Server-side shapes (concurrency, authorization, resilience, data contracts) whose two-sided check you can run locally are safer. When a remote grader disagrees with your local controls, escalate with evidence (the commands, the outputs, the commit) rather than resubmitting blind.

## Working in a hosted workspace

Some pipelines run each task in a hosted workspace with its own Claude Code instead of local worktrees. Then the orchestrator's job becomes writing prompts for that workspace's agent. What we learned:
- The workspace agent may have a smaller context cap (200k in our case). Keep evidence reads narrow (grep or Python extracts), push big reads into subagents, and keep a notes file in the workspace so compaction does not lose the plan.
- Workspaces can be rebuilt from scratch, losing uncommitted drafts and `/tmp`. Commit after every step.
- A save hook can block every prompt while the workspace is saving. Do not force-close workspace tabs mid-save, keep one viewer per workspace, and ask the operators if it persists.
- Screenshots for visual tasks may have to be pasted into the terminal by hand when the file browser is read-only.
- If one model's endpoint is unavailable there, probe with the models that are.

## BOARD.md format

At the workspace root, updated after every merge or verdict.

```markdown
# Board   Accepted: 0   In review: 0   Updated: 10:42

| ID | Type | Title | Owner | Shared files | Status | Notes |
|----|------|-------|-------|--------------|--------|-------|
| T-12 | ticket | Add sort by date | worker-a | none | MERGED | checker PASS 10:40 |
| CT-1 | coding | Off-by-one in pagination | bug-author-1 | none | REVIEW | probe: Opus solved 1/3 |
| CU-1 | cu | Copy invoice total to chat app | worker-d | seed | IDEA | |
```

Statuses: IDEA, RUNNING, DONE, CHECKING, MERGED, PROBED, REVIEW, PASS, FAIL, SHIPPED, ACCEPTED, REJECTED.

## Reviewer subagent prompt (paste and fill)

```
You are an adversarial reviewer for an RL task. You did not write it and you want to find reasons it would be REJECTED. Do not fix anything. Use any resource that helps.
Task path: <path>. Task type: <coding | computer-use>. Target format and rules: <<ws>/<app>/DISCOVERY.md section>.
Run every item of the "Pre-submit checklist" in ~/.claude/skills/<rl-coding-task | rl-computer-use-task>/SKILL.md. Execute each check yourself (run the oracle 3 times, the null attempt, the hacks or adversaries, an alternative valid fix or path; grep the prompt and every agent-visible file for leaked answers, diffs, test names or golden values). Check it matches the target format exactly and the problem statement is clear to someone who has never seen the code. Report the probe result as a RISK if difficulty matters for acceptance.
Return exactly:
VERDICT: PASS or FAIL
FAILED ITEMS: <numbered list with evidence: command run and output>
RISKS: <things that passed but feel borderline>
```

## Files

- `references/making-tasks-hard.md`: ranked hardening recipes with published solve-rate data, and a fairness checklist.
- `references/non-lazy-judges.md`: principles for judges that cheaters and do-nothing agents cannot pass.
- `references/task-formats.md`: public task formats (SWE-bench, SWE-smith, Harbor, HUD, BrowserGym, OSWorld) and their common shape.
- `examples/hardened_grader_example.py`, `examples/state_verifier_example.py`: tested toy judges.

## Writing rules

- No em dashes in anything written for the user or shipped.
- Do not send email or messages on the user's behalf; the user ships and talks to reviewers unless they say otherwise.
