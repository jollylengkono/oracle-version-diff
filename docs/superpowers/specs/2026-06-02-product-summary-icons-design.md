# Product Summary Icons Design

## Goal

Add a compact pixelated SVG badge to the left side of the release delta summary.
The badge changes when the selected product changes.

## Visual Direction

Use concrete product metaphors:

- `oracle-database`: pixel database cylinder.
- `oracle-weblogic-server`: pixel server rack.
- `oracle-goldengate`: pixel replication/link symbol.

The icon should be a compact badge, about 40px wide and tall in the summary
area. It should support the Pixel Dark default theme while remaining legible in
Supabase Light and GitHub Dark.

## Architecture

Create a small inline SVG helper module, `js/productIcons.js`, that exports a
function for resolving icon markup by product ID. The helper should return SVG
strings for known product IDs and a generic fallback pixel tile for unknown
product IDs.

This keeps the icons deterministic, avoids network or asset fetches, and makes
the feature easy to unit test.

## DOM Integration

Update `index.html` so `.delta-summary` includes a left icon host and a text
wrapper:

- `#product-icon.delta-summary__icon` for the selected product icon.
- `.delta-summary__body` containing the existing heading and subheading.

The icon host should be `aria-hidden="true"` because the selected product is
already available through the product selector and updated text.

## Runtime Behavior

In `js/app.js`, import the icon helper and update the summary icon inside the
existing `refresh()` path. The selected product is already resolved there, so
the icon should update whenever:

- the initial default product loads;
- the product selector changes;
- `refresh()` runs after product or version changes.

Unknown product IDs should render the fallback icon rather than throwing.

## Styling

Update all three theme stylesheets:

- `css/theme-pixel-dark.css`
- `css/theme-supabase-light.css`
- `css/theme-github-dark.css`

`.delta-summary` should become a flex row with the icon on the left and summary
text on the right. `.delta-summary__icon` should have a stable compact size,
prevent shrinking, center the SVG, and preserve pixelated edges. On narrow
screens, spacing should remain readable and the icon should not overlap text.

## Testing

Add focused JavaScript tests for:

- known product IDs returning SVG markup;
- unknown product IDs returning fallback SVG markup;
- `index.html` containing the icon host and summary body wrapper;
- each theme stylesheet defining summary icon layout rules.

Run `npm test` and `git diff --check`.
