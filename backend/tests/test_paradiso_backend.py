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


class RootEndpointTests(unittest.TestCase):
    """GET / must return a friendly service descriptor, not a raw 404.

    Mobile users who open the bare backend URL were previously greeted
    by `{"detail":"Not Found"}`. The root route gives them an actionable
    payload pointing at the real frontend (when FRONTEND_URL is set) and
    the available API endpoints.
    """

    def test_root_returns_200_with_service_info(self):
        os.environ.pop("FRONTEND_URL", None)
        client, _ = _client()
        resp = client.get("/")
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertEqual(body.get("service"), "paradiso-backend")
        self.assertEqual(body.get("status"), "ok")
        self.assertIn("Paradiso backend is running", body.get("message", ""))
        self.assertIn("/health", body.get("message", ""))
        self.assertIn("/api/visas", body.get("message", ""))
        self.assertIn("/api/ask", body.get("message", ""))
        self.assertIsNone(body.get("frontend"))

    def test_root_includes_frontend_url_when_configured(self):
        os.environ["FRONTEND_URL"] = "https://lucanomics.github.io/Paradiso/"
        try:
            # FRONTEND_URL is read at import; reload to pick up env override.
            import importlib
            import paradiso_backend  # noqa: WPS433
            importlib.reload(paradiso_backend)
            paradiso_backend._reset_visas_cache_for_tests()
            paradiso_backend._reset_grounding_cache_for_tests()
            from fastapi.testclient import TestClient  # type: ignore
            client = TestClient(paradiso_backend.app)
            resp = client.get("/")
            self.assertEqual(resp.status_code, 200, resp.text)
            self.assertEqual(
                resp.json().get("frontend"),
                "https://lucanomics.github.io/Paradiso/",
            )
        finally:
            os.environ.pop("FRONTEND_URL", None)
            import importlib
            import paradiso_backend  # noqa: WPS433
            importlib.reload(paradiso_backend)

    def test_root_declares_utf8_charset(self):
        client, _ = _client()
        resp = client.get("/")
        ctype = resp.headers.get("content-type", "")
        self.assertIn("application/json", ctype.lower())
        self.assertIn("charset=utf-8", ctype.lower())


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

    def test_response_declares_utf8_charset(self):
        """Without an explicit charset, some legacy clients decode the
        UTF-8 body as latin-1 and render Korean text as mojibake."""
        client, _ = _client()
        resp = client.get("/api/visas")
        ctype = resp.headers.get("content-type", "")
        self.assertIn("application/json", ctype.lower())
        self.assertIn("charset=utf-8", ctype.lower())

    def test_korean_text_round_trips_unchanged(self):
        """The first record (K-ETA) ships with Korean text; any
        encoding round-trip bug would replace those Hangul syllables
        with mojibake or U+FFFD replacement characters."""
        client, _ = _client()
        resp = client.get("/api/visas")
        # Strict UTF-8 decode of the raw body, then JSON parse.
        body_bytes = resp.content
        self.assertEqual(body_bytes.count("�".encode("utf-8")), 0,
                         "response body contains U+FFFD replacement characters")
        import json as _json
        body = _json.loads(body_bytes.decode("utf-8"))
        records = {v.get("code"): v for v in body.get("data", [])}
        self.assertIn("K-ETA", records, "K-ETA record must be present")
        self.assertEqual(
            records["K-ETA"].get("name"),
            "전자여행허가 (K-ETA) 종합 가이드",
            "Korean name field on K-ETA must round-trip exactly",
        )


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

    def test_ungrounded_visa_question_does_not_use_grounding(self):
        """A visa code without a verified grounding entry must fall through
        the grounding path even when the task is recognized as extension."""
        resp = self._post({
            "question": "F-2 비자 연장 서류는?",
            "visa_code": "F-2",
        })
        self.assertEqual(resp.status_code, 503, resp.text)
        detail = resp.json()["detail"]
        self.assertFalse(detail.get("grounding_used"))
        self.assertEqual(detail.get("grounding_sources"), [])
        # Task is still detected as extension; only the grounding gate is narrow.
        self.assertEqual(detail.get("visa_code_detected"), "F-2")
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


