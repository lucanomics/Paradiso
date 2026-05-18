# INDEX_HTML_FUNCTIONAL_UX_AUDIT_AND_CODEX_BRIEF.md

**Branch:** `claude/audit-index-html-apiiq`  
**Audit date:** 2026-05-18  
**Auditor:** Claude Code (automated audit pass)  
**Purpose:** Functional UX audit of index.html after PR #65 (manual-consistency corrections). This document is a planning brief only. index.html is NOT modified in this pass.

---

## 0. Context

PR #65 corrected copy-level overclaiming in index.html — removing the `logo-39` element, replacing hardcoded document lists with cautionary redirects, softening manual-badge logic, and adjusting several wording items.

This brief targets the **next layer**: functional UX gaps, accessibility holes, and small-JS improvements that can be shipped safely without touching backend, data files, AI infrastructure, or Railway-dependent features.

---

## 1. Current index.html Architecture Summary

### File size and structure

- **9,147 lines** (verified). Single-file application: HTML + embedded CSS (~3,500 lines) + embedded JS (~4,500 lines).
- No external JS bundle. No build step. Deployed as a GitHub Pages static file.

### Top-level layout (body class state machine)

| Body class | Visual state |
|---|---|
| `landing` | Hero expanded; landing scroll visible |
| `searching` | Search form visible; visa-manual-section hidden |
| `searched` | Hero compacted to sticky top bar; landing scroll hidden; results visible |
| `anagram-run` / `launching` | Transition animation during first search |

### Major DOM sections

| ID / selector | Description |
|---|---|
| `#hero` / `.hero-container` | Fixed hero header (logo, language, theme, city controls) |
| `.p-hero-copy` | Landing headline + proof chips |
| `.p-entry-rail` | Entry rail: Button A (toggle-search) + Card B (ai.html link) |
| `#heroActions` / `#searchToggleBtn` | Secondary search toggle button (visible after entry rail) |
| `#qaMain` | Job code modal + jurisdiction modal quick-access buttons |
| `#visaManualSection` | Track selector: 입국 전 / 입국 후 track cards |
| `#searchForm` | Search bar (hidden until `toggle-search`) |
| `#rlist` | Live results area (aria-live) |
| `.landing-scroll` | Brand hero, Feature, Pathways, How-it-works, Sources, Tools, Agent finder, About, CTA sections |
| Footer modals | AI modal, Job code modal, Jurisdiction modal, Doc modal, FAQ modal |

### JavaScript architecture

- Single `DOMContentLoaded` handler using **event delegation** via `data-action` attributes.
- `UI_TRANSLATIONS` object with 18 language packs. `applyLanguage()` called on load and language change.
- `VISA_DATA` loaded once via `loadVisaData()` (static JSON fallback; Railway API if available).
- `renderResults()` builds result cards via DocumentFragment and innerHTML string templates.
- `initScrollReveal()` registers two `IntersectionObserver` instances: `_revealObs` (fade-reveal) and `_staggerObs` (count-up stagger). **A second IIFE-scoped observer is also registered at lines ~8584–8605, duplicating the same `[data-reveal]` observation.** Both observers fire on the same elements.
- `initAgentFinder()` IIFE loads `data/agent_registry_2026-04-30.json` via `fetch`.

### Data dependencies

| Source | Fallback | Status |
|---|---|---|
| `visa_data.json` (static) | Embedded inline fallback in JS | Always available offline |
| Railway `/api/visa-data` | Static JSON fallback | On hold (railway work deferred) |
| `data/agent_registry_2026-04-30.json` | Error state shown | Required for agent finder |
| Language pack (`UI_TRANSLATIONS`) | `ko` pack | Always available |

---

## 2. Fragile Areas — Do Not Touch

The following areas have known complexity or dependencies that make changes high-risk. Codex must not modify these unless explicitly specified in a future brief.

| Area | Reason |
|---|---|
| `loadVisaData()` and Railway API fallback logic | Controls data source. Touching breaks both online and offline fallback. |
| `calculateScore()` and `expandKeywords()` + `ALIAS_MAP` | Core search algorithm. Any change could silently break code-normalization (D2 → D-2). |
| `renderResults()` DOM structure (`.vc`, `.vc-h`, `.vc-cw`, `.vc-c`) | CSS rules for `body.searched` state are tightly coupled to these class names. |
| `selectInKoreaAction()` CONFIG structure | Corrections from PR #65 are in place. Document lists are removed. The remaining content is clean. |
| `renderSourceEvidencePanel()` badge logic | PR #65 already corrected the manual-badge overclaim. Any further changes risk reintroducing the problem. |
| `applyLanguage()` and `UI_TRANSLATIONS` | 18-language pack. Adding new keys is safe; changing key names or the `tx()` lookup system is not. |
| `initAgentFinder()` IIFE | Agent finder is self-contained. Modifying its filter logic could break region-select + keyword combined search. |
| `initScrollReveal()` + the duplicate IIFE observer | Both observers fire on `[data-reveal]`. Removing one without understanding the initialization order could break landing animations. Do not merge or remove either observer in PR 1. |
| `body.searched` compact header CSS | Approximately 40 CSS rules scope to `body.searched`. Any structural HTML change to `.hero-container` or `.search-wrap` risks breaking the compact state. |
| `executeSearch()` anagram animation sequence | The `anagram-run` → `launching` → `searched` transition uses hardcoded timeouts (2200ms, 1200ms). Do not change. |
| AI modal and FAB (`a.ai-fab`) | On hold. Do not touch. |

