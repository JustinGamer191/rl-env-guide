# Frist intel (researched Sat Nov 14 2026)

Tags: [VERIFIED] = seen on a source page. [INFERRED] = my reasoning, not stated anywhere.

Key sources:
- Site: https://frist.ai (React SPA; all blog text is bundled in https://frist.ai/assets/index-B8qLCGFE.js, fetched Nov 14 2026)
- Public sample trajectories with full ticket prompts: https://frist.ai/samples/opentable-photos-opus-5-5-r1.json, https://frist.ai/samples/opentable-photos-grok-4-6-r2.json, https://frist.ai/samples/zappos-display-map-gpt-6-astra-r3.json
- Clone repair guide: https://frist.ai/human-guide.html (source repo https://github.com/runfrist/gh-pages-homepage, file human-guide.html, committed May 31 2026)

## Company

- Tagline: "Reinforcement learning environments at internet scale for computer use and coding." Legal name in footer: "Concierge Technologies, Inc. © 2026". https://frist.ai [VERIFIED]
- Self description: "Our reinforcement learning (RL) environments are high-fidelity replicas of real software, where agents are trained and evaluated on economically valuable work." Every app is a "pixel-perfect clone with high DOM fidelity". https://frist.ai/blog/frist-medpractice (Nov 6 2026) [VERIFIED]
- Founders: Sung Ho Choi (@choisungho) and Jeung Park (@jeungfocus). X account https://x.com/FristResearch (6 followers when found Nov 10). Source: frontrun newsletter, Nov 13 2026, https://frontrunvc.substack.com/p/001-frontrun-open-source-deal-flow [VERIFIED]
- Careers: two roles, both New York: "Member of Technical Staff" (Engineering) and "Strategic Projects Lead" (Operations). Apply via careers@frist.ai. MTS duties include "Write rubrics and reward functions that grade multi-step computer workflows" and "Create synthetic data pipelines that turn a handful of human demonstrations into thousands of training-grade trajectories". https://frist.ai/careers [VERIFIED]
- Contacts on blog: research@frist.ai, jeung@frist.ai. https://frist.ai/blog [VERIFIED]
- GitHub org: https://github.com/runfrist ("Browser use agents and workflow automations", blog frist.ai, created Jan 19 2026). Repos: gh-pages-homepage, a fork of PrimeIntellect-ai/prime-rl (last push Jun 29 2026), a fork of openclaw-railway-template. Commits by "Sung" (sung@frist.ai). [VERIFIED]
- Hugging Face: https://huggingface.co/frist-research, one dataset `frist-research/osworld_pro_file_cache` (Jan 2 2026, Apache 2.0). [VERIFIED]
- Training stack: "GRPO with an IPO loss on Prime-RL"; JetBlue post used SFT grounding then GRPO full parameter fine tuning. https://frist.ai/blog/frist-qwen-medpractice (Nov 11 2026), https://frist.ai/blog/improving-qwen3-8-27b-grpo-frist-jetblue-vs-webinfinity (Oct 13 2026) [VERIFIED]
- Funding, YC batch, investors: nothing found. [VERIFIED absence]
- Unrelated namesakes to ignore: frist.dev (Webflow agency, Jared Foy), frist.com (parked), frist.co (lander), usefrist.com (Squarespace placeholder), sareyalcinkaya/fihrist "Frist.ai programme management" (Vienna). [VERIFIED]

### Blog posts (all on https://frist.ai/blog)
1. Oct 13 2026, "Improving Qwen3.8-27B using GRPO - Frist JetBlue vs WebInfinity": three JetBlue clones of rising fidelity (JB1, JB2, ...); live-site accuracy 2x, 2.75x, 4x over base across 32 bookings. [VERIFIED]
2. Oct 17 2026, "FristWorld: A synthetic internet for evaluating computer use agents": six clones (Air Canada, Michaels, Nordstrom, OpenTable, Realtor.com, Zappos), 31 tasks, 8 agents x 3 runs; best GPT-6 Astra 59.1%; "when models said they were done, 57% of the time they had failed". [VERIFIED]
3. Oct 23 2026, "Interactive Debugging Environments: Green Tests, Broken Apps": coding tasks (tickets) made by removing a feature or planting a bug in a working clone. 14 audited tasks on four clones (opentable-v3, nordstrom, aircanada-v3, zappos). [VERIFIED]
4. Nov 6 2026, "Frist MedPractice: An enterprise world for accounts payable agents": clones of NetSuite, Bill.com, Gmail, Google Sheets; 14 long-horizon AP tasks; best 35.7%; built with NewtonX expert network. [VERIFIED]
5. Nov 11 2026, "How synthetic tasks tripled Qwen3.8-27B's pass rate": 100 synthetic task variations via rejection sampling, 86 train / 14 held out; 3 to 10 tasks passed. [VERIFIED]

