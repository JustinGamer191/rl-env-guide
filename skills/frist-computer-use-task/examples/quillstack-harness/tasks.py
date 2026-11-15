"""Five CU tasks on Quillstack. Each: GOAL, target rule (from the seed snapshot), verify(seed, final, report),
oracle (route A, UI), alt (route B, UI), and adversaries (REST, they test the verifier).
Verifier rule: expected = seed + exactly the intended change; full normalized diff must be empty;
report status must match (complete, or infeasible for T4). The report text is never evidence."""
import copy
from world import GUEST, diff, norm_text, report
import ui

CLOSED = ("DONE", "CANCELED")


def verdict(expected, final, rep, want):
    why = diff(expected, final)
    if not rep or rep.get("status") != want: why.append(f"report={rep and rep.get('status')} want {want}")
    return (0.0 if why else 1.0), why


def new_comments(seed_i, final_i):
    left = list(final_i["comments"])
    for c in seed_i["comments"]:
        if c in left: left.remove(c)
        else: return None  # a seed comment was edited or deleted
    return left


# ---------- shared REST helpers for adversaries ----------
def ids(w): return {str(i["number"]): i["id"] for i in w.call("GET", "/api/issues")["issues"]}
def labels(w):
    team = w.call("GET", "/api/teams/" + w.call("GET", "/api/issues")["issues"][0]["project"]["teamId"])
    return {l["name"]: l["id"] for l in team["labels"]}
def me(w): return w.call("GET", "/api/users/me")["id"]
def patch(w, num, **body): return w.call("PATCH", f"/api/issues/{ids(w)[str(num)]}", body)
def add_label_api(w, num, name, seed):
    L = labels(w); cur = [L[n] for n in seed["issues"][str(num)]["labels"]]
    return patch(w, num, labelIds=cur + [L[name]])
def comment_api(w, num, text): return w.call("POST", f"/api/issues/{ids(w)[str(num)]}/comments", {"body": text})
def project_id(w, key): return next(i["project"]["id"] for i in w.call("GET", "/api/issues")["issues"] if i["project"]["key"] == key)


# =====================================================================================
# T1  multi-step edit on an entity found by a property
T1_GOAL = ("In the Main project, find the open issue (not Done or Canceled) that is unassigned and has the highest estimate. "
           "Assign it to yourself, set its priority to High, and add the Performance label without removing its existing labels.")

def t1_target(seed):
    c = {n: i for n, i in seed["issues"].items() if i["project"] == "MAIN" and i["assignee"] is None and i["status"] not in CLOSED}
    top = max(i["estimate"] for i in c.values()); t = [n for n, i in c.items() if i["estimate"] == top]
    assert len(t) == 1, f"T1 ambiguous in seed: {t}"; return t[0]

def t1_verify(seed, final, rep):
    e = copy.deepcopy(seed); i = e["issues"][t1_target(seed)]
    i.update(assignee=GUEST, priority="HIGH", labels=sorted(set(i["labels"]) | {"Performance"}))
    return verdict(e, final, rep, "complete")

def t1_oracle(w):
    n = t1_target(w.seed)
    with ui.browser(w.url) as p:
        ui.open_from_list(p, w.url, f"MAIN-{n}"); ui.pick(p, "Assignee", "You"); ui.pick(p, "Priority", "High"); ui.add_label(p, "Performance"); ui.close_drawer(p)
    report(w.run_dir, "complete", "done")

def t1_alt(w):  # board card, reverse order
    n = t1_target(w.seed)
    with ui.browser(w.url) as p:
        ui.open_from_board(p, w.url, f"MAIN-{n}"); ui.add_label(p, "Performance"); ui.pick(p, "Priority", "High"); ui.pick(p, "Assignee", "You")
    report(w.run_dir, "complete", "Assigned, High, Performance added")

T1_ADV = {
    "change_everything": lambda w: ([(patch(w, n, assigneeId=me(w), priority="HIGH"), add_label_api(w, n, "Performance", w.seed))
                                     for n, i in w.seed["issues"].items() if i["assignee"] is None and i["status"] not in CLOSED],
                                    report(w.run_dir, "complete", "done")),
    "wrong_entity": lambda w: (patch(w, 12, assigneeId=me(w), priority="HIGH"), add_label_api(w, 12, "Performance", w.seed),
                               report(w.run_dir, "complete", "done")),  # MAIN-12: unassigned, est 3, also Backlog
    "partial": lambda w: (patch(w, 8, assigneeId=me(w), priority="HIGH"), report(w.run_dir, "complete", "done")),  # no label
    "labels_replaced": lambda w: (patch(w, 8, assigneeId=me(w), priority="HIGH", labelIds=[labels(w)["Performance"]]),
                                  report(w.run_dir, "complete", "done")),  # dropped Feature
    "oracle_plus_collateral": lambda w: (t1_oracle(w), patch(w, 1, priority="LOW")),
}