class ExpandedGroundingFixtureTests(unittest.TestCase):
    """The first batch of manual-grounding expansion beyond D-2:
    D-4 (어학연수생 D-4-1/D-4-7) and E-7 체류기간 연장허가."""

    FIXTURE = BACKEND_DIR / "data" / "manual_grounding" / "stay_manual_grounding_2026_05.json"

    def _entries(self):
        import json as _json
        data = _json.loads(self.FIXTURE.read_text(encoding="utf-8"))
        return {
            (g.get("visa_code"), g.get("procedure_type")): g
            for g in data.get("groundings", [])
        }

    def test_d4_and_e7_entries_present(self):
        entries = self._entries()
        self.assertIn(("D-4", "체류기간 연장허가"), entries)
        self.assertIn(("E-7", "체류기간 연장허가"), entries)

    def test_d4_entry_metadata_verified(self):
        entry = self._entries()[("D-4", "체류기간 연장허가")]
        self.assertEqual(entry.get("page_range"), "90-91")
        self.assertEqual(entry.get("source_verification_status"), "verified_locally")
        self.assertEqual(entry.get("source_confidence"), "high")
        self.assertTrue((entry.get("verification_note") or "").strip())
        # Section label should explicitly scope to 어학연수생 to avoid implying
        # coverage of all D-4 sub-codes.
        self.assertIn("어학연수생", entry.get("section", ""))
        # Korea-specific 어학연수 documents.
        docs = " ".join(entry.get("required_documents", []))
        for needle in ("신청서", "여권", "외국인등록증", "수수료", "재학을 입증", "재정입증", "체류지 입증서류"):
            self.assertIn(needle, docs, f"expected '{needle}' in D-4 required_documents")

    def test_e7_entry_metadata_verified(self):
        entry = self._entries()[("E-7", "체류기간 연장허가")]
        self.assertEqual(entry.get("page_range"), "226")
        self.assertEqual(entry.get("source_verification_status"), "verified_locally")
        self.assertEqual(entry.get("source_confidence"), "high")
        self.assertTrue((entry.get("verification_note") or "").strip())
        self.assertIn("특정활동", entry.get("section", ""))
        docs = " ".join(entry.get("required_documents", []))
        # E-7 extension is employment-track; the source page lists 고용계약서
        # and 소득금액 증명 alongside the common 신청서/여권/외국인등록증/수수료.
        for needle in (
            "신청서", "여권", "외국인등록증", "수수료",
            "고용계약서", "개인 소득금액 증명",
            "사업자등록증", "체류지 입증서류",
        ):
            self.assertIn(needle, docs, f"expected '{needle}' in E-7 required_documents")

    def test_no_generic_global_wording_in_new_entries(self):
        forbidden = (
            "USCIS",
            "Home Office",
            "embassy",
            "consulate",
            "해당 국가",
            "본인이 체류 중인 국가",
        )
        for key in (("D-4", "체류기간 연장허가"), ("E-7", "체류기간 연장허가")):
            entry = self._entries()[key]
            haystack = " ".join(entry.get("required_documents", [])) + " " + " ".join(entry.get("caveats", []))
            for needle in forbidden:
                self.assertNotIn(
                    needle, haystack,
                    f"{key} grounding must not contain generic/global wording: {needle!r}",
                )