## People

Confirmed at Frist:
- Sung Ho Choi: cofounder (frontrun newsletter). Commits to runfrist repos as sung@frist.ai; the human guide was formatted from "/Users/sung/Downloads/human-guide.md". [VERIFIED]
- Jeung Park: cofounder (frontrun newsletter); jeung@frist.ai listed as contact on JetBlue post. [VERIFIED]
- Remm Brofman: careers page says "You will join forces with Remm as a founding member of the operations team". https://frist.ai/careers [VERIFIED]
- Michael Zhou: a LinkedIn search result is titled "Michael Zhou - Frist" (https://www.linkedin.com/in/michael-zhou-98a27521b/). Page itself blocked (HTTP 999), so role and school unconfirmed. [VERIFIED title only]

Names on blog post bylines/photos (image files in the bundle, so likely authors, but roles not stated) [INFERRED that they are staff or authors]:
- JetBlue post: Jeung Park, Sung Ho Choi, Joannier Pinales
- FristWorld post: Shaheer Aslam
- Debugging (coding tasks) post: Annie Hua, Jay Dey
- MedPractice post: Kevin Su, Nathan Gerevits, Remm Brofman, Shaheer Aslam (one of these may be the NewtonX accounting expert, the post profiles an outside expert)
- Qwen MedPractice post: Joannier Pinales, Remm Brofman
- Also in the bundle: Jonathan Beltran (context unclear)

Not confirmed: Arpit Ramani and Krishna Bhatnagar. Searches pairing them with Frist found nothing; not in the frist.ai bundle. Do not assume they work there.

## Past events

- No public record found of any past Frist hackathon, at any school or city (searched luma, partiful, Devpost, HackPrinceton sponsor list, general web). The Nov 15 Atlanta event may be their first public one, or past ones were invite-only. [VERIFIED absence; INFERRED explanation]
- No recaps, winners, or point totals found anywhere.

## Event format details

From the brief (not found publicly): tickets 10 pts, full clone 100, computer-use task accepted 100, coding RL task accepted 500, first 20 teams to 300 pts get AirPods.

What Frist's own published work says these deliverables look like:

### Clone tickets (finishing clones)
- Clones come from an automated pipeline: "records a video of a real website, decomposes the DOM into snapshots, and assembles those snapshots into React components." https://frist.ai/human-guide.html [VERIFIED]
- Predictable pipeline bugs to expect in an "80% complete" clone [VERIFIED, same source]:
  - Only the recorded click path works; uncaptured components keep `display: none`; "nothing has click handlers".
  - `{state >= N && state < M}` numeric guards are compression artifacts; replace with semantic booleans.
  - Lists split into one file per item, all templated from the first item ("every country shows the same flag"): the "same-list bug". Always scan siblings.
  - Missing global `:root` CSS block, so `var(--brand-...)` tokens resolve to nothing.
  - Frozen calendars/carousels made of many snapshot files; duplicate rendering when two snapshots overlap.
  - Blocking modal must be fixed first ("nothing else works until it's dismissed").
  - Buttons that refresh the page: form default, use preventDefault or type=button.
- Prescribed repair order: Build, Orient, Gate (modal), Mechanics before wiring, Domain context, Cross-cutting lift. [VERIFIED]
- Domain context: name it after the category (`BookingContext` for travel, `ShoppingContext` for e-commerce). Every interaction "carries a tracking obligation: not just make the dropdown open but make it open and track that it opened so the oracle can verify." At the end, replace `useEffect`s with `useWindowAPIs` (window APIs). Reference goldens: JetBlue `BookingContext.tsx`, `useWindowAPIs.ts`, `usePageStore.tsx`. [VERIFIED]
- Evidence sources Frist's internal workflow uses: `step-NN-snapshot.html` (grep by rrweb ID), `step-NN.png` screenshots, raw rrweb data in `traces/primary/events/`, `goldens/clones/`, `references/repair-playbook/`, a `REPAIR-LOG.md`, and Claude skills `/diagnose`, `/watch` (video to Gemini), `/context`, `/wire`. Fixes "must come exactly from a video skeleton", never invented class names. [VERIFIED; whether hackathon repos include these files is unknown]
- Their internal Aer Lingus repair took about 4.5 hours over 7 pages (home page ~1.5h, other pages 30 to 50 min each). [VERIFIED]

### Computer-use tasks (multi-app world)
- FristWorld: "Each of the six applications runs its own backend, and a world ledger sits across all of them to track states and event log. With this visibility, we can deterministically check that a flight booking on Air Canada, a dress purchase on Nordstrom and shoes from Zappos all fall under the task's budget." https://frist.ai/blog/frist-world-benchmark [VERIFIED]
- Clones run offline (no CAPTCHAs, rate limits, real purchases). [VERIFIED]
- Agent ends with `report_complete('...')` or `report_infeasible('...')`. [VERIFIED, sample trajectories in the FristWorld post]
- Example task text (full): Air Canada one-way flight arriving by 1 PM with aisle seat on every leg, traveller details, stop at payment page without paying; Nordstrom black dress size M in bag; Zappos pink running shoes size 8 B in bag; total budget $365; "Leave only the dress in the Nordstrom bag... Do not start checkout". Checks named: "allowed flight, aisle seat, traveller details, no booking", bag contents. The task has exactly one feasible flight+fare (00:30 one-stop on Flex, $253.41), found by "the task's audit". [VERIFIED]
- Task style: one-line titles with a hidden constraint that forces reasoning, e.g. "Find the Brookline three-bedroom home with the lowest monthly payment, not the lowest price", "Count every women's running shoe with a black upper and white midsole across all results", "Save a new-construction Cambridge home under $1M as a guest, stopping at sign-in". Mix of single-site and multi-site. [VERIFIED]
- MedPractice verifier style: many atomic state checks against final app state, e.g. "In Bill, invoice GCR-91207 ($2,439.00) has nothing paid and nothing scheduled and has at least one note; in NetSuite, bill GCR-91207 is on file once with Payment Hold ticked". Note-content checks are semantic ("a note ... says it is a duplicate of an invoice already paid"). Seed data deliberately includes traps: duplicates, overcharges, wrong approvers, pending credits, partial receipts. "Each task has an answer that AP experts universally agree is correct." "The tasks give no hints about the solution." [VERIFIED]
- Reward: pass verifier = 1.0; partial credit per business outcome only when all its checks pass; undoing finished work lowers score; incomplete capped at 0.99; each invalid tool call -0.01 up to -0.20. Difficulty by check count: easy 8 or fewer, medium 9 to 19, hard 20+. [VERIFIED, Qwen MedPractice post]
- Synthetic variant example: "Create a journal entry dated January 31, 2026, for Northfield Health Partners, with memo 'Reclass.' Debit 1,000 to Medical Supplies Expense and credit 1,000 to Phone and Internet Expense." Variants are built from "our catalog of verifiers". [VERIFIED]
- Harness: "standard desktop CUA harness", up to 400 model calls per task. [VERIFIED]

### Coding RL tasks
- Method: "built with a ProgramDistill-inspired approach: we remove a feature from, or plant a bug in, a working app." Tickets "resemble tickets a mid-level software engineer would typically handle". https://frist.ai/blog/interactive-debugging-environments (Oct 23 2026) [VERIFIED]
- Two ticket types seen: `feature` and `bug`. Feature ticket header has Page, Type, Size (e.g. M). [VERIFIED]
- Agent gets: the ticket ("stating the expected behavior and every value the checks look for, without naming files or the cause"), the codebase "with no git history or internet", a browser plus design screenshots, shell/editor/search/sub-agents, 90 minutes. [VERIFIED]
- Grading: "The ticket's user journeys replay in a browser on held-out inputs, regression journeys cover the rest of the app, and the tests expect the app's existing components and labels. Grading is deterministic: the original code passes every task and the broken app fails it." Example counts: 2 feature journeys + 27 regression journeys; another task compares 155 facts from browser journeys and backend API calls. [VERIFIED]
- Rubric criteria they score: Feature works, No regressions, Fits the codebase (no dropping existing names/labels/fallbacks), Tests its work, Reports truthfully, Consistent (pass all 3 rounds). [VERIFIED]
- Ticket template (verbatim structure from the OpenTable sample): `# <title>`, `**Page:** <route> · **Type:** feature · **Size:** M`, `## Description`, `## Requested behavior` (bullets), `## Acceptance criteria` (checkbox bullets each with an "e.g." naming a concrete UI label like "Photos"), then run instructions ("Start the dev server with `bun dev.mjs` (http://127.0.0.1:5173...). Chromium and Playwright are installed."). The Zappos bug ticket is written as a customer report with repro steps, an "**Expected (as shown in `design/`):**" section, explicit formatting rules, "This must hold for every shoe, colour and quantity", and a "## Your environment" section. [VERIFIED]
- Their headline finding: models fail by breaking neighboring functionality or claiming success falsely (84% of failed rounds claimed success); only Opus 5.5 reliable (86%). [VERIFIED]

## Tooling/submission format

- Clone tech stack seen in trajectories [VERIFIED, sample JSONs]:
  - Bun runtime (`bun dev.mjs`, `bun test`, `bun run rubric`, `bun.lock`).
  - Frontend: React + TypeScript + Vite (vite HMR logs), React Router style `route-table.json`, many generated component files like `addition-step1-85--restaurant-card-v0.tsx` with sibling `.data.json` "slots" files, `data-test`/`data-testid` attributes, Tailwind classes on Zappos.
  - Backend: `.mjs` server (`backend.mjs`, `server.mjs`, `api-spec.json`, `domain-model-v1.json`, `seed-plan-v1.json`) with Prisma generated client; models include `WorldState`, `WorldEvent`, `AuditLog`, `RuntimeWorld`. Fresh database per run in a temp folder; fixed clock via `CLOCK_FIXED_TIME` ("The app's data is dated 2026-09-15").
  - OpenTable layout: `/work/backend`, `/work/frontend`, `/work/dev.mjs`, ports 5173 (frontend) and 3001 (backend).
  - Zappos layout: `/work/app/frontend/web/src`, `/work/app/backend/api`, `/work/design/` (screenshots plus each screen's text), helper `/opt/agent-tools/site restart|status|logs`, site on http://localhost:8080, Playwright in `/opt/agent-tools/node_modules`.
  - Eval harness appears to be opencode (`/tmp/opencode/` paths, `todowrite` tool). [INFERRED from paths]
- Internal app URL pattern: `https://app.fristai.dev/polish/coding-debugging-lab/<task-id>` and `.../coding-evals/<task-id>/<model>/R1`. Task IDs look like `pl-d2-view-grill-23-photos-logic-hd`, `zp-display-map-v2`. [VERIFIED URLs; content behind login, not fetched]
- Actual hackathon submission format (portal, task JSON schema, review SLA): not public. [VERIFIED absence]

## Actionable takeaways

1. [INFERRED] Fix clone tickets with the pipeline-bug checklist: dismiss the blocking modal first, replace `state >= N` guards, fix the same-list bug across ALL sibling files, restore `:root` tokens, add click handlers to uncaptured states. Always grep siblings after any fix.
2. [INFERRED] Wire every interaction into the domain context (BookingContext/ShoppingContext) and expose it via window APIs, because Frist verifies tasks from tracked state ("so the oracle can verify"). A clone that looks right but does not record state probably will not count.
3. [INFERRED] Computer-use tasks should be checked by deterministic final-state checks across apps (world ledger style), have exactly one correct answer, contain a hidden constraint or trap (budget, cheapest by derived metric, stop before payment), give no solution hints, and end with report_complete or report_infeasible. Write checks as atomic "In <App>, <record> has <state>" sentences.
4. [INFERRED] Coding tasks: take a working clone feature, remove it or plant a bug, and write the ticket in Frist's template (Page/Type/Size, Description, Requested behavior, Acceptance criteria with concrete UI labels, dev-server instructions). The original code must pass and the broken code must fail, with held-out inputs plus regression journeys in Playwright. Do not name files or the cause in the ticket.
5. [INFERRED] Make coding tasks "fail for real reasons": the best ones in their post required reusing existing components and data (agents that templated from another record or rewrote fallbacks failed). Graders check the app's existing labels and components, so the oracle fix should be minimal and reuse what exists.
6. [INFERRED] Stack expectation: Bun + React/TS/Vite + Prisma, Playwright and Chromium available. Have `bun` and Playwright installed locally before arriving.
7. [INFERRED] Variants are cheap points: Frist itself mints synthetic tasks from a verifier catalog, so templated variants of an accepted computer-use task (change dates, names, budgets) are probably acceptable if each still has one verifiable answer. Confirm with organizers before mass producing.

## Searches that found nothing

- "Frist" hackathon + RL / computer-use / clones / AirPods; "Frist" + luma / partiful; site:luma.com Frist; Frist + HackPrinceton (sponsor list has no Frist).
- Frist funding / YC page / investors.
- "Arpit Ramani" Frist; "Krishna Bhatnagar" Frist.
- "Concierge Technologies" + founders.
- Domains: frist.so, getfrist.com, tryfrist.com, frist.io, frist.app, joinfrist.com, frist.xyz (no response). frist.dev, frist.com, frist.co, usefrist.com are unrelated.
- gh search repos "frist" (only unrelated "first" typos); gh search code "fristai.dev" (0 hits).
- LinkedIn profile pages (blocked, HTTP 999).

## Direct from Sung (Frist co-founder), iMessage Nov 14-15 2026
- Confirmed the hackathon is Sun 9am to 9pm at the same venue; Justin confirmed attendance.
- Asked for tips: "all the tips will be included in the session" (so the kickoff session is where acceptance criteria and tips land; take notes there).
- On sweet-talking Frist staff: everyone will help, but it will be hard for everyone, including Frist's own employees. VERIFIED (screenshot). Read: the acceptance bar is real; staff help is available to all teams equally.
