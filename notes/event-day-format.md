# What the real event looks like (Nov 15, learned live)

The rehearsal assumed we would clone repos locally. The real event runs everything in Frist's cloud workspaces. This file is the corrected picture.

## Kickoff rules
- Goal stated by Frist: tasks a frontier model "can't solve without a hint, and with hints, it's able to solve it". Build "an end to end reinforcement learning environment" for coding or computer use.
- Leaderboard counts tasks accepted by the platform. Instructions and a memo live inside the platform. Help desk on site.

## Portal
- Hackathon portal: gt.fristai.dev (Leaderboard, CUA, Worlds, Coding). Worlds unlock "with your first golden"; Coding unlocks after 1 finished clone OR 10 tickets.
- app.fristai.dev/polish/queue is Frist's internal polisher queue ("Frist Fidelity"); it was not the hackathon's claim flow and claims there were forbidden.

## Clone tickets ("Frist Video Game")
- Pick ONE site (you can hold 1). Its open tickets become claimable under "Find more issues". Sites show open ticket counts (Hertz 73, Warby Parker 54, Coach 23, SoundCloud 16 ... some have 1).
- You may also be handed tickets from other sites (we got Expedia, Calendly, PCPartPicker).
- Tickets are phased: "Phase 1 of 3 · Features", "Phase 2 of 3 · Stitch".
- A ticket untouched for 30 minutes returns to the Ticket Pool (with its saved work).
- Each ticket opens a cloud workspace (about 1 minute to allocate, longer at kickoff rush) with: the clone and the reference crawl side by side, a terminal with Claude Code, and tools: Claude, Gemini Visual, Task verification, Replay Actions, Steps, Replay, Captures, Pick, Names, Files. CLI: `frist verify --preview`.
- Ticket text is written in terms of recorded actions (e.g. 058 to 070) and numbered builder states (26 to 39), with acceptance criteria per state transition.
- Grading needs "tracked state" to report the truth (dialog open/closed, selected format...), not just the DOM.
- Recorded trigger texts can be misleading ("remove X" was really an export-dialog click). Trust the recorded AFTER consequences.
- Finish with "Submit repair" (reconciliation).

## Coding tasks (500 each)
Condensed guide: [CODING-GUIDE.md](CODING-GUIDE.md). Key points:
- Board = clones x shapes (Resilience, Concurrency, AuthZ, Schema migrations, Long-horizon, Visual and interaction bugs, Full-stack bugs, Performance regressions, Propose other). Clones at kickoff: Amazon, BambooHR, DocuSign, Google Sheets, HubSpot, Jira, Photopea, Realtor, Zappos.
- Package: ticket (Context, AC1..n, Pins), hidden tests, reference solution, one mutation per AC. `bun checks/gate.ts <clone>/<id>` must be GREEN.
- TaskCheck takes 1 to 3 hours: controls, mutations, tests-match-ticket, 5 frontier models x 3 attempts (too easy if top two mostly solve), shortcut attempts, unfair-failure review. Then an engineer reviews.
- Limits: 4 claims, 4 running checks, 4 awaiting review. Claim lost after 1 hour with no scaffold.
- Our split-role pipeline maps directly: bug/feature author -> reference; ticket-only test author -> hidden tests; wrong-fix author -> mutations.

## Lessons
- Recon of candidate sites before kickoff was wasted: the site list only appeared in the portal. Next time, wait for the portal.
- Plan for cloud workspaces: the orchestrator's job becomes writing prompts for the workspace's Claude Code, not running local worktrees.
- Staff said TaskCheck's top two models are Opus 5.5 and "Astra".