---

## 3. Audit Findings by Area

### 3.1 Landing hero usability

**Finding A — Duplicate search-trigger mechanism**  
The landing hero has two side-by-side triggers for opening the search form: (1) the `p-entry-card` Button A (`data-action="toggle-search"`) in `.p-entry-rail`, and (2) `#searchToggleBtn` in `#heroActions` directly below it. Both call the same `toggle-search` action. The `#heroActions` row is effectively redundant when `.p-entry-rail` is visible, creating visual clutter on mobile (390px).

**Finding B — `#searchToggleBtn` label redundancy**  
`#searchToggleBtn` reads "비자 코드 및 키워드 직접 검색" (same as `.p-entry-card` Button A title). The aria-label and visible label are identical; when the search form is open, the label changes to "직접 검색 닫기" (correct). However, on narrow screens where the entry rail is stacked, both triggers are visible simultaneously and both say the same thing.

**Finding C — Search input disabled state UX**  
The `<input type="search" id="q">` starts in `disabled` state with `placeholder="데이터 로딩 중…"`. On slow networks this placeholder persists until data loads. There is no visible loading indicator in the search bar beyond the placeholder text. Users may not understand why the input is unresponsive.

**Finding D — Entry rail card B links to ai.html (on hold)**  
Card B ("제 상황만 설명할 수 있어요") links to `ai.html`. This is intentional and must remain, but its `p-entry-sub` text could create expectations about Railway-dependent AI availability. Copy clarification is in scope for PR 1.

---

### 3.2 Visa-code search UX

**Finding E — Autocomplete list closes on blur without delay**  
`#auto-list` closes when `document.click` fires outside it. No delay is applied. If the user tabs through suggestions with keyboard, closing on blur prevents tab-based selection. The `auto-item` elements use `data-action="search-hint"` and `div` elements (not `<button>` or `<option>`), so they are not natively focusable or keyboard-activatable. **Keyboard users cannot navigate autocomplete suggestions.**

**Finding F — Input search mode AND/OR buttons (`#ma`, `#mo`) are hidden on landing**  
The AND/OR toggle in `.ctrls` is positioned after `#searchForm` in the DOM but has no aria description explaining its purpose to screen-reader users. Labels "AND" / "OR" are code-level only; no aria-label clarifies "검색 모드 선택".

**Finding G — Placeholder does not suggest sub-code format**  
Placeholder reads "비자 자격 및 키워드 검색". Many users arrive looking for `D-2-1` or `E-7-4` sub-codes. The entry rail subtitle already shows `"D-2 · F-2-7 · E-7-1 …"` but the actual search input does not. A minor copy improvement.

---

### 3.3 Search result cards

**Finding H — `vc-h` click target has no `aria-expanded` state**  
Each card header (`.vc-h[data-action="toggle-su"]`) toggles the `.open` class on the parent `.vc`. The toggle chevron (`▼`) has no aria state. Screen readers cannot determine whether a card is expanded or collapsed. `aria-expanded` is missing from the toggle element, and `aria-controls` does not point to the `.vc-cw` content region.

**Finding I — Card animation entry index cap**  
`c.style.setProperty('--i', Math.min(idx, 10))` caps the stagger animation index at 10. Cards beyond index 10 all share the same `--i: 10` animation delay. If 30+ results are rendered, cards 11–30 all animate in simultaneously. This is a minor visual issue, not a regression risk, but PR 2 could raise the cap to 20.

**Finding J — `es` empty-state has no recovery action**  
When no results are found, the `.es` empty-state renders a title ("검색 결과 없음") and description with the query. It does not include a "추천 키워드 보기" or "초기화" button. Users at zero results have no in-page next step.

**Finding K — Copy-result button feedback is too subtle**  
`copyVisaResult()` changes the button label from "결과 복사" to "✓" for 1500ms. On narrow screens the button is small and the feedback is easy to miss. A toast message would be more visible.

---

### 3.4 Source/evidence panel in visa result cards

**Finding L — Source evidence panel `<details>` closed by default**  
`renderSourceEvidencePanel()` returns a `<details>` element that is collapsed by default. The unverified disclaimer ("`출처 메타데이터 미확인`") is inside the collapsed panel. Users who do not expand the panel will not see the disclaimer. This is a mild risk for the information-trust story.

**Finding M — `renderSourceReferences()` is defined but never called in the result pipeline**  
The function exists (line ~7155) and builds a rich source-reference box with `manualRefs`, confidence labels, and review status. It is called in neither `renderResults()` nor the card render pipeline. This is dead code in the current UI. It should not be wired up in PR 1 (untested), but should be noted for a future PR.

---

### 3.5 Keyword/direct-search toggle behavior

**Finding N — Close button of search form (`#xb`) double-duties as clear-only**  
When the search form is open and the query is empty, `clearSearch()` calls `closeDirectSearchMode()`. When the query is non-empty, it only clears the query text and keeps the search form open. This behavior is documented in the code (`debugSearchState`) but is not communicated visually. On mobile, a user pressing ✕ on an empty field expects the whole search bar to close, which it does — but the icon and label are both "✕" with no tooltip on mobile.

**Finding O — `aria-expanded` on `#searchToggleBtn` is set correctly (`false`/`true`) but the controlled element is not referenced**  
`#searchToggleBtn` sets `aria-expanded` correctly. However, `aria-controls="searchForm"` is absent, so screen readers cannot navigate from the button to the revealed panel.

