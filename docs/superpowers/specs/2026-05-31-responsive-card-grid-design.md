# Responsive Card Grid Design

Date: 2026-05-31
Status: Approved for implementation planning

## Goal

Change the aggregated release item layout from a single vertical list to a
responsive multi-card grid.

The layout must make release notes easier to scan by showing three cards per row
on desktop, two cards per row on tablet widths, and one card per row on mobile.

## Non-Goals

- No changes to release delta aggregation behavior.
- No changes to tab filtering.
- No changes to product or version selectors.
- No changes to data files, crawler logic, or source URLs.
- No redesign of the Supabase light theme tokens or GitHub dark fallback theme.
- No changes to the older side-by-side compatibility renderer unless tests prove
  it is affected by shared CSS.

## Layout Behavior

The aggregated list rendered by `renderAggregated()` must become a responsive
card grid:

- Desktop (`min-width: 960px`): three cards per row.
- Tablet (`700px` through `959px`): two cards per row.
- Mobile (`max-width: 699px`): one card per row.
- Gaps must stay consistent with the current Supabase-style compact spacing.
- Cards must remain visually recognizable as the current `.item` cards.

Cards in the same row must feel aligned even when descriptions differ in length.
The preferred implementation is to make each `.item` card a flex column so the
`Official source` button sits consistently near the bottom of the card.

## Visual Details

Keep the existing card contents:

- Large muted version number.
- Release item title.
- Optional description.
- Dark `Official source` button.

Keep the Supabase-inspired light theme styling:

- White card surface.
- Thin border.
- Subtle shadow.
- Green active/focus states elsewhere in the UI.

The grid must not introduce masonry ordering, horizontal scrolling, or nested
cards.

## Files And Boundaries

Expected implementation scope:

- Update `css/theme-supabase-light.css` so `.range-list` is a responsive grid and
  `.item` supports equal-height card content.
- Update `css/theme-github-dark.css` with the same layout-only grid rules so the
  preserved fallback theme remains usable if selected.
- Update `tests/js/theme.test.mjs` or `tests/js/render.test.mjs` with assertions
  that protect the responsive grid contract.

JavaScript rendering must remain unchanged unless a test shows the existing
markup cannot support the grid layout. The current `renderAggregated()` wrapper
class, `.range-list`, is the intended layout hook.

## Testing

Run the existing suites after implementation:

- `npm test`
- `.venv/bin/python -m pytest tests/python/ -q`

Theme-specific checks must cover:

- `.range-list` uses CSS grid.
- Desktop grid uses three columns.
- A tablet media query reduces the grid to two columns.
- The existing mobile media query or a new mobile media query reduces the grid to
  one column.
- `.item` supports equal-height card layout without changing the rendered markup.

## Acceptance Criteria

- Aggregated cards show as three per row on desktop.
- Aggregated cards collapse to two per row on tablet and one per row on mobile.
- The source button aligns consistently within cards with different description
  lengths.
- The card content and source links stay unchanged.
- Both the Supabase light theme and GitHub dark fallback share the same responsive
  grid behavior.
