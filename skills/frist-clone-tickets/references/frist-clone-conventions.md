# Known Frist clone conventions (public, verify at kickoff)

From Frist's own repair guide (https://github.com/runfrist/gh-pages-homepage, `human-guide.html`, May 2026) and published sample runs (https://frist.ai/samples/opentable-photos-opus-5-5-r1.json). Strong priors, not facts about today's repos. Sources and more detail: `~/Documents/Hackathons/Frist/frist-intel.md`.

## Stack seen so far

Bun, `bun dev.mjs` (frontend http://127.0.0.1:5173, backend port 3001, fresh DB in a temp dir each start; `PORT` and `BACKEND_PORT` env vars, so give each worker its own pair), `bun test`, React + TypeScript + Vite frontend, `.mjs` backend with Prisma, clock frozen via `CLOCK_FIXED_TIME`, Playwright and Chromium preinstalled, a `design/` folder of reference screenshots. The sample workdir had no `.git`, so you may need `git init` and a first commit before worktrees.

## Predictable generator bugs, in fix order

Clones are machine-generated from a video of the real site decomposed into DOM snapshots and React components.
1. A blocking modal or overlay: fix first, nothing else is testable until it dismisses.
2. `{state >= N}` snapshot guards standing in for real state: replace with real state and handlers.
3. Lists split into templated files where every item copies the first (same flag, same color): once you find one, check every sibling.
4. Missing global `:root` CSS block, so `var(--...)` tokens resolve to nothing (colors, borders, radius, z-index slightly off).
5. Elements never clicked in the recording have no handlers; one widget split into two (for example two calendars that are really one). In the recorded-clone rehearsal, 31 of 59 buttons had no handler, exactly the ones never clicked while recording.
6. The generator invents wording and types for states it never saw: empty states ("No due date" where the real app says "None"), picker labels, narrowed column types (an `Int` estimate where the real app allows 0.5). Check them against `design/` and the ticket text, not against the clone's own code.
7. Buttons that refresh the page (form default): use `preventDefault` or `type="button"`.

## State must be tracked, not just shown

Every interaction records state in a domain context (`BookingContext` for travel, `ShoppingContext` for e-commerce) exposed through `useWindowAPIs` "so the oracle can verify". The guide replaces `useEffect`s with `useWindowAPIs` in one pass at the end. A clone that looks right but does not expose state is probably not done.

Compare against `design/` screenshots for visual tickets. Run the build before and after each fix.
