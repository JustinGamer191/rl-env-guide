"""Seed v3 = v2 plus the second hardening round (writes app/backend/prisma/seed-v3.json and mail/seed-v3.json).
Clock: Tue 2026-09-15 14:00 UTC. dueOffset = days from the clock. Comment and mail bodies may reference other
records as {K:tag}; those resolve to the final issue key after the shuffle. Verifiers re-derive every target from the
seed snapshot and assert their preconditions, so an edit that breaks a task fails loudly."""
import json, os, random, re

HERE = os.path.dirname(os.path.abspath(__file__))
R = random.Random(15)
USERS = [
    ("priya.shah@quillstack.dev", "Priya Shah", "#0ea5e9", "Engineering manager"),
    ("priya.sharma@quillstack.dev", "Priya Sharma", "#14b8a6", "Support engineer"),
    ("marco.diaz@quillstack.dev", "Marco Diaz", "#f97316", "Backend engineer"),
    ("lena.fischer@quillstack.dev", "Lena Fischer", "#a855f7", "Frontend engineer"),
    ("lena.fisher@quillstack.dev", "Lena Fisher", "#d946ef", "QA engineer"),
    ("omar.haddad@quillstack.dev", "Omar Haddad", "#22c55e", "Mobile engineer"),
    ("dana.kim@quillstack.dev", "Dana Kim", "#eab308", "Designer"),
]
U = {"Y": "guest@localhost", "PS": USERS[0][0], "PR": USERS[1][0], "MD": USERS[2][0], "LF": USERS[3][0], "LE": USERS[4][0], "OH": USERS[5][0], "DK": USERS[6][0], None: None}
C1, C2, S14, S15 = "Cycle 1: Groundwork", "Cycle 2: Liftoff", "Sprint 14", "Sprint 15"
issues, TAG = [], {}


def add(project, title, status, priority, who, est, due, cycle=None, labels=("Feature",), comments=(), tag=None, closed=None):
    i = dict(number=len(issues) + 1, project=project, title=title, description=f"{title}.", status=status, priority=priority,
             assignee=U[who], estimate=est, dueOffset=due, cycle=cycle, labels=list(labels),
             comments=[dict(author=U[a], body=b, hoursAgo=h) for (a, b, h) in comments])
    if closed: i["closedBy"], i["closedDaysAgo"] = U[closed[0]], closed[1]
    issues.append(i)
    if tag: TAG[tag] = i["number"]
    return i["number"]


# ================= X1 freeze plan (Main, open, due <= +3). Rules live in Priya Shah's emails; cutoff corrected to 8.
add("MAIN", "Webhook retries flood the audit log", "IN_PROGRESS", "HIGH", "OH", 8, 2, C1, ("Bug",), comments=[("OH", "Merged to the release branch.", 20)])  # v3: leave alone
add("MAIN", "Migrate search index to the new cluster", "BACKLOG", "LOW", None, 13, 3, None, ("Chore",))            # defer, already Backlog
add("MAIN", "Bulk edit for issue labels", "TODO", "MEDIUM", "DK", 5, -3, C1, ("Feature",))                         # urgent (5 < 8)
add("MAIN", "Empty state for archived projects", "TODO", "MEDIUM", None, 3, 1, C1, ("Design",))                    # urgent + Priya
add("MAIN", "Fix tooltip overlap on the board header", "IN_PROGRESS", "HIGH", "MD", 2, 0, C1, ("Bug",), comments=[("MD", "Will merge to the release branch after review.", 5)])  # urgent (twin: not merged yet)
add("MAIN", "Copy tweaks on the invite dialog", "TODO", "LOW", None, 1, -1, None, ("Design",), comments=[("DK", "Merged to the release branch this morning.", 4)])  # v3: leave alone
add("MAIN", "Rate limit the public status endpoint", "TODO", "URGENT", "OH", 4, 3, C1, ("Performance",))           # nothing
add("MAIN", "Add keyboard hint to the filter bar", "BACKLOG", "NONE", None, 0, 2, None, ("Feature",))              # urgent + Priya
add("MAIN", "SCIM provisioning for enterprise", "TODO", "MEDIUM", None, 8, 2, C1, ("Customer",))                   # Customer: urgent + Priya
add("MAIN", "Stale cache after project rename", "TODO", "LOW", None, 5, -2, None, ("Bug",))                        # urgent + Priya (5 < 8)
add("MAIN", "Billing portal times out for large orgs", "IN_PROGRESS", "HIGH", "LF", 13, 1, C1, ("Customer", "Bug"))  # Customer: urgent
add("MAIN", "Reindex job blocks deploys", "TODO", "MEDIUM", "PR", 8, 0, C1, ("Chore",))                            # defer
# twins
add("MAIN", "Shared views for saved filters", "TODO", "MEDIUM", None, 8, 2, C1, ("Feature",))   # v3: defer
add("MAIN", "Trim unused icons from the bundle", "TODO", "LOW", None, 2, 4, None, ("Performance",))
add("MAIN", "Retry banner for failed uploads", "DONE", "HIGH", "LF", 8, -2, C1, ("Feature",))
add("MAIN", "Legacy CSV importer", "CANCELED", "MEDIUM", None, 3, 1, None, ("Chore",))
add("MOB", "Offline queue for comment drafts", "TODO", "HIGH", "OH", 8, 1, S14, ("Feature",))
add("MOB", "Haptics on swipe to archive", "TODO", "LOW", None, 2, -2, S14, ("Design",))
add("WEB", "Pricing page FAQ accordion", "IN_PROGRESS", "MEDIUM", None, 3, 0, None, ("Design",))
add("MAIN", "Two-factor recovery codes", "TODO", "HIGH", None, 8, None, None, ("Feature",))

