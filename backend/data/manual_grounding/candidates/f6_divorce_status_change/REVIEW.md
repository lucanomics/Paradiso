# REVIEW — F-6 divorce / marriage-breakdown status change

> **Candidate status:** `draft`. **Not active grounding.** Nothing in this
> folder is read by `/api/ask`. Human domain-expert sign-off required
> before any consideration of promotion. The `human_review.decision`
> field in `candidate.json` is `"pending"`.

## 1. Source search method

- Tool: `poppler-utils` (`pdftotext -layout` and
  `pdftotext -layout -f N -l N`), installed locally for this session.
- Source files inspected (both committed under `docs/source-manuals/2026-05/`):
  - `stay_manual_2026_05.pdf` — 외국인체류 안내매뉴얼, 법무부 출입국·외국인정책본부, 2026.5, 774 PDF pages.
  - `visa_manual_2026_05.pdf` — 사증발급 안내매뉴얼, same issuing body, same date (not used for this candidate's `source_file`, but spot-checked for cross-references).
- The full stay manual was extracted to `/tmp/stay_manual_2026_05.txt`
  (33,245 lines). Search was performed with `grep -n` against literal
  Korean strings. PDF pages were then re-confirmed via
  `pdftotext -layout -f PAGE -l PAGE` and matched against the printed
  page-footer markers (e.g. `- 498 -`) inside the extracted text.
- No external web requests were made. `law.go.kr`, HiKorea, and the
  Ministry of Justice notice pages were **not** accessed.

## 2. Exact pages checked

| Page  | Content                                                                                                                                                       |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 478   | 결혼이민(F-6) 자격 해당자/활동범위 및 F-6-1 / F-6-2 / F-6-3 세부약호 정의                                                                                          |
| 494   | F-6-1 — 최초 체류기간 연장허가, 일반 체류기간 연장허가                                                                                                              |
| 495   | F-6-1 — 별거·이혼소송·배우자 실종의 경우 체류기간 연장허가, 공통/별거/이혼/실종 시 제출서류                                                                              |
| 496   | F-6-2 — 최초/일반 체류기간 연장허가, 면접교섭권을 가진 경우의 체류허가 특칙                                                                                            |
| 497   | F-6-3 — 가. 배우자 사망 후 최초 체류기간 연장허가; 나. 배우자 실종 후 최초 체류기간 연장허가 (제출서류 포함)                                                            |
| 498   | F-6-3 — 다. 국민 배우자와 이혼한 후 최초 체류기간 연장허가, 귀책사유 입증자료, 제출서류, 외국인 귀책사유 시 특칙                                                          |
| 499   | F-6-3 — 라. 최초 기간연장 후 혼인단절 자격으로 체류 중인 외국인에 대한 연장; **F-1-6 가사정리 체류기간 연장허가** (매회 6개월, 자격변경일로부터 1년, 이후 G-1 전환 규정) |
| 500–501 | F-6-1 / F-6-2 / F-6-3 외국인등록 절차                                                                                                                          |
| 34    | (cross-reference) 외국인등록사항 변경신고 일반 규정 (성명/성별/생년월일/국적·여권번호·발급일자·유효기간, 소속기관/단체 변경) — 15일 이내 신고                            |

`candidate.json`'s `page_range` is set to `"498"` — the single page that
contains the primary 제출서류 list this candidate exposes. Adjacent
F-6 procedures are cited in `caveats` / `risk_notes` with their
specific page numbers but are **not** rolled into the document list,
because they are scenario-different lists that must not silently bleed
through if a future selector ever inherits this entry.

## 3. Claims verified against committed source

These claims appear verbatim or in near-verbatim source text on the
cited pages:

1. **F-6-1 / F-6-2 / F-6-3 sub-code definitions** — p.478 카테고리표.
2. **F-6-1 별거·이혼소송 진행 중·배우자 실종(가정법원 실종선고 전)의 경우 별도의 체류기간 연장 절차가 존재** — p.495. The manual lists separate evidence bundles for each of 별거 / 이혼 / 실종.
3. **F-6-3 다. 국민 배우자와 이혼한 후 최초 체류기간 연장허가** — p.498:
   - 체류허가 대상: F-6-1 자격으로 정상적 혼인생활 중 자신에게 책임 없는 사유(국민의 가출·폭력 등)로 이혼한 사람.
   - 8-item 제출서류 list copied verbatim.
   - 귀책사유 입증자료의 구체 예시 (가출신고서, 진단서, 검찰 불기소결정문, 공인된 여성단체 확인서, 4촌 이내 친척 확인서, 통(반장) 확인서 등).
4. **F-6-2 면접교섭권 특칙** — p.496. 1년 범위 내 F-6-2 자격으로 체류 가능.
5. **F-1-6 가사정리 체류기간** — p.499. 매회 6개월 범위 내, 자격변경일로부터 1년까지. 1년 이후 채권·채무·부동산임대차 보증금 반환 등 소송 계속 시 G-1으로 전환.

## 4. Claims NOT verified (must NOT be asserted by Paradiso as fact)

These are the Gemini-suggested claims the audit explicitly told us to
verify before use. After source inspection, the following remain
**unverified** and are marked as such in `risk_notes`:

1. **"F-6-1 비자는 이혼과 동시에 즉시 취소되지 않으며, 현재 외국인등록증(ARC) 유효기간 만료일까지 자동으로 유지된다."**
   - Not directly stated in the stay manual. The manual instead
     describes separate procedures (p.495 F-6-1 별거·이혼소송 연장,
     p.498 F-6-3 이혼 후 연장) that **require re-application** with
     appropriate evidence. The statement "유효기간까지 자동 유지" is a
     reasonable plain-language summary but cannot be cited as an
     official rule from this PDF alone.
   - Verification path before any future promotion: check
     출입국관리법 제24조(체류자격 변경허가) / 제25조(체류기간 연장허가)
     / 시행령 별표 1의 2 footnotes via `law.go.kr` and any
     HiKorea/MOJ 결혼이민자 가이드 안내문.

2. **"이혼은 출입국관리법 제35조에 따라 사유 발생일로부터 15일 이내에 신고하여야 한다."**
   - Not directly stated in the stay manual. The 15-day rule (출입국관리법
     제35조 / 시행규칙 제49조의2) applies to **외국인등록사항 변경신고**,
     and the enumerated 신고대상 in the stay manual (p.34 etc.) is:
     성명, 성별, 생년월일 및 국적, 여권의 번호·발급일자·유효기간, and
     소속기관/단체 변경 — marriage status itself is **not** in that
     enumerated list.
   - Verification path before any future promotion: read 출입국관리법
     제35조 and 시행규칙 제49조의2 verbatim via `law.go.kr`; check
     HiKorea notice index for any clause that specifies marriage-status
     reporting timing.

3. **"F-1-6 비자는 일반적으로 6개월에서 1년이다."**
   - Manual p.499 specifies "매회 6개월 범위 내, 자격변경일로부터
     1년까지". The Gemini "6개월에서 1년" is consistent but should be
     stated with the exact manual wording, not paraphrased.

4. **"이민청은 반드시 변경을 허가한다 / 자동 grace period가 적용된다."**
   - Not stated. The manual lists 심사기준 (혼인단절 전 정상적인 혼인
     생활 유지 여부, 국내 체류의 불가피성, etc.). Outcomes are not
     guaranteed.

## 5. Why this candidate is **candidate-only** (not active grounding)

- `procedure_type` is `"marriage_divorce_status_change"`, which does
  **not** match the production filter `procedure_type == "체류기간 연장허가"`
  in `_select_grounding()` (backend/paradiso_backend.py:713). Even if
  someone accidentally moved this entry into the active fixture, the
  selector would not return it.
- `visa_code: "F-6"` is **not** in `_GROUNDED_VISA_CODES = ("D-2", "D-4", "E-7")`
  (backend/paradiso_backend.py:613). A second independent safety gate.
- Divorce-related status questions are **scenario-multiplexed**: 사망
  vs. 실종 vs. 이혼(귀책) vs. 별거·소송중 vs. 자녀양육 vs.
  비-F-6-3(가사정리). A single grounding entry cannot safely answer
  all of them. Production routing for these will need a sub-scenario
  selector that does not exist yet.
- Legal/administrative claims about reporting timing and
  automatic-vs-re-application semantics require external source
  verification (law.go.kr / HiKorea) that this PR explicitly did not
  perform.

## 6. What a human reviewer must check before promotion

Before considering promotion of this candidate into the active fixture
(`stay_manual_grounding_2026_05.json`):

1. **Scope decision.** Decide whether to:
   - keep a single high-level "marriage_divorce_status_change" entry
     that returns scenario-routing guidance plus the F-6-3 이혼-후
     document list as one example, or
   - split into per-scenario entries
     (`F-6-1 별거`, `F-6-1 이혼소송 진행`, `F-6-1 배우자 실종`,
     `F-6-3 배우자 사망 후`, `F-6-3 배우자 실종 후`, `F-6-3 이혼 후`,
     `F-6-2 자녀양육`, `F-6-2 면접교섭 특칙`, `F-1-6 가사정리`)
     with `visa_sub_code` and `scenario` populated per entry.
   The architecture in
   `docs/paradiso_ai_safe_automation_architecture.md` §14 PR D
   (subcode-aware selector hardening) is the relevant place to add
   the scenario routing.
2. **Procedure-type consistency.** If the candidate is promoted, the
   reviewer must decide whether to (a) keep
   `procedure_type: "marriage_divorce_status_change"` and extend
   `_select_grounding()` accordingly, or (b) split the candidate so
   each promoted entry uses `procedure_type: "체류기간 연장허가"` and
   relies on `scenario` to distinguish divorce-related extensions from
   ordinary F-6 extensions.
3. **Legal verification.** Confirm the two `claim_to_verify` items in
   `risk_notes` (current-stay-validity-until-ARC-expiration; 15-day
   reporting under Article 35) against:
   - 출입국관리법 (law.go.kr) — articles 24, 25, 35;
   - 출입국관리법 시행령 별표 1의 2;
   - 출입국관리법 시행규칙 제49조의2;
   - HiKorea 외국인종합안내센터 (1345) 결혼이민 안내, when accessible.
4. **Cross-scenario document checklist review.** The 제출서류 list in
   this candidate is the **F-6-3 이혼-후-최초** list (p.498). It
   differs from F-6-1 별거 / 이혼소송 / 실종 (p.495), F-6-3 사망 후
   (p.497), F-6-3 실종 후 (p.498 top), F-6-2 (p.496), and F-1-6 (p.499).
   Promotion must either restrict the candidate to one verified
   scenario or expand it into multiple entries.
5. **No fabricated grace periods.** Any "체류기간 만료 시 N일 이내
   신청" or "자동 grace period" wording in a promoted entry must be
   directly verified against the manual or the law text. The current
   candidate does not include such wording.

## 7. External-source accessibility note

- `law.go.kr` was **not** accessed for this candidate (the audit and
  fallback-quality PRs explicitly prohibit law-API retrieval reachable
  from `/api/ask`; the current PR also avoids ad-hoc scraping).
- HiKorea was **not** accessed.
- The only source consulted was the committed `stay_manual_2026_05.pdf`.
- Visa-issuance manual (`visa_manual_2026_05.pdf`) was spot-checked
  for cross-references but is not the `source_file` of this candidate.

## 8. Non-committed external sources used

**None.** No web searches, no third-party scraping, no LLM-generated
content was used to populate `required_documents`, `source_excerpt`,
or `verification_note`. Every Korean string in `candidate.json` is
either:

- copied verbatim from `stay_manual_2026_05.pdf` p.478 / p.494–499 /
  p.34 cross-reference, or
- written by the candidate author as a meta-description of the source
  (in `caveats`, `risk_notes`, `verification_note`).

The Gemini answer that motivated this work was used as a **quality
benchmark only**, never as a source. Its specific claims are explicitly
re-classified in §3 / §4 above as `verified_claim` / `claim_to_verify` /
`unsupported_claim_not_to_use`.

## 9. Promotion gate

`scripts/promote_grounding_candidate.py` will refuse to promote this
candidate because `candidate_status` is `"draft"` and
`human_review.decision` is `"pending"`. Both gates must change (and
the reviewer fields populated) before any apply path can execute. Even
then, this PR's policy is that the active fixture is changed only via
a separately-reviewed human-authored PR.
