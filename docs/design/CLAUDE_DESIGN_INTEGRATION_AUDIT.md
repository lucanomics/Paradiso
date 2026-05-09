# Claude Design Integration Audit — Paradiso

Date: 2026-05-09
Branch: `audit/claude-design-integration-plan`
Author: production migration agent (analysis only — no production HTML changed in this run)

This document inspects the uploaded Claude Design / Figma Make prototype materials and proposes a safe integration path into the existing static Paradiso repository. It is **planning material only**. No production page (`index.html`, `ai.html`) is modified by this PR.

---

## 1. Current repo status

- **Working tree**: clean before this audit branch was cut. `git status --short` was empty.
- **Branch base**: `main` (latest commit `dbc1a77` — "Merge pull request #23 from lucanomics/backend-migration-gap-and-railway-prep").
- **Production surface** (root-level static HTML served as-is):
  - `index.html` — landing + search + visa manual + tools (5,961 lines, 335,990 bytes)
  - `ai.html` — AI guidance page with consent modal (576 lines, 32,159 bytes)
  - `assets/`, `backend/`, `data/`, `visa_data.json`, `doc_master.json`, `scripts/check_repo.sh`
- **Existing design docs**:
  - `docs/design/MANUAL_BASED_INTERFACE_REBUILD_REVIEW.md`
  - `docs/design/UI_REVIEW_FIGMA_INDEX_POLISH_20260507.md`
- **Validation**: `bash scripts/check_repo.sh` → all 4 steps pass on `main`. JSON valid, manual-aware schema valid, git diff clean, no forbidden branding strings.

---

## 2. Is `index.html` malformed?

**No. The current production `index.html` is structurally valid.**

Sanity checks on `index.html`:

| Check                                  | Expected | Actual |
|----------------------------------------|----------|--------|
| `<!DOCTYPE html>` occurrences          | 1        | 1 (line 1) |
| `<html ...>` opening tag               | 1        | 1 (line 2) |
| `</html>` closing tag                  | 1        | 1 (line 5961) |
| `<head>` opening tag                   | 1        | 1 (line 3) |
| `</head>` closing tag                  | 1        | 1 (line 3002) |
| `<body ...>`                           | 1        | 1 (line 3003, `class="landing" data-theme="light"`) |
| `</body>`                              | 1        | 1 (line 5960) |
| Nested `<!DOCTYPE` inside `<style>`    | 0        | 0 |
| `id="root"` (Vite/React mount)         | 0        | 0 |
| `/src/main.tsx` reference              | 0        | 0 |
| `Paradiso 39` / `Moonshot` substrings  | 0        | 0 |

Note: a naive grep for `<head` returns 3 matches because `<header>` partial-matches the pattern. The actual `<head>` count is 1; the other two are the `<header>` elements at lines 3007 and 3024.

**Conclusion**: production HTML is valid. Per task rules, **Phase 2 minimal repair is NOT triggered**, and `index.html` is not modified in this PR. Only the audit document is added.

`ai.html` is also structurally valid (one DOCTYPE, balanced `<html>`/`<head>`/`<body>`).

---

## 3. Inventory of uploaded Claude Design files

Source uploads (under `/root/.claude/uploads/.../`) extracted to `/tmp/uploads/` for analysis:

### 3.1 `html________.zip` → `html 모음지/` (the actual Claude Design prototype HTML set)

| File | Size | Lines | Notes |
|---|---|---|---|
| `landing.html` | 49 KB | 1024 | New landing layout reference (hero, dual-entry, pathways, trust, tools, roadmap, footer) |
| `search.html`  | 30 KB | 631  | Search results layout reference (filter rail, result cards, compare bar) |
| `detail.html`  | 36 KB | 708  | Visa detail page reference (plain-language summary, at-a-glance grid, doc checklist, timeline, sources) |
| `mobile.html`  | 39 KB | 827  | Mobile-first reference (bottom nav, situation wizard, m-result cards, deadline reminders) |
| `ai (16).html` | 25 KB | 576  | New AI page layout reference (privacy sidebar, per-turn disclaimer, suggested follow-ups) |

All five share the same `data-accent="green"` shell, link to `assets/styles.css`, load `assets/app.js`, and end with **prototype-only React/Babel scripts** (see §5).

### 3.2 `Paradiso_Design.zip` → `assets/`

