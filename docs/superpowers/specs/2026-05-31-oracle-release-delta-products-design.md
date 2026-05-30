# Oracle Release Delta Product Expansion Design

## Goal

Rename and reframe the app as **Oracle Release Delta** and add Oracle Database as a second product with an initial `19c -> 26ai` release-delta dataset.

## Product Model

The app is directional. It answers: "What changed after my current release through my target release?" The selectors are:

- Product
- Current release
- Target release

The result summary uses:

- `Release delta from <current> to <target>`
- `Changes introduced after <current> through <target>`

## Data Scope

Oracle GoldenGate remains crawler-backed. Oracle Database starts with curated seed records:

- `oracle-database/19c.json` as the baseline anchor
- `oracle-database/26ai.json` as the latest target release

The Oracle Database seed uses official Oracle Database 26ai New Features and Upgrade Guide pages. It is enough to make the product path usable now, but it is not yet exhaustive or crawler-backed.

## UI

Add a product selector above the current/target release selectors. Changing product reloads available releases and records for that product.

## Tests

Add JS tests for:

- Oracle Database appearing in `data/index.json`
- Oracle Database `26ai` having all release-delta sections
- default product selection preferring Oracle Database when present
- directional release-delta heading/subheading copy
