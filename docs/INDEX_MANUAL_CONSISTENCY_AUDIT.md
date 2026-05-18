# INDEX_MANUAL_CONSISTENCY_AUDIT.md

**Branch:** `audit/index-manual-consistency`  
**Audit date:** 2026-05-18  
**Auditor:** Claude Code (automated audit pass)  
**Purpose:** Pre-implementation correctness audit of index.html against committed 2026-05 visa/stay manuals. This document is a correction brief only. index.html is NOT modified in this pass.

---

## 1. Summary

An audit of index.html against the repository source hierarchy found **2 BLOCKER**, **3 HIGH**, **5 MEDIUM**, and **3 LOW** issues. No statement in index.html fabricates page numbers or invents documents. However, several user-facing passages overclaim manual grounding, present unverified document lists without disclaimers, and one category chip misclassifies a visa code.

**Manual extraction status:** `pdftotext` is unavailable in this environment. PDF content was not directly extracted. All findings are based on:
1. Committed grounding fixture `backend/data/manual_grounding/stay_manual_grounding_2026_05.json`
2. Committed coverage matrix `backend/data/eval/paradiso_coverage_matrix.json`
3. `visa_data.json` (display data, lowest trust)
4. `d10_candidate_attempt.md` (failure report)
5. Direct inspection of index.html (9,147 lines)

---

## 2. Source Hierarchy Used

| Priority | Source | Trust |
|----------|--------|-------|
| 1 | `docs/source-manuals/2026-05/stay_manual_2026_05.pdf` | Ground truth (unextractable in this env) |
| 2 | `docs/source-manuals/2026-05/visa_manual_2026_05.pdf` | Ground truth (unextractable in this env) |
| 3 | `stay_manual_grounding_2026_05.json` (active fixture) | Verified: D-2 pp.43-44, D-4 pp.90-91, E-7 p.226 |
| 4 | `paradiso_coverage_matrix.json` | Verified metadata control plane |
| 5 | `d10_candidate_attempt.md` | Documents D-10 source gap |
| 6 | `visa_data.json` / `backend/data/visas.json` | Display data only — NOT source of truth |
| 7 | `index.html` copy | Lowest trust — subject of this audit |

**Grounded coverage:** Only 3 (visa_code, procedure) pairs have active manual grounding:
- D-2 체류기간 연장허가 (stay_manual pp.43-44)
- D-4 어학연수생 체류기간 연장허가 (stay_manual pp.90-91)
- E-7 체류기간 연장허가 general (stay_manual p.226)

All other procedures are `scoped_fallback`, `candidate_only`, `clarification_needed`, or `unsupported` per the coverage matrix. All 35+ entries in visa_data.json have `sourceManualStatus.verified: false` and `needsManualReview: true`.

---

## 3. Files Inspected

- `index.html` (9,147 lines — full inspection)
- `backend/data/manual_grounding/stay_manual_grounding_2026_05.json`
- `backend/data/eval/paradiso_coverage_matrix.json`
- `visa_data.json`
- `docs/generated_candidate_attempts/d10_candidate_attempt.md`
- `scripts/check_repo.sh` (check [10/12] branding regex)

---

## 4. Table of Suspect Statements

### BLOCKER Issues

#### BLOCKER-1: D-10 chip displayed under 유학·연수 stat card

