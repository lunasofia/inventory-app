# Manual Test Plan

Manual regression checklist for **Packwell**. Re-run the relevant section after
changes to avoid regressions.

> **UI overhaul (2026-06-23):** adopted the Packwell design (Django+HTMX, no
> React). The app now has a **persistent left sidebar** (trip list w/ progress;
> mobile drawer + top bar), and **planning + packing are merged into one trip
> board** with a **By bag / By category / All items** toggle, tap-to-toggle
> rows, per-row edit/delete, and an add-item modal/FAB. The separate "Packing
> mode" page is **retired** (check-off is inline). The home route (`/`)
> **redirects to your most relevant trip** (or a welcome screen if you have
> none). Sections below reflect this.

> Most of this checklist is now also covered by the **automated suite** (`make
> test` / `pytest`, run in CI on every push) — see `tests/`. This manual plan
> remains useful for **visual/exploratory** checks and the JavaScript-driven
> interactions (autocomplete picking, inline-edit swaps) that the HTTP-level
> tests don't exercise.

## Setup

1. From the repo root: `.venv/bin/python manage.py runserver 8000`
2. Open <http://127.0.0.1:8000/>
3. Test accounts (local dev):
   - **Demo user:** `tourist@example.com` / `packwell-demo-2026`
   - **Admin/superuser** (`/admin/`): `admin@example.com` / `packwell123`

> Tip: for a clean slate, register a brand-new account — signup auto-seeds
> default categories and conditions for that user.

Legend: each case lists **Steps → Expected**. ✅ = pass, mark the date/result.

---

## 1. Registration & account seeding

| # | Steps | Expected |
|---|-------|----------|
| 1.1 | Go to `/accounts/register/`, fill email + display name + matching passwords, submit | Redirects to dashboard, logged in; top bar shows your display name |
| 1.2 | Register with an email that already exists | Form re-renders with an "already exists" error; no account created |
| 1.3 | Register with mismatched passwords | Form error on password confirmation; no account created |
| 1.4 | Register with a too-short / too-common password | Validation error shown; no account created |
| 1.5 | After 1.1, check `/admin/` → Categories & Conditions for the new user | 6 categories (Clothing, Toiletries, Electronics, Documents, Health, Misc) and 4 conditions (OK [default], Missing, Needs restock, Needs laundry) exist |
| 1.6 | While logged in, visit `/accounts/register/` | Redirects to dashboard (no double-registration) |

## 2. Login & logout

| # | Steps | Expected |
|---|-------|----------|
| 2.1 | Log out (top bar), then visit `/` | Redirected to `/accounts/login/?next=/` |
| 2.2 | Log in with correct credentials | Redirected to dashboard |
| 2.3 | Log in with wrong password | Error shown; stays on login page |
| 2.4 | Visit `/accounts/login/` while already logged in | Login page (or redirect) — does not error |
| 2.5 | Log out | Redirected to login; protected pages no longer accessible |

## 3. Profile

| # | Steps | Expected |
|---|-------|----------|
| 3.1 | Go to `/accounts/profile/`, change display name, save | Success message; top bar reflects new name |
| 3.2 | Visit `/accounts/profile/` while logged out | Redirected to login |

## 4. Dashboard

| # | Steps | Expected |
|---|-------|----------|
| 4.1 | Brand-new account with no trips → visit `/` | "Welcome to Packwell" screen with a "Create your first trip" button |
| 4.2 | With ≥1 trip → visit `/` | Redirects to your most relevant (non-complete) trip |
| 4.3 | The sidebar (desktop) / drawer (mobile) | Lists all your trips (owned + shared) with per-trip progress bars; current trip highlighted |
| 4.4 | Sidebar trip entry | Shows name, destination, mini progress bar, and `packed/total` count; links to the trip |

## 5. Trip — create