| File | Lines | Type | Production-safe? |
|---|---|---|---|
| `styles.css` | 520 | Editorial design system: tokens, typography, palette, spacing, shadows, accent variants, layout primitives, common components | Tokens + selected components yes; bulk import no (class-name conflicts likely with `index.html`'s in-page CSS) |
| `app.js` | 57 | Tiny shared JS: `IntersectionObserver` reveal, KO/EN toggle, accent setter, `localStorage` persistence | Yes — small, no deps, can be wrapped behind a feature flag. Not needed unless we ship reveal/lang-toggle UX |
| `tweaks.jsx` | 60 | React/Babel **prototype tooling** (accent/lang/density picker host) | **No** — prototype only |
| `tweaks-panel.jsx` | 568 | React/Babel **prototype tooling** (form-control helpers) | **No** — prototype only |
| `ios-frame.jsx` | 338 | React iOS device frame for mobile mockups | **No** — prototype only |

### 3.3 `Paradiso_Design_1.zip` → `uploads/`

| File | Size | Identity |
|---|---|---|
| `current_ai.html`         | 32,159 B | **Identical to live `ai.html`** (verified by `diff -q`) |
| `ai (16).html`            | 32,159 B | **Identical to live `ai.html`** — duplicate snapshot, NOT the new design (the actual design candidate is in `html 모음지/`) |
| `current_index.html`      | 335,904 B | Older snapshot of live `index.html` |
| `index (38).html`         | 335,904 B | **Identical to `current_index.html`** — older `index.html` snapshot, missing only the 3-line `window.PARADISO_BACKEND_URL` block (lines 2999–3001 of live `index.html`) |
| `Paradiso 후보.make` (×2)  | 13.3 MB  | Figma Make project archives (zip): `canvas.fig`, `ai_chat.json`, `make_binary_files/...`. Proprietary; archival only |

> **Important**: `index (38).html` is **not** a "new working static page". It is a slightly older snapshot of the current production `index.html`. The user's hint that `index (38).html` "may be the intended working static page" — confirmed harmless but redundant. The live `index.html` is the canonical version (and includes the production backend URL override the snapshot lacks).

### 3.4 `Paradiso 후보.make` (top-level upload)

Same Figma Make zip format. Treated as archival reference, not source.

---

## 4. What each file is useful for

| File | Useful as | Useful for | Not for |
|---|---|---|---|
| `landing.html`   | Visual + UX reference | Hero copy/structure ("we map the way"), dual-entry "A/B" search rail (code vs situation), 8-card pathway grid (study/work/family/business/culture/extend/change/exit), 4-step howto, trust/citations panel, practical tools grid, roadmap, footer CTA | Drop-in replacement for `index.html` |
| `search.html`    | Visual + UX reference | Result-card hierarchy, filter rail block layout, query toolbar, compare bar interaction | Replacing current search rendering / data shape |
| `detail.html`    | Visual + UX reference | Detail page card structure, plain-language summary, at-a-glance grid, document checklist, application-flow timeline, sources panel, reminder side card | A new route — Paradiso has no per-visa detail page yet; this informs a future PR only |
| `mobile.html`    | Mobile UX reference | Bottom navigation pattern, situation wizard flow, mobile result cards, deadline reminder UI | Production code (it's a stitched device-frame demo, not a real responsive layout) |
| `ai (16).html`   | Disclaimer/UX reference (compare against current `ai.html`) | "Privacy · 입력하지 마세요" inline list (passport, ARC, address, biometrics, family details), per-turn `disclaimer` callout, suggested follow-ups list, sources panel pattern, source citation in turn footer | Replacing `ai.html` (current consent-modal + privacy enforcement is more robust than the prototype's static panel) |
| `assets/styles.css` | Design system tokens | `--ink`, `--paper`, `--green`, `--accent*`, `--ff-serif-ko/en`, `--fs-*`, `--s-*`, `--r-*`, `--shadow-*`, `--ease*` — these are clean and reusable | Bulk `<link rel="stylesheet">` into production (would import 4 webfont families and conflict with existing in-page CSS class names like `.hero`, `.btn`, `.section`) |
| `assets/app.js`  | Optional shared JS | Reveal-on-scroll, KO/EN toggle scaffolding, accent setter — safe, no deps | Bundling unless reveal/lang-toggle UX is actually adopted in production |
| `assets/tweaks.jsx` / `tweaks-panel.jsx` / `ios-frame.jsx` | Prototype-only | Inspecting how the design system was demoed | **Production**. They require React 18 + `@babel/standalone` runtime in the browser. |
| `*.make`         | Archival | Future Figma round-trips | Code |

---

## 5. What must NOT be copied directly

1. **React 18 + `@babel/standalone` script tags** at the bottom of every Claude Design HTML file:
   ```html
   <script src="https://unpkg.com/react@18.3.1/umd/react.development.js" ...></script>
   <script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.development.js" ...></script>
   <script src="https://unpkg.com/@babel/standalone@7.29.0/babel.min.js" ...></script>
   <script type="text/babel" src="assets/tweaks-panel.jsx"></script>
   <script type="text/babel" src="assets/tweaks.jsx"></script>
   ```
   These exist solely to render the in-page Tweaks panel. They violate project rule 11 (no React/Babel in production static pages) and rule 10 (no new external runtime deps). **Strip on import.**
2. **`.jsx` files** (`tweaks*.jsx`, `ios-frame.jsx`) — prototype tooling only.
3. **`.make` files** — proprietary Figma archives, not source.
4. **Wholesale `assets/styles.css` link** into production. The file imports 4 Google web font families (Newsreader, Gowun Batang, JetBrains Mono, Pretendard via jsDelivr) and defines class names that collide with existing in-page styles in `index.html` (`.hero`, `.btn`, `.section`, `.container`, `.eyebrow`). A blanket import would either break the existing visual system or silently override it inconsistently.
5. **`landing.html` → `index.html` wholesale replacement.** The Claude Design landing has no search backend wiring, no `body.searched`/`body.searching` state machine, no visa data loading, no jurisdiction tools, no `window.PARADISO_BACKEND_URL` override, no consent modal hook. Swapping the file would break:
   - Search + direct-search toggle
   - Result rendering
   - Visa manual section behavior
   - `body.searched` styling cascade
   - Backend URL override mechanism
6. **`ai (16).html` → `ai.html` wholesale replacement.** Current `ai.html` includes a stricter privacy/consent flow (modal + `reference-disclaimer` + per-message `DISCLAIMER`) than the prototype's static sidebar. Replacing it would weaken protections.
7. **`index (38).html` as a "restore" target.** It is older than the live HTML and is missing the `window.PARADISO_BACKEND_URL` override block. Do not use it as a baseline.

---

## 6. Safe components to extract (later PRs)

Listed in increasing risk order:

### A. Design tokens (lowest risk)
- A subset of CSS custom properties from `styles.css` lines 9–79 (palette, type scale, spacing, radius, shadow, motion) can be added to `index.html`/`ai.html` as **additive** custom properties without renaming any existing class.
- Approach: prefix with `--p-` (e.g. `--p-ink`, `--p-accent`) to guarantee no collision with existing CSS variables, and only consume them inside new components we add. Existing styles untouched.

### B. Hero copy + dual-entry "A/B" rail
- Copy text and structure of the entry-card pair from `landing.html` lines 554–569 ("비자 코드를 알고 있어요" / "제 상황만 설명할 수 있어요").
- Wire to existing search behavior — do not replace the existing search form. Add as an **above** or **alongside** affordance.

### C. Pathway grid (8 cards)
- Reference: `landing.html` lines 626–710 (`#pathways` section, `.pathway` cards: study/work/family/business/culture/extend/change/exit).
- Wire each card to existing search query strings the current frontend understands. Do not invent new query params unsupported by the current search code.

### D. Trust/citations strip
- Reference: `landing.html` lines 796–855 (`#trust` section). Pure presentational; safe to port as static content tied to the existing source hierarchy (manual PDFs → `doc_master.json` → display).

### E. Tools grid
- Reference: `landing.html` lines 859–897 (`#tools`). Useful **only** if it links to existing jurisdiction/job-code tools the production app already exposes. Do not invent new tools here.

### F. Roadmap + footer CTA
- Reference: `landing.html` lines 901–`~1010`. Static content; low risk.

### G. AI page polish (compare carefully)
- From `ai (16).html`: the visual "Privacy · 입력하지 마세요" sidebar (lines ~349–360) and the per-turn `.disclaimer` callout pattern (lines 496–499). Add **alongside** the existing consent modal, never replacing it.
- The prototype's `<textarea placeholder>` text ("…여권번호·외국인등록번호 등 민감 식별정보는 입력하지 마세요") could be added to the existing input. Verify current `ai.html` placeholder first.

### H. `app.js` reveal-on-scroll (optional)
- Adds a `[data-reveal]` IntersectionObserver. Safe, ~57 lines, no deps. Only ship if/when reveal animations are explicitly adopted in production sections.

### Detail page (deferred)
- `detail.html` describes a page Paradiso does not currently have. A per-visa detail route is a **separate product decision**, not a UI-polish PR. Treated as design reference for a future feature; not on the near-term sequence.

### Mobile shell (deferred)
- `mobile.html` is a device-frame demo, not a responsive layout. Use only as a sketch of a future mobile information hierarchy (bottom nav, wizard, deadline cards). Not directly portable.

---

## 7. Risk assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Class-name collision when porting `styles.css` | High | Visual regressions across `index.html` | Token-only port with `--p-` prefix; never blanket-import |
| Webfont bloat (Gowun Batang, Newsreader, JetBrains Mono) | High | First-paint slowdown, layout shift | Do not import additional font families. Keep Pretendard only. Use `font-family: serif/monospace` system fallbacks for `serif-en`/`mono` accents |
| React/Babel runtime leaking into production | High | Rule 11 violation, ~250 KB extra JS, security surface | Strip `<script type="text/babel">` and React/Babel CDNs on every import |
| `body.searched` / `body.searching` state machine breakage | High | Header collapses, visa manual hidden incorrectly | Never replace `<body>` markup wholesale; add new sections **inside** the existing layout shell |
| Backend URL override removal | High | Frontend cannot reach Railway backend | Preserve `window.PARADISO_BACKEND_URL` block (line 2999–3001 of `index.html`) |
| Consent modal removal in `ai.html` | High | Privacy regression | Never replace `ai.html` wholesale; add prototype's UX as additive elements |
| Brand drift (`Paradiso 39`, "Moonshot") | Low | Rule 1/2/4 violation | `scripts/check_repo.sh` already greps for these; CI will catch |
| Re-introducing a Vite/React scaffold | Low | Catastrophic frontend break | Hard rule: no `id="root"`, no `/src/main.tsx`, no `package.json` for the frontend |
| Treating `visa_data.json` as source | Low | Rule 5/7 violation | No data changes in this audit. Future PRs must source from manuals/doc_master, not the design files |

---

## 8. Recommended PR sequence

Each PR is small, single-purpose, and reversible. Each ships only if the prior one is green.

1. **PR-A (this PR)** — `audit/claude-design-integration-plan`
   - Adds `docs/design/CLAUDE_DESIGN_INTEGRATION_AUDIT.md` (this document).
   - No production code change.
   - Validation: `bash scripts/check_repo.sh` passes; HTML structure unchanged.

2. **PR-B** — `feat/design-tokens-additive`
   - Add a small block of `--p-*` design tokens (palette + type scale + spacing) to `index.html` and `ai.html` `<style>`. **Additive only**; nothing renamed, nothing removed.
   - No new fonts, no new imports.
   - Validation: visual diff before/after = 0; `check_repo.sh` passes.

3. **PR-C** — `feat/landing-dual-entry-rail`
   - Add the "A. 비자 코드를 알고 있어요 / B. 제 상황만 설명할 수 있어요" entry-card pair to the landing hero, wired to **existing** search query handlers. Above or beside the current search box.
   - No removal of current search form, no change to result rendering.
   - Validation: existing search and direct-search toggle still work; `body.searched` cascade still triggers; `check_repo.sh` passes.

4. **PR-D** — `feat/landing-pathway-grid`
   - Add the 8-card pathway grid linking to existing supported search query strings. Document the exact query strings in the PR body.
   - Validation: every pathway link resolves to a working query against current search.

5. **PR-E** — `feat/landing-trust-roadmap-strip`
   - Trust/citations + roadmap + footer CTA (presentational only). Tie citation copy to actual sources in `doc_master.json` / manual PDFs (rule 6).

6. **PR-F** — `feat/ai-privacy-polish`
   - Add the prototype's visible "Privacy · 입력하지 마세요" inline list and per-turn disclaimer callout to `ai.html` **without** removing the consent modal, `reference-disclaimer`, or `DISCLAIMER` constant.
   - Validation: consent gate still triggers on first visit; `localStorage` consent flow unchanged; `1345` and `매뉴얼` references still present.

7. **PR-G** (optional, deferred) — `feat/reveal-on-scroll`
   - Inline `app.js` reveal observer (≤60 lines) gated to specific new sections via `[data-reveal]`. Skip if motion adds no UX value.

8. **Deferred / discussion**: per-visa detail page, mobile bottom-nav shell, situation wizard. These need separate product decisions and data plumbing — not UI-polish PRs.

---

## 9. Exact implementation plan for the next PR (PR-B: design tokens, additive)

**Goal**: add a small, prefixed design-token block to `index.html` and `ai.html` so subsequent PRs (C/D/E/F) have a shared vocabulary, without touching any existing styles.

### Scope

- Modify: `index.html`, `ai.html`.
- Insert: a single `<style id="paradiso-design-tokens">` block immediately after the existing in-page `<style>` open block (so existing rules still cascade), defining only `--p-*` custom properties.
- No selector changes, no rule removals, no new external imports.

### Token subset to port (from `assets/styles.css` lines 9–79)

```css
/* paradiso-design-tokens — additive, prefixed, no overrides */
:root {
  /* palette */
  --p-ink:        #0E1F1A;
  --p-ink-2:      #233530;
  --p-ink-3:      #4A5852;
  --p-ink-mute:   #7A8580;
  --p-paper:      #F4EEE0;
  --p-paper-2:    #EAE2D0;
  --p-paper-3:    #DDD4BD;
  --p-green:      #1F4F3D;
  --p-green-deep: #143329;
  --p-green-soft: #2E6B53;
  --p-mint:       #B7D9C8;
  --p-mint-soft:  #DCE9DD;
  --p-coral:      #C95440;
  --p-coral-deep: #9F3A28;
  --p-coral-soft: #F2C9BD;
  --p-line:       #C9BFA5;
  --p-line-2:     #DCD3BC;
  --p-accent:        var(--p-green);
  --p-accent-deep:   var(--p-green-deep);
  --p-accent-soft:   var(--p-mint-soft);
  --p-accent-on:     #ffffff;

  /* type scale */
  --p-fs-xs:   0.75rem;
  --p-fs-sm:   0.8125rem;
  --p-fs-base: 0.9375rem;
  --p-fs-md:   1.0625rem;
  --p-fs-lg:   1.25rem;
  --p-fs-xl:   1.5rem;
  --p-fs-2xl:  2rem;

  /* spacing (4pt) */
  --p-s-1: 0.25rem; --p-s-2: 0.5rem; --p-s-3: 0.75rem; --p-s-4: 1rem;
  --p-s-5: 1.5rem;  --p-s-6: 2rem;   --p-s-7: 3rem;    --p-s-8: 4rem;

  /* radius / shadow */
  --p-r-sm: 6px; --p-r-md: 10px; --p-r-lg: 16px; --p-r-xl: 24px;
  --p-shadow-1: 0 1px 0 rgba(14,31,26,0.04), 0 1px 2px rgba(14,31,26,0.05);
  --p-shadow-2: 0 4px 12px rgba(14,31,26,0.06), 0 1px 2px rgba(14,31,26,0.04);
  --p-shadow-3: 0 12px 32px rgba(14,31,26,0.10), 0 2px 6px rgba(14,31,26,0.05);

  /* motion */
  --p-ease: cubic-bezier(0.22, 0.61, 0.36, 1);
  --p-dur-1: 180ms;
  --p-dur-2: 320ms;
}
```

Notes:

- **No** type-family tokens are added in this PR. Pretendard remains the sole font. `serif-en` / `mono` accents from the prototype are deferred until we actually ship a section that uses them; we will reuse system fallbacks then.
- **No** 3xl/4xl/5xl fluid type tokens, since they imply hero typography we are not changing yet.
- The `--accent`/`--accent-deep`/`--accent-soft` triple is included under the `--p-` prefix so PR-C can theme the new entry rail without a second token PR.

### Tests / validation

```bash
bash scripts/check_repo.sh

# HTML sanity (must all be 1, 1, 1, 1):
grep -c '^<!DOCTYPE html>' index.html
grep -c '^<html ' index.html
grep -c '^</html>' index.html
grep -c '^<body' index.html

# No prototype contamination:
grep -nE 'react\.development|babel/standalone|type="text/babel"|id="root"|src/main\.tsx' index.html ai.html  # expect: empty
grep -nE 'Paradiso 39|PARADISO 39|paradiso 39|Paradiso39|Moonshot|moonshot' index.html ai.html visa_data.json  # expect: empty
```

### Out of scope for PR-B

- No HTML markup changes.
- No new fonts.
- No `app.js` import.
- No data file edits.
- No new routes.

---

## Validation results for THIS PR (audit-only)

```text
$ git status --short
(audit doc only)

$ bash scripts/check_repo.sh
[1/4] Validating visa_data.json format...
[2/4] Validating representative manual-aware visa schema...
[3/4] Running git diff --check...
[4/4] Scanning key user-facing files for forbidden branding strings...
INFO: Skipping missing optional file: moonshot_backend_fastapi.py
Success: repository validation passed.

$ grep -c '<!DOCTYPE' index.html      → 1
$ grep -c 'id="root"' index.html      → 0
$ grep -c 'main\.tsx' index.html      → 0
$ grep -in 'Paradiso 39' index.html ai.html  → (no match)
$ grep -in 'Moonshot'    index.html ai.html  → (no match)
```

Production HTML is valid; **no production files are modified by this PR**. Implementation work begins with PR-B.
