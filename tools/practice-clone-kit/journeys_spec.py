# Journeys driven against the ORIGINAL to build the recordings bundle.
# Each step: (kind, *args, '# optional note'). Kinds: goto, click, fill, press, select, hover, scroll, drag, wait.
# Selector forms: 'text=..', 'role=button:..', 'placeholder=..', 'label=..', 'testid=..', or CSS.
JOURNEYS = [
    ('01-dashboard', [
        ('goto', '/app', '# land on the workspace home'),
        ('scroll', 600),
        ('scroll', 800),
    ]),
    ('02-board-overview', [
        ('goto', '/app'),
        ('click', 'text=Board', '# open the board from the dashboard'),
        ('scroll', 400),
    ]),
    ('03-open-issue-drawer', [
        ('goto', '/app/board'),
        ('click', 'text=Pin important comments', '# open an issue'),
        ('scroll', 500),
        ('press', 'Escape', '# close the drawer'),
    ]),
    ('04-change-status-in-drawer', [
        ('goto', '/app/board'),
        ('click', 'text=Quick switcher with fuzzy matching'),
        ('click', 'aside.drawer-in button:has-text("Todo")', '# open the status picker'),
        ('click', 'role=button:In Progress', '# pick In Progress'),
        ('press', 'Escape'),
    ]),
    ('05-change-priority', [
        ('goto', '/app/board'),
        ('click', 'text=High contrast theme'),
        ('click', 'aside button:has-text("Priority")', '# open priority picker'),
        ('click', 'aside button:has-text("Urgent")'),
        ('press', 'Escape'),
    ]),
    ('06-add-comment', [
        ('goto', '/app/board'),
        ('click', 'text=Live cursors in the shared editor'),
        ('fill', 'placeholder=Leave a comment — ⌘/Ctrl + Enter to send', 'Looks good, shipping behind a flag first.'),
        ('click', 'role=button:Comment', '# send the comment'),
    ]),
    ('07-create-issue', [
        ('goto', '/app/board'),
        ('click', 'role=button:New issue'),
        ('fill', 'placeholder=Issue title — what needs to happen?', 'Export audit log as CSV'),
        ('fill', 'placeholder=Add context, steps to reproduce, or a link…', 'Admins need a monthly export for compliance.'),
        ('click', 'role=button:Create issue'),
        ('wait', 600),
    ]),
    ('08-list-view', [
        ('goto', '/app/board'),
        ('click', 'role=link:List', '# switch to list view'),
        ('scroll', 600),
    ]),
    ('09-list-inline-status', [
        ('goto', '/app/issues'),
        ('select', 'tr:has-text("Vim-style navigation keys") select, div:has-text("Vim-style navigation keys") >> select', 'Done', '# change status inline'),
        ('wait', 500),
    ]),
    ('10-filter-priority', [
        ('goto', '/app/board'),
        ('click', 'role=button:Priority', '# open priority filter'),
        ('click', 'button:has-text("Urgent (P0)")'),
        ('press', 'Escape'),
    ]),
    ('11-search-filter', [
        ('goto', '/app/board'),
        ('fill', 'placeholder=Filter issues…', 'theme'),
        ('wait', 500),
        ('fill', 'placeholder=Filter issues…', ''),
    ]),
    ('12-inbox', [
        ('goto', '/app'),
        ('click', 'role=link:Inbox'),
        ('click', 'role=button:Unread'),
    ]),
    ('13-cycles', [
        ('goto', '/app'),
        ('click', 'role=link:Cycles'),
        ('scroll', 500),
    ]),
    ('14-switch-project', [
        ('goto', '/app/board'),
        ('click', 'role=button:Mobile', '# switch to the Mobile project'),
        ('wait', 500),
        ('click', 'role=button:Main'),
    ]),
    ('15-command-menu', [
        ('goto', '/app/board'),
        ('press', 'Meta+k', '# open command menu'),
        ('fill', 'placeholder=Search issues, projects, people — or type a command', 'cursor'),
        ('press', 'Enter', '# open the matching issue'),
    ]),
    ('16-drag-card', [
        ('goto', '/app/board'),
        ('drag', 'text=Cut cold start time in half', 'text=In Progress', '# drag a backlog card to In Progress'),
        ('wait', 500),
    ]),
    ('17-complete-issue-dashboard', [
        ('goto', '/app/board'),
        ('click', 'text=Kanban swimlanes for the release train'),
        ('click', 'aside.drawer-in button:has-text("In Progress")'),
        ('click', 'role=button:Done'),
        ('press', 'Escape'),
        ('click', 'role=link:Home', '# check the dashboard counters'),
    ]),
]