| # | Steps | Expected |
|---|-------|----------|
| 5.1 | Dashboard → "+ New trip", fill name only, submit | Trip created; redirected to its detail page; success message |
| 5.2 | Create with all fields (destination, start/end dates, status, notes) | All values shown correctly on detail page |
| 5.3 | Create with end date **before** start date | Form re-renders with "End date cannot be before the start date."; no trip created |
| 5.4 | Submit with empty name | Form error (name required); no trip created |
| 5.5 | "Cancel" on the new-trip form | Returns to dashboard; nothing created |

## 6. Trip — view (detail)

| # | Steps | Expected |
|---|-------|----------|
| 6.1 | Open a trip you own | Shows name, destination, status badge, dates, owner, notes; Edit + Delete buttons visible |
| 6.2 | Trip with no items | Packing-list section shows "No items yet" placeholder |
| 6.3 | Visit `/trips/<id>/` for a nonexistent or non-accessible trip | 404 |

## 7. Trip — edit

| # | Steps | Expected |
|---|-------|----------|
| 7.1 | Detail → Edit, change name + status, save | Redirected to detail; changes reflected; success message |
| 7.2 | Edit with end date before start date | Validation error; no change saved |
| 7.3 | "Cancel" on edit form | Returns to detail unchanged |

## 8. Trip — delete

| # | Steps | Expected |
|---|-------|----------|
| 8.1 | Detail → Delete | Confirmation page naming the trip |
| 8.2 | Confirm delete | Redirected to dashboard; success message; trip gone from list |
| 8.3 | Visit the deleted trip's `/trips/<id>/` | 404 |
| 8.4 | Cancel on the confirmation page | Returns to detail; trip intact |

## 9. Access control & sharing (foundation)

> Full sharing UI lands in Task 8; these verify the access guards already in place.

| # | Steps | Expected |
|---|-------|----------|
| 9.1 | As user A, note a trip id; log in as user B; visit `/trips/<A's id>/` | 404 (not visible to B) |
| 9.2 | As user B, attempt `/trips/<A's id>/edit/` and `/delete/` directly | 404 |
| 9.3 | Any protected URL while logged out | Redirected to login with `?next=` |

---

## 10. Packing list — add items (Task 4)

Open the trip detail (planning) page as the owner.

| # | Steps | Expected |
|---|-------|----------|
| 10.1 | Type "Wool socks", quantity 3, category "Clothing", Add | Appears under "Clothing" as "3× Wool socks" with no full-page reload (HTMX) |
| 10.2 | After an add | Add field clears and refocuses for the next entry |
| 10.3 | Add with quantity blank | Defaults to 1 |
| 10.4 | Add with no category | Appears under an "Uncategorized" group |
| 10.5 | Submit empty name | Not added; "This field is required." shown; no blank row |
| 10.6 | Add with quantity 0 | Rejected: "Quantity must be at least 1." |
| 10.7 | Add the same name twice | Both lines allowed (duplicates permitted; no auto-merge) |
| 10.8 | Watch the packed/total count | Updates to reflect the new total |

## 11. Hybrid catalog & autocomplete (Task 4)

| # | Steps | Expected |
|---|-------|----------|
| 11.1 | Add a brand-new item | A `catalog.Item` is created for the acting user (verify in `/admin/`) |
| 11.2 | Add a name matching an existing catalog item, any casing ("wool socks") | No duplicate catalog item; existing reused; its `times_used` increments |
| 11.3 | On a new trip, type "wo" after "Wool socks" is in the catalog | Suggestion dropdown lists matches, ranked by `times_used` |
| 11.4 | Click a suggestion | Name fills in; its category pre-fills if set |
| 11.5 | Type a name with no matches | No suggestions; can still add |
| 11.6 | A different user | Does not see this user's catalog suggestions |

## 12. Edit & remove items (Task 4)

