---
name: frist-hackathon-playbook
description: Top-level strategy and orchestrator loop for the Frist RL hackathon (Sun Nov 15 2026, 10am-9pm, Atlanta), where teams finish app-clone tickets (10 pts each, 100 per clone) and then author computer-use tasks (100 pts accepted) and coding RL tasks (500 pts accepted). Use this the moment Frist, the Frist hackathon, app clones, clone tickets, RL task authoring, the points leaderboard, or "what should we do next" at this event comes up, at kickoff, after any submission, and whenever choosing between tickets, coding tasks and computer-use tasks. It routes to frist-clone-tickets, frist-coding-task and frist-computer-use-task and tells the main session how to run parallel subagent workers and a reviewer.
---

# Frist hackathon playbook

You are the **orchestrator**. The main Claude Code session does not write feature code or tasks itself. It discovers, plans, dispatches subagent workers, merges, runs checkers and reviewers, keeps the board, and talks to Justin. Workers do the work in isolated worktrees or sandboxes. This keeps the main context small (the day is 11 hours) and lets 3 to 5 things progress at once.

**At 9:00, start with `references/first-hour.md`.** It is the step-by-step runbook from check-in to the first coding-task screen, naming the section or script for each step.

Frist has published how its clones, tickets and tasks look in production (Bun + React/TS/Vite clones generated from site recordings, tickets with Page/Type/Size and acceptance-criteria checkboxes, grading by replayed browser journeys on held-out inputs plus regression journeys, a cross-app "world ledger" for computer-use tasks). Each worker skill has a "Known Frist ... (public, verify at kickoff)" section; sources are in `~/Documents/Hackathons/Frist/frist-intel.md`. Nothing public describes the hackathon's own submission format, so anything event-specific says "discover": read their template, examples and docs, and ask staff. Never invent a Frist convention.

## Rules of the day (settled)

- **One track per person:** Justin is on **computer use and coding**. Ignore the hardware and security tracks. About 250 people on this track.
- **Winners by leaderboard at 9pm** (the schedule says 9pm; one rules blurb says 10pm, treat 9pm as the cutoff). Only accepted tasks count, so ask staff how long review takes.
- **Points:** ticket 10, clone complete 100, accepted computer-use (CU) task 100, accepted coding task 500, rejected task 0.
- **Multiple clones at once are allowed**, with no limit; tickets on every clone earn points.
- **Pairing up** with another person is allowed only after finishing an application. Teams are 1 or 2 people, so the agent fleet is the real headcount.
- **Prizes:** 1st flight to the Frist NYC hacker house + Meta Ray-Bans, 2nd Mac Mini, 3rd Nintendo Switch; AirPods for the first 20 teams to reach 300 points.
- **AI tools are allowed** by the organizers. Stay within whatever is announced at kickoff.

## Point math (why the order matters)

1. **Finish one clone fast.** It is worth 100 + 10 per ticket and it is the gate to 500-point coding tasks. Clone 1 gets worker priority; when it has fewer independent tickets than free worker slots (or its tickets are blocked on staff), spare slots grind a second clone. A second finished clone also helps build a CU world.
2. **Then coding tasks.** One accepted coding task = 5 CU tasks = 50 tickets. Spend most of the afternoon here.
3. **Acceptance rate beats volume.** Every task gets a fresh reviewer before submission.
4. **AirPods at 300:** 100 (clone) + tickets + one accepted 500 task clears it. Aim for the first coding task submitted by early afternoon.
5. **CU tasks are filler** behind coding tasks: idle slots, a blocked coding pipeline, or a template that mints accepted variants cheaply.

## Timeline

| Time | Goal |
|---|---|
| 9:00-10:00 | Check in, power, wifi, environment checks, staff questions (`references/first-hour.md`). |
| 10:00-10:30 | Claim clone 1, clone it into `~/Hackathons-local/frist/`, discovery, `BOARD.md`, first ticket batch. |
| 10:30-13:00 | Clone 1 tickets, 3 to 5 workers (frist-clone-tickets). Merge each branch as its checker passes. In parallel: catalog and harness agents for coding tasks once discovery is done. |
| ~12:00 | Draft the project submission page (below). |
| 13:00 | Clone 1 must be 100%. If not, every slot goes to its remaining tickets. |
| 13:00-14:00 | First coding task end to end (frist-coding-task), reviewed and submitted. Calibrate from Frist's first verdict. |
| 14:00-19:00 | Coding tasks in parallel, one fresh reviewer per finished task. Spare slots: second clone tickets, then CU tasks once a world exists. |
| 19:00-20:30 | Only finish and submit things already near done. No new ideas after 20:00. At 20:00, polish the submission page. |
| 20:30-21:00 | Confirm every submission shows on the leaderboard. Resubmit anything stuck. |