| Field | Value |
|-------|-------|
| **Location** | `index.html` lines 5016–5025, `<div class="stat-card">` for 유학·연수 |
| **Current wording** | Stat card: `<div class="stat-num" data-count="8">` labeled "유학·연수", with chip `<span class="stat-code-chip">D-10</span>` alongside D-2 and D-4 |
| **Problem** | D-10 is 구직 (job-seeking), **not** a study visa. `visa_data.json` has D-10 with `cat: 'work'`. The coverage matrix labels it "구직" / "Job-seeking". Displaying it under 유학·연수 is factually incorrect. |
| **Severity** | BLOCKER |
| **Manual source** | D-10 = 구직 per both manuals and visa_data.json. No manual pages needed to confirm this is wrong; the visa code name is unambiguous. |
| **Verified source status** | Confirmed incorrect classification against visa_data.json and coverage matrix. |
| **Recommended replacement** | Remove D-10 from the 유학·연수 stat card chip list. Replace with a study-appropriate code (e.g. D-3 기술연수) or leave as D-2, D-4 only. D-10 belongs in the 취업·전문직 card or the 자격 변경 pathway chip only. |
| **Source-backed?** | Yes — D-10 category is unambiguous from visa_data.json and coverage matrix. |

---

#### BLOCKER-2: Hardcoded ungrounded document lists in `selectInKoreaAction`

| Field | Value |
|-------|-------|
| **Location** | `index.html` lines 8862–8898, `selectInKoreaAction` JavaScript function |
| **Current wording — register case** | Under `register` action type: renders `<ul class="jur-list">` with "공통 필요 서류": 통합신청서, 여권 원본 및 사본, 사진 1매 (3.5×4.5cm), 체류지 입증서류, 수수료 |
| **Current wording — workplace case** | Under `workplace` action type: renders `<ul class="jur-list">` with "근무처 변경 신고 서류": 통합신청서, 여권 및 외국인등록증, 사업자등록증 사본, 근로계약서, 특례고용가능확인서 (H-2 해당자) |
| **Problem** | Both document lists are hardcoded in JS with no source attribution and no unverified disclaimer visible to the user. Coverage matrix status for both procedures is `scoped_fallback / source_needed` — no active grounding exists. The `common_foreigner_registration` and `e7_workplace_change` rows in the matrix explicitly state these cannot be machine-answered without a verified source. Presenting specific document lists in a checklist-style UI without a disclaimer implies manual verification. |
| **Severity** | BLOCKER |
| **Manual source** | `common_foreigner_registration`: `scoped_fallback / source_needed`, no candidate. `e7_workplace_change`: `scoped_fallback / source_needed`, no candidate. |
| **Verified source status** | Neither list is grounded. No page numbers cited. Auto-extracted from unverified sources per coverage matrix. |
| **Recommended replacement** | Do not show a specific document checklist for these procedures. Replace both `extra` content blocks with a cautionary redirect: "구체적인 제출서류는 체류자격과 상황에 따라 달라집니다. HiKorea 또는 관할 출입국·외국인청에서 확인하세요." Add a link to HiKorea. The `extend` and `change` cases already use `subcode-warning` boxes without document lists — use the same pattern. |
| **Source-backed?** | Cautionary redirect only. No document list without grounding. |

---

### HIGH Issues

#### HIGH-1: Source Evidence Panel shows manual badge for all unverified entries

| Field | Value |
|-------|-------|
| **Location** | `index.html` lines 7203–7219, `renderSourceEvidencePanel` function |
| **Current wording** | The panel always renders: `<span class="sep-badge visa-manual">사증발급 안내매뉴얼 2026.5</span>` and/or `<span class="sep-badge stay-manual">외국인체류 안내매뉴얼 2026.5</span>` for any visa whose domain includes `visa_issuance` or `stay_sojourn` (inferred from presence of `newReq`/`extReq` fields). This includes all 35+ visa_data.json entries. The `unverified` badge also appears simultaneously. |
| **Problem** | Displaying "외국인체류 안내매뉴얼 2026.5" as a named badge implies this specific entry's information was extracted from that manual. In reality, `getManualDomains()` assigns domains based solely on whether a `newReq` or `extReq` field is populated — not whether the manual was actually consulted. All entries have `verified: false, needsManualReview: true`. The concurrent display of both a manual badge and "출처 메타데이터 미확인" creates a contradictory signal that a user could resolve by believing the manual was used. `renderSourceReferences` (which contains the "대표 데이터이며 전체 수작업 검증 전입니다." disclaimer) is defined but **never called** in the main card render pipeline. |
| **Severity** | HIGH |
| **Manual source** | Active grounding exists only for D-2/D-4/E-7 extension per stay_manual fixture. All others: unverified. |
| **Verified source status** | No entry in visa_data.json has `verified: true`. |
| **Recommended replacement** | Option A (preferred): Separate the domain-classification badge ("사증발급" / "체류민원") from the source-verified badge. Only show "외국인체류 안내매뉴얼 2026.5 (확인됨)" when `status.verified === true`. Otherwise show only "구조화 데이터 (수작업 검증 전)" and the domain label without the specific manual name. Option B: Add the unverified note to the summary level (outside the `<details>` element) so users see it without expanding. |
| **Source-backed?** | Cautionary softening only. |

