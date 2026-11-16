"""Playwright helpers for reference solves. Two routes to every edit so the alt-path check is real:
route A = List view row + drawer pickers; route B = Cmd+K search / board card + other controls."""
import re
from contextlib import contextmanager
from playwright.sync_api import sync_playwright
from world import CHROME


@contextmanager
def browser(url):
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME)
        page = b.new_page(viewport={"width": 1440, "height": 900})
        page.goto(url + "/app"); page.wait_for_selector("text=Your workspace"); page.wait_for_timeout(500)
        try: yield page
        finally: b.close()


def settle(page, ms=500): page.wait_for_load_state("networkidle"); page.wait_for_timeout(ms)


def open_from_list(page, url, key):
    page.goto(url + "/app/issues"); page.wait_for_selector("[data-issue-id]")
    page.locator("[data-issue-id]", has=page.locator(f"text='{key}'")).click()
    page.wait_for_selector("aside"); settle(page)


def open_from_search(page, key, title):
    page.keyboard.press("Meta+k"); page.wait_for_timeout(300)
    page.keyboard.type(title[:18]); page.wait_for_timeout(600)
    page.locator("div[class*='z-[90]'] button", has_text=title).first.click()
    page.wait_for_selector("aside"); settle(page)
    assert page.locator("aside.drawer-in").inner_text().find(key) >= 0, "opened wrong issue"


def open_from_board(page, url, key):
    page.goto(url + "/app/board"); page.wait_for_timeout(800)
    page.locator("div[draggable]", has=page.locator(f"text='{key}'")).first.click()
    page.wait_for_selector("aside"); settle(page)


def pick(page, row_label, option):
    """Open a drawer picker (Assignee / Priority row, or 'status' chip) and choose an option."""
    if row_label == "status":
        page.locator("aside .chip").first.click()
    else:
        page.locator("aside button", has=page.locator(f"text='{row_label}'")).first.click()
    page.wait_for_timeout(250)
    page.locator('aside div[class*="max-h-[260px]"] button', has=page.locator(f"span:text-is('{option}')")).first.click()
    settle(page)


def add_label(page, name):
    page.locator("aside button", has_text="+ add label").click(); page.wait_for_timeout(250)
    page.locator('aside [role=listbox] [role=option]', has_text=name).click(); settle(page)


def comment(page, text, use_shortcut=False):
    box = page.locator("aside textarea"); box.fill(text)
    if use_shortcut: box.press("Meta+Enter")
    else: page.locator("aside button[type=submit]").click()
    settle(page)


def close_drawer(page): page.locator("aside button[title=Close]").click(); page.wait_for_timeout(300)


def list_set_status(page, url, key, status_value):
    page.goto(url + "/app/issues"); page.wait_for_selector("[data-issue-id]")
    page.locator("[data-issue-id]", has=page.locator(f"text='{key}'")).locator("select").select_option(status_value); settle(page)
