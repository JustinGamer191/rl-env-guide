# HIDDEN grading journeys. Never shown to the generator or ticket workers.
# canary: cnry_journeys_e6f0b85f2952
# Every journey must pass on the ORIGINAL (ground truth). Values come from the
# original's seeded data as captured in recordings/ (14 issues, MAIN-1..MAIN-14).
# Journeys only use visible UI labels so they run on any implementation.
import re
from playwright.sync_api import expect

SEED = {  # title: (status column, priority)
    'Rotate API keys without downtime': ('Done', 'High'),
    'Kanban swimlanes for the release train': ('In Progress', 'Urgent'),
    'Illustrations for zero-result searches': ('Todo', 'Medium'),
    'Live cursors in the shared editor': ('In Progress', 'High'),
    'Quick switcher with fuzzy matching': ('Todo', 'Low'),
    'Tablet layout clips the side panel': ('In Progress', 'High'),
    'Nightly backup to cold storage': ('Done', 'Low'),
    'Sprint scope-change report': ('Backlog', 'Medium'),
    'Vim-style navigation keys': ('Backlog', 'Low'),
    'High contrast theme': ('Backlog', 'None'),
    'Generate SDK from the OpenAPI file': ('Todo', 'Medium'),
    'Cut cold start time in half': ('Backlog', 'Low'),
    'Pin important comments': ('Todo', 'Medium'),
    'Guest access with expiring links': ('In Progress', 'Urgent'),
}
COLUMNS = ['Backlog', 'Todo', 'In Progress', 'Done']
T = 6000  # ms per expectation


def vis(page, text):
    return page.get_by_text(text, exact=True).locator('visible=true')


def settle(page, ms=600):
    page.wait_for_load_state('networkidle'); page.wait_for_timeout(ms)


def board(page, base):
    page.goto(base + '/app/board'); settle(page, 900)
    expect(vis(page, 'Pin important comments').first).to_be_visible(timeout=T)


def column_of(page, title, tries=8):
    for i in range(tries):
        try:
            return _column_of(page, title)
        except Exception:
            if i == tries - 1:
                raise
            page.wait_for_timeout(400)


def assert_column(page, title, col, msg=''):
    got = None
    for _ in range(12):
        try:
            got = _column_of(page, title)
        except Exception:
            got = None
        if got == col:
            return
        page.wait_for_timeout(500)
    raise AssertionError(f'{title}: expected column {col}, got {got}. {msg}')


def _column_of(page, title):
    """Which column header sits horizontally over the card with this title (geometry, implementation-agnostic)."""
    card = vis(page, title).first
    card.scroll_into_view_if_needed()
    cb = card.bounding_box()
    cx = cb['x'] + cb['width'] / 2
    for col in COLUMNS:
        for h in vis(page, col).all():
            hb = h.bounding_box()
            if not hb or hb['y'] > cb['y']:
                continue  # header must be above the card
            # column extent: header's left edge to ~300px right
            if hb['x'] - 20 <= cx <= hb['x'] + 300:
                return col
    return None


def click_near(scope, anchor, pattern, maxdx=260):
    """Click the visible option matching pattern closest below anchor (dropdown/picker option)."""
    ab = anchor.bounding_box()
    best = None
    for el in scope.get_by_text(pattern).locator('visible=true').all():
        b = el.bounding_box()
        if not b or b['y'] < ab['y'] + 5 or abs(b['x'] - ab['x']) > maxdx:
            continue
        d = b['y'] - ab['y']
        if best is None or d < best[0]:
            best = (d, el)
    assert best, f'no option {pattern} near anchor'
    btn = best[1].locator('xpath=ancestor-or-self::*[self::button or @role="option" or @role="menuitem" or self::li][1]')
    (btn.first if btn.count() else best[1]).click()


def open_issue(page, title):
    vis(page, title).first.click(); page.wait_for_timeout(700)


def drawer(page):
    """The open issue detail panel: the topmost visible dialog/aside, else the page."""
    for sel in ['aside:visible', '[role=dialog]:visible']:
        loc = page.locator(sel)
        if loc.count():
            return loc.last
    return page


def close_drawer(page):
    page.keyboard.press('Escape'); page.wait_for_timeout(500)


