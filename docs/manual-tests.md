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

## Coverage notes

- **Covered through Task 4:** auth, profiles, dashboard, trip CRUD, and the
  packing-list planning view (add/edit/remove, hybrid catalog, autocomplete,
  grouping, access control).
- **Not yet covered (future tasks):** check-off packing mode (Task 5);
  templates (Task 6); unpacking mode (Task 7); sharing UI (Task 8).
- Update this file as each task lands so the checklist stays in sync.
