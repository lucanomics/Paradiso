# Paradiso AI — fallback answer quality implementation brief

> **Status:** design + implementation brief. No production behavior is
> changed by merging this document. The follow-up PR(s) described here
> tighten the ungrounded `/api/ask` path; this file does not implement
> them.
>
> Read first:
> - `docs/paradiso_ai_safe_automation_architecture.md` — §12 ("PR C —
>   Fallback Korea-immigration guardrail") frames what this brief
>   specifies in detail.
> - `docs/manual_grounding_expansion_plan.md` — schema 1.2 and the
>   deferred F-6 / D-10 sub-code entries that must remain out of scope
>   for this PR.

## 0. Hard rules for the implementation pass

The implementer (Codex or human) **must NOT**:

1. Add, edit, remove, or reorder any entry in
   `backend/data/manual_grounding/stay_manual_grounding_2026_05.json`.
   The fallback-quality work is strictly about the *ungrounded* path.
2. Fabricate F-6 sub-code requirements, document checklists, grace
   periods, or "automatic revocation" claims. F-6-1 / F-6-2 / F-6-3
   pathways may be **named** as "possible paths the user must verify
   with the 출입국·외국인청 / 1345 / HiKorea", never as guaranteed
   options.
3. Implement full RAG, embeddings, vector search, or any live law-API
   retrieval reachable from `/api/ask`.
4. Touch `index.html`, `ai.html`, `visa_data.json`, or
   `backend/data/visas.json`.
5. Modify the registered-agent finder UX.
6. Persist raw prompts or session text server-side.
7. Push directly to `main` or auto-merge any PR.

If a step below appears to require violating one of these rules, **stop
and ask** in the PR description.

## 1. Audit findings (current ungrounded behavior)

These observations come from reading `backend/paradiso_backend.py`,
`backend/tests/test_paradiso_backend.py`, and the schema 1.2 grounding
fixture. They describe the system as it ships today and motivate every
change proposed in §3–§7 below.

### 1.1 How `/api/ask` builds prompts when no grounding is selected

`paradiso_backend.py:904` — `ask()` resolves the raw prompt, runs
detection, calls `_select_grounding(...)`, and:

- If `grounding is not None` → `final_prompt =
  _build_grounded_prompt(prompt, grounding, bundle, lang=req.lang)`.
  This template (defined at `paradiso_backend.py:769`) explicitly
  constrains the model to Korea-only scope, forbids cross-status
  document bleed-through, and pins source attribution.
- If `grounding is None` → **`final_prompt = prompt`** (line 924). The
  user's raw question is sent to the LLM with no system instruction,
  no Korea-immigration scoping, no source-availability caveat, and no
  forbidden-token list.

That single line is the root cause of the F-6-1 divorce failure mode.
There is no fallback system prompt at all today.

### 1.2 Whether ungrounded answers have a Korea-immigration-only
       instruction

No. The grounded path injects a Korean system instruction
("당신은 대한민국 출입국·외국인정책본부의 공식 매뉴얼을 근거로
답하는 한국 비자 안내 도우미입니다 … 다른 나라의 이민 절차나 일반적인
글로벌 이민 안내로 확장하지 마십시오"). The ungrounded path injects
nothing. The LLM is free to answer in USCIS / Home Office /
"contact your embassy or consulate" / generic college-counseling tone,
which is exactly what the observed Gemini-style F-6-1 answer
demonstrated.

### 1.3 How `task_type` is detected

`_detect_task_type(text)` at `paradiso_backend.py:668` returns
`"extension"` when any of these strings appears in the user prompt:

- Korean: `체류기간 연장`, `체류 연장`, `비자 연장`, `연장 신청`,
  `연장허가`, `연장`.
- English (word-boundary): `extend`, `extension`, `renew`, `renewal`.

Otherwise it returns `None`. **Only the extension task is recognized.**
The F-6-1 divorce query — "Will my visa be revoked immediately if an
American who is staying on an F-6-1 visa divorces?" — contains none of
those tokens, so `task_type_detected` is `None`. That is technically
correct (no false-positive extension), but it leaves the ungrounded
branch with no task-type signal to drive a stricter fallback prompt.

### 1.4 How visa-code / sub-code detection works for F-6-1

`_detect_visa_codes(payload_code, visa_data, text)` at
`paradiso_backend.py:627`:

1. If the payload's `visa_code` or `visa_data.code` is set, it is
   normalized via `_normalize_visa_code` and split via
   `_split_visa_code`. `"F-6-1"`, `"f61"`, `"F6-1"`, etc. all resolve
   to `("F-6", "F-6-1")` (covered by
   `SubCodeNormalizationTests.test_normalize_sub_codes_with_and_without_separators`).
2. **Text detection is bounded to a hard-coded list:**
   `for letter, digit in (("D", "2"), ("D", "4"), ("E", "7"))` at line
   661. Even though `_GROUNDED_VISA_CODES = ("D-2", "D-4", "E-7")`
   matches this list, the regex literally does not look for `F-6`,
   `F-6-1`, `D-10`, etc. in free text.

**Consequence for the F-6-1 divorce query:** if the frontend sends
`visa_code: "F-6-1"` in the payload, `visa_code_detected` is `"F-6"`
and `visa_sub_code_detected` is `"F-6-1"`. If the frontend sends only
`question`, both fields are `None`. A fallback policy that wants to
behave well in either case must not assume detection has fired.

### 1.5 Whether F-6-1 is detected from payload only or also from text

Payload-only. Free-text mentions of `F-6`, `F-6-1`, `F-6-2`, `F-6-3`
are **never** parsed. Tests
`AskEndpointSubCodeRoutingTests.test_f6_1_payload_returns_no_grounding`
and `test_f61_contiguous_payload_normalizes_and_returns_no_grounding`
exercise the payload path and confirm `grounding_used == False`. No
test covers the text-only path because the regex does not match.

### 1.6 Whether the fallback prompt prevents generic global / college
       / life advice

It does not. There is no fallback prompt. The raw user prompt goes
straight to the LLM. The only existing forbidden-token assertions
(`USCIS`, `Home Office`, `embassy`, `consulate`, `해당 국가`,
`본인이 체류 중인 국가`) live in *grounded-path* unit tests
(`GroundingHelperTests`, `ExpandedGroundingFixtureTests`,
`AskEndpointSubCodeRoutingTests.test_no_generic_global_wording_after_subcode_routing`
— and the last one only asserts the **detail payload** of the 503
response, not the prompt actually sent upstream). For the ungrounded
path, those tokens are unguarded.

### 1.7 Whether the answer language is preserved on the fallback path

It is not. `_answer_language_instruction(lang)` at
`paradiso_backend.py:754` is currently only called from
`_build_grounded_prompt`. The ungrounded path ignores `req.lang`
entirely, so even when the frontend explicitly says `"lang": "ko"`
the LLM may answer in English (or vice versa), depending on what the
upstream model decides.

### 1.8 Summary of the gap

The ungrounded path has zero guardrails. The grounded path has strong
guardrails (Korea-only scope, no cross-status bleed-through, source
attribution pinned, answer-language honored, forbidden-token tests).
The fallback-quality work is to give the ungrounded path a *subset* of
those guardrails — enough to keep answers Korea-scoped, honest about
uncertainty, and free of fabricated checklists — without ever claiming
to be source-grounded.

## 2. Answer quality policy (ungrounded answers)

This is the policy the follow-up PR enforces via prompt engineering
and tests. The implementer should encode each clause as either a
prompt-builder instruction, a forbidden-token assertion, or both.

An ungrounded Paradiso AI answer **must**:

1. **Stay inside Korean immigration / stay-status context.** No advice
   that assumes US, UK, Schengen, Canadian, Australian, or any other
   national immigration system. No "contact your embassy or consulate"
   boilerplate. The only contact points named are Korean: 출입국·
   외국인청/사무소/출장소, the 1345 외국인종합안내센터, HiKorea.
2. **Not pretend to be officially grounded.** It must explicitly state
   that the answer is *not* drawn from a verified manual excerpt for
   this specific scenario. If a partial manual reference exists for
   the same visa code under a different procedure, that reference may
   be **named** ("the manual covers 체류기간 연장허가 for this
   code; it does not cover the divorce scenario you described") but
   not paraphrased as if it answered the user's actual question.
3. **Not fabricate document lists or legal citations.** No invented
   `제출서류` bullets, no invented 법령 article numbers, no invented
   grace-period day counts, no invented forms (e.g. "별지 34호 서식")
   unless the same form would appear in a verified grounded entry for
   this exact `(visa_code, procedure_type)` pair.
4. **Identify the missing facts required for a specific answer.**
   The model must ask the user to clarify the facts that change the
   outcome. For the F-6-1 divorce case the missing-fact set includes
   (at minimum): current ARC expiration date, whether the divorce is
   finalized or pending (협의이혼/재판이혼 stage), whether there are
   children of the marriage and current custody/visitation status,
   whether spouse fault has been adjudicated, and current
   employment / independent-status eligibility.
5. **Provide useful, bounded pathways when no fixture exists.** The
   model may *name* candidate status pathways the user should ask the
   immigration office about (e.g. for F-6-1 divorce: continued F-6-1
   pending finalization, F-6-2 child-raising, F-6-3 spouse-fault /
   marriage-dissolution, transition to an independent work status such
   as E-series or D-series if qualified). Each pathway must be marked
   **"must be verified with 출입국·외국인청 / 1345 / HiKorea"** and
   must not be presented as guaranteed or as the user's "right".
6. **Use a clearly separated answer shape:**
   - a. **현재 알려진 사실 / Current known facts** — restated from the
        user's prompt only. No invented facts.
   - b. **한국 체류 측면의 쟁점 / Why this matters for Korean stay
        status** — short paragraph, Korea-scoped.
   - c. **가능한 경로(검증 필요) / Possible pathways — must be
        verified** — bullet list of candidate status routes, each
        flagged as unverified.
   - d. **확인이 필요한 정보 / Missing facts to clarify** — bullet
        list of the specific facts the user has not yet supplied.
   - e. **다음 단계 / Next steps and who to contact** — name the
        Korean contact points: 관할 출입국·외국인청/사무소/출장소,
        1345 외국인종합안내센터, HiKorea, and (for legal questions
        about divorce itself) a licensed Korean attorney /
        행정사. No US/UK contacts. No links generated by the model.
   - f. **출처 한계 / Source limitation note** — one sentence stating
        that Paradiso does not have a verified manual excerpt for
        this exact procedure and that the user must confirm details
        with the official channels above.
7. **Use cautious language for unverified claims.** Phrasing like
   "확인이 필요합니다", "가능성이 있습니다", "사안에 따라 다를 수
   있습니다", "must be verified" — never "you will be deported",
   "your visa is revoked immediately", or "you have 30 days" unless
   that exact number is in a verified grounded entry.

The grounded path's policy is unchanged. This policy applies only when
`_select_grounding(...)` returns `None`.

## 3. Risk / domain taxonomy proposal

`_detect_task_type` is extended from a single string return
(`"extension" | None`) to return either `None` or a small structured
value documented below. The implementer chooses between (a) returning
just the new task-type string and computing risk inline, or (b)
returning a small dataclass / tuple. Either is acceptable; the wire
contract on `AskResponse.task_type_detected` stays a single string
(for now).

### 3.1 Task types

| Task type                          | Trigger sketch (Korean & English; case-insensitive)                                                                                                                                                                                                       |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `extension`                        | existing signals: `체류기간 연장`, `체류 연장`, `비자 연장`, `연장 신청`, `연장허가`, `연장`; `\b(extend\|extension\|renew\|renewal)\b`                                                                                                                  |
| `status_change`                    | `체류자격 변경`, `자격 변경`, `변경허가`; `change of status`, `switch (?:to\|from) [A-Z]-\d`, `status change`                                                                                                                                              |
| `foreigner_registration`           | `외국인등록`, `등록증 신청`, `외국인등록증 발급`; `alien registration`, `ARC application`, `register as a foreigner`                                                                                                                                       |
| `workplace_change`                 | `근무처 변경`, `근무처 추가`, `근무처 변경신고`; `change of workplace`, `change employer`, `add (?:a )?second job`                                                                                                                                          |
| `address_report`                   | `체류지 변경신고`, `주소 변경신고`, `이사 신고`; `change of address`, `report new address`                                                                                                                                                                |
| `passport_info_report`             | `여권 재발급 신고`, `여권 정보 변경`; `report new passport`, `passport (?:renewed\|reissued)`                                                                                                                                                            |
| `academic_status_change`           | `휴학`, `복학`, `자퇴`, `제적`, `정학`, `학점 미달`, `학적 변동`; `\b(leave of absence\|gap semester\|drop ?out\|expelled\|return from leave)\b`                                                                                                            |
| `family_status_change`             | `가족관계 변동`, `자녀 출생 신고`, `부양 가족 변경`; `family status change`, `(?:had\|born) a child`, `dependent added`                                                                                                                                    |
| `marriage_divorce_status_change`   | `이혼`, `결혼`, `혼인`, `혼인 무효`, `별거`, `사별`, `재혼`, `귀화 결혼`; `\b(divorce\|divorced\|separated\|widow(?:ed)?\|remarry\|annul(?:led\|ment)?)\b`. Stronger signal when co-occurring with `F-6`, `F-2-1`, `F-1`, or 결혼 / spouse vocabulary. |
| `overstay_deadline_risk`           | `초과체류`, `불법체류`, `만료`, `만료 임박`, `오버스테이`; `\b(overstay\|overstayed\|expired visa\|visa expired)\b`                                                                                                                                       |
| `general_status_summary`           | catch-all when no specific signal fires but a visa code is mentioned. Lowest priority.                                                                                                                                                                   |

Detection rules:

- Detection is **regex-on-text only** for v1. No LLM-side intent
  classification, no embeddings.
- When multiple task types match, prefer the highest-risk match (see
  §3.2). Tie-break by the order above (top wins).
- If both `marriage_divorce_status_change` and `extension` fire (e.g.
  "I'm getting divorced and my F-6-1 extension is next month"),
  prefer `marriage_divorce_status_change`. The user's risk-bearing
  question is the divorce, not the renewal.
- Task-type detection runs **independently** of visa-code detection.
  A divorce question without an explicit visa code still yields
  `marriage_divorce_status_change`.

### 3.2 Risk levels

| Task type                          | risk_level | grounding_status (default when no fixture exists)                          |
| ---------------------------------- | ---------- | -------------------------------------------------------------------------- |
| `extension`                        | medium     | `grounded` when fixture exists; `ungrounded_scoped` otherwise              |
| `status_change`                    | high       | `ungrounded_scoped`                                                        |
| `foreigner_registration`           | medium     | `ungrounded_scoped`                                                        |
| `workplace_change`                 | medium     | `ungrounded_scoped`                                                        |
| `address_report`                   | low        | `ungrounded_scoped`                                                        |
| `passport_info_report`             | low        | `ungrounded_scoped`                                                        |
| `academic_status_change`           | medium     | `ungrounded_scoped`                                                        |
| `family_status_change`             | medium     | `ungrounded_scoped`                                                        |
| `marriage_divorce_status_change`   | **high**   | `ungrounded_scoped` (until verified F-6 fixture exists)                    |
| `overstay_deadline_risk`           | **high**   | `ungrounded_scoped`                                                        |
| `general_status_summary`           | low        | `ungrounded_scoped`                                                        |

`grounding_status` values:

- `grounded` — a verified entry exists in
  `stay_manual_grounding_2026_05.json` and was selected.
- `ungrounded_scoped` — no verified entry; the fallback Korea-scoped
  template (see §4) is used.
- `ungrounded_unknown` — no task type detected; the fallback template
  still applies, with the missing-facts section foregrounded.

The F-6-1 divorce query must classify as:

- `task_type_detected = "marriage_divorce_status_change"`,
- `risk_level = "high"`,
- `grounding_status = "ungrounded_scoped"`,
- `visa_code_detected = "F-6"`, `visa_sub_code_detected = "F-6-1"`
  when the payload carries the code; both `None` when only free text
  is supplied (until a future PR opts into text-side F-6 detection,
  which is out of scope here).

### 3.3 Wire / metadata exposure

`AskResponse` already exposes `task_type_detected`. Add (optional,
nullable, additive) fields **only if all of them can be added in a
single small PR with tests**:

- `risk_level_detected: Optional[str]` — `"low" | "medium" | "high"`.
- `grounding_status: Optional[str]` — `"grounded" | "ungrounded_scoped" | "ungrounded_unknown"`.

These are *additive* fields. Existing clients that ignore them
continue to work. If the implementer is uncertain whether the
frontend will mishandle new keys, ship the prompt-side fallback first
and the wire fields second, in a follow-up PR. Do **not** rename or
remove `task_type_detected`.

## 4. Fallback answer template for high-risk ungrounded cases

The implementer adds a new prompt builder, e.g.
`_build_ungrounded_korea_scoped_prompt(prompt, *, visa_code,
visa_sub_code, task_type, risk_level, lang)`, and routes
`final_prompt` through it on the `grounding is None` branch of
`ask(...)`.

### 4.1 Required prompt sections

Implementer-side: the prompt assembled and sent to the LLM **must**
contain, in this order:

1. **System role** — Korean: "당신은 대한민국 출입국·외국인정책본부
   매뉴얼·법령·HiKorea 안내 범위 내에서만 답하는 한국 비자·체류
   안내 도우미입니다." Mirror the grounded-path role exactly except
   for the "공식 매뉴얼을 근거로 답하는" clause, which must be
   replaced with a scope-only clause that does **not** claim source
   grounding.
2. **Scope guardrail** — "본 답변은 검증된 매뉴얼 발췌가 없는
   상황에서 제공되는 일반 안내입니다. 미국·영국·캐나다·기타 국가의
   이민 절차로 확장하지 마십시오. USCIS, Home Office, embassy,
   consulate, '본인이 체류 중인 국가' 같은 일반화된 안내를 포함하지
   마십시오. 매뉴얼에 없는 구체적인 제출서류 목록, 법령 조문 번호,
   유예 기간(예: '30일')을 임의로 만들어 답하지 마십시오."
3. **Detected metadata block (advisory only)** — when
   `visa_code_detected` / `visa_sub_code_detected` /
   `task_type_detected` are non-null, include them as labelled fields
   ("탐지된 체류자격", "탐지된 세부약호", "탐지된 절차 유형"). When
   `task_type == "marriage_divorce_status_change"`, append a sentence:
   "이혼·혼인 단절 관련 질문은 사안별로 결과가 크게 달라지므로
   일반적인 단정 표현을 피하고, 사용자에게 추가 확인 정보를 요청
   하십시오."
4. **Answer-language instruction** — reuse
   `_answer_language_instruction(lang)` exactly as the grounded path
   does, so that `lang: "ko"` and `lang: "en"` are honored.
5. **Required answer shape** — instruct the model to produce the six
   sections from §2 clause 6, with the labels in the user's answer
   language. The implementer's prompt may use bilingual labels in the
   instruction itself but the model's output uses the answer language.
6. **High-risk addendum (conditional)** — when
   `risk_level == "high"`:
   - For `marriage_divorce_status_change` *and* `visa_code_detected
     == "F-6"`: instruct the model that *if* it names F-6-1 / F-6-2 /
     F-6-3 / F-1-6 / E-series / D-series candidate pathways, each
     **must** be flagged as "must be verified with 관할 출입국·
     외국인청 또는 1345 / HiKorea" and **must not** be presented as
     guaranteed or automatic. The model must not assert that the
     current F-6-1 status is "immediately revoked" on divorce or that
     it is "valid until the current ARC expiration date" — both are
     unverified claims here. It must phrase the question as "현재
     체류자격의 유효 기간과 사후 처분은 관할 출입국·외국인청의
     판단 사항입니다" and route the user to verification.
   - For `overstay_deadline_risk`: instruct the model to avoid
     specific day-count grace periods unless they are in a verified
     grounded entry, and to route the user to 1345 immediately.
7. **User question echo** — `[사용자 질문] \n {prompt}`.
8. **Closing reminder** — "위 6개 섹션을 빠짐없이 포함하고, 검증되지
   않은 항목은 반드시 '확인 필요' 표기로 명시하십시오."

### 4.2 Forbidden content (model output)

The prompt must explicitly forbid the following in the model's
answer. The tests in §5 assert on the prompt string itself, not on
the LLM output:

- generic global immigration advice (USCIS, Home Office, "your home
  country's embassy or consulate", "contact your local immigration
  attorney" without naming Korea);
- unsupported exact grace-period claims ("30 days", "60 days", "you
  must report within X days") unless the same number is in a verified
  grounded entry for this exact `(visa_code, procedure_type)`;
- fake immediate-revocation certainty ("your visa is revoked
  immediately upon divorce", "you must leave Korea today");
- fake document checklists with invented forms or 별지 numbers;
- invented 법령 article numbers or paraphrased clause text;
- generic "embassy / consulate" advice (the prompt names Korean
  contact points explicitly).

### 4.3 What the prompt must NOT do

- Must not claim "this answer is from the 외국인체류 안내매뉴얼" or
  any equivalent. There is no source attribution on the fallback path.
- Must not include `grounding_sources` in the response (the existing
  code already returns `[]` when grounding is `None`; preserve that).
- Must not reuse the grounded-path source-line ("출처를 다음과 같이
  명시하십시오: 외국인체류 안내매뉴얼 (2026.5), 법무부 …"). Keeping
  that wording would falsely imply grounding.

### 4.4 Behavior when no provider is configured

The existing 503 path at `paradiso_backend.py:955` already returns
`grounding_used`, `grounding_sources`, `visa_code_detected`,
`visa_sub_code_detected`, `task_type_detected`. The new
`risk_level_detected` / `grounding_status` (if shipped) must appear
on the 503 detail object too, so tests can assert on them without an
LLM key.

## 5. Tests to add

Add to `backend/tests/test_paradiso_backend.py` (or a sibling file
`test_paradiso_fallback_quality.py`). All tests stay deterministic —
no LLM call. They assert on (a) detection metadata on the 503 detail
payload and (b) the string built by the new ungrounded prompt builder.

### 5.1 Task-type detection tests

| Test name                                                                | Asserts                                                                                                                                                                                                                                                                                       |
| ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `test_f61_divorce_query_triggers_marriage_divorce_status_change`         | Prompt: "Will my visa be revoked immediately if an American who is staying on an F-6-1 visa divorces?" with `visa_code: "F-6-1"`. Expect `task_type_detected == "marriage_divorce_status_change"`, `visa_code_detected == "F-6"`, `visa_sub_code_detected == "F-6-1"`.                       |
| `test_f61_divorce_query_does_not_select_unrelated_grounding`             | Same payload. Expect `grounding_used == False`, `grounding_sources == []`. No D-2 / D-4 / E-7 entry is selected even though the regex change adds new task types.                                                                                                                            |
| `test_f61_divorce_korean_wording_triggers_marriage_divorce_status_change` | Korean prompt with `이혼` and `F-6-1` in payload. Expect same task type.                                                                                                                                                                                                                     |
| `test_extension_still_wins_when_no_divorce_signal`                       | `"D-2 비자 연장에 필요한 서류는?"` — must remain `extension`, must still ground (regression guard for existing D-2 grounded tests).                                                                                                                                                          |
| `test_marriage_divorce_outranks_extension_when_both_signals_present`     | `"이혼했는데 F-6-1 비자 연장이 다음 달이에요. 어떻게 해야 하나요?"` — expect `marriage_divorce_status_change`, not `extension`.                                                                                                                                                              |
| `test_leave_of_absence_query_triggers_academic_status_change`            | `"D-2 비자로 유학 중인데 이번 학기 휴학하면 체류 자격에 문제가 있나요?"` and English equivalent `"I'm on a D-2 visa and taking a leave of absence this semester — does that affect my stay?"`. Expect `task_type_detected == "academic_status_change"`. `grounding_used == False`.            |
| `test_overstay_query_triggers_overstay_deadline_risk`                    | `"비자가 어제 만료됐어요. 어떻게 해야 하나요?"` / `"My visa expired yesterday — what now?"`. Expect `overstay_deadline_risk`, `risk_level_detected == "high"` if the wire field is shipped.                                                                                                  |
| `test_address_change_query_triggers_address_report`                      | `"이사를 했습니다. 어디에 신고해야 하나요?"` / `"I moved. Where do I report my new address?"`. Expect `address_report`, `risk_level_detected == "low"`.                                                                                                                                       |

### 5.2 Ungrounded prompt-builder tests

These tests call the new builder directly and assert on the returned
prompt string (no FastAPI client, no LLM).

| Test name                                                                       | Asserts                                                                                                                                                                                                                                  |
| ------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `test_f61_divorce_fallback_prompt_includes_korea_immigration_framing`           | Prompt contains 한국 / 출입국·외국인 / 1345 / HiKorea. Does NOT contain `외국인체류 안내매뉴얼` source-attribution line (would falsely imply grounding).                                                                                |
| `test_f61_divorce_fallback_prompt_asks_for_missing_facts`                       | Prompt instructs the model to ask the user for: current ARC expiration date, whether divorce is finalized vs. pending, presence/custody of children, spouse-fault status, current employment / independent-status eligibility.            |
| `test_f61_divorce_fallback_prompt_forbids_immediate_revocation_certainty`       | Prompt explicitly forbids strings like "immediately revoked", "즉시 취소", "비자가 즉시 말소", "you must leave Korea today". Forbidden-token list is asserted directly in the prompt string the model receives.                          |
| `test_f61_divorce_fallback_prompt_forbids_global_boilerplate`                   | Prompt contains explicit forbidden-token instructions for `USCIS`, `Home Office`, `embassy`, `consulate`, `해당 국가`, `본인이 체류 중인 국가`, "your home country's immigration office".                                                  |
| `test_f61_divorce_fallback_prompt_mentions_possible_paths_with_verify_marker`   | Prompt instructs the model that *if* it names F-6-2 / F-6-3 / F-1-6 / E-series / D-series pathways, each must be flagged "must be verified with 출입국·외국인청 / 1345 / HiKorea" and must not be asserted as guaranteed.                |
| `test_f61_divorce_fallback_prompt_includes_six_answer_sections`                 | Prompt lists the six sections from §2 clause 6 by name (current known facts, why this matters, possible pathways must-verify, missing facts, next steps, source-limitation note).                                                        |
| `test_ungrounded_prompt_preserves_answer_language_ko`                           | With `lang="ko"`, prompt contains `한국어로 답하십시오.` and not `Answer in English.`.                                                                                                                                                  |
| `test_ungrounded_prompt_preserves_answer_language_en`                           | With `lang="en"`, prompt contains `Answer in English.` and not `한국어로 답하십시오.`.                                                                                                                                                  |
| `test_ungrounded_prompt_preserves_answer_language_default`                      | With `lang=None` or unrecognized value, prompt contains `Answer in the same language as the user's question.`.                                                                                                                          |
| `test_ungrounded_prompt_for_overstay_routes_to_1345`                            | `overstay_deadline_risk` prompt names 1345 / 관할 출입국·외국인청 as immediate contacts and forbids invented grace-period day counts.                                                                                                  |

### 5.3 Regression guards (existing grounded path)

Every existing test in `backend/tests/test_paradiso_backend.py`
**must still pass**. Specifically the implementer must not break:

- `AskEndpointGroundingTests.test_d2_extension_korean_question_selects_grounding`
- `AskEndpointGroundingTests.test_d2_extension_english_wording`
- `AskEndpointExpandedGroundingTests.test_d4_extension_korean_question_selects_grounding`
- `AskEndpointExpandedGroundingTests.test_e7_extension_korean_question_selects_grounding`
- `AskEndpointSubCodeRoutingTests.test_d4_2k_payload_does_not_use_d4_grounding`
- `GroundingSelectorSubCodeTests.test_f6_subcode_returns_none`
- `GroundedPromptLanguageTests.*` (the grounded language-preservation
  tests must remain green; their behavior is unchanged).

Add a single explicit regression test that ties the two paths
together:

`test_d2_extension_still_grounded_and_e7_4_still_ungrounded`:
asserts that a D-2 extension question still hits `grounding_used ==
True` and an E-7-4 extension question still hits `grounding_used ==
False` after the new task-type detector lands. The point is to prove
the new detector did not steal the `extension` path.

### 5.4 Forbidden-token bleed-through guard

`test_ungrounded_prompt_does_not_imply_source_grounding`:

- The new ungrounded prompt builder's output **must not** contain the
  exact strings `외국인체류 안내매뉴얼 (2026.5)` or `법무부 출입국·
  외국인정책본부` as a source-attribution line. (It may mention 관할
  출입국·외국인청 as a contact, which is different.) This guards
  against accidentally copy-pasting the grounded-path attribution.

## 6. Optional: golden eval cases (lightweight, ships with the tests)

A short golden-eval JSON fixture
(`backend/tests/data/fallback_golden_eval.json`, deterministic, no
LLM call) lists 8–12 prompts with expected detection metadata only —
not expected free-form answers. Example shape:

```json
[
  {
    "id": "f61_divorce_en",
    "prompt": "Will my visa be revoked immediately if an American who is staying on an F-6-1 visa divorces?",
    "payload": { "visa_code": "F-6-1", "lang": "en" },
    "expect": {
      "visa_code_detected": "F-6",
      "visa_sub_code_detected": "F-6-1",
      "task_type_detected": "marriage_divorce_status_change",
      "risk_level_detected": "high",
      "grounding_used": false,
      "grounding_status": "ungrounded_scoped"
    }
  }
]
```

A single test iterates the fixture, posts each prompt against the 503
no-LLM-key path, and asserts on the detail payload. This makes
adding new golden cases cheap and turns the eval suite into a
data-only change for future PRs.

Ship the fixture **only if** the wire fields (`risk_level_detected`,
`grounding_status`) are shipped in the same PR. Otherwise omit them
from the `expect` block.

## 7. Documentation deliverables

The follow-up PR must update:

1. **This file** — flip the "Status" banner from "design + brief" to
   "implemented (PR #NNN)" once the code lands.
2. **`docs/paradiso_ai_safe_automation_architecture.md`** — under
   §14 PR C, link to this brief and to the implemented PR.
3. **`docs/manual_grounding_expansion_plan.md`** — add a one-line
   note under "Why not full RAG yet?" pointing readers to the
   ungrounded fallback policy for the unverified majority of stay
   procedures.

No changes to `docs/source_monitoring_pipeline.md`,
`docs/privacy_safe_coverage_analytics.md`, or any frontend doc.

## 8. Out of scope (do not include in the same PR)

The following changes are tempting but **must not** ride along with
the fallback-quality PR. Each is a separate brief / PR:

- Adding F-6 / F-6-1 / F-6-2 / F-6-3 grounding entries. Those require
  PDF-page verification and a `REVIEW.md` per the candidate flow
  (`docs/paradiso_ai_safe_automation_architecture.md` §8–§9).
- Adding D-10 sub-code entries.
- Wiring `LAW_API_KEY` to `/api/ask`.
- Text-side detection of `F-6` / `F-6-1` / `D-10` etc. The current
  `_detect_visa_codes` text path is bounded to `("D", "2"), ("D",
  "4"), ("E", "7")`. Extending it is *useful* for the fallback path
  but is a discrete change that needs its own tests for false-positive
  and false-negative cases (e.g. "F-6 lessons in math" must not match)
  and should not gate the fallback-quality work. The fallback policy
  works correctly whether or not the visa code is detected — the
  missing-facts section just becomes more important when detection
  fails.
- Adding a clarification-prompt mode where Paradiso refuses to answer
  at all and asks back. That is the PR D ("Subcode-aware selector
  hardening") variant in
  `docs/paradiso_ai_safe_automation_architecture.md` §14.
- Persisting any prompt or session data for analytics. Coverage
  analytics is the PR H flow, not this one.

## 9. Validation checklist for the implementing PR

Before requesting review on the follow-up PR:

- [ ] `python3 backend/tests/test_paradiso_backend.py` passes
      (existing tests).
- [ ] New tests in §5 pass.
- [ ] `bash scripts/check_repo.sh` passes end-to-end (the backend
      regression suite runs in step 11 of that script).
- [ ] `grep -n "외국인체류 안내매뉴얼 (2026.5)"` does **not** appear
      in any string produced by the new ungrounded prompt builder.
- [ ] `grep -n "USCIS\|Home Office"` does not appear in any
      runtime-built ungrounded prompt **as content**; it appears only
      in the prompt-side forbidden-token instruction and in test
      assertions.
- [ ] No file under `backend/data/manual_grounding/` is modified.
- [ ] No file under `index.html`, `ai.html`, `visa_data.json`,
      `backend/data/visas.json` is modified.
- [ ] PR is opened as a draft and includes a short note saying the
      fallback path does **not** claim source grounding.

## 10. Related documents

- [`docs/paradiso_ai_safe_automation_architecture.md`](paradiso_ai_safe_automation_architecture.md) —
  §14 PR C is the parent design item for this brief.
- [`docs/manual_grounding_expansion_plan.md`](manual_grounding_expansion_plan.md) —
  schema 1.2, deferred F-6 / D-10 entries that this brief deliberately
  does not implement.
- [`docs/CODEX_SAFE_AUTOMATION_IMPLEMENTATION_BRIEF.md`](CODEX_SAFE_AUTOMATION_IMPLEMENTATION_BRIEF.md) —
  template this brief follows (hard-rules + files-to-create +
  validation checklist shape).
- [`backend/paradiso_backend.py`](../backend/paradiso_backend.py) —
  the file changed by the implementing PR. Today the ungrounded
  fallback is `final_prompt = prompt` on line 924; the implementing
  PR replaces that with the builder described in §4.
