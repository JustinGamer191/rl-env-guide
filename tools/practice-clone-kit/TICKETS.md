# Quillstack clone tickets

Start the dev server with `bun dev.mjs` (frontend on `PORT`, default http://127.0.0.1:5173; backend on `BACKEND_PORT`, default 3001). The app's data is dated 2026-09-15. Chromium and Playwright are installed. Reference screenshots and DOM snapshots of the real app are in `recordings/` (read-only).

---

## QS-1 Add labels from the issue drawer

**Page:** /app/board (issue drawer) · **Type:** feature · **Size:** S

### Description
In the issue drawer, the "+ add label" link next to Labels does nothing.

### Requested behavior
- Clicking "+ add label" opens a picker listing every workspace label (Bug, Feature, Design, Chore, Performance).
- Clicking a label toggles it on the issue; the change is saved to the backend.

### Acceptance criteria
- [ ] Clicking "+ add label" shows the label chips, e.g. "Bug".
- [ ] Clicking "Bug" on MAIN-13 "Pin important comments" adds a "Bug" chip under Labels in the drawer.
- [ ] After a page reload, reopening the issue still shows the "Bug" label.

---

## QS-2 Set the estimate from the issue drawer

**Page:** /app/board (issue drawer) · **Type:** feature · **Size:** S

### Description
The Estimate row in the issue drawer cannot be changed.

### Requested behavior
- Clicking the Estimate row opens a picker with the values 0.5, 1, 2, 3, 5, 8, 13 and a "Clear" button.
- Picking a value saves it; the row reads "<n> pts". Clear removes the estimate (row reads "None").

### Acceptance criteria
- [ ] Clicking Estimate on "Pin important comments" and picking "8" makes the row read "8 pts".
- [ ] The new estimate survives a reload.
- [ ] An issue with no estimate shows "None" in the Estimate row.

---

## QS-3 Set or clear the due date from the issue drawer

**Page:** /app/board (issue drawer) · **Type:** feature · **Size:** M

### Description
The Due date row in the issue drawer cannot be changed, and an issue without a due date reads "No due date" instead of "None".

### Requested behavior
- Clicking the Due date row opens a picker with a date input and the quick options "Today", "Tomorrow", "In a week", "In two weeks", plus "Clear".
- A quick option sets the date relative to today; "Clear" removes it. Changes are saved.
- The row label uses the same wording as the cards: "Today", "Tomorrow", "<n>d left", "<n>d overdue", or a short date like "Sep 22"; with no date it reads "None".

### Acceptance criteria
- [ ] "Pin important comments" shows "5d left"; choosing "Tomorrow" makes the row read "Tomorrow", and it persists after reload.
- [ ] Choosing "Clear" makes the row read "None".

---

## QS-4 Watch / unwatch an issue

**Page:** /app/board (issue drawer) · **Type:** feature · **Size:** S

### Description
The "Watching" button in the issue drawer header does nothing.

### Requested behavior
- Clicking "Watching" stops watching: the button label becomes "Watch" and a toast "Stopped watching" appears. Clicking "Watch" starts watching again (toast "Watching this issue").
- The watch state is saved per issue.

### Acceptance criteria
- [ ] Clicking "Watching" on "Pin important comments" changes the button to "Watch".
- [ ] After closing and reopening the drawer (with a reload in between), the button still reads "Watch".

---

## QS-5 Delete an issue from the drawer

**Page:** /app/board (issue drawer) · **Type:** feature · **Size:** S

### Description
The trash button in the issue drawer header does nothing.

### Requested behavior
- Clicking the trash button asks for confirmation with the browser dialog "Delete MAIN-10? This cannot be undone." (using the issue's key).
- On confirm, the issue is deleted on the backend, the drawer closes and the card disappears from the board.

### Acceptance criteria
- [ ] Deleting "High contrast theme" removes its card from the board, and it stays gone after a reload.
- [ ] Other cards (e.g. "Vim-style navigation keys") are unaffected.

---

## QS-6 Edit and delete comments

**Page:** /app/board (issue drawer) · **Type:** feature · **Size:** M

### Description
The pencil (title "Edit") and trash (title "Delete") buttons under each comment do nothing.

### Requested behavior
- "Edit" turns the comment into a textarea with "Save" and "Cancel" buttons. "Save" stores the new text.
- "Delete" removes the comment.
- Both changes are saved to the backend.

### Acceptance criteria
- [ ] On MAIN-11 "Generate SDK from the OpenAPI file", editing the comment "Reminder: wrap this up before the cycle closes." to "Reminder: ship it before Friday." shows the new text, also after reload.
- [ ] Deleting that comment removes it, also after reload.

---

## QS-7 Shift cycle dates by a week

**Page:** /app/cycles · **Type:** feature · **Size:** M

### Description
The "−7d" and "+7d" buttons on each cycle row do nothing.

### Requested behavior
- "+7d" moves both the start and end of that cycle one week later; "−7d" one week earlier. The change is saved.
- The cycle row's date range updates, e.g. "Sep 21 → Oct 5" becomes "Sep 28 → Oct 12".

### Acceptance criteria
- [ ] "+7d" on "Cycle 2: Liftoff" shows "Sep 28 → Oct 12", and it persists after reload.
- [ ] "−7d" on "Cycle 1: Groundwork" shows "Aug 31 → Sep 14".

---

## QS-8 Sort the board

**Page:** /app/board · **Type:** feature · **Size:** M

### Description
The "Sort" button in the filter bar does nothing.

### Requested behavior
- "Sort" opens a menu with: Last updated, Created, Priority, Status, Due date, Estimate, Title, Issue number.
- Choosing an option re-orders the cards inside every column. "Priority" orders from lowest to highest priority: None, Low, Medium, High, Urgent.

### Acceptance criteria
- [ ] With Sort → "Priority", in the In Progress column both High issues ("Live cursors in the shared editor", "Tablet layout clips the side panel") appear above both Urgent issues.
- [ ] In Backlog, "High contrast theme" (None) appears above "Sprint scope-change report" (Medium); in Todo, "Quick switcher with fuzzy matching" (Low) appears above "Pin important comments" (Medium).

---

## QS-9 Emoji reactions on an issue

**Page:** /app/board (issue drawer) · **Type:** feature · **Size:** M

### Description
The smiley button (title "Add reaction") under the issue description does nothing.

### Requested behavior
- It opens a picker with 👍 🔥 🎉 🚀 ❤️ 👀 ✅ 🙌.
- Picking an emoji adds a reaction pill showing the emoji and a count; clicking the pill again removes your reaction. Reactions are saved.

### Acceptance criteria
- [ ] Reacting 🎉 to "Pin important comments" shows a 🎉 pill with count 1.
- [ ] The reaction is still there after reload.

---

## QS-10 Quick add a card inside a board column

**Page:** /app/board · **Type:** feature · **Size:** S

### Description
The "+" (title "Quick add") button in a column header opens the full New issue dialog. In the real app it adds an inline title field at the top of that column.

### Requested behavior
- Clicking "Quick add" on a column shows an inline input with placeholder "Issue title…" inside that column.
- Typing a title and pressing Enter creates the issue in that column's status, with the next issue key; Escape cancels.

### Acceptance criteria
- [ ] Quick add on Backlog, typing "Audit third-party scripts" + Enter, shows the card in Backlog as MAIN-15.
- [ ] The card is still in Backlog after a reload.
