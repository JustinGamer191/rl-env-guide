"""Playwright helpers for the hard tasks (two apps, paginated lists). Two routes per edit:
route A = List view filtered by key + drawer; route B = Cmd+K search by key (or Board card) + drawer.
Mail: route A = open each message and press Archive; route B = tick rows across pages and bulk-archive."""
from contextlib import contextmanager
from playwright.sync_api import sync_playwright
from world import CHROME
import ui
from ui import settle, pick, comment, close_drawer

PNAME = {"MAIN": "Main", "MOB": "Mobile", "WEB": "Website"}
PRIO = {"URGENT": "Urgent", "HIGH": "High", "MEDIUM": "Medium", "LOW": "Low", "NONE": "None"}
STAT = {"BACKLOG": "Backlog", "TODO": "Todo", "IN_PROGRESS": "In Progress", "DONE": "Done", "CANCELED": "Canceled"}


@contextmanager
def pages(url, mail_url=None):
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME)
        page = b.new_page(viewport={"width": 1440, "height": 900})
        page.goto(url + "/app"); page.wait_for_selector("text=Your workspace"); page.wait_for_timeout(500)
        mail = None
        if mail_url:
            mail = b.new_page(viewport={"width": 1440, "height": 900}); mail.goto(mail_url); mail.wait_for_selector(".row")
        try: yield page, mail
        finally: b.close()


def switch_project(page, key):
    page.locator("aside button[title='%s']" % PNAME[key]).first.click(); page.wait_for_timeout(300)


def open_key_list(page, url, key):
    page.goto(url + "/app/issues"); page.wait_for_selector("text=Your workspace"); page.wait_for_timeout(300)
    switch_project(page, key.split("-")[0])
    page.locator("input[placeholder='Filter issues…']").fill(key); page.wait_for_timeout(400)
    page.locator("[data-issue-id]", has=page.locator(f"span:text-is('{key}')")).click()
    page.wait_for_selector("aside.drawer-in"); settle(page)


def open_key_search(page, key):
    page.keyboard.press("Escape"); page.wait_for_timeout(150)
    page.keyboard.press("Meta+k"); page.wait_for_timeout(300)
    page.keyboard.type(key); page.wait_for_timeout(700)
    page.locator("div[class*='z-[90]'] button", has_text=key).first.click()
    page.wait_for_selector("aside.drawer-in"); settle(page)
    assert key in page.locator("aside.drawer-in").inner_text(), "opened wrong issue"


def drawer_text(page): return page.locator("aside.drawer-in").inner_text()


def set_fields(page, ch, users, order=("status", "priority", "assignee", "labels_add")):
    for f in order:
        if f not in ch: continue
        if f == "status": pick(page, "status", STAT[ch["status"]])
        elif f == "priority": pick(page, "Priority", PRIO[ch["priority"]])
        elif f == "assignee": pick(page, "Assignee", users[ch["assignee"]] if ch["assignee"] else "Unassigned")
        elif f == "labels_add":
            for l in ch["labels_add"]:
                page.locator("aside button", has_text="+ add label").click(); page.wait_for_timeout(250)
                page.locator('aside [role=listbox] [role=option]', has_text=l).click(); settle(page)


def mail_find_and_open(mail, subject, folder="inbox"):
    mail.locator(f"nav button[data-folder={folder}]").click(); mail.wait_for_timeout(400)
    while True:
        row = mail.locator(".row", has=mail.locator(f".subj:text-is('{subject}')"))
        if row.count(): row.first.click(); mail.wait_for_selector(".msg"); mail.wait_for_timeout(200); return
        nxt = mail.locator("#next")
        assert nxt.is_enabled(), f"mail not found: {subject}"
        nxt.click(); mail.wait_for_timeout(400)


def mail_archive_open(mail): mail.locator("#arch").click(); mail.wait_for_timeout(500)


def mail_bulk_archive(mail, subjects):
    mail.locator("nav button[data-folder=inbox]").click(); mail.wait_for_timeout(400)
    left = set(subjects)
    while left:
        for s in list(left):
            row = mail.locator(".row", has=mail.locator(f".subj:text-is('{s}')"))
            if row.count(): row.first.locator(".sel").check(); mail.wait_for_timeout(150); left.discard(s)
        if left:
            assert mail.locator("#next").is_enabled(), f"not found: {left}"
            mail.locator("#next").click(); mail.wait_for_timeout(400)
    mail.locator("#barch").click(); mail.wait_for_timeout(800)


def new_issue_modal(page, spec, users, via_shortcut=False):
    if via_shortcut:
        page.goto(page.url.split("/app")[0] + "/app/board"); page.wait_for_timeout(700); page.keyboard.press("c")
    else:
        page.locator("header button", has_text="New issue").first.click()
    page.wait_for_selector('input[placeholder^="Issue title"]'); page.wait_for_timeout(200)
    page.locator('input[placeholder^="Issue title"]').fill(spec["title_text"])
    page.locator("label:has-text('Project') select").select_option(label=f"{PNAME[spec['project']]} ({spec['project']})")
    page.locator("label:has-text('Status') select").select_option(spec["status"])
    page.locator("label:has-text('Priority') select").select_option(spec["priority"])
    if spec.get("assignee"): page.locator("label:has-text('Assignee') select").select_option(label=users[spec["assignee"]])
    page.locator("label:has-text('Estimate') input").fill(str(spec["estimate"]))
    if spec.get("due"): page.locator("label:has-text('Due date') input").fill(spec["due"])
    page.locator("button[type=submit]", has_text="Create issue").click(); settle(page, 900)