# ================= X2 Cycle 2 planning for Marco (cap 12) then Omar (cap 18); availability lives in their emails
add("MAIN", "Usage-based billing meter", "TODO", "HIGH", "MD", 5, 9, C2, ("Feature",))
add("MAIN", "Split the notifications worker", "IN_PROGRESS", "MEDIUM", "MD", 3, 12, C2, ("Performance",))
add("MAIN", "Remove deprecated v1 endpoints", "BACKLOG", "LOW", "MD", 1, 16, C2, ("Chore",))
add("MAIN", "Retry policy for outbound webhooks", "TODO", "MEDIUM", "MD", 4, 14, C2, ("Feature",))   # Marco load 13 > cap 12
add("MAIN", "Schema for project templates", "DONE", "HIGH", "MD", 8, 7, C2, ("Feature",))
add("MAIN", "GraphQL gateway spike", "CANCELED", "LOW", "MD", 3, None, C2, ("Chore",))
add("MAIN", "Job runner health checks", "IN_PROGRESS", "MEDIUM", "MD", 5, 5, C1, ("Chore",))
add("MOB", "Background sync scheduler", "TODO", "HIGH", "MD", 8, 10, S15, ("Feature",))
add("MAIN", "Read replicas for reporting", "TODO", "HIGH", "OH", 2, 15, C2, ("Performance",))  # v3: est 2 so Omar-first steals Marco's 3-pointer
add("MAIN", "Mobile API pagination contract", "DONE", "MEDIUM", "OH", 5, 8, C2, ("Feature",))
add("MOB", "Widget refresh budget", "TODO", "MEDIUM", "OH", 5, 11, S15, ("Performance",))
add("MAIN", "SSO login with Okta", "BACKLOG", "URGENT", None, 5, 11, C2, ("Feature",))
add("MAIN", "Audit log export to S3", "TODO", "HIGH", None, 8, 13, C2, ("Feature",))
add("MAIN", "Paginate the activity feed API", "BACKLOG", "HIGH", None, 3, 14, C2, ("Performance",))
add("MAIN", "Org-wide default labels", "TODO", "MEDIUM", None, 3, 15, C2, ("Feature",))
add("MAIN", "Cleanup script for orphaned attachments", "BACKLOG", "MEDIUM", None, 2, 17, C2, ("Chore",))
add("MAIN", "Dark mode for email digests", "BACKLOG", "LOW", None, 1, 18, C2, ("Design",))
add("MAIN", "Typeahead for @mentions", "BACKLOG", "NONE", None, 2, None, C2, ("Feature",))
add("MAIN", "Fix flaky cycle burndown test", "DONE", "URGENT", None, 2, 8, C2, ("Chore",))
add("MAIN", "Feature flag for new editor", "CANCELED", "HIGH", None, 1, None, C2, ("Chore",))
add("MAIN", "Hotfix: duplicate invite emails", "TODO", "URGENT", None, 3, 6, C1, ("Bug",))
add("MOB", "Push token refresh on reinstall", "TODO", "URGENT", None, 2, 9, S15, ("Bug",))
add("MAIN", "Granular API token scopes", "TODO", "MEDIUM", "LF", 5, 12, C2, ("Feature",))
add("MAIN", "Command palette actions", "IN_PROGRESS", "MEDIUM", "PS", 8, 10, C2, ("Feature",))
add("MAIN", "Onboarding checklist copy", "TODO", "LOW", "PR", 2, 19, C2, ("Design",))
add("MAIN", "Webhook signing secrets rotation", "BACKLOG", "MEDIUM", "LE", 3, None, C2, ("Feature",))