---

#### HIGH-2: "결과와 근거를 함께 확인" feature checklist item

| Field | Value |
|-------|-------|
| **Location** | `index.html` lines 5085–5086, feature checklist in `<aside class="feature-checklist">` |
| **Current wording** | `<strong>결과와 근거를 함께 확인</strong>` / `<span lang="en">Results paired with sources</span>` |
| **Problem** | Implies that search results come with verified sources. In practice, the source evidence panel shows "출처 메타데이터 미확인" for virtually all entries. The `renderSourceReferences` function (which would show detailed source status) is defined but never called in the card render pipeline. |
| **Severity** | HIGH |
| **Recommended replacement** | Soften to: `<strong>공식 출처 확인 흐름 안내</strong>` / `Results with source-checking guidance`. This conveys the same navigational value without implying verified grounding. |
| **Source-backed?** | Cautionary softening. |

---

#### HIGH-3: Logo-39 / "Paradiso 39" visual present in logo HTML

| Field | Value |
|-------|-------|
| **Location** | `index.html` line 4862, inside `<h1 class="logo-brand">` |
| **Current wording** | `<em class="logo-39 l39">39</em>` — rendered visually adjacent to "Paradiso" on the landing page, producing the visual "Paradiso 39" |
| **Problem** | Task instructions explicitly state "Do NOT reintroduce 'Paradiso 39'". The `check_repo.sh` branding regex (`Paradiso 39` with a space) does not catch this because the "39" is a separate `<em>` element. However, visually the landing page displays the brand name with "39" appended. The CSS classes `logo-39` and `l39` on the element and the `body.anagram-run .logo-brand .l39` animation selector confirm this element was intentionally styled as the "39" brand suffix. |
| **Severity** | HIGH (branding constraint violation) |
| **Recommended replacement** | Remove the `<em class="logo-39 l39">39</em>` element entirely. The `logo-39` CSS class (line 226), `l39` animation rules (lines 240, 244, 247), and related `logo-brand .l39` CSS selectors should also be removed or marked as dead code if the element is removed. |
| **Source-backed?** | Not a manual/source issue — branding constraint per task specification. |

---

### MEDIUM Issues

#### MEDIUM-1: Stat card counts (8/7/10) don't match visa_data.json categorization

| Field | Value |
|-------|-------|
| **Location** | `index.html` lines 5007–5045, `<div class="brand-hero-stats">` |
| **Current wording** | `data-count="14"` (취업·전문직), `data-count="8"` (유학·연수), `data-count="7"` (거주·결혼), `data-count="10"` (방문·기타) |
| **Problem** | Counts sum to 39, matching the "39가지" brand claim. But visa_data.json shows: work+invest = 14 ✓, study = 6 (not 8), family = 6 (not 7), short+other+diplo+etc = 15 (not 10). The counts appear to represent the official Korean immigration law categories, not Paradiso's actual data coverage. If these numbers represent official category counts, the note that explains their basis is missing. If they represent Paradiso's data, they are incorrect. |
| **Severity** | MEDIUM |
| **Recommended replacement** | Either (a) add a footnote: "대한민국 출입국관리법 기준 체류자격 분류" to clarify these are official counts, not Paradiso coverage counts; or (b) adjust the counts to match actual visa_data.json entries. The 14 employment count is correct. |
| **Source-backed?** | Requires human reviewer to verify the 8/7/10 split against the official 출입국관리법 category list. |