---

### 3.6 Registered-agent finder entry and search UX

**Finding P — No initial guidance count**  
On page load, the agent finder section shows the prompt text ("지역명, 사무소명…을 입력해 등록된 민원대행기관을 찾아보세요.") and an empty list. The total number of available agencies is never shown in the initial state, so users don't know the size of the dataset before searching. The `agentCountAll` i18n key exists for post-search use. A simple "총 N개 기관 등록됨" in the prompt area would improve discoverability.

**Finding Q — Region `<select>` and keyword `<input>` are side-by-side but unsynchronized placeholder**  
The region select starts with "전체 지역" and the keyword input has a placeholder. When both are combined, filter logic is AND (both must match). There is no visible label or note explaining that region and keyword filters are combined, which may confuse users who expect OR behavior.

**Finding R — "더 보기" button is hidden initially and appears only when `visibleCount < filteredAgencies.length`**  
This is correct behavior. The `PAGE_SIZE = 12` is a reasonable default. No issue found.

**Finding S — Card `<h3>` for agency name has no minimum height or overflow handling**  
Some agency names are long. On 390px, the name wraps unpredictably. No `min-height` or `overflow-wrap` is set on `.p-agent-finder__card h3`. This is a CSS-only fix.

---

### 3.7 Mobile layout at 390px

**Finding T — `.p-entry-rail` and `#heroActions` stack creates two search triggers on one screen**  
At 390px, both `.p-entry-rail` (with Button A "비자 코드를 알고 있어요") and `#searchToggleBtn` ("비자 코드 및 키워드 직접 검색") are visible. This is the same issue as Finding A, but critically on mobile the two identical CTAs create confusion about which one to tap.

**Finding U — `.top-ctrls` overlaps hero content on 390px**  
The top controls (language, theme, city buttons) are `position: fixed; top: 1.2rem; right: 1.2rem`. On 390px, these buttons overlay the `.p-hero-eyebrow` line and potentially the start of `.p-hero-title`. The `@media (max-width: 640px)` rule reduces the right offset to 0.6rem but does not move the controls below the fixed area. Minor layout overlap.

**Finding V — `.p-pathway-grid` overflows at 390px**  
The pathway grid uses `grid-template-columns: repeat(auto-fill, minmax(220px, 1fr))` with no explicit 390px override. At 390px the `minmax(220px, ...)` means one column of 220px + overflow. A `@media (max-width: 480px)` override setting `minmax(160px, 1fr)` would eliminate horizontal scroll.

**Finding W — `.brand-hero-stats` `.stat-card` grid at 480px**  
The `@media (max-width: 480px)` rule adjusts `.brand-hero-stats` width but not the grid column template. The stat card grid (`grid-template-columns: repeat(4, 1fr)`) collapses to 2x2 only at `768px`. At 390px four columns of stat cards are squeezed and the `.stat-code-chip` text overflows the card boundaries.

---

### 3.8 Language toggle behavior

**Finding X — Language menu `<ul>` items are `<li>` elements with `data-action="set-language"`**  
`renderLanguageMenu()` builds a `<ul role="listbox">` with `<li role="option">` items. The `data-action="set-language"` delegation pattern is used. `aria-selected` is set on the current language option. This is structurally acceptable. However, when a language is changed, `document.documentElement.lang` is updated but the `<html lang="">` attribute is not reflected in screen reader announcements because the update happens after the menu closes. The `aria-live` toast confirms the change. Acceptable as-is.

**Finding Y — Language change does not re-render the agent finder card list**  
`applyLanguage()` calls `setText()` on named UI strings including `#agentFinderShowMore` and `#agentFinderEmpty`. However, already-rendered agent finder cards (built by `buildCard()` in `initAgentFinder()`) use `tx()` calls at render time. If the user changes language after agent results are visible, the card action labels ("네이버 지도", "카카오맵", "주소 복사", phone) remain in the language they were rendered in. This is a low-severity issue — card actions are proper nouns or static map links.

---

### 3.9 Empty/error/loading states

**Finding Z — Visa data load failure has no visible UI fallback**  
`loadVisaData()` has a static offline fallback (`VISA_DATA_OFFLINE`) but no visible error state. If both the API and the static fallback fail, the input remains disabled and `#rc` reads "데이터 로딩 중…" indefinitely. There is no timeout-triggered error message.

**Finding AA — Agent finder error state (`#agentFinderError`) exists but is never re-shown on retry**  
The error element (`role="alert"`) is shown when `fetch()` for the agent registry fails. There is no retry button. The `#agentFinderError` text links to HiKorea (acceptable), but a "다시 시도" button would improve recovery. This belongs in PR 2.

**Finding AB — `inKoreaVisaSearch` input has no loading/empty state**  
Inside `selectInKoreaAction()`, the sub-search input (`#inKoreaVisaSearch`) shows an empty `#inKoreaVisaList` when query is empty or no results match. The `filterInKoreaVisaList()` function sets `listEl.innerHTML = ''` on empty query but provides no prompt text. Users typing in the box see nothing until they start filtering, without knowing whether the system is ready.

---

### 3.10 Accessibility

**Finding AC — `.vc-h` toggle (card expand/collapse) missing `aria-expanded` and `aria-controls`**  
See Finding H. High priority. Affects all search result cards.

