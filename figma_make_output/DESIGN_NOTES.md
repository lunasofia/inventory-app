# Packwell — Design Implementation Notes

These notes accompany the Figma Make prototype and are intended for the engineer implementing this design in the Django/React codebase.

---

## Visual language

**Theme:** Golden Hour — editorial-warm. Feels like a well-designed travel journal, not a SaaS dashboard.

**Fonts** (Google Fonts — add to project):
```html
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;1,9..144,400&family=Inter:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
```
- `Fraunces` — app name ("packwell."), trip title h1, bag/category card headings, button labels
- `Inter` — all body text, labels, form fields
- `DM Mono` — numeric counts and progress fractions (e.g. "7/13"), percentages

**Color tokens** (map these to your CSS custom properties):
```
--background:       #fefcf5   (warm cream page ground)
--foreground:       #1a1a2e   (deep navy-charcoal)
--card:             #fffef9   (slightly lighter cream for cards/panels)
--muted:            #f0e8d5   (subdued surfaces, section headers)
--muted-foreground: #8a825e   (labels, captions, secondary text)
--accent:           #d4920a   (golden amber — primary interactive color, progress bars, FAB)
--accent-foreground:#ffffff
--border:           rgba(26,26,46,0.1)
--input-background: #f0e8d5
--sidebar:          #fdf6e3   (warm parchment)
--sidebar-accent:   #f5e9c4   (active trip highlight)
--sidebar-foreground:#1a1a2e
--sidebar-border:   rgba(26,26,46,0.08)
```

**Border radius:** Cards use 14px. Buttons use 10–12px. Progress bars are fully rounded (99px).

**Category color chips** — all warm-toned to stay cohesive with the golden palette:
- Clothing    → `bg: #fef3c7  fg: #92400e`
- Electronics → `bg: #fde8d0  fg: #7c3a1a`
- Documents   → `bg: #dcfce7  fg: #166534`
- Gear        → `bg: #fce7f3  fg: #831843`

**Bag icon colors** (rotate through by bag index):
- `bg: #fef3c7  fg: #92400e`
- `bg: #fde8d0  fg: #7c3a1a`
- `bg: #dcfce7  fg: #166534`
- `bg: #fce7f3  fg: #831843`

---

## Layout

**Desktop:** Fixed left sidebar (256px, parchment background) + scrollable main panel.

**Mobile:** Sidebar hidden. Replaced by:
- Sticky top bar: hamburger (→ slide-in left drawer) | "packwell." wordmark | search icon
- FAB (floating action button) bottom-right for "Add item", with amber glow shadow

---

## Key components

### Sidebar
- Light parchment background (`#fdf6e3`) — warm, not dark
- Wordmark: Fraunces weight 600, with the trailing `.` in the accent amber color
- Trip list: each trip shows name, destination with MapPin icon, and a mini progress bar
- Active trip: highlighted with `#f5e9c4` background and amber ChevronRight
- Footer: user avatar (accent-colored circle) + name + trip count

### Trip header
- Trip name in Fraunces weight 600, 28px — no heavy weight, let the typeface do the work
- Destination + date in muted text with icons
- Overall progress bar (8px tall, amber fill, `#f0e4b8` track) with `X/Y items` in DM Mono
- "Add item" button top-right (desktop); FAB on mobile

### Bag summary strip
- Horizontal chip row: icon chip + name + `packed/total` in DM Mono + green ✓ when 100%
- Unbagged chip with dashed border if any items have no bag
- Mobile: `overflow-x-auto`, horizontal scroll, no wrapping

### View toggle (3 states)
- "By bag" | "By category" | "All items"
- Segmented control: `#f0e8d5` background, active tab gets card background + subtle shadow
- Mobile: full-width, each tab `flex-1`

### Bag card (By bag view)
- Header: colored icon chip (14px rounded) + Fraunces name + "Packed ✓" badge (green) when 100% + progress bar + `packed/total`
- Actions: "Pack all / Unpack all" text button, trash icon, collapse chevron
- Items listed below, hairline borders between rows
- **Bag is_packed:** computed — badge only appears when `total > 0 AND packed == total`

### Category card (By category view)
- Same card structure as bag card
- Each item row shows assigned bag as a small amber pill on the right

### Item row
- Full row is a tap/click target
- Packed: line-through, muted color, filled CheckSquare in amber
- Unpacked: normal weight, empty Square
- Touch target: minimum 44px height (11px top + bottom padding)

### Add item — modal
- Desktop: centered modal with blurred scrim
- Mobile: same modal (consider converting to bottom sheet in production)
- Fields: name input (full-width), then 2-column grid: Category select | Bag select
- Submit on Enter, dismiss on Escape
- "Add to list" full-width amber button

### Add bag form (inline, within By bag view)
- Dashed-border trigger button: "+ Add a bag"
- Expands inline — no separate page needed

---

## Data model mapping

```
Trip  → trips table  (id, name, destination, dates)
Bag   → bags table   (id, trip_id, name, icon*)
Item  → packing_items (id, trip_id, bag_id nullable, name, packed, category**)
```

`*` `icon` field (luggage/backpack/tote) is prototype-only — not in the Django model. Either add it as a CharField or drop the icon picker and use a single generic bag icon.

`**` `category` is a string enum in the prototype; in the real model it's a `Category` FK on `PackingItem`.

**Bag deletion:** Items become unbagged (`bag_id = null`), not deleted. Matches Django's `SET_NULL`. The "Unbagged" section handles these gracefully.

**Bag is_packed:** Computed — `total_count > 0 AND packed_count == total_count`. Empty bags never show the badge.

---

## Interactions to preserve

- Toggling an item: full row is the tap target, not just the checkbox
- "Pack all" / "Unpack all" bulk action per bag
- Progress bars animate on width change (`transition: width 0.4s`)
- "Packed ✓" badge appears/disappears reactively as items are toggled

## Interactions worth adding in production

- Haptic feedback on mobile when an item is checked (Web Vibration API)
- Brief scale or color-pop animation when a bag hits 100%
- Long-press on bag card to trigger "Pack all" (mobile equivalent of the desktop text button)
- Swipe-to-check on item rows