---

#### MEDIUM-2: "출입국관리매뉴얼" source card: "체류자격별 허가기준과 실무 확인 흐름"

| Field | Value |
|-------|-------|
| **Location** | `index.html` line 5197, `<article class="p-source-card">` in source panel |
| **Current wording** | `<h3>출입국관리매뉴얼</h3><p>체류자격별 허가기준과 실무 확인 흐름.</p>` |
| **Problem** | "체류자격별 허가기준" implies Paradiso has sourced permit criteria for each stay category from the manual. Active grounding covers only 3 (visa, procedure) pairs. The majority of visa_data.json entries were auto-extracted and are marked as needing manual review. |
| **Severity** | MEDIUM |
| **Recommended replacement** | Soften: `<p>체류자격 확인 경로와 공식 매뉴얼 참조 안내.</p>` — removes the implication of full per-category sourcing. |
| **Source-backed?** | Cautionary softening. |

---

#### MEDIUM-3: "서류 점검" how-step description

| Field | Value |
|-------|-------|
| **Location** | `index.html` lines 5172–5175, `<article class="p-how-step">` |
| **Current wording** | `<h3>서류 점검</h3><p>공통서류와 상황별 추가 확인 항목을 놓치지 않게 봅니다.</p>` |
| **Problem** | Implies comprehensive document-level coverage. Most procedures in visa_data.json have auto-extracted, unverified document lists. Only D-2/D-4/E-7 extension documents are actively grounded. |
| **Severity** | MEDIUM |
| **Recommended replacement** | `<p>자격별 구비서류 흐름을 살펴보고, 공식 출처 확인으로 이어집니다.</p>` — adds the "leads to official source confirmation" qualifier. |
| **Source-backed?** | Cautionary softening. |

---

#### MEDIUM-4: "매뉴얼 기반 탐색" footer chip

| Field | Value |
|-------|-------|
| **Location** | `index.html` line 5403, in `<div class="figma-footer-chips">` |
| **Current wording** | `<span class="footer-chip">📑 매뉴얼 기반 탐색</span>` |
| **Problem** | Without qualification, "매뉴얼 기반 탐색" implies the search is backed by the official manual for all entries. Only 3 procedures are actively grounded. |
| **Severity** | MEDIUM |
| **Recommended replacement** | Change to `<span class="footer-chip">📑 공식 출처 확인 경로</span>` — describes what the platform does (guides to official sources) rather than implying all data is manual-grounded. |
| **Source-backed?** | Cautionary softening. |

---

#### MEDIUM-5: "Data Integrity" value card wording

| Field | Value |
|-------|-------|
| **Location** | `index.html` line 5347, in `<div class="hobby-card hobby-1">` |
| **Current wording** | `<div class="hobby-desc">출입국·외국인정책본부 매뉴얼과 시행규칙을 1차 출처로 참고합니다.</div>` |
| **Problem** | "1차 출처로 참고합니다" implies all data in Paradiso uses official manuals as primary sources. In practice, 35+ visa_data.json entries are auto-extracted and flagged `needsManualReview: true`. Only 3 procedures are actively grounded. The aspirational framing may be appropriate for roadmap positioning but is misleading as a description of current data quality. |
| **Severity** | MEDIUM |
| **Recommended replacement** | `<div class="hobby-desc">출입국·외국인정책본부 매뉴얼과 시행규칙을 1차 출처로 삼으며, 검증 범위는 단계적으로 확대 중입니다.</div>` — adds the "being expanded" qualifier. |
| **Source-backed?** | Cautionary softening. |

---

### LOW Issues