**Finding AD — Autocomplete `auto-item` divs are not keyboard-focusable**  
See Finding E. `<div data-action="search-hint">` elements are not in the tab order and have no `role="option"` in a `role="listbox"` container. WCAG 2.1 failure (keyboard navigation). Medium priority — requires JS change, belongs in PR 2.

**Finding AE — `#searchToggleBtn` missing `aria-controls`**  
See Finding O. Add `aria-controls="searchForm"`. CSS-safe, PR 1.

**Finding AF — `.ctrls` AND/OR buttons lack descriptive `aria-label`**  
`<button id="ma">AND</button>` and `<button id="mo">OR</button>` are rendered with just the mode text. A screen reader reads "AND button" and "OR button" with no context. Add `aria-label="AND 검색 모드" / "OR 검색 모드"` or a `title` attribute. PR 1 (HTML-only).

**Finding AG — Visa track cards (`.visa-track-card`) use `onclick` inline handlers and `role="button"` on a `<div>` but are missing `tabindex="0"` focus indicator CSS**  
The track card `<div tabindex="0" role="button">` elements are keyboard-focusable but `:focus-visible` outline is set globally (`2px solid var(--color-accent)`). Verify the outline is visible on the `.visa-track-card` background color. This is a visual audit item.

**Finding AH — Modal focus trap is incomplete for all modals**  
The modals use a simple `closeModal()` / `openModal()` pattern. Focus is not trapped inside modals. Tab key can exit the modal to background content. This is a WCAG 2.1 AA issue (dialog focus trap). Belongs in PR 2.

**Finding AI — `aria-live="polite"` on `#rlist` may be over-announcing**  
When `renderResults()` fires on debounced input, `#rlist` is an `aria-live="polite"` region. Every keystroke after a search triggers a full re-render and re-announcement. Debounce is 150ms (see `handleInput`). This is fast enough to create noisy screen-reader output on keystroke-by-keystroke searches. Low priority.

---

### 3.11 Performance risks

**Finding AJ — Two IntersectionObserver instances observe `[data-reveal]` simultaneously**  
`initScrollReveal()` creates `_revealObs` (lines ~8546–8555). An IIFE at lines ~8584–8605 creates a second `observer` on the same `[data-reveal]` elements. Both fire on intersection. The result is `classList.add('revealed')` is called twice per element — harmless but wasteful. `_staggerObs` duplicates stagger logic already in the IIFE. This should be cleaned up in PR 2 (remove the IIFE, keep `initScrollReveal`).

**Finding AK — `renderResults()` uses `innerHTML` on entire result set**  
`renderResults()` builds a `DocumentFragment` but each card is assigned via `c.innerHTML = ...` with template string interpolation. This constructs potentially 30+ cards with full HTML string generation on every keystroke (debounced 150ms). Not a critical issue for a dataset of ~35–40 items, but worth noting.

**Finding AL — `setInterval` in `initFigmaAnagram()` runs indefinitely on the About section**  
The anagram animation uses `setInterval()` with no cleanup. On pages that keep the browser tab open for extended periods, this interval continues cycling even when the section is offscreen. Low priority, but could be paused with `IntersectionObserver`.

---

### 3.12 Copy clarity

**Finding AM — Hero subtitle `brandHeroSubtitle` in `UI_TRANSLATIONS.ko` still reads "Korea's 39 visa categories. Unified."**  
The HTML at line ~4983 was updated by PR #65 to "Korea's residence categories, organized by purpose." but the `UI_TRANSLATIONS.ko.brandHeroSubtitle` key (line ~7530) still contains the old value: `"Korea's 39 visa categories. Unified."`. When `applyLanguage()` runs on load, it overwrites the corrected HTML with the stale i18n string. This is a **regression from PR #65** — the copy fix was applied to the static HTML but not to the `UI_TRANSLATIONS` JS object.

**Finding AN — `UI_TRANSLATIONS.ko.featureChecks[4]` EN span still reads "Results with source-checking guidance"**  
The static HTML was updated in PR #65 to "공식 출처 확인 흐름 안내 / Results with source-checking guidance". The `UI_TRANSLATIONS.ko.featureChecks[4]` at line ~7536 reads: `'<strong>공식 출처 확인 흐름 안내</strong><span lang="en">Results with source-checking guidance</span>'`. The Korean is correct but the EN sub-span is unchanged from PR #65 (it was acceptable). No change needed.

**Finding AO — `UI_TRANSLATIONS.ko.brandHeroStats` stat card labels include the same count `"8"` for 유학·연수**  
The stat card counts (14/8/7/10) are hardcoded in both the HTML `data-count` attributes and the count-up animation. They are not i18n values. MEDIUM-1 from the previous audit notes the mismatch with visa_data.json. This is out of scope for UX improvements.

**Finding AP — `.p-entry-card` button B links to `ai.html`**  
"제 상황만 설명할 수 있어요 / 안내 질문에 답하면 경로를 찾아드려요" — this copy implies interactive guided navigation. Since `ai.html` work is on hold, the sub-text could be softened to avoid setting expectations. Low severity. PR 1 copy-only change.

---

## 4. Fragile Areas Summary Table