| # | Steps | Expected |
|---|-------|----------|
| 12.1 | Click Edit, change quantity + category, Save | Row updates in place; moves to the new category group; counts update |
| 12.2 | Edit name to empty, Save | Validation error; original retained |
| 12.3 | Cancel an inline edit | Reverts to display unchanged |
| 12.4 | Remove an item | Disappears via HTMX; counts update |
| 12.5 | Remove the last item in a category | The empty category heading disappears |
| 12.6 | Remove the last item on the trip | "No items yet" empty state returns |
| 12.7 | After removing a packing line | The underlying catalog Item still exists (catalog is preserved) |

## 13. Grouping & ordering (Task 4)

| # | Steps | Expected |
|---|-------|----------|
| 13.1 | Add items across multiple categories | Grouped under category headings, not a flat list |
| 13.2 | Heading order | **Alphabetical** by category name |
| 13.3 | Categories with no items on this trip | Show no heading |
| 13.4 | Uncategorized items | Grouped under a single "Uncategorized" heading, shown **last** |
| 13.5 | Reload the page | Items persist in the same groups/order |
| 13.6 | Items within a group | Ordered by category, then bag, then name (all case-insensitive); uncategorized/unbagged sort last within their tier |

## 14. Planning view — access control (Task 4)

| # | Steps | Expected |
|---|-------|----------|
| 14.1 | Owner opens planning view | Add/edit/remove controls visible and functional |
| 14.2 | View-only shared user opens the trip | Item list visible; **no add form / edit / remove controls** |
| 14.3 | View-only user POSTs directly to add/edit/delete endpoints | Rejected (404) |
| 14.4 | Edit-share user | Can add/edit/remove |

---

## Resolved design decisions (Task 4)

- **Duplicate names on a trip:** allowed (separate lines, no auto-merge).
- **Catalog ownership & category dropdown on shared trips:** the **acting
  user's** catalog and categories (their own memory), not the trip owner's.
- **Catalog matching:** case-insensitive (`name__iexact`).

## 15. Bags / containers (Task #12)

Open a trip's planning page. A **bag** is a per-trip named container; items can
be assigned to one; the list can be grouped by bag or category.

| # | Steps | Expected |
|---|-------|----------|
| 15.1 | Add a bag "Blue duffel" via the bags bar | Bag chip appears |
| 15.2 | Add a bag with the same name (any casing) | Rejected: "You already have a bag with that name." |
| 15.3 | Add a bag with an empty name | Rejected (required); no bag created |
| 15.4 | Rename "Blue duffel" → "Black roller" | Name changes; items in it untouched |
| 15.5 | Delete a bag that has items | Bag gone; its items become Unbagged (not deleted) |
| 15.6 | Add an item and assign it to a bag | Item shows the bag tag; under that bag in bag view |
| 15.7 | Edit an item and change its bag | Item moves to the new bag |
| 15.8 | Toggle "Group by: Bag" | Headings become bag names, alphabetical; Unbagged last; empty bags show no heading |
| 15.9 | Toggle "Group by: Category" | Returns to category grouping |
| 15.10 | "Mark packed" on a bag heading (bag view) | Every item in the bag becomes packed in one tap; progress jumps; bag offers "Mark unpacked" |
| 15.11 | "Mark unpacked" on a packed bag | Its items become unpacked; progress drops |
| 15.12 | Pack each item in a bag individually until all packed | Bag automatically reads as packed (status derived from items) |
| 15.13 | Reload the page | Bags, assignments, and grouping default (category) persist; statuses persist |
| 15.14 | View-only shared user | Sees bags + can toggle lens; no add/rename/delete/assign/mark controls; direct POSTs → 404 |

## 16. Unified trip board — check-off & views

The single trip screen (`/trips/<pk>/`) merges planning and packing.

