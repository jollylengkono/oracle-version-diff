# Light Card Dynamic Comparison Design

## Goal

Refine the Oracle Version Diff PR so the UI uses the approved light, card-based visual direction and the comparison model remains useful for arbitrary older/newer version pairs such as `19c` to `21c`, `19c` to `23.26`, and future release pairs added by the data pipeline.

## Approved Visual Direction

Use a light Apple-inspired card layout with Oracle restraint:

- Page background: soft system gray.
- Content cards: white surfaces with subtle borders and shadows.
- Version labels on cards: oversized, visually obvious, and rendered at 30% opacity.
- Official documentation links: compact dark gray Oracle-style buttons, darker on hover, no arrow.
- Preserve the card layout and keep the app simple, with no decorative hero art or heavy dark theme.

## Dynamic Comparison Behavior

The version selectors remain independent. Users can choose any two available versions, and the app aggregates release-note items between the older and newer selections by release date. The selected range excludes the older anchor and includes the newer endpoint, so `19c` to `21c` shows 21c baseline items, while `19c` to a future release automatically includes all releases after 19c up through that future release once the pipeline adds it.

## Data Model

Keep the existing per-version JSON record shape. Curated legacy baseline records may contain section items with official Oracle documentation links. Add meaningful 21c baseline content so baseline-to-baseline comparisons are not empty.

## Testing

Add tests before implementation for:

- `aggregateRange(records, "19c", "21c")` returning the 21c baseline item.
- Rendered cards showing the raw version number as a larger dedicated card label.
- Official document links using the button class.
- The generated 21c baseline containing at least one official-doc-backed item.

## Scope

This change does not add product switching, server-side storage, or live fetching from the browser. Future versions continue to enter through the existing data pipeline.