| Area | Risk | Action |
|---|---|---|
| `calculateScore()` / `expandKeywords()` | HIGH — core search | Never touch |
| `body.searched` CSS (~40 rules) | HIGH — layout state | Only add new rules |
| `loadVisaData()` fallback chain | HIGH — data source | Never touch |
| Railway API integration | HIGH — on hold | Never touch |
| Duplicate `IntersectionObserver` IIFE | MEDIUM — cleanup risk | PR 2 only, with caution |
| `renderSourceEvidencePanel()` badge logic | MEDIUM — post-PR#65 | Do not re-edit in PR 1 |
| `applyLanguage()` key names | MEDIUM — 18 languages | Only add new keys, never rename |
| `selectInKoreaAction()` CONFIG | LOW — PR#65 clean | Do not re-edit in PR 1 |
| Modal open/close system | LOW — functional | Focus trap PR 2 only |

---

## 5. Recommended PR Sequence

```
PR 1 (Safe CSS + HTML attributes + copy fixes)
  └── No JS logic changes
  └── No data file changes
  └── Fix Finding AM (i18n regression)
  └── Add aria attributes
  └── Fix mobile overflow
  └── Clarify search input labels

PR 2 (Safe JS improvements)
  └── Keyboard-accessible autocomplete
  └── Empty state recovery actions
  └── Duplicate observer cleanup
  └── Focus trap for modals (basic)
  └── Agent finder retry button

DEFER
  └── Hero full redesign
  └── ai.html changes
  └── Backend/API changes
  └── Full i18n overhaul
  └── Stay-status quiz
  └── Figma Design output implementation
```

---

## 6. Safe PR 1 Scope

**Category: CSS-only or very small HTML/copy/attribute changes. No JS logic changes. Low regression risk.**

### PR 1 — Item 1: Fix i18n regression — `brandHeroSubtitle` key (FINDING AM)

