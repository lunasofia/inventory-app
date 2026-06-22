# User Interview — 2026-06-22

**Participant:** prospective user (travels/coordinates with her wife). Saw a
live demo of the seeded `demo@packlist.app` account (dashboard + Iceland trip)
in split-screen.

## Headline
**She said she'd actually use it for her next big trip.** Strong adoption signal,
with concrete, fixable UX feedback and one clear feature gap.

## What resonated (validated)
- **Dashboard** reads clearly at a glance.
- **Simple, uncluttered** look — explicitly liked that it's "not too busy."
- **Categories** land well — "a natural way to think about what to bring."
- **Bags** matter — but specifically **for big trips** (not quick ones).
- She'd use **check-off when packing ahead of time**, which is what she does for
  big trips anyway.

## Key insight — check-off granularity
- **Per-item check-off felt like an *interruption*** when she was rushed. She
  stopped ticking items **not because she forgot things**, but because it wasn't
  worth the bother in the moment.
- **But per-item is still valuable** for partial packing ("pack half the bag now,
  finish the rest closer to leaving").
- **The real win is flexibility across three levels: per-item, by-bag, AND
  by-category.** Let the user pick the right granularity for the moment.
- **Concrete gap:** category-level "mark all done" is **not built** (we only have
  bag-level). She explicitly wants it. → small, actionable.

## Her current workflow & core pain (sharing)
- Two systems today: a **mental checklist for her own things** + a **spreadsheet
  for shared things**.
- The shared spreadsheet: **wife created it; both edit it and check items off.**
- **Breakdown:** under time pressure she stopped checking off (friction, per
  above) — not a memory failure.
- This **validates our planned sharing model** (a shared trip both people can
  view/edit/check off). **Sharing (#8) is likely her make-or-break / biggest
  adoption driver.**

## Lukewarm
- **Templates/reuse:** she doesn't reuse lists today; thinks it'd save *some*
  time but is "probably better for other people." Not her draw.

## Actionable UX feedback (layout)
- **Mode switching is clunky.** "Packing mode" (on the trip page) and "Edit list"
  (on the packing page) live in **different spots**, so switching feels like
  jumping. She wants a **persistent Planning | Packing toggle in a fixed
  position** on both views (segmented control), with the **current mode clearly
  highlighted**.
- She mentioned **"a few layout issues"** but we only captured the mode-toggle
  one before the interview ended → see open questions.

## Open questions / follow-ups
1. **The other layout issues** she alluded to but didn't enumerate — ask her
   directly (or do a focused usability pass).
2. **Mobile experience** — she'll likely pack on a phone; we never tested the
   mobile layout. Validate.
3. **First-run / empty state** — she saw *seeded* data. What's it like for a
   brand-new user building their first list from scratch? Untested.
4. **Sharing specifics (for #8):** real-time vs async edits? Any notion of
   "who brings what" / assignment? Notifications, or pull-only? Conflict
   handling when both edit?
5. **Does coarse marking + an exit-style final review reduce the "stop checking
   off when rushed" failure?** We didn't probe the exit-page (#13) idea with her.
6. **Unpacking, buy-when-there, restock** — not explored with her at all.

## Future-interview prompts
- "Pack a real (or imagined) trip start-to-finish on your phone" — observe, don't
  guide; watch where check-off friction and mode-switching show up.
- Probe the shared workflow with the actual partner present if possible.
- Test the new-user first-run with no seeded data.