def dashboard_value(page, label):
    lab = vis(page, label).first
    expect(lab).to_be_visible(timeout=T)
    card = lab.locator('xpath=ancestor::*[self::div or self::section or self::a][1]/..')
    return card.inner_text()


# ---------------- journeys: (id, fn(page, base)) ----------------

def j_dashboard_counters(page, base):
    page.goto(base + '/app'); settle(page)
    txt = dashboard_value(page, 'Total issues')
    assert re.search(r'\b14\b', txt), f'Total issues card: {txt!r}'
    txt = dashboard_value(page, 'Completed')
    assert re.search(r'\b2\b', txt), f'Completed card: {txt!r}'


def j_board_columns(page, base):
    board(page, base)
    for title, (col, _) in SEED.items():
        assert_column(page, title, col)


def j_drawer_details(page, base):
    board(page, base)
    open_issue(page, 'Generate SDK from the OpenAPI file')
    d = drawer(page)
    expect(d.get_by_text('MAIN-11').first).to_be_visible(timeout=T)
    expect(d.get_by_text('One script builds the TypeScript client on every release.').first).to_be_visible(timeout=T)
    close_drawer(page)
    expect(vis(page, 'One script builds the TypeScript client on every release.')).to_have_count(0, timeout=T)


def _pick_status(page, title, current, new):
    open_issue(page, title)
    d = drawer(page)
    chip = d.locator('button', has_text=re.compile(rf'^\s*{re.escape(current)}\s*$')).first
    chip.click()
    page.wait_for_timeout(400)
    click_near(drawer(page), chip, re.compile(rf'^\s*{re.escape(new)}\b'), maxdx=900)
    page.wait_for_timeout(700)
    close_drawer(page)


def j_drawer_status_heldout(page, base):
    board(page, base)
    _pick_status(page, 'Illustrations for zero-result searches', 'Todo', 'Done')
    assert_column(page, 'Illustrations for zero-result searches', 'Done', 'not moved to Done')
    board(page, base)  # reload: must persist via backend
    assert_column(page, 'Illustrations for zero-result searches', 'Done', 'Done not persisted after reload')


def j_drawer_priority_heldout(page, base):
    board(page, base)
    open_issue(page, 'Sprint scope-change report')
    d = drawer(page)
    row = d.locator('button', has_text='Priority').first
    row.click(); page.wait_for_timeout(400)
    click_near(drawer(page), row, re.compile(r'^\s*High\b'), maxdx=900); page.wait_for_timeout(700)
    expect(drawer(page).locator('button', has_text='Priority').first).to_contain_text('High', timeout=T)
    close_drawer(page)
    board(page, base)
    open_issue(page, 'Sprint scope-change report')
    expect(drawer(page).locator('button', has_text='Priority').first).to_contain_text('High', timeout=T)


def j_comment_heldout(page, base):
    board(page, base)
    open_issue(page, 'Tablet layout clips the side panel')
    box = page.get_by_placeholder(re.compile('Leave a comment')).first
    box.fill('Reproduced on an iPad mini in portrait.')
    page.get_by_role('button', name=re.compile(r'^\s*Comment\s*$')).first.click(); page.wait_for_timeout(800)
    expect(vis(page, 'Reproduced on an iPad mini in portrait.').first).to_be_visible(timeout=T)
    close_drawer(page)
    board(page, base)
    open_issue(page, 'Tablet layout clips the side panel')
    expect(vis(page, 'Reproduced on an iPad mini in portrait.').first).to_be_visible(timeout=T)


def j_create_issue_heldout(page, base):
    board(page, base)
    page.get_by_role('button', name=re.compile(r'New issue')).locator('visible=true').last.click(); page.wait_for_timeout(500)
    page.get_by_placeholder(re.compile('Issue title')).first.fill('Rate limit the login endpoint')
    page.get_by_role('button', name=re.compile(r'^\s*Create issue\s*$')).first.click(); page.wait_for_timeout(900)
    expect(vis(page, 'Rate limit the login endpoint').first).to_be_visible(timeout=T)
    assert_column(page, 'Rate limit the login endpoint', 'Backlog', '')
    board(page, base)
    expect(vis(page, 'Rate limit the login endpoint').first).to_be_visible(timeout=T)
    expect(page.get_by_text('MAIN-15').locator('visible=true').first).to_be_visible(timeout=T)