#### LOW-1: "체류 절차를 더 쉽게, 더 정확하게" — footer CTA

| Field | Value |
|-------|-------|
| **Location** | `index.html` line 5422, `<h2 id="pFooterCtaTitle">` |
| **Current wording** | `체류 절차를 더 쉽게, 더 정확하게.` |
| **Problem** | "정확하게" (accurately) is a strong claim for a system where most document lists are auto-extracted and unverified. Not a legal claim, but sets expectations the system cannot fully meet. |
| **Severity** | LOW |
| **Recommended replacement** | `체류 절차 경로를 더 쉽게, 더 체계적으로.` — replaces "정확하게" with "체계적으로" (systematically). |
| **Source-backed?** | Tone adjustment only. |

---

#### LOW-2: "Korea's 39 visa categories. Unified." — brand subtitle

| Field | Value |
|-------|-------|
| **Location** | `index.html` line 4992, `<p class="brand-hero-subtitle">` |
| **Current wording** | `Korea's 39 visa categories. Unified.` |
| **Problem** | "Unified" implies a complete, integrated system. Paradiso's coverage is partial, with most procedures at scoped_fallback or unverified status. Note: the count "39" itself requires verification against the 2026-05 manuals (pdftotext unavailable). |
| **Severity** | LOW |
| **Recommended replacement** | `Korea's residence categories, organized by purpose.` — removes both the unverifiable count and the overstated "Unified". |
| **Source-backed?** | Tone/scope adjustment. The 39 count itself requires verification (see below). |

---

#### LOW-3: Footer version `v38` vs "39가지" brand claims

| Field | Value |
|-------|-------|
| **Location** | `index.html` line 5603, `<footer class="ft">` |
| **Current wording** | `Paradiso v38 · ※ 본 서비스는 베타 테스트 중이며...` |
| **Problem** | The footer says `v38` while the brand repeatedly claims "39가지" categories. This version-count inconsistency could confuse users who notice the discrepancy. Low severity since `v38` is an internal version number, not a visa category count. |
| **Severity** | LOW |
| **Recommended replacement** | No change required, or update to `v39` if the intent is to keep version tracking aligned with the 39-category brand. |
| **Source-backed?** | Internal consistency only. |

---

## 5. Known Risky Areas: Special Audit Notes

### D-10 Extension
Per `d10_candidate_attempt.md` (2026-05-15): The 2026-05 stay manual has **no dedicated D-10 체류기간 연장허가 제출서류 section**. Sections present cover: status change TO D-10 (pp.144-155), part-time work permit, alien registration, training notifications. Both D-10 and D-10-1 rows in the coverage matrix are `scoped_fallback / source_needed`. The index.html does not make specific D-10 extension document claims in static HTML (the source evidence panel is dynamic), but BLOCKER-2 covers the generic `extend` pathway which would apply to D-10 extension searches.

### F-6 Divorce
F-6 has three coverage rows: `candidate_only` (F-6 general, F-6-3), `scoped_fallback / source_needed` (F-6-1), and `clarification_needed / source_needed` (F-6-2). No active grounding. Index.html references F-6 in stat cards and pathway cards without procedure-specific claims, which is acceptable. The pathway card text ("결혼이민, 동반 가족, 자녀와 가족 체류 확인") is appropriately general.

### D-2/D-4/E-7 Extension
Active grounding exists for these three. However, `visa_data.json` entries for all three still have `verified: false, needsManualReview: true` — meaning the grounding badge "2026.5 매뉴얼 확인됨" will NEVER render for these either (it requires `verified: true` in visa_data.json). The grounding lives in the AI backend fixture only. Index.html users searching D-2/D-4/E-7 will see "2026.5 매뉴얼 확인 필요" badges on the card, which is conservative but inconsistent with the actual grounding state.

