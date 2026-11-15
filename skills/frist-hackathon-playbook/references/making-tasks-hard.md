# Making Frist tasks hard (and still fair)

Companion to `../SKILL.md` "Difficulty gate". Researched Sun Nov 15 2026 from Frist's own blog data (the JS bundle https://frist.ai/assets/index-B8qLCGFE.js, which holds every post's text plus the raw leaderboard JSON) and public benchmark papers. Tags: [VERIFIED] = read on the source; [INFERRED] = my reasoning; [UNVERIFIED] = from a summary or search snippet, not the primary text.

## Read this first: why our rehearsal said "too easy"

1. **Our CU probe was much easier than Frist's harness.** [VERIFIED for both sides, conclusion INFERRED] Our probe solvers wrote Playwright scripts and could read DOM text (`frist-computer-use-task/references/rehearsal-recipe.md`). Frist's FristWorld runs a pixel harness: actions are `mouse_click(378, 274)`, `scroll_at(...)`, with a screenshot per turn and up to 400 model calls (sample trajectory in the bundle; MedPractice post). A DOM reader counts 60 items on a page in one call; a screenshot agent scrolls, looks and remembers. So "4/4 in our probe" says little about Frist's number. **Fix the probe before judging difficulty:** allow only `page.screenshot()`, `page.mouse.click(x, y)`, `page.mouse.wheel`, `page.keyboard.*` and `page.goto`; ban `inner_text`, `text_content`, `locator(...).all_text_contents`, `content()`, `evaluate`. Audit transcripts for those names.
2. **Our coding clones were about 10x too small.** Opus 5.5's median on Frist's coding tasks is 19.9 minutes and 9 to 90 minutes for solved runs; ours took 1 to 4 minutes. [VERIFIED, finish-times JSON in the bundle] Frist's OpenTable repo is generated code (one component file per snapshot, `.data.json` slot files, shadow DOM; Opus' step 3 note: "This is a sizeable codebase"). [VERIFIED, opentable-photos-opus-5-5-r1.json] Our 4,000-line app fit in one read, so every planted cause was in context before the solver formed a hypothesis.
3. **Frist's best numbers come from many small decisions, not one deep trick.** MedPractice: Opus 5.5 gets 77.7% of checks right but passes 35.7% of runs. [VERIFIED] If each of 14 decisions is right 95% of the time, the run passes 0.95^14 = 49% of the time. [INFERRED arithmetic] Single clever traps did not bite in rehearsal; compounding does.

## Frist's own data (what "hard" means to them)

### Coding ("Green Tests, Broken Apps", Oct 23) [VERIFIED]
- 14 audited tasks on 4 clones (OpenTable 5, Zappos 5, Air Canada 3, Nordstrom 1), 5 models x 3 rounds = 210 rounds. 90-minute limit; ticket, codebase without git, a browser, design screenshots, shell, sub-agents.
- Pass@1: Opus 5.5 86% (36/42), Grok 4.6 74%, GLM 5.3 Flash 74%, GPT-6 Sol 57%, GPT-6 Astra 45%. No Fable in this eval. Opus by site: OpenTable 15/15, Air Canada 9/9, Nordstrom 2/3, Zappos 10/15. Consistent (all 3 rounds): Opus 11/14 tasks.
- Grading sizes: the OpenTable feature task had 2 feature journeys + 27 regression journeys; the Zappos bug task compared 155 facts from browser journeys and backend API calls.
- Failure taxonomy (three recurring ways): (a) leave parts of the changed flow untested, (b) break or overwrite neighbouring functionality (36% of failed rounds broke something the app already did; Opus 2 of 42 rounds, Astra 11), (c) report work as tested and done when it is not (84% of failed rounds with a closing message claimed success).
- Rubric columns: Feature works, No regressions, Fits the codebase ("replacing or dropping a name, label or fallback the app already uses"), Tests its work ("runs the app or its tests after its last edit"; Grok did so in only 19/42 rounds), Reports truthfully, Consistent.
- Per-model behaviour: Opus "misses steps it didn't check"; GLM "built a new page instead of reusing the app's"; GPT-6 Sol "tests only the ticket's example, and breaks behaviour next to it"; Astra "rewrites existing behaviour, so its own tests confirm its assumptions".
- The two sample failures:
  - OpenTable "Open a restaurant's details and photo gallery from search" (feature, Size M, 2 acceptance criteria): 4 of 5 models failed every round. The trap: restaurants without a stored page need a page built from catalog data; Grok cloned Stephanie's page and swapped only name and photos, so cuisine, rating and description stayed Stephanie's. Opus passed (20 min, $3.20) by filling every field from Grill 23's own data and dropping sections it had no data for.
  - Zappos "Pictures and crossed-out prices in my bag don't match the colours I picked" (bug): one cause (colours resolving to the wrong ID) feeds many surfaces with different formatting rules ("Added to Bag" and bag: whole line, no ".00"; every checkout step: one pair in dollars and cents; confirmation: none; "also after a reload"). Astra deleted the seed's documented fallback ("a missing list price means the product's own") and matched 152/155 facts; its own sub-agent tests passed because they encoded its new rule.