def j_list_view(page, base):
    page.goto(base + '/app/issues'); settle(page)
    for t in ['Vim-style navigation keys', 'Guest access with expiring links', 'Nightly backup to cold storage']:
        expect(vis(page, t).first).to_be_visible(timeout=T)
    for col in COLUMNS:
        expect(vis(page, col).first).to_be_visible(timeout=T)


def j_list_inline_status_heldout(page, base):
    page.goto(base + '/app/issues'); settle(page)
    row = page.locator('div, tr', has=vis(page, 'Generate SDK from the OpenAPI file')).filter(has=page.locator('select')).last
    row.locator('select').first.select_option(label='In Progress'); page.wait_for_timeout(900)
    board(page, base)
    assert_column(page, 'Generate SDK from the OpenAPI file', 'In Progress', '')


def j_priority_filter_heldout(page, base):
    board(page, base)
    page.get_by_role('button', name=re.compile(r'^\s*Priority')).locator('visible=true').first.click(); page.wait_for_timeout(400)
    page.locator('button:visible', has_text=re.compile(r'^\s*High\b')).first.click(); page.wait_for_timeout(700)
    page.keyboard.press('Escape'); page.wait_for_timeout(300)
    shown = {t for t in SEED if vis(page, t).count() > 0}
    want = {t for t, (_, p) in SEED.items() if p == 'High'}
    assert shown == want, f'High filter shows {sorted(shown)}'


def j_search_heldout(page, base):
    board(page, base)
    page.get_by_placeholder(re.compile('Filter issues')).first.fill('SDK'); page.wait_for_timeout(700)
    shown = {t for t in SEED if vis(page, t).count() > 0}
    assert shown == {'Generate SDK from the OpenAPI file'}, f'search SDK shows {sorted(shown)}'
    page.get_by_placeholder(re.compile('Filter issues')).first.fill(''); page.wait_for_timeout(700)
    shown = {t for t in SEED if vis(page, t).count() > 0}
    assert shown == set(SEED), f'cleared search shows {len(shown)} of 14'


def j_status_filter_heldout(page, base):
    board(page, base)
    btn = page.get_by_role('button', name=re.compile(r'^\s*Status')).locator('visible=true').first
    btn.click(); page.wait_for_timeout(400)
    click_near(page, btn, re.compile(r'^\s*Todo\b')); page.wait_for_timeout(700)
    page.keyboard.press('Escape'); page.wait_for_timeout(300)
    shown = {t for t in SEED if vis(page, t).count() > 0}
    want = {t for t, (c, _) in SEED.items() if c == 'Todo'}
    assert shown == want, f'Todo filter shows {sorted(shown)}'


def j_inbox_page(page, base):
    page.goto(base + '/app'); settle(page)
    page.get_by_role('link', name='Inbox').locator('visible=true').first.click(); settle(page)
    expect(vis(page, 'Inbox zero').first).to_be_visible(timeout=T)
    page.get_by_role('button', name='Mentions').first.click(); page.wait_for_timeout(400)
    expect(vis(page, 'Inbox zero').first).to_be_visible(timeout=T)


def j_cycles_page(page, base):
    page.goto(base + '/app'); settle(page)
    page.get_by_role('link', name='Cycles').locator('visible=true').first.click(); settle(page)
    expect(vis(page, 'Cycle 1: Groundwork').first).to_be_visible(timeout=T)
    expect(vis(page, 'Cycle 2: Liftoff').first).to_be_visible(timeout=T)
    expect(vis(page, 'Active').first).to_be_visible(timeout=T)


def j_command_menu_heldout(page, base):
    board(page, base)
    page.keyboard.press('Meta+k'); page.wait_for_timeout(500)
    page.get_by_placeholder(re.compile('Search issues')).first.fill('backup'); page.wait_for_timeout(700)
    page.keyboard.press('Enter'); page.wait_for_timeout(900)
    expect(vis(page, 'Compress and upload the database every night at 02:00.').first).to_be_visible(timeout=T)