### F-2/F-5/E-7 Workplace Change
Coverage matrix confirms: F-2 extension = `scoped_fallback`, F-5 card renewal = `scoped_fallback`, E-7 workplace change = `scoped_fallback`. Index.html pathway cards reference these statuses but only at a general "경로 확인" level, which is acceptable. The specific workplace-change document list in BLOCKER-2 is the higher-risk issue.

### "39가지" Count Verification
The number 39 cannot be verified against the 2026-05 manuals in this pass (pdftotext unavailable). The official Korean immigration law may list a different number of 체류자격 in the 2026.5 edition. This requires a human reviewer with PDF access to confirm. If the number is wrong, all occurrences of "39" in the brand must be updated.

---

## 6. Required Corrections for Implementation PR

Priority order for the follow-up PR:

1. **BLOCKER-1**: Remove D-10 chip from the 유학·연수 stat card (line ~5023).
2. **BLOCKER-2**: Replace hardcoded document lists in `selectInKoreaAction` `register` and `workplace` cases with cautionary redirect text + HiKorea link. No document checklist without grounding.
3. **HIGH-1**: Decouple the "외국인체류 안내매뉴얼 2026.5" / "사증발급 안내매뉴얼 2026.5" source badge from the domain-inference logic. Do not show the named-manual badge when `verified: false`. Show domain label only.
4. **HIGH-2**: Soften "결과와 근거를 함께 확인" to "공식 출처 확인 흐름 안내".
5. **HIGH-3**: Remove `<em class="logo-39 l39">39</em>` from logo HTML and remove associated CSS (`logo-39`, `l39`, related rules).
6. **MEDIUM-2 through MEDIUM-5**: Apply softened wording to the four medium-severity items.
7. **LOW-1 through LOW-3**: Apply tone adjustments.

---

## 7. Statements That Should Be Removed Entirely

- `<em class="logo-39 l39">39</em>` (HIGH-3) — entire element
- The `register` action `extra` content block containing the hardcoded document `<ul>` (BLOCKER-2)
- The `workplace` action `extra` content block containing the hardcoded document `<ul>` (BLOCKER-2)

---

## 8. Statements That Can Remain with Softened Wording

All items in MEDIUM-1 through LOW-3 can remain with the recommended wording edits. No removal needed.

The following static claims are acceptable as-is (appropriately hedged):
- Line 4876: "공식 자료로 이어지는 확인 경로를 정리합니다." ✓
- Line 4879-4881: `p-proof-chip` badges: "공개 자료 기반", "목적별 경로 정리", "최종 확인은 공식 출처" ✓
- Line 4949: disclaimer "본 서비스는 공개 법령·매뉴얼 기반 참고용 정보 제공 도구이며, 법적 상담이나 민원 대행이 아닙니다." ✓
- Line 5063-5064: feature body "구조화된 체류자격 데이터를 토대로 공식 자료 확인을 전제로 한 정보 탐색을 보조합니다. 최종 판단과 신청 절차는 관할 출입국·외국인관서 안내 확인이 필요합니다." ✓
- Line 5192: "최종 판단은 관할 출입국·외국인관서, HiKorea, 1345 또는 자격 있는 전문가에게 확인해야 합니다." ✓
- Line 5202: "Paradiso는 법률 자문이나 민원 대행을 제공하지 않으며, 이에 따른 어떠한 법적 책임도 지지 않습니다." ✓
- Line 5603: footer beta disclaimer ✓
- `extend` and `change` action cases in `selectInKoreaAction`: use `subcode-warning` boxes without document lists — acceptable pattern ✓
- `renderCautionBlock()` / `cautionText`: "심사 과정에서 제출서류는 가감될 수 있으며, 최종 허가 여부는 관할 출입국·외국인청의 심사에 따릅니다." ✓

---

## 9. Areas Needing Future Source Verification