# =====================================================================================
# T2  hidden trap: two near-identical urgent in-progress issues, only the sooner-due one is correct
T2_GOAL = ("Two urgent issues are in progress in the Main project. The customer deadline for the one that is due sooner has moved, "
           "so lower that issue's priority to High and leave a comment on it saying: Downgraded: customer deadline moved")
T2_COMMENT = "downgraded customer deadline moved"

def t2_target(seed):
    c = [(i["due"], n) for n, i in seed["issues"].items() if i["project"] == "MAIN" and i["priority"] == "URGENT" and i["status"] == "IN_PROGRESS"]
    assert len(c) == 2 and c[0][0] != c[1][0] and None not in (c[0][0], c[1][0]), c
    return min(c)[1]

def t2_verify(seed, final, rep):
    n = t2_target(seed); e = copy.deepcopy(seed); e["issues"][n]["priority"] = "HIGH"
    fi = final["issues"].get(n); req = []
    new = new_comments(seed["issues"][n], fi) if fi else None
    if new is not None and len(new) == 1 and new[0]["author"] == GUEST and norm_text(new[0]["body"]) == T2_COMMENT:
        e["issues"][n]["comments"] = fi["comments"]
    else: req.append(f"required comment missing or wrong on {n}: {new}")  # fail closed: the addition is REQUIRED, not merely tolerated
    s, why = verdict(e, final, rep, "complete")
    return (0.0 if req else s), req + why

def t2_oracle(w):
    n = t2_target(w.seed)
    with ui.browser(w.url) as p:
        ui.open_from_list(p, w.url, f"MAIN-{n}"); ui.pick(p, "Priority", "High"); ui.comment(p, "Downgraded: customer deadline moved")
    report(w.run_dir, "complete", "done")

def t2_alt(w):  # command-menu search, comment first via Cmd+Enter, different punctuation/case
    n = t2_target(w.seed)
    with ui.browser(w.url) as p:
        ui.open_from_search(p, f"MAIN-{n}", w.seed["issues"][n]["title"]); ui.comment(p, "downgraded - customer deadline moved.", use_shortcut=True)
        ui.pick(p, "Priority", "High")
    report(w.run_dir, "complete", "ok")

T2_ADV = {
    "change_everything": lambda w: ([(patch(w, n, priority="HIGH"), comment_api(w, n, "Downgraded: customer deadline moved")) for n in ("2", "14")],
                                    report(w.run_dir, "complete", "done")),
    "wrong_entity": lambda w: (patch(w, 14, priority="HIGH"), comment_api(w, 14, "Downgraded: customer deadline moved"), report(w.run_dir, "complete", "done")),
    "partial": lambda w: (patch(w, 2, priority="HIGH"), report(w.run_dir, "complete", "done")),
    "comment_twice": lambda w: (patch(w, 2, priority="HIGH"), comment_api(w, 2, "Downgraded: customer deadline moved"),
                                comment_api(w, 2, "Downgraded: customer deadline moved"), report(w.run_dir, "complete", "done")),
    "oracle_plus_collateral": lambda w: (t2_oracle(w), comment_api(w, 14, "fyi")),
}

# =====================================================================================
# T3  read-then-act: read Cycle 2's scoped points, create an issue carrying that number
T3_GOAL = ('Create a new issue in the Main project titled "Cycle 2 kickoff checklist" with status Todo and priority Medium. '
           "Set its estimate to the total number of points currently scoped in Cycle 2: Liftoff.")

def t3_points(seed): return sum(i["estimate"] for i in seed["issues"].values() if i["project"] == "MAIN" and i["cycle"] == 2)

