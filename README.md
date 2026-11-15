# Frist hackathon playbook

Skills, scripts and notes for the Frist RL hackathon (Sun Nov 15 2026, computer use and coding track). Built and rehearsed on Nov 14 against real open-source apps and a clone generated from recordings.

## What's here

- `skills/frist-hackathon-playbook/`: the day plan and orchestrator loop. Start here.
- `skills/frist-clone-tickets/`: finishing clone tickets with parallel workers, an independent acceptance checker, and the own-file merge layout.
- `skills/frist-coding-task/`: 500-point coding tasks. Split roles (bug author, test author, wrong-fix author, checker), `scripts/verify_task.sh`, `scripts/mutation_bar.py`, `scripts/isolation_check.py`.
- `skills/frist-computer-use-task/`: 100-point computer-use tasks with fail-closed state verifiers and adversary runs.
- `notes/`: what we know about Frist, the prep checklist and questions for staff, and the RL environment research.

## Install (Claude Code)

```bash
git clone <this repo> ~/frist-playbook
mkdir -p ~/.claude/skills
cp -R ~/frist-playbook/skills/* ~/.claude/skills/
```

Restart Claude Code. The skills load automatically when you mention Frist, clone tickets, coding tasks or computer-use tasks. To update later: `git pull`, then copy again.

## Using Codex instead

Codex does not load skills automatically. Point it at the files: start with `skills/frist-hackathon-playbook/SKILL.md` and tell it to follow the sections it routes to. `AGENTS.md` in this repo does that for you if you run Codex from this folder.

## Things that bit us in rehearsal

- Clone repos outside iCloud-synced folders (`~/Documents`, `~/Desktop`).
- On a laptop, keep 3 to 5 workers at most and watch `uptime`; six rehearsals at once nearly crashed an M5.
- A worker saying DONE is a claim. A fresh checker that sees only the ticket decides.
- Opus 5.5 and Fable 5.2 solved every task we built on small clones. Ask staff whether acceptance depends on difficulty before spending time hardening.