- **D-10 extension documents**: Per `d10_candidate_attempt.md`, no source page found in stay_manual_2026_05.pdf. Needs human reviewer with PDF access.
- **"39가지" count**: Cannot verify 39 is the correct 2026-05 count without PDF access. Flag for human verification.
- **외국인등록 common document list**: Basis for `통합신청서, 여권 원본 및 사본, 사진 1매, 체류지 입증서류, 수수료` is not grounded. Need stay_manual source page.
- **근무처 변경 document list**: Basis for the 5-item list in `workplace` action is not grounded. Coverage matrix: `scoped_fallback / source_needed`.
- **F-6-1, F-6-2, F-1-6**: Coverage matrix identifies source pages (pp.495-499) but no candidates created yet. Do not add procedure-level content to index.html for these.
- **D-4 sub-codes other than D-4-1 and D-4-7**: Grounding covers only language trainees. D-4-2K, D-4-3, D-4-5, D-4-6 are not grounded.
- **E-7-4 숙련기능인력**: Grounding covers general E-7 extension only; E-7-4 is explicitly excluded.

---

## 10. Manual Test Checklist (for Implementation PR)

After applying corrections, verify:

- [ ] D-10 chip is absent from 유학·연수 stat card; D-2 and D-4 remain
- [ ] `selectInKoreaAction('register')` shows no document checklist, only cautionary redirect text
- [ ] `selectInKoreaAction('workplace')` shows no document checklist, only cautionary redirect text
- [ ] Source evidence panel for D-2/D-4/E-7 search results does NOT show "외국인체류 안내매뉴얼 2026.5 (확인됨)" — only domain label and unverified note
- [ ] Logo area does not show "39" adjacent to "Paradiso" in the landing state
- [ ] Feature checklist item reads "공식 출처 확인 흐름 안내" (or equivalent), not "결과와 근거를 함께 확인"
- [ ] Footer CTA reads "더 체계적으로" not "더 정확하게"
- [ ] "출입국관리매뉴얼" source card reads softened description
- [ ] Data Integrity hobby card includes "단계적으로 확대 중" qualifier
- [ ] `bash scripts/check_repo.sh` steps [1–10] pass (steps [11–13] may fail due to environment; acceptable)
- [ ] `git diff --check` on index.html passes (check_repo.sh step [8])
- [ ] No new branding strings `Paradiso 39` / `Paradiso39` introduced (check_repo.sh step [10])
- [ ] AI modal, jurisdiction modal, and job code modal behavior unchanged
- [ ] Search results still render for D-2, E-7, F-6 queries
- [ ] `extend` and `change` action types in `selectInKoreaAction` still show their `subcode-warning` boxes (these are acceptable and should not be changed)

---

## 11. Codex Implementation Prompt

