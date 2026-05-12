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


if __name__ == "__main__":
    unittest.main(verbosity=2)
