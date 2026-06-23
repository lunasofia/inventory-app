# Packwell — Design Implementation Notes

These notes accompany the Figma Make prototype and are intended for the engineer implementing this design in the Django/React codebase.

---

## Visual language

**Stance:** Editorial-warm. Feels like a well-designed travel journal, not a SaaS dashboard.

**Fonts** (Google Fonts — add to project):
- `DM Serif Display` — app name ("packwell."), trip title h1
- `Inter` — all UI text, labels, body
- `DM Mono` — numeric counts and progress fractions (e.g. "7/13"), percentages

**Color tokens** (map these to your CSS custom properties):
```
--background:       #f5f0e8   (warm cream page ground)
--foreground:       #1c1a16   (near-black charcoal)
--card:             #faf7f2   (slightly lighter cream for cards/panels)
--muted:            #ede7da   (subdued surfaces, section headers)
--muted-foreground: #7a7060   (labels, captions, secondary text)
--accent:           #c4622d   (terracotta — primary interactive color, progress bars, FAB)
--accent-foreground:#ffffff
--border:           rgba(28,26,22,0.12)
--sidebar:          #eee8db
--sidebar-accent:   #e2d9c8   (active trip highlight)
--input-background: #ede7da
```

**Border radius:** Cards use `rounded-xl` (12px). Buttons use `rounded-lg` or `rounded-md`. Progress bars are `rounded-full`.

**Category color chips** (used in category view headers and add-item selectors):
- Clothing → `bg-amber-100 text-amber-800`
- Electronics → `bg-blue-100 text-blue-800`
- Documents → `bg-emerald-100 text-emerald-700`
- Gear → `bg-orange-100 text-orange-800`

**Bag icon colors** (rotate through this list by bag index):
`amber-100/800`, `blue-100/800`, `emerald-100/700`, `rose-100/800`, `violet-100/800`

---

## Layout

**Desktop:** Fixed left sidebar (256px) + scrollable main panel. Sidebar shows trip list with per-trip progress bars and user profile footer.

**Mobile:** Sidebar is hidden. Replaced by:
- Sticky top bar: hamburger (→ slide-in drawer) | "packwell." wordmark | search icon
- The drawer is a left-side overlay (272px wide) with the same trip list content as the desktop sidebar
- Floating action button (FAB) in bottom-right corner for "Add item"

---

## Key components

### Trip header
- Large serif trip name, destination + date in muted text with icons
- Overall progress bar (accent color fill) with `X/Y items` count in DM Mono
- "Add item" button top-right on desktop; FAB on mobile

### Bag summary strip
- Horizontal chip row showing each bag: icon + name + `packed/total` count in DM Mono + green ✓ when 100%
- An "unbagged" chip (dashed border) if any items have no bag
- **On mobile:** `overflow-x-auto`, horizontal scroll, `flex-nowrap`, chips have `shrink-0`. Bleeds edge-to-edge with negative margin.

### View toggle (3 states)
- "By bag" | "By category" | "All items"
- Segmented control style: muted background, active tab gets card background + shadow
- **On mobile:** stretches full-width, each tab `flex-1`

### Bag card (By bag view)
- Header: bag icon chip (colored) + name + "Packed" badge when 100% + mini progress bar + `packed/total`
- Actions: "Pack all / Unpack all" text button (desktop only), trash icon, collapse chevron
- Items listed below header, separated by hairline borders
- **Bag is_packed** computed from items — no explicit "mark packed" action; badge appears automatically

### Category card (By category view)
- Same card structure as bag card but with category icon/color
- Each item row shows the assigned bag as a small icon pill on the right
  - On mobile: show icon only (no bag name text) to prevent overflow

### Item row
- Full row is a click/tap target for toggling packed state
- Packed: `line-through` text, muted color, filled CheckSquare in accent color
- Unpacked: normal text, empty Square icon
- **Touch targets:** minimum `py-4` (16px top+bottom padding) on mobile
- In "All items" view: category chip + bag chip shown on right (category chip hidden on mobile)

### Add item — bottom sheet (mobile) / modal (desktop)
- Mobile: slides up from bottom, rounded top corners (`rounded-t-2xl`), drag handle bar
- Desktop: centered modal with scrim
- Fields: item name (full-width text input), then a 2-column grid: Category select | Bag select
- Submit on Enter key, dismiss on Escape
- "Add to list" full-width button at bottom

### Add bag form (inline, within By bag view)
- Icon picker: 3 buttons for Luggage / Backpack / ShoppingBag icons — selected state uses accent bg + white icon
- Text input for bag name
- Collapses to a dashed "Add a bag" button when not active

---

## Data model mapping

The prototype uses this shape — map to your Django models:

```
Trip       → trips table (id, name, destination, dates)
Bag        → bags table (id, trip_id, name, icon*)
Item       → packing_items table (id, trip_id, bag_id nullable, name, packed, category**)
```

`*` `icon` is prototype-only (luggage/backpack/tote) — not in the Django model. Either add it or drop the icon picker and use a generic bag icon.

`**` `category` maps to the optional `Category` FK on `PackingItem`. In the prototype it's a simple string enum; in the real model it's a user-owned catalog object.

**Bag deletion behavior:** When a bag is deleted, its items become unbagged (`bag_id = null`) — they are NOT deleted. This matches the Django model's `SET_NULL` on the bag FK. The "Unbagged" section in the By bag view handles this gracefully.

**Bag is_packed:** Computed — true only when `total_count > 0` AND `packed_count == total_count`. Empty bags never show the "Packed" badge.

---

## Interactions to preserve

- Toggling an item: click/tap anywhere on the row (not just the checkbox icon)
- "Pack all" bulk action on a bag: sets all items in that bag to `packed=true`
- "Unpack all": shown instead of "Pack all" when all items are already packed
- Progress bars animate with `transition-all duration-500` on width change
- The "Packed" badge on a bag/category appears/disappears reactively as items are toggled

## Interactions worth adding in implementation

- Haptic feedback on mobile when an item is checked (use the Vibration API or native equivalent)
- A subtle completion moment when a bag hits 100% (e.g. brief scale animation on the "Packed" badge)
- Long-press on a bag card on mobile to trigger "Pack all" (currently desktop-only)
- Swipe-to-check on item rows (common mobile list pattern)