```
TASK: Apply wording corrections to index.html only.

CONTEXT:
- Branch: audit/index-manual-consistency
- Source doc: docs/INDEX_MANUAL_CONSISTENCY_AUDIT.md
- This is a copy/wording-only pass. Do NOT change JavaScript logic, event
  handlers, CSS structure, modal behavior, or data loading.
- Do NOT add new claims. Do NOT cite manual page numbers in new text.
- Do NOT touch ai.html, visa_data.json, or backend files.
- Do NOT reintroduce "Paradiso 39" branding.

REQUIRED CHANGES in index.html:

1. [BLOCKER-1] Remove D-10 from 유학·연수 stat card chip list (~line 5023):
   Delete: <span class="stat-code-chip">D-10</span>
   (Keep D-2 and D-4 chips. Adjust data-count from 8 to 6, or verify correct
   count with a human reviewer before setting a different number.)

2. [BLOCKER-2] In function selectInKoreaAction (~lines 8862–8898):
   For the 'register' case: replace the entire <div class="jur-section">…</div>
   block in `extra` with:
   <div class="subcode-warning" style="margin-top:0.8rem;">
     ⚠️ <strong>주의:</strong> 외국인등록 제출서류는 체류자격에 따라 다릅니다.
     <a href="https://www.hikorea.go.kr" target="_blank" rel="noopener noreferrer">
     HiKorea</a> 또는 관할 출입국·외국인청에서 확인하세요.
   </div>

   For the 'workplace' case: replace the entire <div class="jur-section">…</div>
   block in `extra` with:
   <div class="subcode-warning" style="margin-top:0.8rem;">
     ⚠️ <strong>주의:</strong> 근무처 변경·추가 서류는 체류자격에 따라 다릅니다.
     <a href="https://www.hikorea.go.kr" target="_blank" rel="noopener noreferrer">
     HiKorea</a> 또는 관할 출입국·외국인청에서 확인하세요.
   </div>

3. [HIGH-1] In function renderSourceEvidencePanel (~lines 7203–7219):
   Change the badge rendering logic so that the named-manual badges
   ("사증발급 안내매뉴얼 2026.5", "외국인체류 안내매뉴얼 2026.5") only appear
   when isVerified is true. When !isVerified, show only the domain-type label
   ("사증발급" or "체류민원" from renderDomainBadges) without the version string.
   The 'unverified' badge and note should remain when !isVerified.

4. [HIGH-2] Change feature checklist item (~line 5085):
   From: <strong>결과와 근거를 함께 확인</strong>
   To:   <strong>공식 출처 확인 흐름 안내</strong>
   From: <span lang="en">Results paired with sources</span>
   To:   <span lang="en">Guidance to official sources</span>

5. [HIGH-3] Remove logo-39 element (~line 4862):
   Delete: <em class="logo-39 l39">39</em>
   Also remove or comment out related CSS rules for .logo-39 and .l39
   (body.anagram-run .logo-brand .l39, body.launching .logo-brand .l39,
   body.searched .logo-brand .l39, .logo-brand .l39, and .logo-brand .logo-39).

6. [MEDIUM-2] Change "출입국관리매뉴얼" source card (~line 5197):
   From: <p>체류자격별 허가기준과 실무 확인 흐름.</p>
   To:   <p>체류자격 확인 경로와 공식 매뉴얼 참조 안내.</p>

7. [MEDIUM-3] Change "서류 점검" how-step description (~line 5174):
   From: <p>공통서류와 상황별 추가 확인 항목을 놓치지 않게 봅니다.</p>
   To:   <p>자격별 구비서류 흐름을 살펴보고, 공식 출처 확인으로 이어집니다.</p>

8. [MEDIUM-4] Change footer chip (~line 5403):
   From: <span class="footer-chip">📑 매뉴얼 기반 탐색</span>
   To:   <span class="footer-chip">📑 공식 출처 확인 경로</span>

9. [MEDIUM-5] Change Data Integrity hobby card (~line 5347):
   From: <div class="hobby-desc">출입국·외국인정책본부 매뉴얼과 시행규칙을 1차 출처로 참고합니다.</div>
   To:   <div class="hobby-desc">출입국·외국인정책본부 매뉴얼과 시행규칙을 1차 출처로 삼으며, 검증 범위는 단계적으로 확대 중입니다.</div>

10. [LOW-1] Change footer CTA (~line 5422):
    From: <h2 id="pFooterCtaTitle">체류 절차를 더 쉽게, 더 정확하게.</h2>
    To:   <h2 id="pFooterCtaTitle">체류 절차 경로를 더 쉽게, 더 체계적으로.</h2>

11. [LOW-2] Change brand hero subtitle (~line 4992):
    From: Korea's 39 visa categories. Unified.
    To:   Korea's residence categories, organized by purpose.

VALIDATION:
After edits, run: bash scripts/check_repo.sh
Steps [1]–[10] must pass.
Steps [11]–[13] may fail due to missing fastapi (environment issue, not regression).
git diff --check on index.html must pass.
Do not commit until the checklist in docs/INDEX_MANUAL_CONSISTENCY_AUDIT.md
Section 10 has been verified.
```

---

*End of audit document. Produced as audit-only pass on branch `audit/index-manual-consistency`. No changes to index.html in this PR.*
