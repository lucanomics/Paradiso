#!/usr/bin/env python3
"""Tests for scripts/generate_candidate_from_matrix.py.

These tests exercise the pure-Python logic (matrix lookup, refusal
paths, page location, 제출서류 extraction) using a synthetic
``pdftotext``-style text fixture. They do NOT require poppler-utils
to be installed and do NOT touch any real PDF, the active fixture, or
the coverage matrix.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import generate_candidate_from_matrix as gcfm  # noqa: E402


SYNTHETIC_PDF_TEXT = (
    "\f"
    "page 1 cover\n"
    "- 1 -\n"
    "\f"
    "구직(D-10) 비자 안내\n"
    "체류자격 해당자 ...\n"
    "- 100 -\n"
    "\f"
    "체류기간 연장허가\n"
    "제출서류\n"
    "  ❍ 신청서, 여권, 외국인등록증, 수수료\n"
    "  ❍ 재정입증 서류\n"
    "  ❍ 구직활동 입증서류\n"
    "특 칙\n"
    "이하 생략\n"
    "- 101 -\n"
)


class MatrixLookupTests(unittest.TestCase):
    def test_real_matrix_has_eligible_rows(self):
        matrix = gcfm._load_matrix()
        rows = matrix.get("rows", [])
        self.assertTrue(
            any(
                isinstance(r, dict)
                and r.get("coverage_status") in gcfm._ELIGIBLE_COVERAGE_STATUSES
                for r in rows
            ),
            "matrix must contain at least one row eligible for candidate generation",
        )

    def test_find_row_returns_none_for_unknown(self):
        matrix = {"rows": [{"id": "abc"}]}
        self.assertIsNone(gcfm._find_row(matrix, "does_not_exist"))

    def test_find_row_finds_by_id(self):
        matrix = {"rows": [{"id": "abc"}, {"id": "xyz"}]}
        self.assertEqual(gcfm._find_row(matrix, "xyz"), {"id": "xyz"})


class HeaderAndSignalTests(unittest.TestCase):
    def test_visa_headers_d10(self):
        headers = gcfm._visa_header_candidates(
            {"visa_code": "D-10", "visa_sub_code": None}
        )
        self.assertIn("구직(D-10)", headers)
        self.assertIn("(D-10)", headers)

    def test_visa_headers_subcode(self):
        headers = gcfm._visa_header_candidates(
            {"visa_code": "D-10", "visa_sub_code": "D-10-1"}
        )
        self.assertIn("(D-10-1)", headers)

    def test_visa_headers_wildcard(self):
        headers = gcfm._visa_header_candidates(
            {"visa_code": "*", "visa_sub_code": None}
        )
        self.assertEqual(headers, [])

    def test_procedure_signals_known(self):
        signals = gcfm._procedure_signals(
            {"procedure_type": "체류기간 연장허가"}
        )
        self.assertIn("체류기간 연장허가", signals)

    def test_procedure_signals_internal_token_not_echoed(self):
        signals = gcfm._procedure_signals(
            {"procedure_type": "marriage_divorce_status_change"}
        )
        # Internal english_underscore token must not be echoed as a
        # Korean search term.
        self.assertNotIn("marriage_divorce_status_change", signals)
        self.assertIn("이혼", signals)


class PageLocationTests(unittest.TestCase):
    def test_locate_page_finds_candidate(self):
        pages = gcfm._split_pages(SYNTHETIC_PDF_TEXT)
        loc = gcfm._locate_page(
            pages,
            ["구직(D-10)", "(D-10)"],
            ["체류기간 연장허가"],
        )
        self.assertIsNotNone(loc)
        pdf_idx, printed = loc
        self.assertEqual(printed, 101)
        self.assertGreaterEqual(pdf_idx, 1)

    def test_locate_page_returns_none_when_no_header(self):
        pages = gcfm._split_pages(SYNTHETIC_PDF_TEXT)
        loc = gcfm._locate_page(
            pages,
            ["NONEXISTENT_HEADER"],
            ["체류기간 연장허가"],
        )
        self.assertIsNone(loc)

    def test_locate_page_returns_none_when_no_submission_block(self):
        text = (
            "\f구직(D-10) 안내\n체류자격...\n- 99 -\n"
            "\f다른 내용\n- 100 -\n"
        )
        pages = gcfm._split_pages(text)
        loc = gcfm._locate_page(
            pages,
            ["구직(D-10)", "(D-10)"],
            ["체류기간 연장허가"],
        )
        self.assertIsNone(loc)


class SubmissionBlockTests(unittest.TestCase):
    def test_extract_block_returns_bullets(self):
        pages = gcfm._split_pages(SYNTHETIC_PDF_TEXT)
        loc = gcfm._locate_page(
            pages,
            ["구직(D-10)", "(D-10)"],
            ["체류기간 연장허가"],
        )
        self.assertIsNotNone(loc)
        pdf_idx, _ = loc
        out = gcfm._extract_submission_block(pages[pdf_idx - 1])
        self.assertIsNotNone(out)
        excerpt, bullets = out
        self.assertEqual(
            bullets,
            [
                "신청서, 여권, 외국인등록증, 수수료",
                "재정입증 서류",
                "구직활동 입증서류",
            ],
        )
        self.assertIn("제출서류", excerpt)

    def test_extract_block_returns_none_on_no_heading(self):
        out = gcfm._extract_submission_block("nothing here\n- 1 -\n")
        self.assertIsNone(out)

    def test_extract_block_returns_none_on_no_bullets(self):
        text = "제출서류\nprose only, no bullets\n- 2 -\n"
        self.assertIsNone(gcfm._extract_submission_block(text))


class CandidateBuildTests(unittest.TestCase):
    def _row(self):
        return {
            "id": "d10_extension_general",
            "visa_code": "D-10",
            "visa_sub_code": None,
            "procedure_type": "체류기간 연장허가",
            "scenario": "general",
            "requires_subcode": False,
            "requires_scenario": False,
        }

    def test_candidate_marks_machine_extracted_low_confidence(self):
        c = gcfm._build_candidate(
            self._row(),
            section_label="구직(D-10) — 체류기간 연장허가",
            printed_page=101,
            excerpt="제출서류\n  ❍ ...",
            bullets=["신청서"],
            source_file_rel="docs/source-manuals/2026-05/stay_manual_2026_05.pdf",
            pdftotext_path="/usr/bin/pdftotext",
        )
        self.assertEqual(c["candidate_status"], "draft")
        self.assertEqual(c["source_verification_status"], "machine_extracted")
        self.assertEqual(c["source_confidence"], "low")
        self.assertEqual(c["page_range"], "101")
        self.assertEqual(c["required_documents"], ["신청서"])
        self.assertIn("MACHINE EXTRACT ONLY", c["verification_note"])
        self.assertEqual(c["human_review"]["decision"], "pending")

    def test_candidate_passes_existing_validator(self):
        c = gcfm._build_candidate(
            self._row(),
            section_label="구직(D-10) — 체류기간 연장허가",
            printed_page=101,
            excerpt="제출서류\n  ❍ ...",
            bullets=["신청서"],
            source_file_rel="docs/source-manuals/2026-05/stay_manual_2026_05.pdf",
            pdftotext_path="/usr/bin/pdftotext",
        )
        with tempfile.TemporaryDirectory() as tmp:
            d = os.path.join(tmp, "row")
            os.makedirs(d)
            with open(os.path.join(d, "candidate.json"), "w", encoding="utf-8") as f:
                json.dump(c, f, ensure_ascii=False)
            # Import the validator and run it on this candidate.
            sys.path.insert(0, SCRIPTS_DIR)
            import validate_manual_grounding_candidate as v  # noqa: E402
            errs = v._validate_one(os.path.join(d, "candidate.json"))
            self.assertEqual(errs, [], f"candidate should pass validator; got: {errs}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