| # | Steps | Expected |
|---|-------|----------|
| 16.1 | Open a trip | One screen: header + progress, bag summary strip, By bag/By category/All items toggle, grouped item rows |
| 16.2 | Tap an item row | Toggles packed (checkbox fills, label dims/strikes) without a full reload |
| 16.3 | Tap a packed row | Toggles back to unpacked |
| 16.4 | Check items off | Overall progress bar + "N/total" update live; bag-strip counts update |
| 16.5 | Check the last remaining item | Progress hits 100%; "All packed" message shown |
| 16.6 | Switch to "By bag" | Groups become bags (alphabetical, Unbagged last); "Pack all/Unpack all" per bag |
| 16.7 | Switch to "By category" | Groups become categories |
| 16.8 | Switch to "All items" | Two groups: "To pack — N" and "Packed — N"; each row shows category + bag chips |
| 16.9 | "Pack all" on a bag heading (by-bag view) | All items in the bag check off; progress jumps; offers "Unpack all" |
| 16.10 | Per-row edit (✎) / delete (✕) | Edit opens an inline edit row; delete confirms and removes; both update the board |
| 16.11 | "Add item" button / mobile FAB | Opens the add-item modal/sheet; adding updates the board and closes the modal |
| 16.12 | View-only shared user | Sees the board read-only; no toggle/edit/add controls; direct POST to toggle/add/etc. → 404 |
| 16.13 | Reload after checking items | Packed states persist |
| 16.14 | Open the trip on a narrow viewport | Sidebar collapses to a hamburger→drawer; FAB shows; bag strip scrolls horizontally |

## 17. Templates / reuse (Task #6)

Reuse a packing list across trips; keep the baseline from drifting via a diff view.

| # | Steps | Expected |
|---|-------|----------|
| 17.1 | On a trip, "Save as template", name it | Template created with an item per packing line (name/category/quantity); packed state not copied |
| 17.2 | Save with a duplicate template name (same owner) | Rejected: "already have a template with that name" |
| 17.3 | New trip → "Start from template" → pick one | Trip populated from the template; trip's `origin_template` set |
| 17.4 | Cloned items | Linked to catalog; `times_used` NOT bumped by the clone |
| 17.5 | New trip with no template | Empty list; no origin template |
| 17.6 | Templates nav → list | Shows your templates with item counts |
| 17.7 | Template detail: add / edit / remove items | Inline HTMX editing persists |
| 17.8 | Rename / delete a template | Updates / removes; trips made from it unaffected |
| 17.9 | Another user's template (view/edit/delete) | 404 |
| 17.10 | View-only shared trip → "Save as template" | Allowed; template owned by the acting user |
| 17.11 | "Update template…" on a trip with an origin | Diff view: Added / Removed / Changed (quantity or category) vs the template |
| 17.12 | Select some changes → Apply selected | Only chosen changes written to the template; others untouched |
| 17.13 | Diff matching | Case-insensitive by name (e.g. "wool socks" vs "Wool socks" = a change, not add+remove) |
| 17.14 | "Update template…" on a trip with no origin | Picker to choose a target template, or "Save as new template" |
| 17.15 | Template: owner opens detail → Share | Owner-only "Share" button visible in action bar; modal opens with current collaborators and add-by-email form |
| 17.16 | Add a registered user's email to a template with "Can edit" | Collaborator added; appears in the list with permission set to "Can edit" |
| 17.17 | Add an email not associated with an account | Rejected: "No Packwell account with that email."; no share created |
| 17.18 | Add your own email to a template | Rejected: "You already own this template."; no share created |
| 17.19 | Re-add an existing template collaborator with a different permission | Updates their permission (no duplicate entry) |
| 17.20 | Change a collaborator's permission in the template share modal | Permission updates immediately; collaborator's view of template adjusts (edit → can edit template content; view → read-only) |
| 17.21 | Revoke a template collaborator | Removed from list; collaborator loses access to the template (404 on detail) |

## 18. Category management (small feature)

Add / rename / delete your own categories. Categories are **global to the user**
(shared across all trips and templates). Panel on the planning view + a manager
page linked from Profile.

