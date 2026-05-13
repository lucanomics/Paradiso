"""Lightweight, deterministic tests for the Paradiso backend.

Covers the two regressions the Railway production audit surfaced:

  1. /api/visas must return the real visa dataset, not DEFAULT_VISAS,
     whenever backend/data/visas.json exists in the deploy context.
  2. /api/ask must accept message / query / question and must not crash
     on the optional metadata (visa_code, visa_data, lang, ...).

Run from repo root:

    python3 -m pytest backend/tests -q

or use the bundled runner (no pytest needed):

    python3 backend/tests/test_paradiso_backend.py
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _client():
    # Ensure no LLM provider is configured so /api/ask never makes a
    # real upstream call. We only assert on schema-level behavior here.
    for key in ("OPENROUTER_API_KEY", "GROQ_API_KEY"):
        os.environ.pop(key, None)
    from fastapi.testclient import TestClient  # type: ignore

    import paradiso_backend  # noqa: WPS433 — late import after sys.path setup

    paradiso_backend._reset_visas_cache_for_tests()
    paradiso_backend._reset_grounding_cache_for_tests()
    return TestClient(paradiso_backend.app), paradiso_backend


class BackendImportTests(unittest.TestCase):
    def test_module_imports(self):
        import paradiso_backend  # noqa: F401

    def test_visa_data_file_present(self):
        """The deploy-context visa file must exist; this is the fix."""
        target = BACKEND_DIR / "data" / "visas.json"
        self.assertTrue(
            target.is_file(),
            f"backend/data/visas.json is missing — Railway will fall back to "
            f"DEFAULT_VISAS. Run scripts/sync_visa_data.py.",
        )


class VisasEndpointTests(unittest.TestCase):
    def test_returns_real_data_not_default(self):
        client, _ = _client()
        resp = client.get("/api/visas")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("data", body)
        self.assertIn("count", body)
        self.assertGreater(
            body["count"], 5,
            "DEFAULT_VISAS has 5 entries; real data must have more.",
        )
        self.assertNotIn(
            "warning", body,
            f"/api/visas returned fallback warning: {body.get('warning')!r}",
        )
        self.assertIn(body.get("source_type"), {"backend-data", "repo-root", "explicit"})

    def test_returns_known_visa_code(self):
        """Real Paradiso data must include D-2 (used by ask payload tests)."""
        client, _ = _client()
        resp = client.get("/api/visas")
        codes = {v.get("code") for v in resp.json().get("data", [])}
        self.assertIn("D-2", codes)

    def test_no_replacement_character_in_response_strings(self):
        client, _ = _client()
        resp = client.get("/api/visas")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()

        def _iter_strings(value):
            if isinstance(value, str):
                yield value
            elif isinstance(value, dict):
                for v in value.values():
                    yield from _iter_strings(v)
            elif isinstance(value, list):
                for item in value:
                    yield from _iter_strings(item)

        corrupted = [s for s in _iter_strings(body) if "\uFFFD" in s]
        self.assertFalse(corrupted, f"/api/visas contains replacement char in strings: {corrupted[:3]!r}")

    def test_keta_name_contains_korean_text(self):
        client, _ = _client()
        resp = client.get("/api/visas")
        self.assertEqual(resp.status_code, 200)
        rows = resp.json().get("data", [])
        keta = next((row for row in rows if row.get("code") == "K-ETA"), None)
        self.assertIsNotNone(keta, "K-ETA record must exist")
        self.assertIn("전자여행허가", keta.get("name", ""))


class AskEndpointSchemaTests(unittest.TestCase):
    """No LLM keys are set, so /api/ask returns 503 once the prompt
    passes schema validation. The point of these tests is to assert the
    request *parses* and resolves a non-empty prompt — not to call an
    LLM. 503 here is the success signal; 400 (empty_prompt) is the
    failure signal we are guarding against.
    """

    PROMPT = "D-2 비자 연장에 필요한 서류는?"

    def _post(self, payload):
        client, _ = _client()
        return client.post("/api/ask", json=payload)

    def test_accepts_message(self):
        resp = self._post({"message": self.PROMPT})
        self.assertEqual(resp.status_code, 503, resp.text)
        self.assertEqual(resp.json()["detail"]["error"], "no_llm_provider_configured")

    def test_accepts_query(self):
        resp = self._post({"query": self.PROMPT})
        self.assertEqual(resp.status_code, 503, resp.text)

    def test_accepts_question(self):
        resp = self._post({"question": self.PROMPT})
        self.assertEqual(resp.status_code, 503, resp.text)

    def test_accepts_visa_code_without_400(self):
        resp = self._post({"question": self.PROMPT, "visa_code": "D-2"})
        self.assertEqual(resp.status_code, 503, resp.text)

    def test_accepts_full_frontend_payload(self):
        """The shape index.html / ai.html actually send."""
        resp = self._post({
            "question": self.PROMPT,
            "consent": True,
            "context": "doc guide",
            "lang": "ko",
            "visa_data": {"code": "D-2", "name": "유학"},
        })
        self.assertEqual(resp.status_code, 503, resp.text)

    def test_empty_payload_returns_updated_error_message(self):
        resp = self._post({})
        self.assertEqual(resp.status_code, 400)
        detail = resp.json()["detail"]
        self.assertEqual(detail["error"], "empty_prompt")
        self.assertIn("question", detail["message"])

    def test_resolution_order_prefers_message(self):
        """If multiple aliases are sent, message wins."""
        resp = self._post({
            "message": "primary",
            "query": "secondary",
            "question": "tertiary",
        })
        self.assertEqual(resp.status_code, 503, resp.text)


class GroundingFixtureTests(unittest.TestCase):
    """The grounding fixture is shipped with the deploy context, must be
    valid JSON, and must contain honest, non-fabricated metadata."""

    FIXTURE = BACKEND_DIR / "data" / "manual_grounding" / "stay_manual_grounding_2026_05.json"

    def test_fixture_present(self):
        self.assertTrue(self.FIXTURE.is_file(), f"missing fixture: {self.FIXTURE}")

    def test_fixture_metadata_is_korea_specific(self):
        import json as _json
        data = _json.loads(self.FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(data.get("source_file"), "docs/source-manuals/2026-05/stay_manual_2026_05.pdf")
        self.assertEqual(data.get("source_title"), "외국인체류 안내매뉴얼")
        self.assertEqual(data.get("source_date"), "2026.5")
        self.assertEqual(data.get("issuing_body"), "법무부 출입국·외국인정책본부")
        groundings = data.get("groundings") or []
        self.assertTrue(groundings, "groundings list must not be empty")
        d2_ext = next(
            (g for g in groundings
             if g.get("visa_code") == "D-2"
             and g.get("procedure_type") == "체류기간 연장허가"),
            None,
        )
        self.assertIsNotNone(d2_ext, "D-2 체류기간 연장허가 grounding entry missing")
        self.assertEqual(d2_ext.get("section"), "유학(D-2)")
        # page_range must be either null (unverified) or a non-empty string.
        page_range = d2_ext.get("page_range")
        self.assertTrue(page_range is None or (isinstance(page_range, str) and page_range.strip()))
        # Verification metadata must be present and explicit.
        self.assertIn(d2_ext.get("source_verification_status"), {"verified_locally", "unverified", "pending_verification"})
        self.assertIsInstance(d2_ext.get("verification_note"), str)
        self.assertTrue(d2_ext["verification_note"].strip())

    def test_fixture_documents_are_korea_specific_and_conservative(self):
        import json as _json
        data = _json.loads(self.FIXTURE.read_text(encoding="utf-8"))
        d2_ext = next(
            g for g in data["groundings"]
            if g.get("visa_code") == "D-2"
            and g.get("procedure_type") == "체류기간 연장허가"
        )
        docs = " ".join(d2_ext.get("required_documents", []))
        # Must include Korea-specific stay-manual items.
        for needle in ("신청서", "여권", "외국인등록증", "수수료", "재정입증", "체류지 입증서류"):
            self.assertIn(needle, docs, f"expected '{needle}' in required_documents")
        # Must NOT include generic global immigration items.
        forbidden = (
            "USCIS",
            "Home Office",
            "embassy",
            "consulate",
            "해당 국가",
            "본인이 체류 중인 국가",
        )
        haystack = docs + " " + " ".join(d2_ext.get("caveats", []))
        for needle in forbidden:
            self.assertNotIn(
                needle, haystack,
                f"grounding must not contain generic/global wording: {needle!r}",
            )


class AskEndpointGroundingTests(unittest.TestCase):
    """Verify that D-2 + 체류기간 연장 questions select the grounding,
    and unrelated questions do not. With no LLM keys we still get a 503,
    but the response detail carries the grounding metadata."""

    def _post(self, payload):
        client, _ = _client()
        return client.post("/api/ask", json=payload)

    def test_d2_extension_korean_question_selects_grounding(self):
        resp = self._post({
            "question": "D-2 비자로 체류중인 경우에는 비자 연장 신청시 서류가 무엇이 필요합니까?",
            "visa_code": "D-2",
            "lang": "ko",
        })
        self.assertEqual(resp.status_code, 503, resp.text)
        detail = resp.json()["detail"]
        self.assertTrue(detail.get("grounding_used"))
        self.assertEqual(detail.get("visa_code_detected"), "D-2")
        self.assertEqual(detail.get("task_type_detected"), "extension")
        sources = detail.get("grounding_sources") or []
        self.assertEqual(len(sources), 1)
        src = sources[0]
        self.assertEqual(src.get("source_file"), "docs/source-manuals/2026-05/stay_manual_2026_05.pdf")
        self.assertEqual(src.get("source_title"), "외국인체류 안내매뉴얼")
        self.assertEqual(src.get("source_date"), "2026.5")
        self.assertEqual(src.get("visa_code"), "D-2")
        self.assertEqual(src.get("procedure_type"), "체류기간 연장허가")

    def test_d2_extension_detection_from_text_only(self):
        """No explicit visa_code in payload; detection must still fire."""
        resp = self._post({
            "question": "유학(D-2) 자격으로 체류 중인데 체류기간 연장허가 신청에 필요한 서류는?",
        })
        self.assertEqual(resp.status_code, 503, resp.text)
        detail = resp.json()["detail"]
        self.assertTrue(detail.get("grounding_used"))
        self.assertEqual(detail.get("visa_code_detected"), "D-2")
        self.assertEqual(detail.get("task_type_detected"), "extension")

    def test_d2_extension_english_wording(self):
        resp = self._post({
            "question": "What documents do I need to extend my D-2 student visa stay?",
            "visa_code": "D-2",
        })
        self.assertEqual(resp.status_code, 503, resp.text)
        detail = resp.json()["detail"]
        self.assertTrue(detail.get("grounding_used"))
        self.assertEqual(detail.get("visa_code_detected"), "D-2")
        self.assertEqual(detail.get("task_type_detected"), "extension")

    def test_non_d2_question_does_not_use_grounding(self):
        resp = self._post({
            "question": "E-7 비자 연장 서류는?",
            "visa_code": "E-7",
        })
        self.assertEqual(resp.status_code, 503, resp.text)
        detail = resp.json()["detail"]
        self.assertFalse(detail.get("grounding_used"))
        self.assertEqual(detail.get("grounding_sources"), [])
        # Task is still detected as extension; only the grounding gate is narrow.
        self.assertEqual(detail.get("visa_code_detected"), "E-7")
        self.assertEqual(detail.get("task_type_detected"), "extension")

    def test_d2_non_extension_question_does_not_use_grounding(self):
        resp = self._post({
            "question": "D-2 자격 신청에 필요한 학력 증빙은 무엇인가요?",
            "visa_code": "D-2",
        })
        self.assertEqual(resp.status_code, 503, resp.text)
        detail = resp.json()["detail"]
        self.assertFalse(detail.get("grounding_used"))
        self.assertEqual(detail.get("visa_code_detected"), "D-2")
        self.assertIsNone(detail.get("task_type_detected"))


class GroundingHelperTests(unittest.TestCase):
    """Unit tests for the pure helpers — no FastAPI client involved."""

    def test_grounded_prompt_includes_source_attribution_and_documents(self):
        client, mod = _client()
        bundle = mod._load_stay_manual_grounding()
        self.assertIsNotNone(bundle)
        grounding = mod._select_grounding("D-2", "extension")
        self.assertIsNotNone(grounding)
        user_q = "D-2 연장 서류 알려줘"
        built = mod._build_grounded_prompt(user_q, grounding, bundle)
        self.assertIn(user_q, built)
        self.assertIn("외국인체류 안내매뉴얼", built)
        self.assertIn("2026.5", built)
        self.assertIn("법무부 출입국·외국인정책본부", built)
        self.assertIn("유학(D-2)", built)
        self.assertIn("체류기간 연장허가", built)
        self.assertIn("재정입증 서류", built)
        self.assertIn("체류지 입증서류", built)
        # Guardrails against generic/global content.
        for forbidden in ("USCIS", "Home Office", "해당 국가"):
            self.assertNotIn(forbidden, built)


class VisaCodeNormalizationTests(unittest.TestCase):
    """The grounding lookup expects 'D-2'; payloads in the wild send d2,
    D2, d-2, etc. _normalize_visa_code must reshape those equivalently."""

    def test_normalize_variants(self):
        _, mod = _client()
        cases = {
            "D-2": "D-2",
            "d-2": "D-2",
            "D2": "D-2",
            "d2": "D-2",
            "D 2": "D-2",
            "  d-2  ": "D-2",
            "D-2-1": "D-2-1",
            "d-2-1": "D-2-1",
            "F-5": "F-5",
            "f5": "F-5",
        }
        for raw, expected in cases.items():
            self.assertEqual(mod._normalize_visa_code(raw), expected, f"input={raw!r}")

    def test_normalize_preserves_multi_digit_main_codes(self):
        """Regression guard for the Codex P1 finding: D-10 / E-10 / F-10
        must not be rewritten to D-1-0 / E-1-0 / F-1-0."""
        _, mod = _client()
        cases = {
            "D-10": "D-10",
            "d-10": "D-10",
            "D10": "D-10",
            "d10": "D-10",
            "D 10": "D-10",
            "d 10": "D-10",
            "E10": "E-10",
            "E-10": "E-10",
            "F10": "F-10",
            "F-10": "F-10",
            "f-10": "F-10",
            "H-2": "H-2",
            # Subcodes on multi-digit main codes still parse when an
            # explicit separator precedes the subcode.
            "D-10-1": "D-10-1",
            "d-10-1": "D-10-1",
            # Subcodes on single-digit main codes parse with or without
            # a leading separator before the main number.
            "d2-1": "D-2-1",
            "D2-1": "D-2-1",
        }
        for raw, expected in cases.items():
            self.assertEqual(mod._normalize_visa_code(raw), expected, f"input={raw!r}")

    def test_normalize_does_not_split_multi_digit_into_subcode(self):
        """Explicit anti-regression: 'D-10' must never come out as 'D-1-0'."""
        _, mod = _client()
        for raw in ("D-10", "d-10", "D10", "d10", "E10", "E-10", "F10", "F-10"):
            self.assertNotEqual(
                mod._normalize_visa_code(raw),
                f"{raw[0].upper()}-1-0",
                f"input={raw!r} was incorrectly split into a subcode",
            )

    def test_normalize_passes_through_special_codes(self):
        _, mod = _client()
        # K-STAR and REGION-S are not Letter+digits; they pass through.
        self.assertEqual(mod._normalize_visa_code("K-STAR"), "K-STAR")
        self.assertEqual(mod._normalize_visa_code("k-star"), "K-STAR")
        self.assertEqual(mod._normalize_visa_code("REGION-S"), "REGION-S")

    def test_normalize_empty_and_none(self):
        _, mod = _client()
        self.assertIsNone(mod._normalize_visa_code(None))
        self.assertIsNone(mod._normalize_visa_code(""))
        self.assertIsNone(mod._normalize_visa_code("   "))


class AskEndpointVisaCodeNormalizationTests(unittest.TestCase):
    """End-to-end: lowercase / no-hyphen variants of D-2 must still trip
    the grounding selector."""

    PROMPT = "유학 비자로 체류 중인데 연장 신청 서류가 무엇인가요?"

    def _post(self, payload):
        client, _ = _client()
        return client.post("/api/ask", json=payload)

    def test_lowercase_d2_payload_triggers_grounding(self):
        resp = self._post({"question": self.PROMPT, "visa_code": "d2"})
        self.assertEqual(resp.status_code, 503, resp.text)
        detail = resp.json()["detail"]
        self.assertTrue(detail.get("grounding_used"))
        self.assertEqual(detail.get("visa_code_detected"), "D-2")

    def test_uppercase_no_hyphen_d2_payload_triggers_grounding(self):
        resp = self._post({"question": self.PROMPT, "visa_code": "D2"})
        self.assertEqual(resp.status_code, 503, resp.text)
        detail = resp.json()["detail"]
        self.assertTrue(detail.get("grounding_used"))
        self.assertEqual(detail.get("visa_code_detected"), "D-2")

    def test_lowercase_visa_data_code_triggers_grounding(self):
        resp = self._post({
            "question": self.PROMPT,
            "visa_data": {"code": "d2", "name": "유학"},
        })
        self.assertEqual(resp.status_code, 503, resp.text)
        detail = resp.json()["detail"]
        self.assertTrue(detail.get("grounding_used"))
        self.assertEqual(detail.get("visa_code_detected"), "D-2")


class GroundedPromptLanguageTests(unittest.TestCase):
    """The Korea-specific grounding content stays the same, but the
    'answer language' instruction must follow req.lang."""

    USER_Q = "What documents do I need to extend my D-2 student visa stay?"

    def _built(self, lang):
        _, mod = _client()
        bundle = mod._load_stay_manual_grounding()
        grounding = mod._select_grounding("D-2", "extension")
        return mod._build_grounded_prompt(self.USER_Q, grounding, bundle, lang=lang)

    def test_lang_en_instructs_english_not_korean(self):
        built = self._built("en")
        self.assertIn("Answer in English.", built)
        self.assertNotIn("한국어로 답하십시오.", built)
        # Korea-specific source attribution still present.
        self.assertIn("외국인체류 안내매뉴얼", built)
        self.assertIn("법무부 출입국·외국인정책본부", built)

    def test_lang_ko_instructs_korean(self):
        built = self._built("ko")
        self.assertIn("한국어로 답하십시오.", built)
        self.assertNotIn("Answer in English.", built)
        self.assertIn("외국인체류 안내매뉴얼", built)

    def test_unknown_lang_falls_back_to_user_language(self):
        built = self._built(None)
        self.assertIn("Answer in the same language as the user's question.", built)
        self.assertNotIn("한국어로 답하십시오.", built)
        self.assertNotIn("Answer in English.", built)
        # Korea-specific source attribution unchanged.
        self.assertIn("외국인체류 안내매뉴얼", built)

    def test_unrecognized_lang_value_also_falls_back(self):
        built = self._built("fr")
        self.assertIn("Answer in the same language as the user's question.", built)

    def test_answer_language_helper_directly(self):
        _, mod = _client()
        self.assertEqual(mod._answer_language_instruction("ko"), "- 한국어로 답하십시오.")
        self.assertEqual(mod._answer_language_instruction("KO"), "- 한국어로 답하십시오.")
        self.assertEqual(mod._answer_language_instruction("en"), "- Answer in English.")
        self.assertEqual(mod._answer_language_instruction("EN"), "- Answer in English.")
        for unknown in (None, "", "fr", "ja", "x"):
            self.assertEqual(
                mod._answer_language_instruction(unknown),
                "- Answer in the same language as the user's question.",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