# ================= X3 Northwind triage (corrections, duplicates, repeats)
add("MAIN", "CSV export drops non-ASCII names", "TODO", "MEDIUM", "LF", 3, 9, C1, ("Bug", "Customer"), tag="csv")
add("MOB", "Crash when opening a shared board link", "IN_PROGRESS", "URGENT", "OH", 5, 6, S14, ("Bug", "Customer"), tag="crash")
add("MOB", "Board link previews show the wrong title", "TODO", "LOW", "DK", 2, 13, S15, ("Bug",), tag="crash_wrong")
add("WEB", "Invoice PDF shows the wrong tax ID", "DONE", "HIGH", "LE", 2, -4, None, ("Customer",), tag="tax")
add("MAIN", "Webhook payload missing project key", "TODO", "LOW", "MD", 2, 14, None, ("Customer",), tag="hook")
add("MAIN", "Webhooks omit the project key", "CANCELED", "MEDIUM", None, 2, None, None, ("Bug",), tag="hook_dup",
    comments=[("LF", "Duplicate of {K:hook}, closing this one.", 70)])
add("MOB", "Push notifications arrive twice", "TODO", "LOW", "OH", 3, 12, S15, ("Bug",), tag="push")
add("MAIN", "SAML login loops on Safari", "IN_PROGRESS", "HIGH", "MD", 5, 8, C1, ("Bug", "Customer"), tag="saml")
add("WEB", "Export billing history to Excel", "CANCELED", "LOW", "PR", 2, None, None, ("Feature", "Customer"), tag="excel",
    comments=[("PS", "Not planned this quarter, closing.", 120)])
add("MAIN", "Slow load on the cycles page", "TODO", "LOW", "LF", 3, 11, C1, ("Performance",), tag="t_slow")
add("MAIN", "Seat count off by one on the billing page", "TODO", "MEDIUM", "PR", 2, 13, None, ("Bug",), tag="t_seat")
add("MOB", "Dark mode contrast on the inbox list", "TODO", "MEDIUM", "DK", 2, 14, S15, ("Design",), tag="t_dark")
add("WEB", "Contact form rejects plus addresses", "TODO", "LOW", "LF", 1, 10, None, ("Bug", "Customer"), tag="t_plus")
add("MAIN", "Timezone shown wrong in digests", "TODO", "MEDIUM", None, 2, None, None, ("Bug",), tag="t_tz")

