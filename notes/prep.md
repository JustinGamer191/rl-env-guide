# Frist hackathon prep (Sun Nov 15, 10am to 9pm, Atlanta)

Step-by-step for 9:00 to 11:00 lives in the playbook skill: references/first-hour.md (it wins if anything here disagrees).

Skills ready in Claude Code: `frist-hackathon-playbook` (start here), `frist-clone-tickets`, `frist-coding-task`, `frist-computer-use-task`. Background: `rl-env-research.md`, `frist-intel.md` in this folder.

## Tonight

Checked on this Mac Nov 14:

| Tool | Status |
|---|---|
| Node | v22.22.2, npm 10.9.7: ok |
| Python | 3.12.9 (miniforge), Python Playwright importable: ok |
| uv / bun | uv 0.11.2, bun 1.3.11: ok (Bun is what Frist's published clones use: `bun dev.mjs`, `bun test`) |
| git | 2.54.0, global name/email set: ok |
| gh | logged in as JustinGamer191: ok |
| Claude Code | 2.1.283: ok (login expired once today; re-check) |
| Codex CLI | 0.169.0: ok |
| Docker | 29.6.1 installed, **daemon not running** |
| Playwright (Node) | **no global CLI**; npx would download playwright 1.65.1. Cached browser: chromium_headless_shell-1243 only |
| pnpm | **missing** |
| SSH key | **none in ~/.ssh** (HTTPS via gh works) |
| Disk | 315 GB free: ok |
| Battery | 78% and discharging when checked |

To do tonight:
- [ ] Open Docker.app once so the daemon starts; run `docker run --rm hello-world`.
- [ ] Warm Playwright: `npx -y playwright@latest install chromium` (gets the full Chromium, not just headless shell).
- [ ] Decide on pnpm: `corepack enable` (ships with Node 22) makes pnpm/yarn available if a clone uses them.
- [ ] `gh auth setup-git` so git over HTTPS uses gh, since there is no SSH key.
- [ ] `claude` then `/login` if prompted; confirm `/mcp` shows what you need. Same for `codex login`.
- [ ] Skim Frist's own material (15 min): one sample run (https://frist.ai/samples/opentable-photos-opus-5-5-r1.json) to see a real ticket and grading, and the clone repair guide (`human-guide.html` in https://github.com/runfrist/gh-pages-homepage). Key points are in `frist-intel.md`.
- [ ] Laptop charger, phone charger, extension cord or power strip. Charge to 100%.
- [ ] Make a workspace: `~/Hackathons-local/frist/` (NOT under ~/Documents: iCloud breaks node_modules there).
- [ ] Sleep. The event is 11 hours.

## First 30 minutes tomorrow

1. **10:00** Get repo/clone access, rules, scoring page, submission portal. Write team name and links into `~/Hackathons-local/frist/DISCOVERY.md`.
2. **10:05** Ask staff the questions below; write answers into DISCOVERY.md.
3. **10:10** Start Claude Code in `~/Hackathons-local/frist/`, say "Frist kickoff" so the playbook loads. It runs discovery: install, run, test, lint, build the clone, list tickets, find Frist's task template and categories, list shared hot files.
4. **10:20** Orchestrator creates `BOARD.md`, triages tickets by size, dispatches 3 to 5 ticket workers in worktrees.
5. **10:30** While workers run: read Frist's task template and one example task end to end so coding-task workers can start the moment the clone is done.

## Questions for Frist staff

Submission and scoring
- Exactly how is a ticket marked done, and how is a clone judged 100%? Tests, checklist, or a staff demo?
- Where and how do we submit tasks? Is there a template repo, a validator or CLI we can run locally?
- Who reviews tasks and how long does acceptance take? Do we get rejection reasons? Can a rejected task be fixed and resubmitted?
- Is the leaderboard live? When is the 300-point AirPods cutoff counted (on acceptance or submission)?

Coding tasks (500)
- What are the predefined categories? Is there an example accepted task?
- Is task acceptance gated on difficulty? Which model do you measure solve rate against, and what rate do you want? (Opus 5.5 and Fable 5.2 solved every task we built in rehearsal in 1 to 4 min.)
- Must a coding ticket list every fact the tests check, or can it be short (like your OpenTable task) while hidden tests check details visible only on the working site, such as empty-field wording, list caps and zero-state text? And will a task frontier models solve in about 5 minutes still be accepted? (Overnight: with a fair short ticket Opus still solved in 5 min; it only "failed" on details it had to guess. So this answer decides how hard our tasks can be.)
- Teams of 2: do both teammates' points combine on the leaderboard, and are prizes per person (two flights and two Ray-Bans for a winning pair) or one per team? Does each person still need to finish their own app before pairing?
- Required pieces: problem statement, hidden tests, reference solution, docker image? Test framework constraints?
- Do bug-injection tasks count, or only feature tasks? Any minimum difficulty (for example a model must fail it)?
- Can multiple tasks come from the same clone and the same feature area? From a clone another team finished?

Computer-use tasks (100)
- Which apps make up the world, and how is it seeded and reset?
- What does the verifier read (DB, API, provided helper) and what does it return (binary, partial credit)?
- Are templated variants of one task accepted as separate tasks?

Logistics
- (Answered: multiple clones at once, no limit.) How long does task acceptance review take? Anything submitted too late to be reviewed by 9pm is worth 0.
- Any rules on which AI tools or models may be used, or on running agents against Frist's infrastructure?
- Wifi, power, and the hard stop time for submissions.
