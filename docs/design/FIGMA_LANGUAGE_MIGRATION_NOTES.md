# Figma Language Migration — Notes

**Branch:** `design/figma-language-migration`
**Source reference (visual only):** Figma Make — `Paradiso 후보` (`N695iXnoavEOSHITttdCCu`)
**Target file:** `index.html` (production source of truth, untouched HTML)
**Strategy:** CSS-only additive translation. The Figma Make React/HTML is treated as a visual reference and is **not** copied wholesale. All changes live in a single, clearly-tagged `FIGMA LANGUAGE MIGRATION` block at the bottom of the existing `<style>` element.

---

## 1. Figma visual elements migrated

The migration is namespaced through existing production classes — no new IDs/classes were introduced.

### Global tokens (additive `:root` block)
- `--fig-glass-bg`, `--fig-glass-bg-hi`, `--fig-glass-border`, `--fig-glass-border-hi`, `--fig-glass-blur`
- `--fig-glass-shadow`, `--fig-card-shadow`, `--fig-card-shadow-hi`
- `--fig-green-glow`, `--fig-coral-glow`
- `--fig-ease-out: cubic-bezier(0.16, 1, 0.30, 1)` (Figma's signature easing)

These complement, not replace, the existing `--p-*`, `--color-*`, `--btn-*` token systems.

### Hero section
- **Search bar (`.sbar`)** — true glassmorphism on the photo hero: `rgba(255,255,255,0.13)` + `blur(20px) saturate(140%)`, full-radius pill, `inset 0 1px 0 rgba(255,255,255,0.10)` highlight, deep `0 16px 48px -8px rgba(0,0,0,0.28)` shadow.
- **Search "go" button (`.sbar-go`)** — solid `#0EA37B` pill with `0 8px 22px rgba(14,163,123,0.40)` green glow, hover lifts and deepens to `#085E48`.
- **Direct-search toggle (`.search-toggle-btn`)** — glass dashed border that fills with mint glow on hover/active.
- **Quick-action grid tiles (`.qa-main .hero-action-btn`)** — glass tiles with mint hover (`rgba(14,163,123,0.16)` bg, mint border).
- **Hero proof chips (`.p-proof-chip`)** — uppercase tracking 0.04em, mint hover.
- **Hero eyebrow (`.p-hero-eyebrow`)** — tightened tracking 0.22em.
- **A/B entry rail (`.p-entry-card`)** — richer glass, mint hover with inner ring shadow; mark icon shifts to mint+green fill on hover.
- **Visa-track cards** — same mint-glow hover language.
- **AI secondary link** — Figma's coral-tinted glass pill.
- **Reference disclaimer** — softened cream tone over the dark hero.

### Search/keyword chips
- **Keyword pills (`.lh`)** — full-radius, weight 600, mint hover (`#7DD8B8` text, mint border, soft green glow).

### Lower sections
- **Section kickers (`.p-kicker`)** — tightened tracking (0.18em) + weight 900 to match Figma.
- **Section titles (`.p-section-title`)** — letter-spacing -0.024em.
- **Pathway / tool cards** — `translateY(-3px)` lift with `--fig-card-shadow-hi`, mint border on hover.
- **Source / how / reminder cards** — base `--fig-card-shadow` elevation, lift on hover.
- **Status pills (`.p-status`)** — tighter letter-spacing (0.10em), weight 900.
- **Pathway code chips (`.p-code`)** — Figma's mint-soft background with deep-green text.
- **Source panel** — three-stop diagonal gradient (mint-soft → paper → coral-soft) with deep-green border.
- **Roadmap dots (`.exp-dot`)** — coral with `0 0 0 5px rgba(255,184,168,0.32)` ringed halo, scales to 1.18× on row hover.
- **Roadmap year chip (`.exp-year`)** — Figma's pill with subtle border and shadow.
- **Stat cards** — coral big number with subtle text-shadow, hover lift, refined chip palette.
- **Hobby/value cards** — hover lift with deeper shadow.

### Footer CTA
- **`.p-footer-cta` panel** — radial green glow at top-left over the existing deep-green linear gradient, mint border.
- **`.p-cta-btn`** — Figma easing, lift on hover.
- **`.p-cta-btn.primary`** — coral glow `0 6px 20px rgba(255,107,91,0.35)`, deeper coral on hover.
- **Figma footer hero (`.figma-footer-hero-title`, `.figma-footer-chips`)** — title tracking, chip backdrop-blur and mint hover.

### Brand-hero CTAs
- **`.brand-hero .btn-primary` / `.btn-secondary`** — radius-14px pill, lift on hover with deeper shadow.

### Responsive polish (≤640px)
- Search bar steps down to `border-radius: 18px`, padded comfortably.
- Search "go" becomes a 40-tall, 12-radius rect for mobile thumbs.
- Proof chips and footer chips reduce font-size for tight wrap.

### Accessibility
- All hover transforms are wrapped in a `@media (prefers-reduced-motion: reduce)` block that disables them.

---

## 2. Functional areas preserved (verified)

`git diff` against `origin/main` shows **483 additions, 0 deletions**. No HTML, JS, IDs, classes, ARIA attributes, data-action hooks, or behaviour were removed or renamed.

Confirmed intact:
- Existing search logic — `#searchForm`, `#q`, `#xb`, `.sbar-go` submit, `id="searchForm"` style="display:none" toggle.
- Direct-search toggle — `#searchToggleBtn` with `data-action="toggle-search"` and `aria-expanded` semantics.
- Direct-search open/close behaviour — `body.searching:not(.searched) #xb { display: block; }` and the `searched` state are not touched.
- `body.searched` state and the compact-header layout — only one cosmetic addition (`body.searched .sbar { border-radius: 14px; }`) which is purely visual.
- Keyword chips — `.lh`, `.landing-hints`, `.landing-hints-section`, `#landingHints` markup unchanged. Only colour/border/shadow on hover added.
- `visa_data.json` loading — file untouched (validated by `check_repo.sh`).
- Result rendering — `.rlist`, `.qf`, `.vc`, `.su` and all sub-classes untouched.
- Mobile responsive behaviour — additive `@media (max-width: 640px)` block, no edits to existing media queries.
- Validation script compatibility — `bash scripts/check_repo.sh` passes all 5 steps (JSON, manual schema, git diff --check, i18n, branding scan).
- Brand wordmark, anagram animation, scroll cue, modals, jurisdiction & jobcode tools — all untouched.

---

## 3. Figma elements intentionally NOT copied

These were considered and **not** ported to keep production stable:

- **`HeroGateway.tsx` markup** — its 4-tile gateway grid would replace the production hero rail (`.hero-actions` + `.qa-main` + `#visaManualSection`). We kept production's existing structure and only restyled it.
- **Framer Motion (`motion/react`)** — would add a runtime dependency. Migration uses CSS transitions only.
- **`lucide-react` icons (Search, Briefcase, Building2, Plane, ShieldCheck, etc.)** — production uses inline SVG and emoji icons. Not swapped.
- **Tailwind utility classes** — production is a single hand-written `<style>` block; we did not introduce a Tailwind build.
- **`shadcn/ui` primitives (button.tsx, dialog.tsx, etc.)** — large component library not needed for this design polish.
- **Anagram component (Diaspora ↔ Paradiso) re-implementation** — production already has a working `#anagram` SVG/JS implementation; only the dot/colour palette is aligned.
- **Wordmark image (`paradiso-wordmark-brush-white-2.png` from Figma's import folder)** — production already serves `assets/brand/paradiso-wordmark-brush-white.png`.
- **The Figma copy "Paradiso의 시작" + 300만 statements** — production has its own approved Korean copy. Copy was not altered.
- **The "Paradiso.ai — 내 상황 AI 분석" coral pill, the "자주 찾는" popover, and the gateway-tile sub-labels** — production has its own AI link (`.hero-ai-secondary`) and popover replacement; only colour was tuned.
- **The Figma `BrandHero` "Korea's 39 visa categories. Unified." stat-card overlap (translate-y-1/2)** — production places `.brand-hero-stats` inline; the floating overlap was not introduced (it would require structural HTML changes).

---

## 4. Risks checked

| Risk | Outcome |
| --- | --- |
| Forbidden branding strings (`Paradiso 39`, `Moonshot`, etc.) | 0 hits in `index.html`, `ai.html`, `visa_data.json` |
| `visa_data.json` modified | No (validated) |
| Backend files modified | No (none touched) |
| `body.searched` compact header broken | No — only `border-radius` cosmetic added; layout rules untouched |
| `#searchToggleBtn` direct-search toggle broken | No — only restyled `.search-toggle-btn` |
| `.lh` keyword chips selectable / clickable | Yes — only colour/border/shadow on hover added |
| `:focus-visible` outlines preserved | Yes — global `:focus-visible` rule untouched |
| `prefers-reduced-motion` honoured | Yes — added a dedicated `@media` block disabling new transforms |
| `body.night-light-mode` and `[data-theme="dark"]` rules preserved | Yes — none of those selectors were edited |
| `git diff --check` (whitespace, conflict markers) | Clean |
| `scripts/check_repo.sh` | All 5 steps pass |
| HTML structure overwritten | No — `git diff --numstat` = 483 / 0 (additions / deletions) |

---

## 5. Manual QA checklist

Run a local server and walk through:

- [ ] Landing hero renders: glass search bar visible over background, green search button has glow.
- [ ] Click `#searchToggleBtn` "비자 코드 및 키워드 직접 검색" — `#searchForm` opens; click again or click outside — closes (existing JS).
- [ ] Type a query (e.g. `D-2`) — autocomplete appears; press Enter — `body.searched` activates and the compact header replaces the hero.
- [ ] In compact header (`body.searched`), confirm: brand wordmark left, search bar centre, AND/OR/접기/펼치기 controls right; `.sbar` border-radius is the new 14px.
- [ ] `.landing-hints` chips: hover one — should turn mint with green glow; click — fills `#q` and triggers search.
- [ ] Brand-hero buttons (`서비스 소개`, `1345 직접 문의`) — hover lifts with deeper shadow.
- [ ] Stat cards (`.brand-hero-stats`) — hover lifts; numbers are coral.
- [ ] Pathway grid (`.p-pathway-card`) — hover: lift + mint border + deep shadow.
- [ ] Tool grid (`.p-tool-card`) — hover: same lift treatment; LIVE/PLANNED status pills tighter.
- [ ] Source panel (`.p-source-panel`) — three-stop gradient visible.
- [ ] Roadmap (`.about-experience .exp-row`) — hover: dot scales with halo.
- [ ] Footer CTA (`.p-footer-cta`) — radial green glow visible top-left, coral primary button has glow that deepens on hover.
- [ ] About-footer (`.about-footer .figma-footer-chips .footer-chip`) — chips lift on hover, mint border.
- [ ] Mobile (≤640px viewport): search bar pads comfortably, "go" button is 40-tall rectangle.
- [ ] Open `prefers-reduced-motion: reduce` (browser/OS) — hover transforms suppressed.
- [ ] Open dark theme (`◐ 테마 변경`) — design tokens still readable; no obvious regressions in compact header.
- [ ] Open jurisdiction modal, jobcode modal, AI modal — all still open/close.
- [ ] Refresh in `?lang=en` (or use language picker) — i18n still applies.

---

## 6. Recommended next PR (if more polish is desired)

- **Hero background photo system** — Figma uses a randomised set of 4–5 Jeju/Seoul photos with a deep-green tint (`rgba(5,66,52,0.62)`). Production currently uses CSS radial gradients on `.hero-container::before`. A future PR could lazy-load 1–2 hero JPGs (≤180KB each) and apply the same tint, behind a feature flag.
- **HeroGateway 4-tile rail** — port the Figma `GATEWAY_ACTIONS` 4-up grid (취업신고용 / 관할 출입국 / 입국 전 / 입국 후) as an *additional* layout under the search bar, behind a config flag, without removing the existing `#visaManualSection` track cards.
- **Brand-hero stat-card overlap** — implement Figma's `translate-y-1/2` floating stat panel that bridges the hero photo and the white sections (requires small HTML restructure to wrap `.brand-hero-stats` in a `position: relative` container).
- **Anagram visual** — adopt Figma's animated SVG-line bridge (active green / dim grey markers) to enrich the existing `#anagram` widget.
- **`shadcn/ui`-style focus ring tokens** — formalise the new mint focus glow as a reusable `--focus-ring-mint` token and migrate `.jc-search-input`, `.jur-select`, etc. onto it.
- **Brand-hero gradient background** — Figma's `BrandHero` uses `from-[#5b7ea6] via-[#7aaa8a] to-[#2d6a8f]`. Production's `.brand-hero` could borrow this for a richer mid-page gradient.

---

## 7. Implementation rule honoured

**Prefer CSS changes first. Only make HTML changes where necessary.**

→ **Zero HTML changes were made.** Every Figma design token was applied through additive CSS scoped to existing class/ID selectors.
