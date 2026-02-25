# auto_recalls — Model Update Summary

## What Changed

Full rewrite of `auto_recalls.malloy` and `README.malloynb` to follow current Malloy modeling best practices.

### Model (`auto_recalls.malloy`)

**Structure**
- Added `##! experimental.access_modifiers` with explicit `include {}` block
- Every column explicitly listed as `public:` or `internal:`
- Added `primary_key: NHTSA ID`
- Workspace-relative table path (`auto_recalls/data/auto_recalls.csv`) for IDE compatibility

**Curation (5 columns marked `internal`)**
- `Report Received Date` — superseded by `recall_date` and `recall_year` dimensions
- `Manufacturer` — superseded by `manufacturer` dimension (with `#(filter)` annotation)
- `Subject` — superseded by `recall_subject` dimension (with `#(index_values)` + `#(filter)`)
- `Component` — superseded by `component` dimension (with `#(filter)` annotation)
- `Recall Link` — superseded by `recall_url` dimension (clean URL vs boilerplate text)

**Documentation**
- `#(doc)` tags on the source, all public columns, all dimensions, all measures, and all views
- Source-level doc describes what questions the model answers
- `#(filter)` annotations for notebook interactivity: `manufacturer` (Star), `component` (Star), `recall_subject` (Retrieval), `is_major_recall` (Boolean)

**Dimensions (7 new/improved)**
- `recall_url` — direct NHTSA link (`# link`)
- `recall_date` — date cast of report received date
- `recall_year` — year truncation for time series
- `recall_subject` — alias of Subject with semantic search indexing
- `manufacturer` — alias of Manufacturer with dropdown filter
- `component` — alias of Component with dropdown filter
- `is_major_recall` — boolean: 100K+ potentially affected (threshold validated against data distribution — top ~7% of recalls)

**Measures (4)**
- `recall_count` — count of recalls
- `percent_of_recalls` — share of total (`# percent`, uses `nullif` for safe division)
- `total_affected` — sum of potentially affected (`# number=auto`, method syntax `.sum()`)
- `avg_affected` — average per recall (`# number=auto`, `nullif` division)

**Views (8)**
- `summary` — `# big_value` KPI cards (recall count, total affected, avg per recall)
- `by_year` — `# line_chart` trend over time
- `by_manufacturer` — table with count, total affected, % of total
- `by_type` — table by recall type (Vehicle, Equipment, Tire, Child Seat)
- `by_component` — table by vehicle component
- `recent_recalls` — detail view of most recent recalls
- `biggest_recalls` — detail view by most vehicles affected
- `recall_dashboard` — `# dashboard` combining manufacturer breakdown, time trend by type, type table, recent and biggest recalls

### Notebook (`README.malloynb`)

- Updated filter references to use new dimension names (`manufacturer`, `is_major_recall`, `recall_subject`)
- Fixed typo ("effected" → "affected")
- Added `by_component` section
- Improved descriptions and narrative flow
- Removed reference to deleted `by_year_manufacturer_line_chart` view

### Workspace Config

- Created `malloy-config.json` at workspace root with DuckDB connection (was missing — caused all models to show IO errors in IDE)

## What Was Removed

- `##! m4warnings` pragma (replaced by `##! experimental.access_modifiers`)
- Verbose rename hack (`Subject_old`, `Manufacturer_old`, etc.) — replaced by clean dimension aliases with `internal` raw columns
- `percent_of_recalls` manual `*100` multiplication (now uses `# percent` annotation)
- `by_year_manufacturer_line_chart` — overly complex composite view; replaced by simpler `recalls_over_time` nested in the dashboard

## Assumptions Flagged

- **Major recall threshold (100K)**: Validated against data — captures top ~7% of recalls. Median is well under 1K. Kept as-is.
- **`Recall Link` marked internal**: Raw column contains boilerplate text; `recall_url` dimension provides clean URL.
