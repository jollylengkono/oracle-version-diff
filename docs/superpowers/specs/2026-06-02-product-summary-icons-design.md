# Product Summary Icons Design

## Goal

Add a compact pixelated SVG badge to the left side of the release delta summary.
The badge changes when the selected product changes.

## Visual Direction

Use concrete product metaphors, informed by Oracle-hosted product imagery and
product descriptions:

- `oracle-database`: pixel database cylinder.
- `oracle-weblogic-server`: pixel server rack.
- `oracle-goldengate`: pixel replication/link symbol.

The icon should be a compact badge, about 40px wide and tall in the summary
area. It should support the Pixel Dark default theme while remaining legible in
Supabase Light and GitHub Dark.

The implementation should not copy, trace, or embed Oracle artwork. It should
use the reference material only to choose recognizable product metaphors and
then create original, simplified pixel SVGs.

## Reference Material

Use these Oracle-hosted references while designing the original pixel SVGs:

- Oracle Database: Oracle's AI Database page references database services,
  Exadata, Autonomous AI Database, and multiple data models in one database
  engine. Use this to support a database-cylinder/storage metaphor. Reference:
  `https://www.oracle.com/database/`
- Oracle WebLogic Server: Oracle documentation describes WebLogic Server as an
  application server and runtime platform for enterprise Java applications. Use
  this to support a server-rack/runtime metaphor. Reference:
  `https://docs.oracle.com/en/middleware/standalone/weblogic-server/`
- Oracle GoldenGate: Oracle documentation describes GoldenGate as foundational
  for data replication and change data capture. Oracle's GoldenGate data sheet
  also emphasizes real-time replication, data pipelines, and connected data
  fabric. Use this to support a linked-systems/replication metaphor. References:
  `https://docs.oracle.com/en/database/goldengate/index.html` and
  `https://www.oracle.com/a/ocom/docs/oracle-goldengate-datasheet.pdf`

If implementation work needs direct visual references, use Oracle-hosted images
from those pages as rough inspiration only; do not include external image assets
in the app.

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