# ================= X4 bug bash: Bug + Done + moved to Done during Cycle 1 (Sep 7 on). closed=(who moved it to Done, days ago)
add("MAIN", "Login form ignores the Enter key", "DONE", "MEDIUM", "LF", 2, -6, C1, ("Bug",), closed=("LF", 6))
add("MAIN", "Board drag drops card in wrong column", "DONE", "HIGH", "LE", 3, -4, C1, ("Bug",), closed=("PS", 4))
add("MAIN", "Comment count stale after delete", "DONE", "LOW", "OH", 1, -1, C1, ("Bug",), closed=("OH", 1))
add("MOB", "Keyboard covers the reply box", "DONE", "HIGH", "LF", 2, -3, S14, ("Bug",), closed=("PS", 3))
add("MOB", "Avatar cache never expires", "DONE", "LOW", "LE", 1, -9, None, ("Bug", "Performance"), closed=("LE", 12))
add("MOB", "Badge count wrong after logout", "DONE", "MEDIUM", "DK", 1, None, S14, ("Bug",), closed=("DK", 2))
add("WEB", "Footer links 404 on the blog", "DONE", "MEDIUM", "LF", 1, 2, None, ("Bug",), closed=("LF", 20))
add("WEB", "Signup button misaligned on Safari", "DONE", "LOW", "OH", 1, -5, None, ("Bug", "Design"), closed=("PS", 5))
add("MAIN", "Rotate API keys without downtime", "DONE", "HIGH", "Y", 3, -7, C1, ("Bug",), closed=("Y", 7))
add("MAIN", "Mention emails sent twice", "DONE", "MEDIUM", "LF", 2, 1, C1, ("Bug",), closed=("LF", 2))
add("WEB", "Docs sidebar collapses on scroll", "DONE", "LOW", "LE", 1, -2, None, ("Bug",), closed=("LE", 10))
add("MAIN", "Search results flicker on refresh", "CANCELED", "MEDIUM", "LE", 2, 10, None, ("Bug",), closed=("LE", 3))
add("WEB", "Hero video stutters on Firefox", "DONE", "MEDIUM", "LE", 2, 5, None, ("Regression",), closed=("LE", 2))
add("MOB", "Login screen freezes on iPad", "DONE", "HIGH", "LE", 2, -2, S14, ("Regression", "Performance"), closed=("LE", 3))

# ================= filler (never matches a task rule)
FILL = {
    "MAIN": ["Inline images in comments", "Saved replies for support", "Audit trail for permission changes", "Mention autocomplete ranking",
             "Faster cold start for workers", "Project archive flow", "Custom fields on issues", "Recurring issues", "Issue templates per project",
             "SLA timers on support issues", "Markdown tables in descriptions", "Roadmap view prototype", "Usage dashboard for admins",
             "Better empty state for inbox", "Import from Jira", "Pin important comments", "Live cursors in the shared editor",
             "Quick switcher with fuzzy matching", "Generate SDK from the OpenAPI file", "Nightly backup to cold storage"],
    "MOB": ["Widget for today's issues", "Biometric unlock", "Share sheet extension", "Tablet split view", "Deep links from email",
            "Offline image cache", "Voice notes in comments", "Android 15 edge-to-edge", "Reduce app size", "Pull to refresh polish"],
    "WEB": ["Customer stories page", "Changelog RSS feed", "Docs search with Algolia", "Status page redesign", "Careers page refresh",
            "Localized landing pages", "Cookie banner update", "Integrations directory"],
}
people = ["PS", "PR", "LF", "LE", "DK", "Y"]   # no Marco or Omar: X2 counts their loads
for proj, titles in FILL.items():
    for t in titles:
        st = R.choice(["BACKLOG", "TODO", "TODO", "IN_PROGRESS", "DONE", "CANCELED"])
        who = R.choice(people + [None]) if st in ("BACKLOG", "TODO") else R.choice(people)
        cyc = None
        if proj == "MAIN": cyc = R.choice([C1, C1, None]) if who is None else R.choice([C1, C2, None])
        if proj == "MOB": cyc = R.choice([S14, S15, None])
        due = R.choice([None, 4, 5, 7, 9, 12, 16, 21, 26]) if st not in ("DONE", "CANCELED") else R.choice([None, -12, -8, -3, 1])
        add(proj, t, st, R.choice(["HIGH", "MEDIUM", "MEDIUM", "LOW", "NONE"]), who, R.choice([0, 1, 2, 3, 5, 8]), due, cyc,
            (R.choice(["Feature", "Design", "Chore", "Performance"]),))
TEXTS = ["Can we pair on this tomorrow?", "Blocked on design review.", "Repro steps are in the thread.", "Pushed a draft PR.",
         "Moving this after the release.", "Customer asked about this again.", "Looks good to me."]
for i in R.sample(issues, 22):
    i["comments"].append(dict(author=U[R.choice(people)], body=R.choice(TEXTS), hoursAgo=R.choice([3, 20, 50, 90])))