def j_drag_heldout(page, base):
    board(page, base)
    src = vis(page, 'Pin important comments').first
    dst = vis(page, 'Done').first
    src.drag_to(dst); page.wait_for_timeout(900)
    assert_column(page, 'Pin important comments', 'Done', 'drag did not move card')
    board(page, base)
    assert_column(page, 'Pin important comments', 'Done', 'drag not persisted')


def j_dashboard_after_complete(page, base):
    board(page, base)
    _pick_status(page, 'Live cursors in the shared editor', 'In Progress', 'Done')
    page.get_by_role('link', name='Home').locator('visible=true').first.click(); settle(page)
    txt = dashboard_value(page, 'Completed')
    assert re.search(r'\b3\b', txt), f'Completed card after completing one: {txt!r}'


def j_labels_heldout(page, base):
    board(page, base)
    open_issue(page, 'Pin important comments')
    drawer(page).get_by_text('+ add label').first.click(); page.wait_for_timeout(400)
    page.locator('button:visible', has_text=re.compile(r'^\W*Bug\s*$')).last.click(); page.wait_for_timeout(700)
    close_drawer(page)
    board(page, base)
    open_issue(page, 'Pin important comments')
    expect(drawer(page).get_by_text('Bug', exact=True).first).to_be_visible(timeout=T)


def j_estimate_heldout(page, base):
    board(page, base)
    open_issue(page, 'Pin important comments')
    drawer(page).locator('button', has_text='Estimate').first.click(); page.wait_for_timeout(400)
    page.locator('button:visible', has_text=re.compile(r'^\s*8\s*$')).last.click(); page.wait_for_timeout(700)
    expect(drawer(page).locator('button', has_text='Estimate').first).to_contain_text('8 pts', timeout=T)


def j_project_breadcrumb(page, base):
    board(page, base)
    page.get_by_role('button', name=re.compile(r'^\s*Mobile')).locator('visible=true').first.click(); page.wait_for_timeout(700)
    expect(page.get_by_text(re.compile(r'Your workspace\s*/\s*Mobile')).locator('visible=true').first).to_be_visible(timeout=T)


JOURNEYS = [
    ('dashboard_counters', j_dashboard_counters),
    ('board_columns', j_board_columns),
    ('drawer_details', j_drawer_details),
    ('drawer_status_heldout', j_drawer_status_heldout),
    ('drawer_priority_heldout', j_drawer_priority_heldout),
    ('comment_heldout', j_comment_heldout),
    ('create_issue_heldout', j_create_issue_heldout),
    ('list_view', j_list_view),
    ('list_inline_status_heldout', j_list_inline_status_heldout),
    ('priority_filter_heldout', j_priority_filter_heldout),
    ('search_heldout', j_search_heldout),
    ('status_filter_heldout', j_status_filter_heldout),
    ('inbox_page', j_inbox_page),
    ('cycles_page', j_cycles_page),
    ('command_menu_heldout', j_command_menu_heldout),
    ('drag_heldout', j_drag_heldout),
    ('dashboard_after_complete', j_dashboard_after_complete),
    ('labels_heldout', j_labels_heldout),
    ('estimate_heldout', j_estimate_heldout),
    ('project_breadcrumb', j_project_breadcrumb),
]


# ---------------- ticket journeys (gaps found in the generated clone) ----------------

def reopen(page, base, title):
    board(page, base); open_issue(page, title); return drawer(page)


def j_t_watch_toggle(page, base):
    d = reopen(page, base, 'Pin important comments')
    d.get_by_role('button', name=re.compile(r'^\s*Watching\s*$')).first.click(); page.wait_for_timeout(700)
    expect(drawer(page).get_by_role('button', name=re.compile(r'^\s*Watch\s*$')).first).to_be_visible(timeout=T)
    close_drawer(page)
    d = reopen(page, base, 'Pin important comments')
    expect(d.get_by_role('button', name=re.compile(r'^\s*Watch\s*$')).first).to_be_visible(timeout=T)