| # | Steps | Expected |
|---|-------|----------|
| 18.1 | In the Categories panel, add "Beach gear" | Created; appears as a chip and becomes selectable in item dropdowns |
| 18.2 | Add an existing name, any casing | No duplicate (case-insensitive dedupe) |
| 18.3 | Add an empty name | Rejected; nothing created |
| 18.4 | Rename a category (fix a typo) | Name updates; items keep their association (now show the new name) |
| 18.5 | Rename to a name that duplicates another | Rejected: "already have a category with that name" |
| 18.6 | Delete a category in use | Confirm states impact ("used by N items… they'll become Uncategorized") |
| 18.7 | Confirm delete | Category gone; affected items across all trips + template entries become Uncategorized; items not deleted |
| 18.8 | After add/delete | Reflected in item dropdowns and the template editor (global) |
| 18.9 | Another user's category (rename/delete) | 404 |
| 18.10 | Category panel placement | Shown on the planning view (when editable) and on the `/categories/` page linked from Profile |

## Resolved design decisions (Categories)

- Categories are **global to the user**; managed in one place, reflected
  everywhere. No schema change (reuses `catalog.Category`).
- Add **dedupes case-insensitively**; rename enforces case-insensitive uniqueness.
- **Delete** uses the existing `SET_NULL` FKs → items everywhere become
  Uncategorized (never deleted); confirm shows usage count (packing + template
  items).
- Panel re-renders the planning region on the planning view (dropdowns refresh)
  and just the panel on the standalone manager page.

## Resolved design decisions (Templates)

- Drift solved via a **diff view** (added/removed/changed), promoted back per-change.
- Match by **name, case-insensitive**; duplicate-named trip lines aggregated
  (quantities summed) for the diff.
- Changed = **quantity or category** differs; applying updates both.
- Applying a category resolves to the **template owner's** category by name
  (no cross-user leak).
- Trips remember their **origin template** (`Trip.origin_template`).
- v1 templates capture **name + category + quantity** only (bags deferred).

## 19. Sharing (Task #8)

Owner shares a trip with registered users (view/edit). Share UI is a modal from
the trip header (owner only).

| # | Steps | Expected |
|---|-------|----------|
| 19.1 | As owner, click "Share" | Modal opens: current collaborators + add-by-email form |
| 19.2 | Add a registered user's email, "Can edit" | Added; appears in the list |
| 19.3 | Email with no account | Rejected: "No Packwell account with that email." |
| 19.4 | Your own email | Rejected: "You already own this trip." |
| 19.5 | Re-add an existing collaborator | No duplicate; updates their permission |
| 19.6 | Open the Share modal | A "Recent people" row shows your past collaborators as **always-visible chips labeled by display name** (excludes those already on the trip); clicking one fills their email. Typing also still autocompletes. |
| 19.7 | Change a collaborator view↔edit | Permission updates; takes effect immediately |
| 19.8 | Remove a collaborator | Gone from list; trip leaves their sidebar; their access 404s |
| 19.9 | Edit-collaborator logs in | Trip shows in sidebar with "shared" tag; can add/edit/check off |
| 19.10 | View-collaborator logs in | Trip read-only; mutating endpoints 404 |
| 19.11 | Non-owner hits any share endpoint | 404 (only the owner manages sharing) |
| 19.12 | Owner deletes the trip | Disappears from all collaborators' sidebars |

## 20. Final check / exit page (Task #13)

A "Final check" page (from the trip board) with two lists for any departure.

| # | Steps | Expected |
|---|-------|----------|
| 20.1 | Click "Final check" on a trip | Page with **Final reminders** + **Items not yet packed** lists, and links to the board + template-diff |
| 20.2 | First open | Reminders seed from the template's (if from one) else your default reminders |
| 20.3 | Tick / untick a reminder | Persists per trip across reload |
| 20.4 | Add / remove a trip reminder | Affects this trip only |
| 20.5 | "Reset to defaults" | Re-seeds this trip's reminders |
| 20.6 | Tap an unpacked item | Marked packed; drops off the not-yet-packed list |
| 20.7 | Last unpacked item checked | "Everything's packed" state |
| 20.8 | Reminders settings page (`/reminders/`, from Profile/sidebar) | Add/remove your default reminders |
| 20.9 | Template detail | Has a "Final-check reminders" section (add/remove); these seed trips made from it |
| 20.10 | View-only collaborator | Both lists read-only; mutating endpoints → 404 |