R.shuffle(issues)
old2new = {}
for n, i in enumerate(issues, 1): old2new[i["number"]] = n; i["number"] = n
KEY = {tag: f"{next(i['project'] for i in issues if i['number'] == old2new[num])}-{old2new[num]}" for tag, num in TAG.items()}
sub = lambda s: re.sub(r"\{K:(\w+)\}", lambda m: KEY[m.group(1)], s)
for i in issues:
    for c in i["comments"]: c["body"] = sub(c["body"])

seed = {
    "clock": "2026-09-15T14:00:00Z",
    "team": {"name": "Your workspace", "description": "A private sandbox workspace. Edit anything you like."},
    "users": [dict(email=e, name=n, avatarColor=c, title=t) for (e, n, c, t) in USERS],
    "projects": [dict(name="Main", key="MAIN", description="Core product work", color="#5b5bd6", icon="box"),
                 dict(name="Mobile", key="MOB", description="iOS and Android apps", color="#ec4899", icon="phone"),
                 dict(name="Website", key="WEB", description="Marketing site and docs", color="#0ea5e9", icon="globe")],
    "labels": [dict(name=n, color=c) for n, c in [("Bug", "#ef4444"), ("Feature", "#10b981"), ("Design", "#8b5cf6"), ("Chore", "#6b7280"),
                                                  ("Performance", "#06b6d4"), ("Customer", "#f59e0b"), ("Regression", "#be123c")]],
    "cycles": [dict(project="MAIN", number=1, name=C1, startOffset=-8, endOffset=6), dict(project="MAIN", number=2, name=C2, startOffset=6, endOffset=20),
               dict(project="MOB", number=14, name=S14, startOffset=-8, endOffset=6), dict(project="MOB", number=15, name=S15, startOffset=6, endOffset=20)],
    "issues": issues,
}
json.dump(seed, open(os.path.join(HERE, "app/backend/prisma/seed-v3.json"), "w"), indent=1)

# ================= Quillmail v2
mail = []
def msg(mid, nm, frm, subject, body, when, folder="inbox", read=False):
    mail.append(dict(id=mid, fromName=nm, from_=frm, to="you@quillstack.dev", subject=subject, body=sub(body), date=when, folder=folder, read=read, starred=False))

# X1 policy thread
msg("p1", "Priya Shah", "priya.shah@quillstack.dev", "Release freeze plan for Main",
    "Hi all,\n\nThe Main release freeze starts at the end of Friday, September 18. Before then, please triage every open Main issue "
    "(Backlog, Todo or In Progress) that is due on or before Sep 18, including overdue ones:\n\n"
    "1. Estimate of 5 points or more: it will not make the freeze. Move it to Backlog and comment \"Deferred past the Sep 18 freeze\".\n"
    "2. Anything smaller: set its priority to Urgent, and if nobody owns it, assign it to me.\n\n"
    "Customer-labeled issues are never deferred; treat them like rule 2 whatever their size. Leave existing assignees alone.\n\nThanks,\nPriya Shah",
    "2026-09-14T09:05:00Z", read=True)
msg("p2", "Priya Sharma", "priya.sharma@quillstack.dev", "Re: Release freeze plan for Main",
    "Suggestion: should we defer anything of 3 points or more? Happy to own the unassigned ones myself.\n\nPriya Sharma", "2026-09-14T13:20:00Z")
msg("p3", "Priya Shah", "priya.shah@quillstack.dev", "Correction: release freeze plan",
    "One correction to yesterday's freeze plan: the cutoff for deferring is 8 points, not 5. Also, anything that already has a comment "
    "saying it was merged to the release branch is fine as it is: leave those alone. Everything else in the plan stays the same.\n\nPriya Shah",
    "2026-09-15T10:40:00Z")
msg("p4", "Priya Shah", "priya.shah@quillstack.dev", "Re: Correction: release freeze plan",
    "Update from the release meeting: the freeze now starts at the end of Thursday, September 17, so only issues due on or before Sep 17 are in scope. "
    "When you defer something, comment \"Deferred past the release freeze\" instead.\n\nPriya Shah", "2026-09-15T12:55:00Z")
