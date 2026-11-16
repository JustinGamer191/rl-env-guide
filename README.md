# RL environment guide

A guide and Claude Code toolkit for building reinforcement-learning environments and graded tasks: finishing an app or app clone to build on, coding tasks with hidden tests, and computer-use tasks with a state verifier. One Claude Code session acts as the orchestrator, parallel worker agents do the building in their own worktrees, and nobody grades their own work.

## What an RL task is

A task is five things:

| Piece | Coding task | Computer-use task |
|---|---|---|
| Prompt | A ticket that describes the symptom or feature, never the cause | A goal a user would write, naming each target uniquely |
| Initial state and reset | A repo with a planted bug or a removed feature | An app world with seeded data and a reset that restores it |
| Grader the agent cannot see | Hidden tests overlaid only at grading time | A verifier that reads backend state |
| Reference solution | A patch that restores the working app | A scripted run through the UI |
| Metadata | Category, difficulty | Apps involved, difficulty |

The reward is only useful if it is trustworthy: the reference scores 1, doing nothing scores 0, cheating scores 0, every valid solution scores 1, and the result is the same on every run. Most of this guide is about making that true and proving it.

## The pipeline

![How the pipeline runs](docs/img/pipeline.svg)

1. **Finish the base app.** Ticket workers each take one ticket in their own git worktree. A fresh checker that sees only the ticket text decides whether it is done. Each passing branch merges right away.
2. **Build tasks on it.** For a coding task, a bug author plants the bug and writes the ticket, a test author writes hidden tests from the ticket and the working original only, a wrong-fix author writes plausible wrong fixes without seeing the tests, and a checker runs the scripts. Computer-use tasks follow the same split: verifier, oracle, adversarial agents.
3. **Review and probe.** A fresh reviewer that wrote nothing runs the checklist. An isolated solver probe measures difficulty.

## Lessons

These come from our tests on open-source apps and on a clone we generated from screen recordings.

1. **Split roles so nobody grades their own work.** Agents write weak tests and then pass them. With the test author kept away from the bug and a separate author writing wrong fixes, the hidden tests caught far more wrong fixes:

   ![Wrong fixes caught](docs/img/wrong-fixes-caught.svg)

2. **Use a mutation bar with one mutation per acceptance criterion.** Each criterion gets at least one wrong version that breaks only that criterion, and the tests must catch it. Auto mutants near the fix must be 80% or more killed.
3. **Run controls.** The empty change scores 0 and the reference scores 1, three runs in a row from a clean copy. The empty change must fail on an assertion, not a crash.
4. **Test only what the ticket states.** A test that checks a fact the solver had to guess is an ambiguity bug, not difficulty.
5. **Keep hidden tests and answers out of reach.** Nothing in the shipped repo, its git history, backup files, logs, seed data or anything the app serves (a Vite dev server serves its root over `/@fs/`).
6. **Shortcut and reward-hack attempts score 0.** Deleted tests, skip-all configs, hardcoded examples, constant stubs and fake runners all fail.
7. **Probe difficulty in isolation and aim for a mixed pass rate.** The probe solver sees only what the real solver sees, and its transcript is audited. Training tasks are most useful when the top model passes about 1 of 3 attempts. In our tests every fair hardening lever we tried on its own (a 160k-line app, an 8-step dependent chain, browser-only state, a tempting template, terse tickets, screenshot-only control) was still solved by Opus 5.5 in 2 to 7 minutes. What is left: many compounding decisions, outcome-only tickets, invariants across every write path, and facts spread across many pages.
8. **Computer-use verifiers fail closed.** Every intended change is a required assertion, the whole relevant state is diffed against seed plus that change, and the agent's report text is never evidence. In our tests, verifiers that accepted a new record "if present" scored do-nothing runs as 1 on 2 of 5 tasks.
9. **Workers finish tickets in one shot if a separate checker decides.** One worker labeled a button "8 pts" when the ticket said "8", checked its own work with a loose match, and reported done. Workers now find controls by the ticket's exact words, and a fresh checker signs off before anything merges.

   ![Clone tickets finished in one shot](docs/img/clone-one-shot.svg)

10. **Merging is the bottleneck on generated clones.** Every ticket touches the same shared files. Putting each ticket's code in its own file and adding one line to the shared files cut hand-fixed merge conflicts from 4 to 1, and a one-line resolver handles the rest.
11. **Respect machine limits.** On a 10-core laptop, run 3 to 5 workers at most and keep the 1-minute load under 12. Nine helpers plus four mutation bars pushed load to 60 to 100 and nearly crashed the machine. Never kill dev servers by name (`pkill -f`); it takes down every other worker's server too.

## What's in the repo

| Path | What it is |
|---|---|
| `skills/rl-env-playbook/` | The orchestrator loop, the lessons, difficulty data, judge design and public task formats. Start here. |
| `skills/rl-clone-tickets/` | Finishing an app or clone: worker prompt, acceptance checker prompt, own-file merge layout and resolver. |
| `skills/rl-coding-task/` | Coding tasks: role prompts, `verify_task.sh`, `mutation_bar.py`, `isolation_check.py`. |
| `skills/rl-computer-use-task/` | Computer-use tasks: fail-closed state verifiers, oracle and adversary runs, screenshot-only probes, tested example harnesses. |
| `tools/practice-clone-kit/` | Record a local app, generate a clone from the recordings, grade workers with hidden journeys. For practice runs. |
| `tools/merge/` | Merge helpers for the own-file layout. |
| `notes/rl-env-research.md` | Survey of RL environments for computer-use and coding agents, with sources. |

## Install

Claude Code:

```bash
git clone https://github.com/JustinGamer191/rl-env-guide ~/rl-env-guide
mkdir -p ~/.claude/skills
cp -R ~/rl-env-guide/skills/* ~/.claude/skills/
```

Restart Claude Code. The skills load when you ask to build an RL environment, make a coding task with hidden tests, build a computer-use task with a state verifier, finish an app clone for training, or harden a task. To update: `git pull` and copy again.

Codex: run it from this folder. `AGENTS.md` tells it to start from the playbook skill.

## Setup notes

- Keep the workspace out of iCloud-synced folders like `~/Documents`; they break `node_modules`.
- Use a real charger. A 15 W USB brick drained the battery while "charging".
- Run installs, builds, tests and probes under `nice -n 15`.