def t3_verify(seed, final, rep):
    e = copy.deepcopy(seed); why = []
    new = [n for n in final["issues"] if n not in seed["issues"]]
    if len(new) == 1:
        f = final["issues"][new[0]]
        ok = (f["project"] == "MAIN" and norm_text(f["title"]) == "cycle 2 kickoff checklist" and f["status"] == "TODO"
              and f["priority"] == "MEDIUM" and f["estimate"] == t3_points(seed) and f["parent"] is None and f["comments"] == [])
        if ok: e["issues"][new[0]] = f  # unspecified fields (assignee, labels, due, cycle, description) are free
        else: why.append(f"new issue {new[0]} wrong: {f}")
    else: why.append(f"want exactly 1 new issue, got {new}")  # fail closed
    s, w2 = verdict(e, final, rep, "complete")
    return (0.0 if why else s), why + w2

def _new_issue(p, title, estimate, description=None, assignee=False):
    p.locator('input[placeholder^="Issue title"]').fill(title)
    if description: p.locator('textarea[placeholder^="Add context"]').fill(description)
    p.locator("label:has-text('Status') select").select_option("TODO")
    p.locator("label:has-text('Priority') select").select_option("MEDIUM")
    if assignee: p.locator("label:has-text('Assignee') select").select_option(label="You (you)")
    p.locator("label:has-text('Estimate') input").fill(str(estimate))
    p.locator("button[type=submit]", has_text="Create issue").click(); ui.settle(p, 800)

def t3_oracle(w):
    with ui.browser(w.url) as p:
        p.goto(w.url + "/app/cycles"); p.wait_for_selector("text=Cycle 2: Liftoff")
        p.locator("header button", has_text="New issue").click(); p.wait_for_timeout(300)
        _new_issue(p, "Cycle 2 kickoff checklist", t3_points(w.seed))
    report(w.run_dir, "complete", "done")

def t3_alt(w):  # "c" compose shortcut from the board, different case, description + assignee set
    with ui.browser(w.url) as p:
        p.goto(w.url + "/app/board"); p.wait_for_timeout(600); p.keyboard.press("c"); p.wait_for_timeout(300)  # compose shortcut
        _new_issue(p, "Cycle 2 Kickoff Checklist ", t3_points(w.seed), description="Prep for Liftoff", assignee=True)
    report(w.run_dir, "complete", "created")

def _create(w, title, est, status="TODO", prio="MEDIUM"):
    return w.call("POST", "/api/issues", {"projectId": project_id(w, "MAIN"), "title": title, "status": status, "priority": prio, "estimate": est})

T3_ADV = {
    "change_everything": lambda w: ([_create(w, "Cycle 2 kickoff checklist", est) for est in (3, 10, 13, 38)], report(w.run_dir, "complete", "done")),
    "wrong_entity": lambda w: (_create(w, "Cycle 2 kickoff checklist", 38), report(w.run_dir, "complete", "done")),  # Cycle 1's points
    "partial": lambda w: (_create(w, "Cycle 2 kickoff checklist", 10, status="BACKLOG", prio="NONE"), report(w.run_dir, "complete", "done")),
    "edit_existing_instead": lambda w: (patch(w, 8, title="Cycle 2 kickoff checklist", status="TODO", estimate=10), report(w.run_dir, "complete", "done")),
    "oracle_plus_collateral": lambda w: (t3_oracle(w), patch(w, 10, priority="LOW")),
}

# =====================================================================================
# T4  infeasible: there is no Bug in Cycle 2 (the two Bugs are in Cycle 1); correct = report_infeasible, no changes
T4_GOAL = "Move the issue labeled Bug in Cycle 2: Liftoff to In Progress and assign it to yourself."

def t4_check_seed(seed):
    assert not [n for n, i in seed["issues"].items() if i["cycle"] == 2 and "Bug" in i["labels"]], "T4 became feasible"
    assert [n for n, i in seed["issues"].items() if "Bug" in i["labels"]], "T4 lost its near-miss Bugs"

def t4_verify(seed, final, rep):
    t4_check_seed(seed)
    return verdict(copy.deepcopy(seed), final, rep, "infeasible")

def t4_oracle(w):
    report(w.run_dir, "infeasible", "No issue in Cycle 2: Liftoff has the Bug label; the Bugs (MAIN-1, MAIN-6) are in Cycle 1.")

def t4_alt(w):  # actually look: open every Cycle 2 issue's drawer from the list, then refuse (viewing must not count as a change)
    with ui.browser(w.url) as p:
        for n, i in w.seed["issues"].items():
            if i["cycle"] == 2: ui.open_from_list(p, w.url, f"MAIN-{n}"); ui.close_drawer(p)
    report(w.run_dir, "infeasible", "none of the Cycle 2 issues is a Bug")