# X2 time off
msg("o1", "Marco Diaz", "marco.diaz@quillstack.dev", "Time off",
    "Heads up: I'm out from Thursday, September 24 through Tuesday, September 29, back on Wednesday the 30th.\n\nMarco", "2026-09-14T15:30:00Z", read=True)
msg("o2", "Omar Haddad", "omar.haddad@quillstack.dev", "PTO",
    "I'm taking Friday, October 2 and Monday, October 5 off.\n\nOmar", "2026-09-11T09:40:00Z", folder="archive", read=True)   # v3: archived
msg("o5", "Marco Diaz", "marco.diaz@quillstack.dev", "Re: Time off",
    "Small change: my trip got shorter, so I'm only out Thursday the 24th and Friday the 25th. I'll be back on Monday, September 28.\n\nMarco",
    "2026-09-15T11:15:00Z")
msg("o3", "Marco Diaz", "marco.diaz@quillstack.dev", "Out Tuesday and Wednesday",
    "Reminder that I'm out Tuesday September 8 and Wednesday September 9 for a conference.\n\nMarco", "2026-09-03T08:00:00Z", folder="archive", read=True)
msg("o4", "Lena Fischer", "lena.fischer@quillstack.dev", "Vacation",
    "I'm off the whole week of September 28.\n\nLena", "2026-09-12T12:00:00Z", read=True)
# X3 Northwind
msg("m01", "Ana Ruiz", "ana@northwind.io", "CSV export still mangles our names",
    "Hi team,\n\nOur finance export still turns accented names into question marks. This is the one you track as {K:csv}.\nCould you bump it? Month end is close.\n\nAna Ruiz\nNorthwind", "2026-09-15T09:12:00Z")
msg("m02", "Raj Mehta", "raj@northwind.io", "Shared board links crash the iOS app",
    "Hello,\n\nThree more of our managers hit the crash when opening a shared board link on iPhone ({K:crash_wrong}). Any ETA?\n\nRaj", "2026-09-14T16:40:00Z")
msg("m02c", "Raj Mehta", "raj@northwind.io", "Re: Shared board links crash the iOS app",
    "Sorry, I pasted the wrong key in my last email. The crash is {K:crash}, not {K:crash_wrong}.\n\nRaj", "2026-09-14T17:05:00Z")
msg("m03", "Ana Ruiz", "ana@northwind.io", "Tax ID on invoices is wrong again",
    "Hi,\n\nThe September invoice PDF shows our old tax ID. I thought {K:tax} fixed this, but it is back.\n\nAna", "2026-09-14T08:05:00Z", read=True)
msg("m04", "Northwind Ops", "ops@northwind.io", "Webhooks still omit the project key",
    "Team,\n\nOur integration still receives webhook payloads without the project key ({K:hook_dup}).\n\nNorthwind Operations", "2026-09-15T11:30:00Z")
msg("m06", "Raj Mehta", "raj@northwind.io", "Safari SAML loop",
    "Hi,\n\nPeople on Safari still bounce between our IdP and your login page forever ({K:saml}).\n\nRaj", "2026-09-14T10:02:00Z")
msg("m12", "Kim Larsen", "kim@northwind.io", "Accented names in exports",
    "Hello,\n\nSame problem as Ana reported: accents break in the CSV export ({K:csv}).\n\nKim", "2026-09-15T12:20:00Z")
msg("m13", "Ana Ruiz", "ana@northwind.io", "Excel export",
    "Hi,\n\nWe really need billing history in Excel, can you reconsider {K:excel}?\n\nAna", "2026-09-14T14:10:00Z")
msg("m07", "Ana Ruiz", "ana@northwind.io", "Cycles page is slow for us",
    "Hi,\n\nThe cycles page takes a while to load for our big workspace ({K:t_slow}). Not urgent.\n\nAna", "2026-09-13T18:20:00Z")
msg("m08", "Northwind Billing", "billing@northwind.co", "Seat count on your billing page",
    "Hello,\n\nYour billing page shows one seat more than we pay for ({K:t_seat}). Please review.\n\nBilling", "2026-09-15T10:45:00Z")
msg("m09", "Raj Mehta", "raj@northwind.io", "Inbox contrast in dark mode",
    "Hey,\n\nThe inbox list is hard to read in dark mode on Android ({K:t_dark}).\n\nRaj", "2026-09-14T12:15:00Z", folder="archive", read=True)
