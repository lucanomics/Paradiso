# F-1 and Family/Status-Related Residence Status Audit

## 1) Scope

This audit is a **documentation-only** assessment of document/scenario coverage gaps for:
- F-1
- F-2
- F-3
- F-5
- F-6
- G-1 (where relevant to F-series transitions)

The goal is to distinguish:
- rendering-layer issues,
- data/manual-grounding coverage issues,
- scenario/subcode routing issues.

No document list is added or inferred in this audit.

---

## 2) Source hierarchy

For claims in this audit, use sources in this order:

1. **Committed structured data** (`visa_data.json`, `backend/data/visas.json`) for current display payload shape.
2. **Coverage policy metadata** (`backend/data/eval/paradiso_coverage_matrix.json`) for active/non-active grounding posture and caution notes.
3. **Active stay grounding fixture** (`backend/data/manual_grounding/stay_manual_grounding_2026_05.json`) for what is currently promoted.
4. **Draft candidates** (`backend/data/manual_grounding/candidates/`) for in-progress scenario work (non-runtime).
5. **Manual PDFs**:
   - `docs/source-manuals/2026-05/stay_manual_2026_05.pdf` for domestic stay procedures.
   - `docs/source-manuals/2026-05/visa_manual_2026_05.pdf` for visa issuance procedures.

### Non-mixing rule

- Do **not** use visa issuance manual to justify domestic stay-procedure statements.
- Do **not** use domestic stay manual to justify visa issuance claims.

---

## 3) F-1 current display behavior

Current F-1 record has both legacy and procedure-structured document-related fields populated, including `newReqDocs`, `extReqDocs`, `initialReqDocs`, `extensionReqDocs`, `changeReqDocs`, and `procedures`. `sourceManualStatus.verified` is `false` with `needsManualReview: true`. This means the UI can render structured document groups, but source verification remains pending/manual-review state. 

F-1 currently includes `procedures.extension` and `procedures.registration`; extension is marked available, while registration is marked unavailable (`available: false`) even though a `requiredDocs` structure exists.

---

## 4) F-1 data fields present/missing

## Present (data side)
- Top-level doc-related fields exist (legacy aliases included).
- `procedures` object exists.
- Procedure-level `requiredDocs` structures are present.
- `manualRefs` and `sourceManualStatus` metadata exist.

## Missing / not complete (verification side)
- `sourceManualStatus.verified` is not true.
- Review notes explicitly state manual page-level comparison is still required.

Interpretation: this is **not a pure “no-data” state**; it is a **partially structured + pending verification** state.

---

## 5) F-1 procedure/scenario complexity

F-1 has multiple subcodes in data and, per existing repo notes, is connected to family-status transitions where scenario details matter (e.g., family breakdown / domestic cleanup pathways). Treating F-1 as one flat document list risks over/under-inclusion.

Conservative conclusion:
- F-1 issues are likely not solved by adding one new static list.
- Correctness depends on subcode/scenario-aware routing and verified manual mapping.

---

## 6) Related statuses

## F-2
- Data has similar legacy + procedure structures and review-pending metadata.
- Coverage matrix notes that F-2 has many materially different subcodes and should not be answered as a single undifferentiated bucket.

## F-3
- Data fields exist, but coverage matrix has no dedicated row in the current matrix file.
- High risk of scenario variance by principal status linkage.

## F-5
- Data fields exist.
- Coverage matrix explicitly warns that “extension” framing may be wrong for F-5 and card-renewal framing differs.

## F-6
- Data fields are richer than peer F-codes and include many procedure keys.
- Coverage matrix contains multiple cautionary rows for F-6 scenario splits.
- Candidate folder contains a draft F-6-3 divorce/breakdown candidate, but candidates are non-runtime until promoted.

## G-1 (relevance)
- G-1 appears in matrix notes as a relevant transition context in family-breakdown pathways.
- Active stay grounding fixture currently has no F/G family entries promoted.

---

## 7) Which gaps are rendering bugs

Potential rendering-bug class (frontend-side symptoms):
1. A status has recognized doc fields but UI renders neither checklist nor explicit fallback state.
2. A procedure marked unavailable but containing structured docs is handled inconsistently in procedure tab/panel selection.
3. Recognized alias fields are present but not surfaced due to mapping drift.

Given current data shape for F-1/F-2/F-3/F-5/F-6/G-1, complete absence of rendered output is more likely a **renderer-selection/availability-path issue** than missing raw fields.

---

## 8) Which gaps are data/manual grounding gaps

Data/manual-grounding gaps:
1. `sourceManualStatus.verified` remains false for audited statuses.
2. Active stay grounding fixture does not include audited F-series/G-1 entries.
3. Coverage matrix flags scenario risks (especially F-2, F-5, F-6) that are not resolved by generic lists.
4. Only a draft F-6 candidate exists in `candidates/`; no promoted family-status grounding entry is active.

These are not fixable by frontend-only tweaks.

---

## 9) Which gaps require scenario/subcode routing

Routing-required gaps:
1. **F-2**: many subcodes with materially different requirements.
2. **F-6**: scenario split (e.g., divorce/litigation/child-custody/death/disappearance pathways) requires branch-specific handling.
3. **F-5**: “extension” vs card-renewal procedural framing mismatch.
4. **F-1**: family-status adjacent pathways likely need scenario context, not one static response.
5. **F-3**: dependency on principal-holder context likely requires scenario-aware prompts.

---

## 10) Recommended next PRs

1. **Renderer observability PR (non-content):**
   - Add deterministic snapshot/log checks for per-procedure availability vs requiredDocs presence.
   - Confirm that when a procedure is unavailable, user still receives clear fallback text.

2. **Family-status matrix enrichment PR (metadata only):**
   - Add missing F-3/G-1 row coverage notes to coverage matrix with conservative caution language.

3. **Grounding candidate expansion PR (draft-only):**
   - Add scoped draft candidates for high-risk family scenarios (without activating).
   - Keep strict human-review gates.

4. **Subcode/scenario routing design PR:**
   - Define deterministic selector behavior before promoting any F-family grounding entries.

---

## 11) Do-not-fix-by-inventing list

Do **not** do the following in a quick fix:
- Do not add inferred F-1/F-2/F-3/F-5/F-6/G-1 document lists without verified source mapping.
- Do not collapse F-2 or F-6 into one generic checklist.
- Do not claim “officially verified” for rows still marked `needsManualReview`.
- Do not treat draft candidate content as active runtime grounding.
- Do not mix domestic stay manual claims with visa issuance manual claims.

---

## 12) Candidate grounding priorities

Priority order (for draft-candidate work, not immediate activation):
1. **F-6 scenario-split candidates** (highest risk / highest user impact).
2. **F-2 subcode-bucket candidates** (avoid one-size-fits-all errors).
3. **F-5 framing candidate(s)** for permanent-residence card lifecycle vs extension wording.
4. **F-1 targeted scenarios** that commonly co-occur with family breakdown/transition contexts.
5. **F-3 dependency scenarios** tied to principal-holder status changes.
6. **G-1 transition scenarios** where matrix notes already indicate relevance.

Promotion should remain blocked until:
- source pages are verified,
- scenario routing is explicit,
- human review is approved.