Read every rejection immediately; a pattern in rejections changes the prompts for every running worker.

## Workspace and discovery

The workspace is `~/Hackathons-local/frist/`: every repo, worktree, task dir, `DISCOVERY.md` and `BOARD.md` live there. Never `~/Documents` or `~/Desktop` (prep.md's `~/Documents/Hackathons/Frist/work/` is superseded): those sync to iCloud, Justin's shell turns `node_modules` there into a `.nosync` symlink, which broke Vite (blank page) and slipped past `node_modules/` gitignore rules in rehearsal. Start Claude Code with the clone repo as cwd if you want `isolation: "worktree"` to work; otherwise create worktrees by hand (frist-clone-tickets section 3).

Run one discovery subagent (or inline if tiny) that writes `~/Hackathons-local/frist/DISCOVERY.md`:
- Everything in frist-clone-tickets section 1 (commands, baseline, tickets, hot files, worktree bootstrap, offline Playwright, env quirks).
- Frist's task template(s): directory layout, required files, schema fields, predefined coding categories, any validator, one example copied verbatim.
- World composition for CU tasks if one is provided (apps, ports, seed and reset, verifier API).
- Staff answers, as they come in.

Every worker prompt starts with "Read DISCOVERY.md first".

## The orchestrator loop

1. **Plan.** Turn tickets or task ideas into `BOARD.md` rows with a files-touched guess and a shared-file flag.
2. **Dispatch.** One `Agent` subagent per independent row, launched together in one message so they run concurrently. Model: omit `model` (workers inherit Opus 5.5, the default); Fable 5.2 matched Opus in rehearsal at about 2x cost, so use it only as a second solver family on probes when staff say difficulty matters.
3. **Machine limits (Justin's M5, 10 cores).** At most **3 to 5 concurrent workers**, counting every agent that boots a dev server, a browser or a mutation bar. Check `uptime` before each batch and keep the 1-minute load **under 12**; prefix installs, builds, test runs, probes and `mutation_bar.py` with `nice -n 15`; **drop to 2 workers if load climbs**. (Rehearsal: 4 workers plus graders hit 19; 9 helpers plus 4 mutation bars hit 60 to 100 and nearly crashed the machine.)
4. **Serialize shared files.** No two concurrent workers on package.json or lockfiles, migrations, schema, route registries or seed fixtures; one integrator worker owns those. New dependencies are reported (NEEDS-DEP), never installed in parallel. Clone tickets avoid most contention with the own-file layout (frist-clone-tickets section 3).
5. **Verify, then merge.** A worker's DONE or READY is a claim. Tickets: a fresh acceptance checker that sees only the ticket, then merge right away with the diff3 merge plus perl resolver (frist-clone-tickets section 4). Tasks: the checker pipeline in the task skill. If main breaks, stop dispatching, fix or revert.
6. **Review (tasks only).** A **fresh** reviewer subagent (prompt below) that did not author the task. Only PASS goes to submission; FAIL goes back with reasons.
7. **Submit and record.** Justin submits per Frist's process; mark SUBMITTED, then ACCEPTED or REJECTED with the reason.
8. **Repeat** until 20:00, re-reading the point math each loop.

Workers run in the background and notify you when done. Do not poll and do not predict their results.

## Event mode vs isolation

Our own agents (orchestrator, ticket workers, checkers, bug and test authors, wrong-fix authors, reviewers) use every resource that helps: web search, docs, the real product's public site, any file in the repo, staff advice, other teams' public posts. Within Frist's rules, anything goes. Isolation rules (no web, canaries, locked folders, transcript audits) apply to exactly two things:
- **Difficulty probes.** A solver probe sees only what Frist's solver will see (the ticket or goal plus the broken repo or running app), or its result means nothing.
- **The environment we ship.** Hidden tests, verifier code, seed answers and reference fixes must be unreachable from inside the task (no `/@fs` exposure, no DB path in logs, no answers in git history).

Separately, the coding pipeline's **role firewall** (test author never sees the bug, wrong-fix author never sees tests or the reference) is about test strength, not secrecy; it stays on all day (frist-coding-task).

## Difficulty gate (record, do not block)

Rehearsal (Nov 14 night): on small clones (about 4,000 lines), Opus 5.5 and Fable 5.2 solved every coding and CU task we built, including two linked causes, a cause in a shared SQL helper used by 4 readers, removed logic with about 15 rules, and 20-check two-app tasks with layered corrections. Solvers read the whole backend first and grep every ticket noun. On a small clone, a solve is the normal result, not a defect.

So difficulty is a question for staff, not a gate we set:
- **Screen every candidate with one Opus run** (coding: frist-coding-task "Pipeline" step 2; CU: frist-computer-use-task step 7) and write the result on BOARD.md.
- **Submit correct, well-tested tasks even if Opus solves them.** A held task is worth 0. Calibrate from Frist's first review and staff answers.
- **Only if staff or a rejection say difficulty matters:** harden (coding: bigger clones, 8+ edits across 5+ files that a grep of the ticket's nouns does not reach, UI-heavy logic-only removals, runtime-only behavior; CU: frist-computer-use-task "Making it hard"), then probe 2 Opus + 2 Fable and aim for a mixed result.
- A 0-solve result means read the failures: ambiguity or over-fit tests get fixed before calling it hard.

## BOARD.md format

At the workspace root, updated after every merge or verdict.

```markdown
# Frist board   Score (confirmed): 0   Pending: 0   Updated: 10:42

| ID | Type | Title | Owner | Shared files | Status | Pts | Notes |
|----|------|-------|-------|--------------|--------|-----|-------|
| T-12 | ticket | Add sort by date | worker-a | none | MERGED | 10 | checker PASS 10:40 |
| C1 | clone | Clone 1 complete | - | - | 7/9 tickets | 100 | |
| CT-1 | coding | Off-by-one in pagination | bug-author-1 | none | REVIEW | 500 | screen: Opus solved 3 min |
| CU-1 | cu | Copy invoice total to chat clone | worker-d | seed | IDEA | 100 | |
```

Statuses: IDEA, RUNNING, DONE, CHECKING, MERGED, SCREENED, REVIEW, PASS, FAIL, SUBMITTED, ACCEPTED, REJECTED.

## Reviewer subagent prompt (paste and fill)

```
You are an adversarial reviewer for a Frist RL task. You did not write it and you want to find reasons it would be REJECTED. Do not fix anything. Use any resource that helps.
Task path: <path>. Task type: <coding | computer-use>. Frist template/rules: <~/Hackathons-local/frist/DISCOVERY.md section>.
Run every item of the "Pre-submit checklist" in ~/.claude/skills/<frist-coding-task | frist-computer-use-task>/SKILL.md. Execute each check yourself (run the oracle 3 times, the null attempt, the hacks or adversaries, an alternative valid fix or path; grep the prompt and every agent-visible file for leaked answers, diffs, test names or golden values). Check it matches Frist's template exactly and the problem statement is clear to someone who has never seen the code. Difficulty is recorded, not a reason to fail: report the screen result as a RISK only.
Return exactly:
VERDICT: PASS or FAIL
FAILED ITEMS: <numbered list with evidence: command run and output>
RISKS: <things that passed but feel borderline>
```

## Project submission page

Needs a **name, a one-line tagline, its story, and at least one link**. Editable until the deadline, then locked, so a missing page at 21:00 is a hard loss. Draft around noon (placeholder story plus repo link), polish at 20:00 with what happened (clones finished, tasks accepted, how the orchestrator, worker, checker and reviewer loop ran). Draft the text in chat for Justin to paste; no em dashes.

## Asking Frist staff

Ask early, ask once, write answers into DISCOVERY.md so every worker sees them. The question list is in `~/Documents/Hackathons/Frist/prep.md` ("Questions for Frist staff"); the must-ask subset is in `references/first-hour.md`. Ask again when a ticket spec is ambiguous, a ticket needs something outside the repo, or a rejection reason is vague.

## Files

- `references/first-hour.md`: 9:00 to 11:00 runbook.
- `references/non-lazy-judges.md`: principles for judges that cheaters and do-nothing agents cannot pass.
- `references/task-formats.md`: public task formats (SWE-bench, SWE-smith, Harbor, HUD, BrowserGym, OSWorld) to map onto Frist's.
- `examples/hardened_grader_example.py`, `examples/state_verifier_example.py`: tested toy judges.
- `~/Documents/Hackathons/Frist/rl-env-research.md`, `frist-intel.md`, `prep.md`: research, Frist intel, staff questions.

## Rules for Justin's session

- No em dashes in anything written for him or submitted.
- Do not send email or messages on his behalf; he submits and talks to staff unless he says otherwise.