msg("m10", "Priya Shah", "priya.shah@quillstack.dev", "Fwd: Northwind contact form issue",
    "Forwarding from Northwind: their contact form submissions with plus addresses bounce ({K:t_plus}). Can someone take a look?\n\nPriya", "2026-09-15T08:30:00Z")
msg("m11", "Ana Ruiz", "ana@northwind.io", "Digest timezone",
    "Hi,\n\nThe daily digest shows times in UTC instead of our timezone ({K:t_tz}).\n\nAna", "2026-09-11T15:00:00Z", read=True)
FILLMAIL = [("GitHub", "notifications@github.com", "[quillstack/api] PR #482 approved", "Marco Diaz approved your pull request."),
            ("Linearly Weekly", "digest@linearly.news", "This week in product ops", "Five reads on running better sprints."),
            ("Dana Kim", "dana.kim@quillstack.dev", "New icon set for review", "Figma link inside, comments welcome by Thursday."),
            ("AWS Billing", "billing@aws.example", "Your August invoice is ready", "Your invoice for August is available."),
            ("Omar Haddad", "omar.haddad@quillstack.dev", "TestFlight build 2.14 is up", "Build 2.14 includes the offline queue."),
            ("Lena Fischer", "lena.fischer@quillstack.dev", "Lunch and learn on Friday", "I will demo the new board filters."),
            ("Calendar", "calendar@quillstack.dev", "Reminder: sprint planning Monday", "Sprint planning for Cycle 2 starts Monday at 10."),
            ("Acme Support", "help@acme.io", "Re: export limits", "Thanks, the higher export limit works for us."),
            ("Priya Sharma", "priya.sharma@quillstack.dev", "Support rotation swap", "Can we swap rotations next week?"),
            ("Sentry", "alerts@sentry.example", "New issue: TypeError in board.tsx", "TypeError: cannot read properties of undefined."),
            ("Lena Fisher", "lena.fisher@quillstack.dev", "QA sign-off for 2.14", "Regression suite passed on iOS 18 and 26."),
            ("Northwind Newsletter", "news@northwind-updates.com", "Northwind product digest", "What Northwind shipped in August."),
            ("Stripe", "receipts@stripe.example", "Receipt for your payment", "Receipt #1932-8812 for $49.00."),
            ("Marco Diaz", "marco.diaz@quillstack.dev", "Redis maintenance window", "Thursday 02:00 UTC, about ten minutes."),
            ("Recruiting", "jobs@quillstack.dev", "Interview loop on Wednesday", "Two candidates for the mobile role."),
            ("Figma", "no-reply@figma.example", "Dana Kim mentioned you", "Dana Kim mentioned you in Icon set v3."),
            ("Globex", "it@globex.example", "Question about SSO", "Do you support SCIM provisioning?"),
            ("Calendar", "calendar@quillstack.dev", "Reminder: retro Friday", "Cycle 1 retro on Friday at 3.")]
days = ["2026-09-15T13:10", "2026-09-15T12:05", "2026-09-15T06:40", "2026-09-14T19:30", "2026-09-14T15:00", "2026-09-14T09:20",
        "2026-09-13T11:00", "2026-09-12T17:45", "2026-09-12T08:00", "2026-09-11T10:10", "2026-09-10T16:20", "2026-09-10T09:00",
        "2026-09-09T14:30", "2026-09-08T11:15", "2026-09-07T13:00", "2026-09-06T10:00", "2026-09-05T09:30", "2026-09-04T15:45"]
for n, ((nm, frm, s, body), d) in enumerate(zip(FILLMAIL, days), 20):
    msg(f"f{n:02d}", nm, frm, s, body + f"\n\n{nm}", d + ":00Z", folder="archive" if n % 7 == 0 else "inbox", read=n % 3 != 0)
json.dump({"me": {"name": "You", "address": "you@quillstack.dev"}, "messages": mail}, open(os.path.join(HERE, "mail/seed-v3.json"), "w"), indent=1)
print(len(issues), "issues;", len(mail), "messages;", sum(1 for m in mail if m["folder"] == "inbox"), "in inbox;", KEY)
