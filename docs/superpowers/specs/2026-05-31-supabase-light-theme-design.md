# Supabase-Inspired Light Theme Design

Date: 2026-05-31
Status: Approved for implementation planning

## Goal

Replace the current OpenClaw-inspired default light theme with a Supabase-inspired
light theme for Oracle Release Delta.

The app should feel like a clean developer tool: white card surfaces, fine neutral
borders, compact spacing, subtle elevation, and Supabase-style green interaction
states. The existing GitHub dark theme remains preserved as the fallback theme.

## Non-Goals

- No release-delta behavior changes.
- No product, source, crawler, or data changes.
- No new theme switcher.
- No redesign of the preserved GitHub dark fallback.
- No layout migration to a sidebar or dashboard shell.

## Visual Direction

Use the selected "Close Supabase Light" direction from the brainstorming mockup.

Required traits:

- Near-white page background.
- White card, picker, tab, and summary surfaces.
- Thin neutral borders with slightly stronger hover borders.
- Supabase-style green as the main accent for active tabs, focus rings, and
  selected interactive states, using `#3ECF8E` or a close accessible variant.
- Compact developer-tool spacing, keeping the current card-based workflow.
- Subtle shadows only where useful for hierarchy.
- Existing dark source link button remains dark gray/black, with darker hover.
- Large muted version numbers remain visible on cards at the current 30% opacity
  intent.

## Files And Boundaries

Expected implementation scope:

- Rename the default light theme to `css/theme-supabase-light.css` and update
  `index.html` to reference it.
- Remove the old OpenClaw default stylesheet from active use. It does not need to
  remain as a fallback; the preserved fallback is the GitHub dark theme.
- Keep `css/theme-github-dark.css` unchanged except for accidental formatting
  prevention.
- Update theme tests in `tests/js/theme.test.mjs` so they assert the Supabase
  default tokens and continued GitHub dark fallback preservation.
- Update user-facing documentation in `README.md` and `docs/HANDOVER.md` from
  OpenClaw-inspired to Supabase-inspired.

The preferred implementation is CSS-first. JavaScript should not change unless a
test or selector proves the CSS cannot express the chosen state.

## Interaction Details

- Active tabs use a green-tinted background or green border treatment instead of
  a filled black active state.
- Select focus states use green focus outlines.
- Card hover states become slightly more defined through border and surface
  changes, not heavy motion.
- The Official source button keeps the current dark treatment and does not regain
  an arrow icon.

## Testing

Run the existing JS and Python suites after implementation:

- `npm test`
- `.venv/bin/python -m pytest tests/python/ -q`

Theme-specific checks should cover:

- `index.html` references the Supabase-inspired default theme.
- The default light theme includes Supabase-style green accent tokens.
- The default light theme keeps white card surfaces and near-white page
  background.
- The GitHub dark fallback still contains the expected GitHub dark tokens.
- Hidden tab panels remain hidden in both themes.

## Acceptance Criteria

- Opening the app shows the Supabase-inspired light theme by default.
- The GitHub dark fallback remains available as a one-line stylesheet swap.
- The card layout remains intact.
- Source buttons remain dark and arrow-free.
- Documentation and tests no longer describe the default theme as
  OpenClaw-inspired.
