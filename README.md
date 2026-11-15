# Frist hackathon playbook

How we plan to run the Frist RL hackathon (Sun Nov 15 2026, computer use and coding track): one Claude Code session as the orchestrator, parallel worker agents in git worktrees, and a rule that nobody grades their own work.

Everything here was rehearsed on Nov 14 on real open-source apps and on a clone we generated from screen recordings, the same way Frist builds theirs. The numbers below come from those runs.

![How the day runs](docs/img/pipeline.svg)

## About the event

Frist builds reinforcement learning environments. At the hackathon, each person picks an app clone that is about 80% done and finishes it, then builds training tasks on top of it.

| Work | Points |
|---|---|
| One clone ticket | 10 |
| One finished clone | 100 |
| One accepted computer-use task | 100 |
| One accepted coding task | 500 |

Coding tasks dominate the leaderboard, so the plan is: finish the first clone fast, then turn it into coding tasks all afternoon. A coding task is a planted bug, a ticket that describes only the symptom, and hidden tests that pass the real fix and fail fake ones.

## What rehearsal taught us

**Agents write weak tests and pass their own bad tests.** The fix is to split the job: one agent plants the bug, a second writes tests from the ticket and the working original only, a third writes plausible wrong fixes without seeing the tests, and a checker requires the tests to fail every wrong fix.

![Wrong fixes caught](docs/img/wrong-fixes-caught.svg)

**Workers finish tickets in one shot, if a separate checker decides.** One worker labeled a button "8 pts" when the ticket said "8", checked its own work with a loose match, and reported done. Workers now find controls by the ticket's exact words, and a fresh checker that sees only the ticket signs off before anything merges.

![Clone tickets finished in one shot](docs/img/clone-one-shot.svg)

**Merging is the real bottleneck on generated clones.** Every ticket touches the same shared files. Putting each ticket's code in its own file and adding one line to the shared files cut hand-fixed merge conflicts from 4 to 1, and a one-line resolver handles the rest.

**Small clones are easy for frontier models.** Opus 5.5 and Fable 5.2 solved every task we built, including linked bugs and 20-check computer-use tasks, usually in 1 to 4 minutes. So we ask Frist staff early whether acceptance depends on difficulty, and we do not hold back a correct task just because Opus solved it.

## What's in the repo

| Path | What it is |
|---|---|
| `skills/frist-hackathon-playbook/` | The day plan and orchestrator loop. Start with `references/first-hour.md`. |
| `skills/frist-clone-tickets/` | Finishing tickets: worker prompt, acceptance checker prompt, merge layout and resolver. |
| `skills/frist-coding-task/` | 500-point tasks: role prompts, `verify_task.sh`, `mutation_bar.py`, `isolation_check.py`. |
| `skills/frist-computer-use-task/` | 100-point tasks: fail-closed state verifiers, oracle and adversary runs, tested example harnesses. |
| `tools/practice-clone-kit/` | Record a local app, generate a clone from the recordings, grade workers with hidden journeys. For practice runs. |
| `tools/merge/` | The merge helpers from the merge-strategy test. |
| `notes/` | Frist research, the prep checklist with questions for staff, and the RL environment survey. |

## Install

Claude Code:

```bash
git clone https://github.com/JustinGamer191/frist-playbook ~/frist-playbook
mkdir -p ~/.claude/skills
cp -R ~/frist-playbook/skills/* ~/.claude/skills/
```

Restart Claude Code and say "Frist kickoff". The skills also load on their own when you mention clone tickets, coding tasks or computer-use tasks. To update: `git pull` and copy again.

Codex: run it from this folder. `AGENTS.md` tells it to start from the playbook skill.

## Gotchas

- Clone Frist repos into `~/Hackathons-local/frist/`, not an iCloud-synced folder like `~/Documents`.
- On a laptop, run 3 to 5 workers at most and keep the 1-minute load under 12. Six rehearsals at once nearly crashed an M5.
- Use a real charger. A 15 W USB brick drained the battery while "charging".
- Never kill dev servers by name (`pkill -f`); it takes down every other worker's server too.
