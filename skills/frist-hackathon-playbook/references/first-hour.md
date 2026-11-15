# First two hours: 9:00 to 11:00 (Sun Nov 15)

Follow in order. Each step names the skill section or script to use. Workspace is `~/Hackathons-local/frist/` all day (this supersedes prep.md's `~/Documents/Hackathons/Frist/work/`). No em dashes in anything written for Justin.

## 9:00 Check in, power, environment (15 min)

1. Plug in (battery was 78% the night before). Join wifi.
2. Run these and fix anything red before 10:00:
   ```bash
   mkdir -p ~/Hackathons-local/frist && cd ~/Hackathons-local/frist
   uptime; node -v; ~/.bun/bin/bun -v; python3 -c "import playwright; print('py playwright ok')"
   ls ~/Library/Caches/ms-playwright/        # note the chromium_headless_shell-* path for launch lines
   gh auth status; git --version             # Xcode license error: prefix DEVELOPER_DIR=/Library/Developer/CommandLineTools
   docker info >/dev/null 2>&1 && echo docker ok || echo "docker daemon off (open Docker.app only if a clone needs it)"
   claude --version
   ```
   `bun` is a shell function wrapper on this Mac; scripts call `~/.bun/bin/bun`. Python Playwright needs `executable_path=` pointing at the cached headless shell (`frist-computer-use-task/references/rehearsal-recipe.md` section 6).
3. Create `~/Hackathons-local/frist/<clone>/DISCOVERY.md` with headings: Event links, Staff answers, Clone 1, Task template, World. Create `BOARD.md` from the playbook "BOARD.md format".

## 9:15 Staff questions (before kickoff fills up)

Justin asks; the orchestrator writes every answer under "Staff answers" in DISCOVERY.md. Must-ask subset of `~/Documents/Hackathons/Frist/prep.md` "Questions for Frist staff":
1. How is a ticket marked done, and how is a clone judged 100% (tests, checklist, staff demo)?
2. Where and how do we submit tasks? Is there a template repo, a validator or CLI we can run locally?
3. How long does task review take, do we get rejection reasons, and can a rejected task be fixed and resubmitted? Is the 300-point AirPods count on acceptance or submission?
4. Is acceptance gated on difficulty? Which model do you measure solve rate against, and what rate do you want? (Opus 5.5 and Fable 5.2 solved every task we built in rehearsal.)
5. What are the predefined coding categories, and is there an example accepted task? Do bug-injection tasks count, or only feature tasks?
6. Can several tasks come from the same clone and feature area? May we start authoring before the clone is officially marked complete, or on a clone another team finished?
7. CU world: which apps, how is it seeded and reset, what does the verifier read and return? Are templated variants accepted as separate tasks?

Until question 4 is answered, the playbook "Difficulty gate" default holds: screen, record, submit anyway.

## 9:45 Kickoff session

Sung said "all the tips will be included in the session". Take notes on acceptance criteria, task format and tips straight into DISCOVERY.md. Get repo or portal access, rules, scoring page and submission portal links.

## 10:00 Claim clone 1 and clone it

1. Claim the first clone through Frist's process. If there is a choice, prefer the one with the most small, independent tickets and a working baseline.
2. Clone into the workspace, never `~/Documents` or `~/Desktop`:
   ```bash
   mkdir -p ~/Hackathons-local/frist/<clone1> && cd ~/Hackathons-local/frist/<clone1> && git clone <url> repo   # or gh repo clone, or unpack the provided archive
   cd <clone1> && [ -d .git ] || { git init -q && git add -A && git commit -qm base; }
   ```
3. The orchestrator session runs from `~/Agent`, so `isolation: "worktree"` will not work: create worktrees by hand (`frist-clone-tickets` section 3).

## 10:05 Discovery (one subagent, 10 to 15 min)

Dispatch one discovery subagent with: `frist-clone-tickets` section 1 checklist, plus the playbook "Workspace and discovery" bullets (task template, categories, one verbatim example, world). It also reads `frist-clone-tickets/references/frist-clone-conventions.md` and flags generator bugs it sees (blocking modal first). Output goes into DISCOVERY.md. Must include: the worktree bootstrap command, the offline Playwright launch line, port env vars, hot files, baseline test results.

While it runs: the orchestrator reads Frist's task template and example end to end.

## 10:20 Triage and BOARD.md

`frist-clone-tickets` section 2: size each ticket, list files and hot-file flags, order dependencies first, then S, M, L. Do not group tickets per worker (own-file layout merged with 0 conflicts in the dry run). One integrator worker for anything needing a dependency or migration.

## 10:25 Dispatch the first ticket batch

1. `uptime`: 1-minute load under 12 (playbook "The orchestrator loop" step 3).
2. Per ticket: `git worktree add ../wt/<ID> -b <ID>` from the clone, then the bootstrap command from DISCOVERY.md (`cp -cR <clone>/node_modules ../wt/<ID>/`).
3. Fill `frist-clone-tickets` "Worker prompt template", paste the own-file layout block (section 3) with real file names, give each worker its own port pair (3101/3102, 3111/3112, ...).
4. Launch 3 workers in one message (room for the catalog and harness agents below; 5 total at most). Default model.

## 10:30 to 11:00 Check and merge as workers report

For each DONE: `frist-clone-tickets` "Acceptance checker prompt" (fresh agent, ticket text only, one browser at a time), then section 4 merge snippet (diff3 merge plus perl resolver), then typecheck, suite and build on main, then BOARD.md. Refill the freed slot with the next ticket. Check `uptime` before each launch; drop to 2 workers if load climbs.

## 10:40 Start the coding pipeline in parallel

As soon as DISCOVERY.md has the task template and categories, launch (they count toward the 5-worker cap):
- `frist-coding-task/references/role-prompts.md` 0a (catalog agent) on a disposable copy of clone 1 main.
- `role-prompts.md` 0b (harness agent).

## 10:55 First coding-task screen

Goal: learn early how hard our tasks are on Frist's clone, before the afternoon pipeline.
1. Pick the catalog's top site in a feature area no open ticket touches.
2. Bug author (`role-prompts.md` 1) on clone 1 main as of now, in `~/Hackathons-local/frist/<clone>/roles/ct-1/bug/`.
3. Opus screen: `frist-coding-task/SKILL.md` "Pipeline" step 2 (headless `claude -p --model claude-opus-5-5` in a solver sandbox, `screen_check.sh`, then `scripts/isolation_check.py --no-network` on its transcript).
4. Record "screen: ..." on BOARD.md. It does not block anything.
5. If staff said tasks need a finished clone (question 6), this task is rebuilt on final main when clone 1 is complete: re-apply the bug author's change (`git apply -R solution.patch` on a copy of final main), rerun `screen_check.sh`, then continue the pipeline.

## 11:00 Checkpoint

BOARD.md summary line to Justin: tickets merged, tickets running, load, staff answers still missing, screen result. Then continue the playbook loop toward "clone 1 at 100% by 13:00".