## Resolved design decisions (Final check)

- One page for any departure (leaving home or heading home).
- Two lists: **final reminders** (default + per-template + per-trip; ticks
  persist per trip; lazy-seeded once, `Reset to defaults` re-seeds) and
  **items not yet packed** (tappable to check off). Plus links to the board and
  the template-diff flow. **No per-item flags.**

## Resolved design decisions (Sharing)

- Registered users only (by email); unknown email rejected. Owner-only manages
  sharing; permissions view/edit; owner keeps delete + manage-sharing.
- Re-adding updates permission (no duplicate). Revoke cuts access immediately.
- **Recent collaborators** suggested from prior shares (both directions);
  no new model. No notifications; async last-write-wins; recipient self-leave
  deferred. Reuses the existing access helpers — no model changes.

## Resolved design decisions (Bags)

- **Per-trip bags** (no reusable "bags I own" library yet; reuse comes via
  templates). No logical/physical split — a bag is just a named container.
- **"Swap the bag"** = rename a bag (contents stay) and/or move items between bags.
- **Bag-level status is a bulk shortcut over items** — "mark bag packed" sets
  every item packed; a bag *displays* packed when it has items and all are packed.
- **Bag vs category are two grouping lenses**; lens defaults to category on each
  full page load (not yet remembered across visits). Unbagged group shown last.
- Bag names are **unique (case-insensitive) per trip**.

## 21. CSV import (templates & packing lists)

Populate a template or a trip's packing list by uploading a CSV instead of
typing items one at a time.

| # | Steps | Expected |
|---|-------|----------|
| 21.1 | Templates list → "Import CSV", enter a name + choose a CSV | New template created; items imported; redirected to it with `Imported N items…` |
| 21.2 | Template detail (edit rights) → "Import CSV" | Items appended after existing ones; counts in the message |
| 21.3 | Trip planning (edit rights) → "Import CSV" | Items appended to the packing list; catalog remembers them; default condition set |
| 21.4 | CSV with header `name,quantity,category` (any order/case) | `name` required; blank names skipped; blank/invalid quantity → 1; category auto-created by name |
| 21.5 | CSV missing a `name` column | Form error; nothing created |
| 21.6 | Empty file / zero valid rows | Friendly "No items found" message; nothing created |
| 21.7 | Non-UTF-8 or over 1 MB / 500 rows | Form error; nothing created |
| 21.8 | View-only collaborator hits an import endpoint | 404 |

## Resolved design decisions (CSV import)

- Columns `name` / `quantity` / `category`, header required, matched
  case-insensitively in any order; extra columns ignored. UTF-8 (+ BOM); caps
  1 MB / 500 rows. Whole import is one transaction.
- Category names resolve to the **acting** user (shared-template safety); trip
  imports mirror normal add-item (catalog `_remember_item` + default condition).
- Uploads are plain full-page POSTs (not HTMX) — simpler for file inputs.

## 22. Add from template (compose multiple templates)

Build one packing list from several templates — at creation and afterward.

| # | Steps | Expected |
|---|-------|----------|
| 22.1 | Trip → new, "Start from templates" multi-select, pick two | Trip created with the **union** of both templates' items; overlapping names not duplicated |
| 22.2 | Create from exactly one template | `origin_template` set (diff/drift flow still offered) |
| 22.3 | Create from two or more templates | `origin_template` left null |
| 22.4 | Trip detail (edit rights) → "Add from template", choose a template | Its items append after the current list; dedup by name; `Added N items… (M skipped)` |
| 22.5 | Add the same template again | All items skipped as duplicates |
| 22.6 | Add an empty template | `"<template>" has no items to add.`; nothing created |
| 22.7 | View-only collaborator / inaccessible template | 404 |
| 22.8 | Any add-from-template | Items catalog-linked (usage **not** bumped) + default condition set |