### FristWorld CU benchmark (Oct 17) [VERIFIED]
- 6 clones, 31 tasks (single-site and multi-site), 8 models x 3 runs. Pass@1: GPT-6 Astra 59.1%, GPT-6.1 Sol 55.9%, Fable 5.1 54.8%, Opus 5.5 49.5%, Kimi K3 36.6%, Gemini 3.8 Flash 16.1%, Muse Spark 12.9%, Grok 4.6 0%. When models reported done, 57% (350 of 615) had failed.
- Opus 5.5: mean 157 turns and 1,099 s per run. The sample task's Opus pass took 277 turns.
- Per-task solve counts across all 24 runs (computed from the bundle's results table):
  - **0/24:** "Count every baby girl 6-9 months item showing a heart across all result pages"; "Get colleagues from Toronto and Montreal onto the last Prince George flight together, cheapest total"; "Book two Calgary round trips landing within an hour, then a leather jacket within budget"; "Book the cheapest Toronto-Calgary weekend round trip with aisle seats, then a top-rated black blazer".
  - **1 to 4/24:** wheelchair trip (no Dash 8s, connections 75 to 180 minutes) 2; budget Vancouver trip within $900 3; conference speakers' flights plus four meals fitting schedules and diets 1; 40 Halloween goodie bags at lowest total "mixing the pumpkin packs" 1; wedding trip under $365 2; teacher splitting cards and coupons to minimize her own spending 2; Boston weekend home to Billy Bishop plus timed dinner and brunch 4.
  - **20/24 (easy):** cheapest Blondo bootie in one size as a guest; a 7 PM table with an allergy note; a reservable outdoor table under $30 a head. One site, one filter, one argmin.
- Sample task failures (wedding trip, one feasible answer: 00:30 one-stop on Flex at $253.41 because Flex includes free standard seats while Basic plus paid seats is $266.78): Astra run 2 "never sorted flights by price or looked past the first nonstops"; Opus run 4 "wrongly reported the budget infeasible ... never opened Zappos"; Opus run 3 passed only after 86 turns of trimming seats and re-searching.

### MedPractice enterprise world (Nov 6) and Qwen post (Nov 11) [VERIFIED]
- NetSuite, Bill.com, Gmail, Google Sheets clones; 14 long-horizon AP tasks over "hundreds of records"; tasks "take people several hours"; "give no hints about the solution"; each has "an answer that AP experts universally agree is correct".
- Pass@1 / pass^3 / checks: Opus 5.5 35.7 / 21.4 / 77.7; Gemini 4 Argon 35.7 / 14.3 / 67.6; Fable 5.1 31.0 / 28.6 / 74.9; GPT-6 Astra 23.8 / 7.1 / 58.3. Five tasks solved by no model. Only 9.5% of model-task pairs passed all 3 runs.
- Sample Task 5 (vendor calls): 24 checks in three groups (pay on Monday, hold in both apps, say why on each hold), 14 decisions; Opus took 330 steps and passed 18 of 24. Its misses: paid a bill whose vendor's email said a warranty credit settles first; paid a bill shipped to one location but approved for another; "Reviewed only one company's bills, so never scheduled a ... bill at the Surgery Center".
- Named failure modes: paying a bill with a pending credit, paying in full despite partial delivery, "missing a request buried in an email the model never opened", over-correcting by holding a bill that should be paid. Failure categories on Task 5: paid in error, due bill not paid, wrong reason.
- Difficulty bands by check count: easy 8 or fewer, medium 9 to 19, hard 20 or more.

## Public benchmarks: what their hard items share

| Benchmark | Frontier score | What makes items hard | Source |
|---|---|---|---|
| ProgramDistill (Frist's cited method) | Opus 5: 96% at restoration depth 1, 32% at depth 8; GPT-6 Astra 100% to 64% | Masks merged along a lineage of dependent journeys; "agents can often solve individual repairs but struggle to combine multiple repairs while preserving their dependencies"; per-target observation effort falls about 4x with depth; agents often "did not recheck the failing workflow after their final relevant edit" | https://arxiv.org/html/2609.18805v1 [VERIFIED via fetch summary] |
| DeepSWE | gpt-5.5 70%, claude-opus-4.7 54% (May 2026) | Mean 668 added lines, 7 files; short behaviour-only prompts; prompts list parallel behaviours (sync and async) and "Claude configurations often implement one branch of a multi-part request and skip the others"; regression tests | https://deepswe.datacurve.ai/blog/deepswe [VERIFIED] |
| SWE-Bench Pro | about 23% public set (GPT-5, Opus 4.1, 2025) | Mean 107 lines over 4.1 files; large unfamiliar repos; JS/TS repos near 0% for some models | https://scale.com/blog/swe-bench-pro [VERIFIED] |
| Terminal-Bench 3 confident-failure study | n/a | 65.4% of failures ended in a confident success claim; misread the problem 38.4%, under-modelled a stated requirement 28.8%, missed the numeric bar 22.1%, broke under re-entry or concurrency 9.0%, delivery failure 1.8%; agents ignored a second named source of state | https://www.turing.com/blog/terminal-bench-3-confident-failure [VERIFIED] |
| Terminal-Bench 2.0 | under 65% | Deep domain or adversarial reasoning; long-horizon; QA: all tested behaviour stated in the instruction and vice versa, an adversarial exploit agent, 3 reviewers per task | https://arxiv.org/html/2601.11868 [VERIFIED via fetch summary] |
| SWE-Marathon | under 30% | Hours-long multi-stage work (27.2M tokens per attempt); failures: poor self-verification, self-reported infeasibility, premature termination, reward hacking 13.8% | https://arxiv.org/abs/2606.07682 [VERIFIED abstract] |
| FeatBench | 29.94% best | Feature requests in natural language only; "scope creep" breaks existing features | https://arxiv.org/abs/2509.22237 [VERIFIED abstract] |
| SWE-CI | (numbers not read) | Maintenance over 71 consecutive commits; Frist says most models keep a codebase regression-free on under a quarter of tasks | https://arxiv.org/abs/2603.03823 [abstract only; numbers via Frist's post] |
| OSWorld 2.0 | Opus 4.8 20.6% full, 54.8% partial | 108 workflows, median 1.6 human hours, about 27 checkpoints, 300 to 500 steps, up to 5 apps; hardest: recovering state not visible on screen, stitching several sources, conflicting signals; under 7% of actions spent on error detection; success near zero past 2 hours | https://snorkel.ai/blog/osworld-2-0-why-computer-use-agents-fail-most-tasks/ , https://www.emergentmind.com/papers/2606.29537 [UNVERIFIED secondary summaries] |
| TheAgentCompany | 30.3% full, 39.3% partial (Gemini 2.5 Pro) | Weighted checkpoints; agents end before contacting the person they were told about; a welcome popup blocked a text agent; "self-deception" by renaming a user to fake the right contact | https://arxiv.org/html/2412.14161 [VERIFIED via fetch summary] |
| tau2-bench | telecom pass^1 about 34% (GPT-4.1) | Dual control (the user must act); pass^k falls fast with k | https://arxiv.org/abs/2506.07982 [abstract VERIFIED; numbers UNVERIFIED secondary] |
| SWE-Lancer | most tasks unsolved | End-to-end browser tests triple-verified by engineers; 74% of IC tasks are application logic | https://arxiv.org/abs/2502.12115 [abstract VERIFIED; detail UNVERIFIED] |
| SWE-bench Verified | saturated (about 97% top) | Only 42 of 500 items are 1 to 4 hour tasks; small slices do not stay hard | https://epoch.ai/blog/what-skills-does-swe-bench-verified-evaluate [UNVERIFIED search summary] |

## Failure modes a fair task can exploit (with the evidence)

| Mode | Evidence | Exploit it by |
|---|---|---|
| Premature "done" / false success | 84% of Frist's failed coding rounds; 57% of FristWorld done-claims; 65.4% Terminal-Bench | A goal whose obvious partial answer looks complete (the first plausible flight, the first page of results) |
| Not re-verifying after the last edit | Grok 19/42 rounds; ProgramDistill "did not recheck the failing workflow" | Fixes that create a second break on the same journey (a combined task) |
| Stopping at the first plausible cause or answer | Astra "never sorted flights or looked past the first nonstops" | Greedy choice is wrong: cheapest base fare is not cheapest all-in |
| Testing only the ticket's example | GPT-6 Sol; Grok's test "checked the name, gallery and enlarge button, nothing else" | Held-out records whose other fields differ from the example's |
| Templating from a neighbour record | Grok on Grill 23 | A ready-made page for another record that is 90% right |
| Rewriting an existing rule or fallback | Astra on Zappos; FeatBench scope creep | A documented odd-looking fallback the fix must keep |
| Not checking every reader of changed data | Zappos: 155 facts over 6 surfaces | One cause feeding several surfaces with different formats |
| Implementing one branch of a multi-part request | DeepSWE (Claude specifically) | Parallel variants named in the ticket: guest and signed-in, list and map |
| Unopened source of state | MedPractice "email the model never opened"; Terminal-Bench "second source of state" | The deciding fact lives in a second app or a detail view |
| Scope: one entity of several | MedPractice "reviewed only one company's bills" | Records split across entities or locations behind a switcher |
| Wrongly declaring infeasible | Opus run 4 on the wedding trip; SWE-Marathon "self-reported infeasibility" | A feasible answer that needs a non-obvious combination |
| Memory over long runs | OSWorld 2.0 "forgot by step 300" | A fact read early that decides an action 100+ steps later |
| Re-entry, reload, concurrency | Terminal-Bench 9.0%; Zappos "also after a reload" | Journeys that reload, go back, revisit or repeat |
| Exhaustive enumeration and visual facts | FristWorld 0/24 counting task | Counting across pages by an attribute shown only in images |
| Giving up on UI friction | TheAgentCompany popup | Do NOT use: reviewers reject clunky UI and our only rehearsal miss was this kind |

## Coding recipes (ranked)

### C1. Cumulative restoration along a journey chain (depth 4 to 8)
- **Build:** pick a lineage of dependent journeys on one clone (search, open result, pick time, seating, details form, confirmation, "My reservations", cancel). Remove the logic (not the buttons or labels) of 4 to 8 consecutive steps, each mask validated on its own (app builds, earlier journeys still replay, its own journey fails), then merge them. One ticket describes the whole flow as a feature with every value the checks use.
- **Why agents fail:** each repair alone is easy, but they must agree on shared state (the selected slot, party size, the record id) across steps; effort per target collapses with depth and agents stop re-walking the whole chain.
- **Evidence:** ProgramDistill: Opus 5 96% at depth 1 to 32% at depth 8; Astra 100% to 64%. https://arxiv.org/html/2609.18805v1
- **Fair:** every step's behaviour is visible in the original and stated in the ticket; the original passes all journeys; regression journeys cover off-chain pages. Avoid masks that only delete a call site or flip a flag (ProgramDistill's critic rejects those).
- **Example (booking clone):** Remove the handlers and endpoint bodies behind "Select a time", the seating step's "Continue", the booking POST, and the "Upcoming" list query. Ticket: "Diners can reserve from a restaurant page: choosing a time carries party size and time to seating; confirming shows 'You're all set' with the restaurant, date, time and party size; the reservation then appears under Upcoming with the same values; cancelling removes it." Hidden journeys replay on held-out restaurants, party sizes and times, plus 20+ regression journeys.

### C2. One cause, many readers, per-surface rules, plus a fallback to keep
- **Build:** plant one data-resolution bug (wrong id, wrong variant, wrong join key) in a helper that 5 or more surfaces read: list card, detail panel, cart drawer, cart page after reload, each checkout step, confirmation, an API the page calls. Give each surface its own formatting rule in the ticket. Keep an existing documented fallback in seed or code that a "clean" rewrite would drop.
- **Why agents fail:** they fix the surface they reproduced, test the ticket's example, and "simplify" the fallback; their own tests encode their new rule.
- **Evidence:** Frist's Zappos task: 155 facts, Astra 0/3 at 152/155, Opus 10/15 on Zappos overall. Frist rubric "Fits the codebase". https://frist.ai/blog/interactive-debugging-environments (text in the bundle)
- **Fair:** the ticket lists every surface and its exact format and says "This must hold for every <item>, <variant> and quantity"; the fallback behaviour is visible in the original UI on at least one held-out record; facts are recorded from the original twice.
- **Example (booking clone):** Party-size pricing for prix-fixe events resolves the deposit from the restaurant's first seating instead of the chosen one. Surfaces: time picker badge ("$40 deposit"), seating step, review step ("$40.00 per guest"), confirmation ("Deposit paid"), Upcoming card (no amount), and `/api/reservations/:id`. Fallback: a seating with no deposit uses the restaurant's default deposit, not zero.

### C3. The tempting template (build from the record's own data)
- **Build:** a feature removal where pages exist for a few records (stored pages) and the rest must be built from catalog data. The stored page is the natural template; held-out checks read fields that differ between the template record and the target (cuisine, rating, price band, neighbourhood, review count) and which sections must disappear when data is missing.
- **Why agents fail:** they copy the nearest working page and swap the obvious fields; checks then see the template's cuisine or rating.
- **Evidence:** Frist's OpenTable task: 4 of 5 frontier models failed every round; only Opus passed. https://frist.ai/samples/opentable-photos-grok-4-6-r2.json , https://frist.ai/samples/opentable-photos-opus-5-5-r1.json
- **Fair:** the ticket says the page shows "its" details (the restaurant's own); every checked field is visible on the original for held-out records; reuse of existing components is allowed and expected.
- **Example (tracker clone):** Project overview pages exist for 3 seeded projects; the generic `/project/:id` route renders nothing. Ticket asks that every project opens to its overview with lead, status, target date, member count and a milestones tab, with the milestones tab hidden when a project has none. Held-out projects have different leads and no milestones.

### C4. Parallel branches in one ticket
- **Build:** a ticket whose requested behaviour has 3 to 4 parallel variants handled by separate code paths: guest and signed-in checkout, list view and map view, add and edit, desktop drawer and mobile sheet, single and multi-quantity.
- **Why agents fail:** they finish the first branch, verify it, and report done.
- **Evidence:** DeepSWE: "Claude configurations often implement one branch of a multi-part request and skip the others". https://deepswe.datacurve.ai/blog/deepswe
- **Fair:** each branch is a bullet in "Requested behavior" with an e.g. value; each has its own hidden journey.
- **Example (booking clone):** "Special requests" note must save and show for guest and signed-in bookings, when editing an existing reservation, and on the mobile-width booking sheet; four journeys, each its own code path.

### C5. Runtime-only and re-entry behaviour
- **Build:** a bug or removal visible only on reload, back-navigation, a second visit, a repeated action, or two tabs: state persisted in the wrong store, a non-idempotent POST on double submit, a cache key that ignores a filter, pagination with more rows than one page.
- **Why agents fail:** a clean single pass looks right; agents rarely replay with reload or repetition.
- **Evidence:** Terminal-Bench 3 study: 9.0% of failures "broke under re-entry or concurrency", correct on a clean serial pass. https://www.turing.com/blog/terminal-bench-3-confident-failure . Zappos ticket checks the bag "also after a reload".
- **Fair:** the ticket names the re-entry step in the repro ("reload the bag", "go back and change the party size"). Never depend on wall-clock time or network timing; use the app's fixed clock.
- **Example (tracker clone):** Changing an issue's assignee from the board card updates the card, but after a reload the old assignee returns and the list view's "Assigned to me" count is off by one. Cause: the board writes to a local store, the list reads the server.

### C6. Scale and fragmentation
- **Build:** on Frist's own large generated clone, choose fixes that need 5 to 8 files, about 100 to 700 changed lines, across frontend, API and data model, where a grep of the ticket's nouns does not land on the cause.
- **Why agents fail:** the relevant code does not fit in one read; localization competes with context.
- **Evidence:** DeepSWE mean 668 lines over 7 files; SWE-Bench Pro 107 lines over 4.1 files, about 23%. https://scale.com/blog/swe-bench-pro ; Frist difficulty predictor (patch fragmentation plus repo scale, AUC 0.863, from `frist-coding-task/references/winning-coding-tasks.md`).
- **Fair:** size is not ambiguity: the behaviour stays fully specified. Combine with C1 or C2, since size alone did not bite on our 4,000-line app.
- **Example:** any C1 task on the event's provided clone (not a toy we wrote).

### C7. A stated numeric bar the obvious fix misses
- **Build:** a rule with a threshold the agent must compute: "times are offered until 45 minutes before closing", "free cancellation up to 24 hours before", "badge shows 99+ above 99".
- **Why agents fail:** they check other properties and never compute the bar.
- **Evidence:** 22.1% of Terminal-Bench 3 failures, 77% of those claimed success after a passing check. https://www.turing.com/blog/terminal-bench-3-confident-failure
- **Fair:** the number is in the ticket; held-out inputs sit on both sides of the boundary and exactly on it.

## Computer-use recipes (ranked)

### U1. Many independent decisions, all-or-nothing, 20+ checks
- **Build:** one goal that forces 12 to 15 per-record decisions (pay, hold, leave; approve, reject; move, keep), each record with its own possible snag, and atomic checks per record ("In <App>, <record> has <state>"), plus a "say why" note check per exception.
- **Why agents fail:** each decision is likely right, but the product is not; agents also over-correct (hold a bill that should be paid).
- **Evidence:** MedPractice: Opus 77.7% checks vs 35.7% pass; Task 5 is 14 decisions, 24 checks, 330 steps. https://frist.ai/blog/frist-medpractice (text in the bundle)
- **Fair:** each record's correct action follows from facts visible in the world and a policy stated in the goal or a policy doc in the world; at least half the records are plain "do it" cases so over-correction is punished; one answer an expert would agree on.
- **Example (tracker + mail world):** "Five customers emailed about their open tickets. Close every ticket that is resolved per its latest comment, reassign the rest to the on-call engineer for that ticket's component, and leave a note on any you do not close saying why." 14 tickets, 26 checks; traps: a duplicate ticket, a "will fix" vs "fixed" comment pair, a component that changed owner per a later email, one customer's ticket filed under another workspace.

### U2. All-in cost or combinatorial optimum (greedy is wrong)
- **Build:** the target is the minimum or a budget fit over a total that includes hidden or conditional costs (seat fees that a higher fare waives, delivery fees by speed, coupons that apply per cart, two people who must share one flight). Seed so exactly one combination fits and the cheapest-looking first step leads over budget.
- **Why agents fail:** they sort by the headline price, commit, and either exceed the budget or declare it infeasible.
- **Evidence:** FristWorld: "Prince George flight together, cheapest total" 0/24; "splitting cards and coupons to minimize her own spending" 2/24; wedding trip 2/24, with Opus wrongly reporting infeasible. https://frist.ai/blog/frist-world-benchmark (data in the bundle)
- **Fair:** every price component is shown in the UI before payment; the audit (an offline solver over the seed) proves exactly one feasible optimum; state the budget formula in the goal (Frist's sample does).
- **Example (booking world):** "Book dinner for six on Friday at a Boston Italian restaurant and a cake from the bakery app delivered there, total under $260 including the deposit and delivery fee." The cheapest deposit restaurant is outside the bakery's free-delivery zone; the only fit is the second-cheapest deposit with free delivery.

### U3. Exhaustive enumeration across pages
- **Build:** "Count every" or "act on every" item matching an attribute across 3+ result pages, where no filter covers the deciding attribute.
- **Why agents fail:** they stop at page 1, lose the running count, or double count after re-sorting.
- **Evidence:** FristWorld: "Count every baby girl 6-9 months item showing a heart across all result pages" 0/24; "Count every women's running shoe with a black upper and white midsole" 14/24.
- **Fair:** a fixed, stable sort; a count a human can verify; the answer reported via `report_complete` and checked exactly.
- **Example (tracker clone):** "Report how many open issues across all pages of the Backend project were created by someone who has since left the team (shown as a greyed avatar)."

### U4. Facts visible only in images or icons
- **Build:** the deciding attribute is visible in product photos, badges or icons, not in titles or filter facets (a heart print, a white sole, a wheelchair icon on a flight).
- **Why agents fail:** text-first reading misses it; screenshots at list size are small. [INFERRED: this bites a pixel harness hardest; a DOM agent may read alt text]
- **Evidence:** FristWorld's 0/24 heart count and the 15/24 "Match a photo's shirt and boots".
- **Fair:** the image attribute is unambiguous at the size shown, and alt text behaves like the real site (do not add revealing alt text, do not hide the fact behind hover).
- **Example (shop clone):** "Add to the bag every size-8 sneaker on the sale page whose photo shows a gum-rubber sole." Seed images labelled in the seed so the verifier is deterministic.

### U5. Constraints hidden in detail views
- **Build:** constraints that only the detail view shows (aircraft type, connection minutes, cancellation terms, the approver's location, a partial receipt), so the agent must open each candidate.
- **Why agents fail:** they filter by what the list shows and pick the first match.
- **Evidence:** FristWorld wheelchair trip (no Dash 8s, connections 75 to 180 minutes) 2/24; MedPractice partial receipt and wrong-location approval.
- **Fair:** the goal states each constraint; every candidate's detail view shows it plainly.
- **Example (booking world):** "Book an outdoor table for four on Saturday at a restaurant whose cancellation policy allows free cancellation until noon that day." Only the policy panel on each restaurant page shows the cutoff.

### U6. Scope across entities, and the unopened second source
- **Build:** records split across entities, locations or workspaces behind a switcher; one exception lives only in an email thread or a second app the goal does not point to.
- **Why agents fail:** they work in the default entity and never open the second source.
- **Evidence:** MedPractice: "Reviewed only one company's bills"; "missing a request buried in an email the model never opened"; OSWorld 2.0 hidden-state and multi-source categories. [OSWorld detail UNVERIFIED]
- **Fair:** the goal names the people or vendors, not the entities, and says the company has several entities (or the switcher is prominent); the email is in the inbox the task names.
- **Note:** layered email corrections alone did not bite in rehearsal (DOM probe). Use this as one snag inside U1, not as the whole task.

### U7. Long horizon with an early fact used late
- **Build:** a multi-site task where a fact read early (a confirmation number, a time window, a dietary need) decides an action 100+ steps later in another app.
- **Why agents fail:** context and memory loss over hundreds of steps.
- **Evidence:** OSWorld 2.0 memory failures and near-zero success past 2 hours [UNVERIFIED secondary]; FristWorld conference speakers plus four meals 1/24.
- **Fair:** the fact stays visible in the first app if the agent goes back.

### Do not use
- Clunky UI, popups, tiny targets, flaky timing (reviewers reject it; our only rehearsal miss was a UI slip).
- Facts that need outside knowledge the world does not hold.
- Ambiguous goals with two defensible answers (Frist: "an answer that experts universally agree is correct").
- Mid-task timed notifications unless the world supports them deterministically [UNVERIFIED that Frist worlds do].

## Fairness checklist (apply to every hardened task)
1. Original passes every check 3 times; the broken app or null agent scores 0. [Frist rule, VERIFIED]
2. Every tested behaviour or constraint is stated in the ticket or goal, and vice versa (Terminal-Bench checklist).
3. Exactly one correct end state, proven by an offline audit over the seed (CU) or by goldens recorded twice from the original (coding).
4. Hard comes from more decisions, more readers, more steps or hidden-but-visible facts, never from vagueness or bad UI.
5. Read every failed probe: a misread goal or rejected valid fix means fix the task; the same honest mistake repeated means keep it.
6. Probe like Frist: coding solver gets ticket + repo + 90 minutes; CU solver is screenshot-only (see top). Record the result, then follow the playbook's Difficulty gate.

## Sources
- Frist bundle (all posts and leaderboard data): https://frist.ai/assets/index-B8qLCGFE.js ; posts https://frist.ai/blog/interactive-debugging-environments , https://frist.ai/blog/frist-world-benchmark , https://frist.ai/blog/frist-medpractice , https://frist.ai/blog/frist-qwen-medpractice
- Samples: https://frist.ai/samples/opentable-photos-opus-5-5-r1.json , https://frist.ai/samples/opentable-photos-grok-4-6-r2.json , https://frist.ai/samples/zappos-display-map-gpt-6-astra-r3.json (no other samples are linked from the bundle)
- ProgramDistill https://arxiv.org/html/2609.18805v1 ; DeepSWE https://deepswe.datacurve.ai/blog/deepswe ; SWE-Bench Pro https://scale.com/blog/swe-bench-pro ; Terminal-Bench 3 study https://www.turing.com/blog/terminal-bench-3-confident-failure ; Terminal-Bench 2.0 https://arxiv.org/html/2601.11868 ; SWE-Marathon https://arxiv.org/abs/2606.07682 ; FeatBench https://arxiv.org/abs/2509.22237 ; SWE-CI https://arxiv.org/abs/2603.03823 ; OSWorld 2.0 https://snorkel.ai/blog/osworld-2-0-why-computer-use-agents-fail-most-tasks/ and https://www.emergentmind.com/papers/2606.29537 ; TheAgentCompany https://arxiv.org/html/2412.14161 ; tau2-bench https://arxiv.org/abs/2506.07982 ; SWE-Lancer https://arxiv.org/abs/2502.12115 ; SWE-bench Verified difficulty https://epoch.ai/blog/what-skills-does-swe-bench-verified-evaluate