class AskEndpointExpandedGroundingTests(unittest.TestCase):
    """End-to-end: D-4 (어학연수생) and E-7 extension questions must trip
    the grounding selector with the correct source metadata."""

    def _post(self, payload):
        client, _ = _client()
        return client.post("/api/ask", json=payload)

    # ---- D-4 ----
    def test_d4_extension_korean_question_selects_grounding(self):
        resp = self._post({
            "question": "D-4 어학연수 자격으로 체류 중인데 체류기간 연장에 필요한 서류는 무엇입니까?",
            "visa_code": "D-4",
            "lang": "ko",
        })
        self.assertEqual(resp.status_code, 503, resp.text)
        detail = resp.json()["detail"]
        self.assertTrue(detail.get("grounding_used"))
        self.assertEqual(detail.get("visa_code_detected"), "D-4")
        self.assertEqual(detail.get("task_type_detected"), "extension")
        src = (detail.get("grounding_sources") or [{}])[0]
        self.assertEqual(src.get("visa_code"), "D-4")
        self.assertEqual(src.get("procedure_type"), "체류기간 연장허가")
        self.assertEqual(src.get("page_range"), "90-91")
        self.assertEqual(src.get("source_file"), "docs/source-manuals/2026-05/stay_manual_2026_05.pdf")

    def test_d4_extension_english_question_selects_grounding(self):
        resp = self._post({
            "question": "What documents do I need to extend my D-4 language-training stay in Korea?",
            "visa_code": "D-4",
        })
        self.assertEqual(resp.status_code, 503, resp.text)
        detail = resp.json()["detail"]
        self.assertTrue(detail.get("grounding_used"))
        self.assertEqual(detail.get("visa_code_detected"), "D-4")
        self.assertEqual(detail.get("task_type_detected"), "extension")

    def test_d4_payload_variants_normalize(self):
        for raw in ("d4", "D4", "d-4", "D 4"):
            resp = self._post({
                "question": "체류기간 연장 신청에 필요한 서류는?",
                "visa_code": raw,
            })
            self.assertEqual(resp.status_code, 503, resp.text)
            detail = resp.json()["detail"]
            self.assertTrue(detail.get("grounding_used"), f"raw={raw!r} did not ground")
            self.assertEqual(detail.get("visa_code_detected"), "D-4")

    def test_d4_non_extension_question_does_not_use_grounding(self):
        resp = self._post({
            "question": "D-4 자격 신청에 필요한 학력 증빙은 무엇인가요?",
            "visa_code": "D-4",
        })
        self.assertEqual(resp.status_code, 503, resp.text)
        detail = resp.json()["detail"]
        self.assertFalse(detail.get("grounding_used"))
        self.assertEqual(detail.get("visa_code_detected"), "D-4")
        self.assertIsNone(detail.get("task_type_detected"))

    # ---- E-7 ----
    def test_e7_extension_korean_question_selects_grounding(self):
        resp = self._post({
            "question": "E-7 특정활동 자격으로 체류 중인데 체류기간 연장허가 신청에 필요한 서류는 무엇입니까?",
            "visa_code": "E-7",
            "lang": "ko",
        })
        self.assertEqual(resp.status_code, 503, resp.text)
        detail = resp.json()["detail"]
        self.assertTrue(detail.get("grounding_used"))
        self.assertEqual(detail.get("visa_code_detected"), "E-7")
        self.assertEqual(detail.get("task_type_detected"), "extension")
        src = (detail.get("grounding_sources") or [{}])[0]
        self.assertEqual(src.get("visa_code"), "E-7")
        self.assertEqual(src.get("procedure_type"), "체류기간 연장허가")
        self.assertEqual(src.get("page_range"), "226")

    def test_e7_extension_english_question_selects_grounding(self):
        resp = self._post({
            "question": "What documents do I need to extend my E-7 specially-designated activity status in Korea?",
            "visa_code": "E7",
        })
        self.assertEqual(resp.status_code, 503, resp.text)
        detail = resp.json()["detail"]
        self.assertTrue(detail.get("grounding_used"))
        self.assertEqual(detail.get("visa_code_detected"), "E-7")
        self.assertEqual(detail.get("task_type_detected"), "extension")

    def test_e7_payload_variants_normalize(self):
        for raw in ("e7", "E7", "e-7", "E 7"):
            resp = self._post({
                "question": "체류기간 연장에 필요한 서류는?",
                "visa_code": raw,
            })
            self.assertEqual(resp.status_code, 503, resp.text)
            detail = resp.json()["detail"]
            self.assertTrue(detail.get("grounding_used"), f"raw={raw!r} did not ground")
            self.assertEqual(detail.get("visa_code_detected"), "E-7")

    def test_e7_non_extension_question_does_not_use_grounding(self):
        resp = self._post({
            "question": "E-7 자격으로 변경할 수 있는 조건은 무엇인가요?",
            "visa_code": "E-7",
        })
        self.assertEqual(resp.status_code, 503, resp.text)
        detail = resp.json()["detail"]
        self.assertFalse(detail.get("grounding_used"))
        self.assertEqual(detail.get("visa_code_detected"), "E-7")
        self.assertIsNone(detail.get("task_type_detected"))

    # ---- Text-only detection ----
    def test_text_only_detection_for_d4_and_e7(self):
        resp = self._post({
            "question": "일반연수(D-4) 자격으로 체류기간 연장허가 신청에 필요한 서류는?",
        })
        detail = resp.json()["detail"]
        self.assertTrue(detail.get("grounding_used"))
        self.assertEqual(detail.get("visa_code_detected"), "D-4")

        resp = self._post({
            "question": "특정활동(E-7) 자격으로 체류기간 연장허가 신청 시 제출서류가 무엇인지 알려주세요.",
        })
        detail = resp.json()["detail"]
        self.assertTrue(detail.get("grounding_used"))
        self.assertEqual(detail.get("visa_code_detected"), "E-7")

    # ---- Cross-contamination guards ----
    def test_d4_grounding_does_not_contain_e7_documents(self):
        _, mod = _client()
        bundle = mod._load_stay_manual_grounding()
        d4 = mod._select_grounding("D-4", "extension")
        built = mod._build_grounded_prompt("D-4 연장 서류?", d4, bundle, lang="ko")
        # E-7 specific item (고용계약서 / 소득금액 증명) must not bleed into D-4 prompt.
        self.assertNotIn("고용계약서", built)
        self.assertNotIn("소득금액 증명원", built)
        # D-4-specific item must be present.
        self.assertIn("재학을 입증", built)

    def test_e7_grounding_does_not_contain_d2_specific_documents(self):
        _, mod = _client()
        bundle = mod._load_stay_manual_grounding()
        e7 = mod._select_grounding("E-7", "extension")
        built = mod._build_grounded_prompt("E-7 연장 서류?", e7, bundle, lang="ko")
        # D-2-specific 'wording 지도교수' must not appear in E-7 prompt.
        self.assertNotIn("지도교수", built)
        # E-7 specific items present.
        self.assertIn("고용계약서", built)
        self.assertIn("소득금액", built)


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