def j_t_due_date(page, base):
    d = reopen(page, base, 'Pin important comments')
    row = d.locator('button', has_text='Due date').first
    expect(row).to_contain_text('5d left', timeout=T)
    row.click(); page.wait_for_timeout(400)
    click_near(drawer(page), row, re.compile(r'^\s*Tomorrow\s*$'), maxdx=900); page.wait_for_timeout(700)
    expect(drawer(page).locator('button', has_text='Due date').first).to_contain_text('Tomorrow', timeout=T)
    close_drawer(page)
    d = reopen(page, base, 'Pin important comments')
    row = d.locator('button', has_text='Due date').first
    expect(row).to_contain_text('Tomorrow', timeout=T)
    row.click(); page.wait_for_timeout(400)
    click_near(drawer(page), row, re.compile(r'^\s*Clear\s*$'), maxdx=900); page.wait_for_timeout(700)
    expect(drawer(page).locator('button', has_text='Due date').first).to_contain_text('None', timeout=T)


def j_t_delete_issue(page, base):
    page.on('dialog', lambda dlg: dlg.accept())
    d = reopen(page, base, 'High contrast theme')
    d.locator('button:has(svg.lucide-trash-2), button:has(svg.lucide-trash)').first.click(); page.wait_for_timeout(1000)
    expect(vis(page, 'High contrast theme')).to_have_count(0, timeout=T)
    board(page, base)
    expect(vis(page, 'High contrast theme')).to_have_count(0, timeout=T)
    expect(vis(page, 'Vim-style navigation keys').first).to_be_visible(timeout=T)


def j_t_comment_edit_delete(page, base):
    d = reopen(page, base, 'Generate SDK from the OpenAPI file')
    expect(d.get_by_text('Reminder: wrap this up before the cycle closes.').first).to_be_visible(timeout=T)
    d.locator('button[title="Edit"]').first.click(); page.wait_for_timeout(400)
    box = drawer(page).locator('textarea:visible').filter(has_not_text='Leave a comment')
    box = [t for t in drawer(page).locator('textarea:visible').all() if 'Reminder' in (t.input_value() or '')][0]
    box.fill('Reminder: ship it before Friday.')
    drawer(page).get_by_role('button', name=re.compile(r'^\s*Save\s*$')).first.click(); page.wait_for_timeout(800)
    expect(vis(page, 'Reminder: ship it before Friday.').first).to_be_visible(timeout=T)
    close_drawer(page)
    d = reopen(page, base, 'Generate SDK from the OpenAPI file')
    expect(d.get_by_text('Reminder: ship it before Friday.').first).to_be_visible(timeout=T)
    # comment-level delete: the button next to the comment's Edit button (header trash may share the title)
    d.locator('button[title="Edit"] ~ button[title="Delete"], button[title="Edit"] + button').first.click(); page.wait_for_timeout(800)
    expect(vis(page, 'Reminder: ship it before Friday.')).to_have_count(0, timeout=T)
    close_drawer(page)
    d = reopen(page, base, 'Generate SDK from the OpenAPI file')
    page.wait_for_timeout(500)
    expect(vis(page, 'Reminder: ship it before Friday.')).to_have_count(0, timeout=T)
    expect(vis(page, 'Reminder: wrap this up before the cycle closes.')).to_have_count(0, timeout=T)


def cycles(page, base):
    page.goto(base + '/app'); settle(page)
    page.get_by_role('link', name='Cycles').locator('visible=true').first.click(); settle(page, 900)


def j_t_cycle_shift(page, base):
    cycles(page, base)
    expect(vis(page, 'Cycle 2: Liftoff').first).to_be_visible(timeout=T)
    card = page.locator('div', has=vis(page, 'Cycle 2: Liftoff')).filter(has=page.get_by_role('button', name='+7d')).last
    expect(card).to_contain_text('Sep 21 → Oct 5', timeout=T)
    card.get_by_role('button', name='+7d').first.click(); page.wait_for_timeout(900)
    expect(page.get_by_text(re.compile(r'Sep 28\s*→\s*Oct 12')).locator('visible=true').first).to_be_visible(timeout=T)
    cycles(page, base)
    expect(page.get_by_text(re.compile(r'Sep 28\s*→\s*Oct 12')).locator('visible=true').first).to_be_visible(timeout=T)
    card = page.locator('div', has=vis(page, 'Cycle 1: Groundwork')).filter(has=page.get_by_role('button', name='−7d')).last
    card.get_by_role('button', name='−7d').first.click(); page.wait_for_timeout(900)
    expect(page.get_by_text(re.compile(r'Aug 31\s*→\s*Sep 14')).locator('visible=true').first).to_be_visible(timeout=T)


