# Manual Test Plan

Manual regression checklist for Packlist. Re-run the relevant section after
changes to avoid regressions.

> Most of this checklist is now also covered by the **automated suite** (`make
> test` / `pytest`, run in CI on every push) — see `tests/`. This manual plan
> remains useful for **visual/exploratory** checks and the JavaScript-driven
> interactions (autocomplete picking, inline-edit swaps) that the HTTP-level
> tests don't exercise.

## Setup

1. From the repo root: `.venv/bin/python manage.py runserver 8000`
2. Open <http://127.0.0.1:8000/>
3. Test accounts (local dev):
   - **Demo user:** `tourist@example.com` / `packlist-demo-2026`
   - **Admin/superuser** (`/admin/`): `admin@example.com` / `packlist123`

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
| 4.1 | Brand-new account with no trips → dashboard | "No trips yet" empty state under Active; no Completed section |
| 4.2 | With ≥1 active trip | Trip appears as a card under Active; card links to its detail page |
| 4.3 | Trip with status "Complete" | Appears under a separate Completed section, dimmed |
| 4.4 | Card display | Shows name, destination (if set), status badge, and `packed/total` count |

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
| 13.6 | Items within a group | Ordered by `sort_order` then name |

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

## 16. Check-off packing mode (Task #5)

A focused page at `/trips/<pk>/pack/`, reached via "🎒 Packing mode" on the
trip page. Check-off only (editing stays on the planning view).

| # | Steps | Expected |
|---|-------|----------|
| 16.1 | Click "Packing mode" on a trip | Focused packing page loads; item list with check controls + progress; no add/edit controls |
| 16.2 | "Edit list" link | Returns to the planning view |
| 16.3 | Tap an unpacked item | Becomes packed (checked, dimmed, struck through) without full reload |
| 16.4 | Tap a packed item | Toggles back to unpacked |
| 16.5 | Packed item position | Stays in place in its group |
| 16.6 | Check items off | Overall progress bar + "N/total packed" update live; per-group counts update |
| 16.7 | Check the last remaining item | Progress hits 100%; "All packed" message shown |
| 16.8 | Uncheck from 100% | Message clears; progress drops |
| 16.9 | Toggle "Group by: Bag" | Regroups by bag (alphabetical, Unbagged last); check states unchanged |
| 16.10 | "Pack all" on a bag heading (bag view) | All items in the bag check off; progress jumps; offers "Unpack all" |
| 16.11 | Open packing mode for a trip with no items | Friendly empty state linking back to add items |
| 16.12 | View-only shared user | Sees list + progress read-only; no check controls; direct POST to toggle/bag-mark → 404 |
| 16.13 | Reload after checking items; also view planning page | Packed states persist and are reflected on the planning view (shared field) |

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

## Resolved design decisions (Bags)

- **Per-trip bags** (no reusable "bags I own" library yet; reuse comes via
  templates). No logical/physical split — a bag is just a named container.
- **"Swap the bag"** = rename a bag (contents stay) and/or move items between bags.
- **Bag-level status is a bulk shortcut over items** — "mark bag packed" sets
  every item packed; a bag *displays* packed when it has items and all are packed.
- **Bag vs category are two grouping lenses**; lens defaults to category on each
  full page load (not yet remembered across visits). Unbagged group shown last.
- Bag names are **unique (case-insensitive) per trip**.

## Coverage notes

- **Covered through Task #6 + category management:** auth, profiles, dashboard,
  trip CRUD, the packing-list planning view, bags/containers, check-off packing
  mode, templates/reuse (incl. the diff/drift flow), and category add/rename/delete.
- **Not yet covered (future tasks):** unpacking mode (Task 7); sharing UI
  (Task 8); exit page (#13); people (#14); buy-when-there (#15). Deferred: bag
  (re)assignment during packing; templates capturing bags; sharing templates/
  catalog items.
- Update this file as each task lands so the checklist stays in sync.