**Priority: CRITICAL (regression from PR #65)**  
`UI_TRANSLATIONS.ko.brandHeroSubtitle` at line ~7530 still contains `"Korea's 39 visa categories. Unified."`. When `applyLanguage()` runs on DOMContentLoaded, it overwrites the corrected HTML with this stale string. The corrected value is `"Korea's residence categories, organized by purpose."`.

- Also check and update the same key in all other language packs where the EN subtitle is mirrored. (Non-KO language packs that have the old subtitle are best left for a human reviewer to translate; for PR 1 it is sufficient to update the `ko` pack and any EN-language pack.)
- **Change:** `UI_TRANSLATIONS.ko.brandHeroSubtitle` value → `"Korea's residence categories, organized by purpose."`
- **Verify:** After change, reload with language=ko and inspect `.brand-hero-subtitle` text.

---

### PR 1 — Item 2: `#searchToggleBtn` — add `aria-controls` (FINDING AE / AO)

Add `aria-controls="searchForm"` to the `#searchToggleBtn` button element.

**HTML change (line ~4896):**
```html
<!-- Before -->
<button type="button" id="searchToggleBtn" class="hero-action-btn search-toggle-btn"
  data-action="toggle-search" aria-expanded="false">

<!-- After -->
<button type="button" id="searchToggleBtn" class="hero-action-btn search-toggle-btn"
  data-action="toggle-search" aria-expanded="false" aria-controls="searchForm">
```

---

### PR 1 — Item 3: AND/OR search mode buttons — add `aria-label` (FINDING AF)

Add descriptive `aria-label` attributes to the AND/OR control buttons.

**HTML change (lines ~4944–4945):**
```html
<!-- Before -->
<button class="cb on" id="ma" data-action="set-search-mode" data-mode="and">AND</button>
<button class="cb" id="mo" data-action="set-search-mode" data-mode="or">OR</button>

<!-- After -->
<button class="cb on" id="ma" data-action="set-search-mode" data-mode="and"
  aria-label="AND 검색 모드 (모든 키워드 포함)">AND</button>
<button class="cb" id="mo" data-action="set-search-mode" data-mode="or"
  aria-label="OR 검색 모드 (키워드 중 하나 포함)">OR</button>
```

---

### PR 1 — Item 4: Mobile `.p-pathway-grid` overflow fix (FINDING V)

Add a 480px breakpoint override for the pathway grid column template to prevent horizontal overflow on 390px.

**CSS addition (add after existing `@media (max-width: 480px)` block, or inside it):**
```css
@media (max-width: 480px) {
    .p-pathway-grid {
        grid-template-columns: 1fr;
    }
}
```

---

### PR 1 — Item 5: `.brand-hero-stats` — fix 4-column stat grid on narrow screens (FINDING W)

Add a 600px breakpoint (currently missing) to collapse the stat grid to 2×2.

**CSS addition:**
```css
@media (max-width: 600px) {
    .brand-hero-stats {
        grid-template-columns: repeat(2, 1fr);
    }
}
```

---

### PR 1 — Item 6: Entry Card B copy softening (FINDING AP)

The sub-text for the AI entry card currently implies interactive guided navigation. While the link to `ai.html` must remain, the sub-text can be softened.

**HTML change (line ~4889–4890):**
```html
<!-- Before -->
<span class="p-entry-sub">안내 질문에 답하면 경로를 찾아드려요</span>

<!-- After -->
<span class="p-entry-sub">상황 설명으로 적합한 자격 경로를 안내받을 수 있어요</span>
```

---

### PR 1 — Item 7: Agent finder card `overflow-wrap` fix (FINDING S)

Ensure long agency names do not overflow card boundaries on narrow screens.

**CSS addition (inside existing `.p-agent-finder__card` rule or a new addition):**
```css
.p-agent-finder__card h3 {
    overflow-wrap: break-word;
    word-break: keep-all;
}
```

---

### PR 1 — Item 8: Search input `aria-label` improvement (FINDING G)

The search input placeholder does not surface sub-code format. Update the placeholder in the i18n pack (not hardcoded HTML, since `applyLanguage()` overwrites it).

**i18n change — `UI_TRANSLATIONS.ko.qPlaceholder` (line ~7525):**
```js
// Before
qPlaceholder: '비자 자격 및 키워드 검색',

// After
qPlaceholder: '비자 코드 또는 키워드 검색 (예: D-2, E-7-1, 유학)',
```

Also update the `aria-label` via the `qAria` key:
```js
// Before
qAria: '비자 자격 및 키워드 검색',

// After
qAria: '비자 코드 또는 키워드 검색',
```

---

### PR 1 — Item 9: Source evidence panel — show unverified note outside `<details>` (FINDING L)

Move the unverified disclaimer note above the `<details>` summary so users see it without expanding. This is a pure HTML template string change inside `renderSourceEvidencePanel()`.

**Change in `renderSourceEvidencePanel()` function body (~line 7207):**
```js
// Before
return `<details class="source-evidence-panel">
    <summary><span class="sep-title">...</span><span class="sep-chevron">▾</span></summary>
    <div class="sep-body"><div class="sep-badges">${badges}</div>${noteHtml}</div>
</details>`;

// After
return `${noteHtml}<details class="source-evidence-panel">
    <summary><span class="sep-title">...</span><span class="sep-chevron">▾</span></summary>
    <div class="sep-body"><div class="sep-badges">${badges}</div></div>
</details>`;
```

Note: `noteHtml` is empty (`''`) when `isVerified` is true, so this change is invisible for verified entries. The note only appears when `!isVerified`.

---

## 7. Safe PR 2 Scope

**Category: Small JS-safe improvements. Low regression risk if changes are isolated.**

### PR 2 — Item 1: Keyboard-accessible autocomplete suggestions (FINDING E / AD)

Replace `<div>` elements in `#auto-list` with keyboard-focusable `<button>` elements (or add `role="option"` and `tabindex="0"`). Add keyboard handler for `ArrowUp`/`ArrowDown` navigation and `Enter` to select.

Minimum safe approach:
- Change `div.auto-item` to `button type="button" class="auto-item"` in `showSuggestions()`.
- The existing `data-action="search-hint"` delegation handles clicks already. Buttons are focusable and activatable by Enter/Space natively.
- Add `role="listbox"` to `#auto-list` and `role="option"` to each auto-item.

---

### PR 2 — Item 2: Empty-state recovery action (FINDING J)

When `renderResults()` finds zero matches, add a "추천 키워드 보기 →" button that clears the search query and scrolls to the `#landingHints` section.

```js
// Inside renderResults(), empty branch:
box.innerHTML = `<div class="es">
  <div class="es-t">${escapeHtml(tx('resultEmptyTitle'))}</div>
  <div class="es-d">${tx('resultEmptyDesc', { query: escapeHtml(query) })}</div>
  <button type="button" class="cb" style="margin-top:1rem;" data-action="reset-to-landing">
    ← 처음으로 돌아가기
  </button>
</div>`;
```

---

### PR 2 — Item 3: Copy-result feedback — add toast (FINDING K)

`copyVisaResult()` currently only mutates a button label for 1500ms. `showToast()` already exists in the codebase. Call `showToast(tx('copySuccess') || '복사되었습니다.', 'success')` after clipboard write.

---

### PR 2 — Item 4: Duplicate IntersectionObserver cleanup (FINDING AJ)

Remove the IIFE `observer` at lines ~8584–8605. `initScrollReveal()` handles all the same observation with better lifecycle control (re-observe on `resetReveal()`). The IIFE does not call `resetReveal()` on the observers it creates, so animations do not re-play when navigating back to the landing state.

**Before removing:** Manually test landing → search → reset with both paths to ensure `data-reveal` animations and `data-count` count-up animations still work after removal.

---

### PR 2 — Item 5: Agent finder retry button (FINDING AA)

Add a "다시 시도" button to `#agentFinderError`. On click, re-run the data fetch.

---

### PR 2 — Item 6: Basic modal focus trap (FINDING AH)

For each modal (`aiModalOverlay`, `jobCodeModalOverlay`, `jurisdictionModalOverlay`, `docModalOverlay`, `faqModalOverlay`):
- On `openModal()`: capture current `document.activeElement`, set focus to first focusable element in `.modal-box`, trap Tab key inside `.modal-box`.
- On `closeModal()`: restore focus to the element that triggered the modal open.

---

### PR 2 — Item 7: `inKoreaVisaSearch` initial prompt (FINDING AB)

Add a prompt `<p>` inside `#inKoreaVisaList` when query is empty:

```js
function filterInKoreaVisaList(query) {
  const listEl = document.getElementById('inKoreaVisaList');
  if (!listEl) return;
  if (!query || !query.trim()) {
    listEl.innerHTML = '<p style="font-size:0.85rem;color:var(--t3);padding:0.5rem 0;">코드 또는 이름을 입력하면 목록이 표시됩니다.</p>';
    return;
  }
  // ... existing filter logic
}
```

---

### PR 2 — Item 8: Agent finder — show total count in initial state (FINDING P)

After the agent registry is loaded but before any filter is applied, update `#agentFinderCount` with the total count (or add it to the prompt text):

```js
promptEl.hidden = false;
countEl.textContent = tx('agentTotalCount', { count: dataset.agencies.length }) || `총 ${dataset.agencies.length}개 기관`;
```

---

## 8. Explicit Out-of-Scope List

The following are explicitly deferred and must NOT be included in PR 1 or PR 2:

- Hero full redesign or layout restructure
- Figma or Claude Design output implementation
- ai.html changes of any kind
- Backend file changes (`moonshot_backend_fastapi.py`, `backend/` directory)
- Railway API integration or Railway-dependent behavior
- `visa_data.json` or `backend/data/visas.json` data changes
- `doc_master.json` changes
- Manual grounding / candidate / eval file changes
- API behavior changes
- Full internationalization overhaul (all 18 language packs updated simultaneously)
- Stay-status quiz implementation
- `renderSourceReferences()` wiring into the card pipeline (dead code, needs design review first)
- `setInterval` cleanup in `initFigmaAnagram()` (low priority, no regression risk)
- Changes to `calculateScore()`, `expandKeywords()`, or `ALIAS_MAP`
- Changes to `executeSearch()` timing values
- Reintroduction of "Paradiso 39" in any form

---

## 9. Codex Implementation Prompt for PR 1

```
TASK: Apply safe UX and accessibility improvements to index.html only.
No redesign. No backend changes. No data file changes. No ai.html changes.
Do NOT reintroduce "Paradiso 39".

BRANCH: claude/audit-index-html-apiiq (or create a new branch from main)

CONTEXT:
- Source doc: docs/INDEX_HTML_FUNCTIONAL_UX_AUDIT_AND_CODEX_BRIEF.md
- Previous corrections: docs/INDEX_MANUAL_CONSISTENCY_AUDIT.md (PR #65, merged)
- check_repo.sh steps [1]–[10] must pass after all changes
- git diff --check on index.html must pass

REQUIRED CHANGES (all in index.html):

1. [CRITICAL — i18n REGRESSION] Fix UI_TRANSLATIONS.ko.brandHeroSubtitle
   File location: search for `brandHeroSubtitle: 'Korea\'s 39 visa categories`
   Change value from: "Korea's 39 visa categories. Unified."
   Change value to:   "Korea's residence categories, organized by purpose."
   Note: Also check the `en` language pack for the same key. Update if present.

2. [ARIA] Add aria-controls to #searchToggleBtn
   Find: id="searchToggleBtn" ... aria-expanded="false"
   Add attribute: aria-controls="searchForm"

3. [ARIA] Add aria-label to AND/OR search mode buttons
   Find: id="ma" data-action="set-search-mode" data-mode="and"
   Add: aria-label="AND 검색 모드 (모든 키워드 포함)"
   Find: id="mo" data-action="set-search-mode" data-mode="or"
   Add: aria-label="OR 검색 모드 (키워드 중 하나 포함)"

4. [CSS — mobile] Add pathway grid single-column at 480px
   Find the @media (max-width: 480px) block.
   Add inside it (or in a new 480px block if cleaner):
     .p-pathway-grid { grid-template-columns: 1fr; }

5. [CSS — mobile] Add stat-card 2-column grid at 600px
   Add a new @media block:
     @media (max-width: 600px) {
       .brand-hero-stats { grid-template-columns: repeat(2, 1fr); }
     }

6. [CSS] Add overflow-wrap to agent finder card names
   Find the .p-agent-finder__card CSS rule (or add after it):
     .p-agent-finder__card h3 { overflow-wrap: break-word; word-break: keep-all; }

7. [COPY — soft] Soften entry rail Card B sub-text
   Find: <span class="p-entry-sub">안내 질문에 답하면 경로를 찾아드려요</span>
   Change to: <span class="p-entry-sub">상황 설명으로 적합한 자격 경로를 안내받을 수 있어요</span>

8. [i18n — search input] Update qPlaceholder and qAria in UI_TRANSLATIONS.ko
   Find: qPlaceholder: '비자 자격 및 키워드 검색'
   Change to: qPlaceholder: '비자 코드 또는 키워드 검색 (예: D-2, E-7-1, 유학)'
   Find: qAria: '비자 자격 및 키워드 검색'
   Change to: qAria: '비자 코드 또는 키워드 검색'

9. [UX — source panel] Move unverified note outside <details> in renderSourceEvidencePanel
   Find the return statement inside renderSourceEvidencePanel() that starts with:
     return `<details class="source-evidence-panel">
   Change so that ${noteHtml} appears BEFORE the <details> element, not inside it:
     return `${noteHtml}<details class="source-evidence-panel">
       <summary>...</summary>
       <div class="sep-body"><div class="sep-badges">${badges}</div></div>
     </details>`;

VALIDATION AFTER CHANGES:
1. Run: bash scripts/check_repo.sh
   Steps [1]–[10] must pass.
   Steps [11]–[13] may fail (fastapi/backend environment issue — not a regression).
2. Run: git diff --check -- index.html
3. Manually verify the manual test checklist in Section 10 of this document.
4. Do NOT commit until all checkboxes in Section 10 are verified.
```

---

## 10. Validation Checklist for PR 1

After applying all PR 1 changes, verify each item:

**i18n regression fix:**
- [ ] Load index.html in browser (or open static file). With default language (ko), inspect `.brand-hero-subtitle` — it should read "Korea's residence categories, organized by purpose." (NOT "Korea's 39 visa categories. Unified.")
- [ ] Switch language to EN; verify subtitle updates correctly for the EN pack.

**ARIA attributes:**
- [ ] `#searchToggleBtn` has `aria-controls="searchForm"` in the rendered DOM.
- [ ] `#ma` has `aria-label="AND 검색 모드 (모든 키워드 포함)"`.
- [ ] `#mo` has `aria-label="OR 검색 모드 (키워드 중 하나 포함)"`.

**Mobile layout:**
- [ ] At 390px viewport width: `.p-pathway-grid` shows as single column (no horizontal overflow).
- [ ] At 390px viewport width: `.brand-hero-stats` shows as 2×2 grid (not 4 columns).
- [ ] At 390px viewport width: no horizontal scrollbar on the main page body.
- [ ] At 390px: agent finder card names with long text wrap correctly inside card bounds.

**Copy / UX:**
- [ ] Entry rail Card B sub-text reads "상황 설명으로 적합한 자격 경로를 안내받을 수 있어요".
- [ ] Search input placeholder in KO mode reads "비자 코드 또는 키워드 검색 (예: D-2, E-7-1, 유학)".
- [ ] Source evidence panel unverified note is visible WITHOUT expanding the `<details>` element for a D-2 search result.
- [ ] For a verified entry (if any exist with `verified: true`), the note is absent.

**Regression checks:**
- [ ] `bash scripts/check_repo.sh` steps [1]–[10] pass.
- [ ] `git diff --check -- index.html` passes (no trailing whitespace or mixed line endings).
- [ ] No string "Paradiso 39" or "paradiso39" appears in index.html (check_repo.sh step [10] covers this).
- [ ] Search for D-2 still returns results.
- [ ] Search for D2 (no hyphen) still returns results (normalization must still work).
- [ ] Search for D-10 still returns results.
- [ ] Search for E-7 still returns results.
- [ ] Unknown visa code search (e.g. "ZZZZ") shows empty-state message.
- [ ] Direct-search toggle open (click Button A) → search form appears, visa-manual-section hides.
- [ ] Direct-search toggle close (click ✕ when query is empty) → search form hides.
- [ ] Language toggle: switch to EN and back to KO — UI strings update correctly.
- [ ] `body.searched` compact header: after a D-2 search, the header collapses to compact sticky bar, logo is visible, search form remains in top bar.
- [ ] Registered agent finder initial state: prompt text is visible, list is empty, no error shown.
- [ ] Agent finder search "서울": returns results.
- [ ] Agent finder search "제주": returns results.
- [ ] Agent finder search "강릉": returns results.
- [ ] Agent finder search "존재하지않는도시": shows empty-state message, not error.

---

## 11. Manual Test Checklist

Load `index.html` (GitHub Pages URL or local static file):

**Page load:**
- [ ] Page loads without console errors
- [ ] Default language is Korean (ko)
- [ ] Brand hero subtitle is "Korea's residence categories, organized by purpose."
- [ ] Logo area shows "Paradiso" — no "39" adjacent to brand name

**Search function:**
- [ ] Type "D-2" in search → cards for D-2 and sub-codes appear
- [ ] Type "D2" (no hyphen) → same D-2 cards appear (normalization working)
- [ ] Type "D-10" → D-10 구직 cards appear
- [ ] Type "E-7" → E-7 cards appear
- [ ] Type "ZZZZUNKNOWN" → empty-state "검색 결과 없음" message appears

**Source evidence panel:**
- [ ] Expand a D-2 result card → source evidence panel is present
- [ ] If the unverified note is displayed, it is visible BEFORE expanding `<details>`

**Search toggle:**
- [ ] Click "비자 코드를 알고 있어요" (Button A) → search form opens
- [ ] Click "직접 검색 닫기" (✕ button when query is empty) → search form closes, visa-manual-section returns
- [ ] After a search, body has `searched` class, compact header visible

**Language toggle:**
- [ ] Click language button → language menu opens
- [ ] Select English → UI updates to English
- [ ] Brand hero subtitle in English is correct
- [ ] Select Korean → UI reverts to Korean

**Registered-agent finder:**
- [ ] Scroll to "가까운 행정 도움 찾기" section
- [ ] Initial state: prompt text shown, result list empty
- [ ] Type "서울" in keyword field → results appear
- [ ] Type "제주" → results from 제주 appear
- [ ] Type "강릉" → results for 강릉 area appear (춘천 office with 강릉 listing)
- [ ] Type "ABCDEFGH_UNKNOWN" → empty-state message shown
- [ ] Select a region from the dropdown → filters results correctly

**Mobile 390px:**
- [ ] Resize browser to 390px width (or use DevTools device simulation)
- [ ] No horizontal scrollbar on body
- [ ] Pathway grid shows as single column
- [ ] Stat cards show as 2×2 (not 4 across)
- [ ] Search form fits within 390px without overflow
- [ ] Agent finder card names wrap without overflow

**Compact header after search:**
- [ ] Search for "D-2" from landing state → animation plays → `body.searched`
- [ ] Compact sticky header shows logo + search bar
- [ ] Clicking logo resets to landing state
- [ ] Landing scroll sections are hidden in `body.searched`
- [ ] Scrolling up/down while in searched state — header remains sticky at top

---

*End of audit and brief. Produced as audit-only pass on branch `claude/audit-index-html-apiiq`. No changes to index.html in this pass.*
