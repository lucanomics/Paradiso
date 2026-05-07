# UI Review: Figma to index.html Polish

## Scope
This PR safely reflects the Figma Make visual direction into the existing production static `index.html` without changing application architecture or search/data behavior.

## Design Diagnosis
- **Hierarchy**: Landing visual hierarchy was close, but hero-to-search emphasis still needed a clearer focal path.
- **Spacing**: Landing vertical rhythm between logo, search, and CTA card groups was uneven at some breakpoints.
- **Korean typography**: Some button/label density created readability pressure in narrow widths.
- **Hero readability**: Scenic + overlay looked good but needed stronger contrast consistency for input and CTA layers.
- **CTA hierarchy**: Search needed clearer primacy; helper action cards needed tighter grouping and consistent visual weight.
- **Card rhythm**: Action card spacing and corner rhythm varied from section to section.
- **Responsive behavior**: Mobile/tablet needed better touch-target confidence and less crowding in the hero cluster.
- **Scroll stability**: Decorative/section shells needed stricter clipping and layer containment to avoid perceived jitter.

## Changes Applied
- Added narrowly scoped landing-state polish for hero padding and header spacing to better match cinematic civic-gateway composition.
- Strengthened glass-like search surface treatment (`.sbar`) with refined border, translucency, and shadow.
- Unified hero interactive surface width constraints (`.search-wrap`, `.hero-actions`, `.qa-main`, `#visaManualSection`) for consistent rhythm.
- Refined translucent action card treatment and minimum button touch confidence in landing action groups.
- Applied consistent rounded container/clipping treatment to key lower visual blocks to reduce edge noise and overlap risk.
- Added mobile-safe refinements for hero top spacing and logo wordmark width.

## Behavior Preservation
Search submission, direct-search toggle/open/close flow, modal triggers, and result rendering logic were not intentionally changed in this PR.

## Deferred Work
- Remaining Moonshot file migration
- RAG/backend migration
- `visa_data.json` / `doc_master.json` audit or structural changes
- Full React/Vite rewrite
- Major information architecture restructuring