def j_t_sort_priority(page, base):
    board(page, base)
    btn = page.get_by_role('button', name=re.compile(r'^\s*Sort')).locator('visible=true').first
    btn.click(); page.wait_for_timeout(400)
    click_near(page, btn, re.compile(r'^\s*Priority\s*$')); page.wait_for_timeout(800)
    page.keyboard.press('Escape'); page.wait_for_timeout(300)
    y = lambda t: vis(page, t).first.bounding_box()['y']
    urgent = [y('Guest access with expiring links'), y('Kanban swimlanes for the release train')]
    high = [y('Live cursors in the shared editor'), y('Tablet layout clips the side panel')]
    assert max(high) < min(urgent), f'In Progress not sorted High before Urgent: high {high} urgent {urgent}'
    order = [y(t) for t in ['High contrast theme', 'Sprint scope-change report']]
    assert order[0] < order[1], 'Backlog: None should come before Medium'
    todo = [y('Quick switcher with fuzzy matching'), y('Pin important comments')]
    assert todo[0] < todo[1], 'Todo: Low should come before Medium'


def j_t_project_move(page, base):
    d = reopen(page, base, 'High contrast theme')
    row = d.locator('button', has_text='Project').first
    row.click(); page.wait_for_timeout(400)
    click_near(drawer(page), row, re.compile(r'^\s*Mobile'), maxdx=900); page.wait_for_timeout(900)
    expect(drawer(page).locator('button', has_text='Project').first).to_contain_text('Mobile', timeout=T)
    expect(drawer(page).get_by_text('MOB-1').first).to_be_visible(timeout=T)
    close_drawer(page)
    board(page, base)
    expect(page.get_by_text('MOB-1').locator('visible=true').first).to_be_visible(timeout=T)


def j_t_reaction(page, base):
    d = reopen(page, base, 'Pin important comments')
    d.locator('button[title="Add reaction"]').first.click(); page.wait_for_timeout(400)
    drawer(page).get_by_role('button', name='🎉').first.click(); page.wait_for_timeout(800)
    expect(drawer(page).locator('button', has_text='🎉').first).to_contain_text('1', timeout=T)
    close_drawer(page)
    d = reopen(page, base, 'Pin important comments')
    expect(d.locator('button', has_text='🎉').first).to_contain_text('1', timeout=T)


def j_t_quick_add(page, base):
    board(page, base)
    hb = vis(page, 'Backlog').first.bounding_box()
    btns = [b_ for b_ in page.locator('button[title="Quick add"]:visible').all()
            if hb['x'] - 20 <= b_.bounding_box()['x'] <= hb['x'] + 300 and abs(b_.bounding_box()['y'] - hb['y']) < 40]
    assert btns, 'no Quick add button in the Backlog column header'
    btns[0].click(); page.wait_for_timeout(400)
    inp = page.get_by_placeholder('Issue title…').locator('visible=true').first
    expect(inp).to_be_visible(timeout=T)
    inp.fill('Audit third-party scripts'); page.keyboard.press('Enter'); page.wait_for_timeout(1000)
    expect(vis(page, 'Audit third-party scripts').first).to_be_visible(timeout=T)
    assert_column(page, 'Audit third-party scripts', 'Backlog', 'quick-added card not in Backlog')
    board(page, base)
    assert_column(page, 'Audit third-party scripts', 'Backlog', 'quick add not persisted')
    expect(page.get_by_text('MAIN-15').locator('visible=true').first).to_be_visible(timeout=T)


JOURNEYS += [
    ('t_quick_add', j_t_quick_add),
    ('t_watch_toggle', j_t_watch_toggle),
    ('t_due_date', j_t_due_date),
    ('t_delete_issue', j_t_delete_issue),
    ('t_comment_edit_delete', j_t_comment_edit_delete),
    ('t_cycle_shift', j_t_cycle_shift),
    ('t_sort_priority', j_t_sort_priority),
    ('t_reaction', j_t_reaction),
]