## Resolved design decisions (Add from template)

- **Both entry points**: multi-select at creation + a repeatable "Add from
  template" modal (mirrors the Add-item modal) on the trip planning header.
- **Skip duplicates by name** (case-insensitive) against items already on the
  trip; dedup also accumulates across a multi-template batch.
- Cloning reuses the single-template semantics (`_clone_template_into_trip`,
  now returning `(added, skipped)`): catalog-linked without bumping usage,
  default condition, owner-resolved categories, appended `sort_order`.
- `origin_template` set only when exactly one template seeds a new trip;
  add-from-template on an existing trip never changes it.

## 23. Quick move (reassign bag / category from the row)

A per-row **move** button (⇄) next to edit/delete that reassigns an item without
opening the full edit form. It is **context-aware**: it moves the item's **bag**
when grouped by bag and its **category** when grouped by category.

| # | Steps | Expected |
|---|-------|----------|
| 23.1 | Group "By bag", click ⇄ on an item, pick another bag | Row swaps to a single bag dropdown; on selecting, item reflows into the chosen bag's group; board re-renders |
| 23.2 | In the move dropdown, pick the blank option | Item becomes **Unbagged** and lands in the "Unbagged" group (shown last) |
| 23.3 | Group "By category", click ⇄, pick another category | Moves the item's **category**; item reflows to that category group |
| 23.4 | In category-mode move, pick the blank option | Item becomes **Uncategorized** (group shown last) |
| 23.5 | Group "All items", look at each row | **No ⇄ button** (move is meaningless without a bag/category lens) |
| 23.6 | Click ⇄ then "Cancel" | Row reverts to its display state (via `item_row`); no change saved |
| 23.7 | View-only shared user | No ⇄ button; a direct POST to the move endpoint → 404 |
| 23.8 | Move preserves other fields | Name, quantity, packed state, condition, notes unchanged after a move |
| 23.9 | Render/smoke check | The move row + ⇄ button render with **ASCII quotes** and valid HTMX attributes; existing edit/delete markup intact |

## Resolved design decisions (Quick move)

- The ⇄ button reuses the **edit swap mechanic** (`hx-get` swaps just that row;
  Cancel restores via `item_row`) but swaps into a **single-dropdown move row**
  that **auto-submits on change** (`hx-trigger="change"`) — two interactions vs.
  the four the full edit form takes.
- **Target field derives from the current group lens** (`_group_mode`): bag in
  bag-mode, category in category-mode; hidden entirely in "all" mode.
- Only the moved field is saved (`update_fields`); bag choices scoped to the
  trip, category choices to the **acting** user (mirrors `PackingItemForm`).

## 24. Category & Bag colors + template-view category creation

### Steps → Expected

