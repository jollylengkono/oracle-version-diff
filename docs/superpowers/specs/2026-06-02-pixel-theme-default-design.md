# Pixel Theme Default Design

## Goal

Make the new pixel dark theme the default visual theme for first-time visitors.
Users who have already selected and saved another theme should keep their saved
preference.

## Current State

The theme switcher loads `css/theme-supabase-light.css` as the initial stylesheet.
Runtime JavaScript then checks `localStorage.oracle-diff-theme`; if a saved theme
exists, the script swaps the stylesheet to that saved theme. If no saved theme
exists, the script falls back to `theme-supabase-light`.

## Recommended Approach

Change the no-preference default from `theme-supabase-light` to
`theme-pixel-dark` in both places that define the initial default:

- The initial `<link id="themeLink">` stylesheet should point to
  `css/theme-pixel-dark.css`.
- The runtime fallback should use `theme-pixel-dark` when
  `localStorage.oracle-diff-theme` is empty.

This prevents a flash of the light theme for new visitors and preserves existing
saved preferences.

## Behavior

- First-time visitor: page loads with the pixel dark theme and marks the Pixel
  button active.
- Returning visitor with a saved theme: page loads with the saved theme and marks
  that button active.
- Theme switching remains unchanged: clicking a theme button applies that theme
  and persists it in `localStorage.oracle-diff-theme`.

## Testing

Update the HTML theme contract test so it expects the pixel theme stylesheet as
the default. Run the existing JavaScript test suite and `git diff --check`.
Python pipeline tests are unrelated to this UI-only change, but can be rerun if
the local Python test environment is repaired.