T4_ADV = {
    "change_everything": lambda w: ([patch(w, n, status="IN_PROGRESS", assigneeId=me(w)) for n, i in w.seed["issues"].items() if i["cycle"] == 2],
                                    report(w.run_dir, "complete", "done")),
    "wrong_entity": lambda w: (patch(w, 6, status="IN_PROGRESS", assigneeId=me(w)), patch(w, 1, status="IN_PROGRESS"), report(w.run_dir, "complete", "done")),
    "make_it_feasible": lambda w: (add_label_api(w, 12, "Bug", w.seed), patch(w, 12, status="IN_PROGRESS", assigneeId=me(w)), report(w.run_dir, "complete", "done")),
    "partial_then_infeasible": lambda w: (patch(w, 12, assigneeId=me(w)), report(w.run_dir, "infeasible", "no bug")),
    "oracle_plus_collateral": lambda w: (patch(w, 3, priority="HIGH"), t4_oracle(w)),
}

# =====================================================================================
# T5  precise end state across several records
T5_GOAL = "Pull every Backlog issue in Cycle 2: Liftoff into Todo and assign each of them to yourself."

def t5_targets(seed):
    t = sorted(n for n, i in seed["issues"].items() if i["status"] == "BACKLOG" and i["cycle"] == 2)
    assert len(t) >= 2 and [n for n, i in seed["issues"].items() if i["status"] == "BACKLOG" and i["cycle"] != 2], "T5 lost its trap"
    return t

def t5_verify(seed, final, rep):
    e = copy.deepcopy(seed)
    for n in t5_targets(seed): e["issues"][n].update(status="TODO", assignee=GUEST)
    return verdict(e, final, rep, "complete")

def t5_oracle(w):
    with ui.browser(w.url) as p:
        for n in t5_targets(w.seed):
            ui.open_from_list(p, w.url, f"MAIN-{n}"); ui.pick(p, "status", "Todo"); ui.pick(p, "Assignee", "You"); ui.close_drawer(p)
    report(w.run_dir, "complete", "done")

def t5_alt(w):  # inline status select in List, then assign from Board cards
    with ui.browser(w.url) as p:
        for n in t5_targets(w.seed): ui.list_set_status(p, w.url, f"MAIN-{n}", "TODO")
        for n in t5_targets(w.seed): ui.open_from_board(p, w.url, f"MAIN-{n}"); ui.pick(p, "Assignee", "You"); ui.close_drawer(p)
    report(w.run_dir, "complete", "done")

T5_ADV = {
    "change_everything": lambda w: ([patch(w, n, status="TODO", assigneeId=me(w)) for n, i in w.seed["issues"].items() if i["status"] == "BACKLOG"],
                                    report(w.run_dir, "complete", "done")),  # includes MAIN-9 (no cycle)
    "wrong_entity": lambda w: ([patch(w, n, status="TODO", assigneeId=me(w)) for n in ("9", "10", "12")], report(w.run_dir, "complete", "done")),
    "partial": lambda w: ([patch(w, n, status="TODO", assigneeId=me(w)) for n in ("8", "10")], report(w.run_dir, "complete", "done")),
    "status_only": lambda w: ([patch(w, n, status="TODO") for n in ("8", "10", "12")], report(w.run_dir, "complete", "done")),
    "oracle_plus_collateral": lambda w: (t5_oracle(w), patch(w, 9, priority="HIGH")),
}

COMMON_ADV = {
    "null": lambda w: None,
    "report_only": lambda w: report(w.run_dir, "complete", "Done: all requested changes are made."),
}

TASKS = {
    "T1": dict(goal=T1_GOAL, verify=t1_verify, oracle=t1_oracle, alt=t1_alt, adv=T1_ADV),
    "T2": dict(goal=T2_GOAL, verify=t2_verify, oracle=t2_oracle, alt=t2_alt, adv=T2_ADV),
    "T3": dict(goal=T3_GOAL, verify=t3_verify, oracle=t3_oracle, alt=t3_alt, adv=T3_ADV),
    "T4": dict(goal=T4_GOAL, verify=t4_verify, oracle=t4_oracle, alt=t4_alt, adv=T4_ADV),
    "T5": dict(goal=T5_GOAL, verify=t5_verify, oracle=t5_oracle, alt=t5_alt, adv=T5_ADV),
}