| Step | Expected |
|------|----------|
| Open /categories/ (or the trip planning panel) | Each category chip is rendered with its stored swatch color (e.g. Clothing = amber yellow, Toiletries = rose pink) |
| Click the color-square (&#9632;) button on a category chip | A color picker inline replaces the chip, showing 12 colored dots |
| Click a swatch dot in the picker | Chip immediately updates to the chosen color; change persists on reload |
| Click Cancel in the picker | Chip restores to plain display with no change |
| Open a trip's planning panel; click color-square on a bag chip | Bag color picker appears with 12 swatches |
| Choose a new swatch for a bag | Bag chip updates to chosen color |
| Create a new user; inspect their default categories | Clothing=amber, Electronics=terracotta, Documents=sage, Toiletries=rose, Health=coral, Misc=sand |
| Create a new category from the /categories/ page | Chip renders with a random swatch from the 12-swatch palette |
| Open a template detail page as owner | A "Categories" section appears below Items, showing the categories panel with colored chips and an add form |
| Add a category from the template detail page | New category appears in the panel; `id="template-categories"` is used (not `id="categories"`) |
| View a trip item in "By bag" mode | Item's category chip uses `swatch-<slug>` class (not old `cat-<name>` class) |
| View exit page (final check) | Unpacked items show category chips with swatch colors |
| Share a template as view-only; log in as view-only; try to add a category via the template panel | 404 — view-only users cannot add categories via the template param |
| Try to set a bag color as a view-only trip share | 404 |

### Resolved design decisions

- **12-swatch palette:** amber, terracotta, sage, rose, coral, sand, sky, lavender, teal, lime, peach, slate. Swatches are defined as `SWATCHES` in `catalog/models.py` and shared with `trips/models.py` via import.
- **Random default via callable:** `default=random_swatch` (a callable) means each newly created Category or Bag gets a random swatch without manual intervention.
- **Seeded defaults keep mapped colors:** `seed_user_defaults` uses `DEFAULT_CATEGORY_COLORS` so the 6 standard categories always start with their brand-appropriate swatch (amber for Clothing etc.), not a random one.
- **Picker on categories+bags everywhere:** `_category_chip.html` always shows the color picker button (no `can_edit` guard — the panel is already owner-scoped). Bag picker requires trip edit permission.
- **Template panel mirrors trip panel:** `_categories_panel` accepts `template=` kwarg; `_categories.html` renders `id="template-categories"` when in template context; `category_add` / `category_rename` / `category_delete` all read `_opt_template` and route the re-render accordingly.

## 25. "Hide packed" filter

| # | Steps | Expected |
|---|-------|----------|
| 25.1 | Open a trip with a mix of packed and unpacked items; click **Hide packed** | Packed items disappear from all groups; button becomes highlighted (active) |
| 25.2 | While Hide packed is on, unpack an item (click its checkbox) | The item reappears; the filter stays active |
| 25.3 | While Hide packed is on, check off an unpacked item | The newly-packed item disappears from the list immediately |
| 25.4 | While Hide packed is on, switch group lens (By bag / By category / All items) | Items remain filtered across all lenses; button stays highlighted |
| 25.5 | While Hide packed is on, a group whose only items are all packed | The entire group heading disappears (empty group is not rendered) |
| 25.6 | Click **Hide packed** again (toggle off) | Packed items reappear; button returns to its inactive style |
| 25.7 | With Hide packed on, navigate away and return to the trip (full page load) | Filter resets to **off**; all items show — mirrors the group lens reset |
| 25.8 | With Hide packed on, all items are packed | Board shows no groups / empty-state message; "All packed" progress banner still appears at top |
| 25.9 | Render/smoke check | "Hide packed" button renders with ASCII quotes and valid HTMX attributes (`hx-target="#planning"`); no smart quotes |

## Design decision: "Hide packed" filter state

- State kept in session per trip (`session['hide_packed_{trip.pk}']`), **same as the group lens**.
- **Resets to off on every full page load** of the trip detail view — consistent with group lens behavior; user starts each visit with a full view of their list.
- The toggle is a GET endpoint (`set_hide_packed`) that flips the session bool and returns the re-rendered `#planning` fragment — no separate JS needed.

## Coverage notes

- **Covered through Task #6 + category management:** auth, profiles, dashboard,
  trip CRUD, the packing-list planning view, bags/containers, check-off packing
  mode, templates/reuse (incl. the diff/drift flow), and category add/rename/delete.
- **Also covered:** category management, the Packwell UI overhaul (sidebar +
  unified trip board), **sharing** (Task #8, incl. recent collaborators),
  **CSV import** (templates + packing lists), and **add-from-template**
  (compose multiple templates into one list).
- **Not yet covered (future tasks):** unpacking mode (Task 7); people (#14);
  buy-when-there (#15); category-level marking (#16). Deferred: bag
  (re)assignment during packing; templates capturing bags; sharing
  templates/catalog items; sharing notifications + recipient self-leave; per-item
  pack-last/always-check flags (dropped from the exit page).
- Update this file as each task lands so the checklist stays in sync.
