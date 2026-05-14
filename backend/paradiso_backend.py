"""Paradiso backend service.

FastAPI application exposing the routes used by the Paradiso frontend:

- GET  /
- GET  /health
- GET  /api/visas
- POST /api/ask
- POST /api/jobcodekeywords

Configuration is read from the environment. No secrets are baked in;
the service degrades gracefully when optional integrations (LLM
providers, database) are not configured and returns a clear JSON error
instead of crashing.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class UTF8JSONResponse(JSONResponse):
    # Starlette only auto-appends `charset=utf-8` to text/* media types,
    # so the default application/json response carries no charset and
    # legacy clients (older browsers, some proxies, terminal viewers)
    # may decode the UTF-8 body as latin-1 and render Korean text as
    # mojibake. JSON is always UTF-8 (RFC 8259); say so explicitly.
    media_type = "application/json; charset=utf-8"

try:  # httpx is listed in requirements.txt; guard so the file still imports
    import httpx  # type: ignore
except Exception:  # pragma: no cover - import-time guard only
    httpx = None  # type: ignore


logger = logging.getLogger("paradiso.backend")
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

OPENROUTER_API_KEY: Optional[str] = os.environ.get("OPENROUTER_API_KEY")
GROQ_API_KEY: Optional[str] = os.environ.get("GROQ_API_KEY")
LAW_API_KEY: Optional[str] = os.environ.get("LAW_API_KEY")
DATABASE_URL: Optional[str] = os.environ.get("DATABASE_URL")
SUPABASE_URL: Optional[str] = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY: Optional[str] = os.environ.get("SUPABASE_SERVICE_KEY")

OPENROUTER_MODEL: str = os.environ.get(
    "OPENROUTER_MODEL", "openrouter/auto"
)
GROQ_MODEL: str = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")

SITE_URL: str = os.environ.get("SITE_URL", "")
SITE_TITLE: str = os.environ.get("SITE_TITLE", "Paradiso")

# Optional pointer to the human-facing Paradiso frontend (e.g. the
# GitHub Pages deployment). Surfaced by GET / so that a person who hits
# the bare Railway URL on a phone is not greeted by a raw 404 detail
# blob with no hint where the actual app lives.
FRONTEND_URL: str = os.environ.get("FRONTEND_URL", "").strip()

CORS_ALLOW_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOW_ORIGINS", "*").split(",")
    if origin.strip()
] or ["*"]


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Paradiso Backend",
    version="0.1.0",
    default_response_class=UTF8JSONResponse,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class AskRequest(BaseModel):
    # Prompt aliases. Resolution order: message -> query -> question.
    # `question` is the field the Paradiso frontend currently sends; the
    # other two keep parity with curl-driven clients and earlier docs.
    message: Optional[str] = None
    query: Optional[str] = None
    question: Optional[str] = None

    # Optional metadata accepted to keep the contract stable. These fields
    # are not yet used for answer generation, but declaring them prevents
    # accidental schema rejection and documents the wire format.
    visa_code: Optional[str] = None
    visa_data: Optional[Dict[str, Any]] = None
    context: Optional[str] = None
    lang: Optional[str] = None
    consent: Optional[bool] = None
    history: Optional[List[Dict[str, Any]]] = None
    model: Optional[str] = None


class AskResponse(BaseModel):
    answer: str
    provider: str
    model: str
    grounding_used: bool = False
    grounding_sources: List[Dict[str, Any]] = Field(default_factory=list)
    visa_code_detected: Optional[str] = None
    visa_sub_code_detected: Optional[str] = None
    task_type_detected: Optional[str] = None


class JobCodeKeywordsRequest(BaseModel):
    query: str = Field(..., min_length=1)


class JobCodeKeywordsResponse(BaseModel):
    query: str
    keywords: List[str]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _providers_configured() -> Dict[str, bool]:
    return {
        "openrouter": bool(OPENROUTER_API_KEY),
        "groq": bool(GROQ_API_KEY),
        "law_api": bool(LAW_API_KEY),
        "database": bool(DATABASE_URL),
        "supabase": bool(SUPABASE_URL and SUPABASE_SERVICE_KEY),
    }


def _extract_keywords(text: str, max_keywords: int = 12) -> List[str]:
    """Best-effort keyword extraction without external dependencies.

    Splits on non-word characters, lowercases, drops short tokens and a
    small Korean/English stopword set, and de-duplicates while keeping
    insertion order.
    """
    import re

    stopwords = {
        "the", "and", "for", "with", "that", "this", "from", "into",
        "have", "has", "are", "was", "were", "you", "your", "but", "not",
        "위해", "그리고", "있는", "있습니다", "관련", "대한",
    }
    tokens = re.split(r"[^0-9A-Za-z가-힣]+", text or "")
    seen: List[str] = []
    for token in tokens:
        token = token.strip().lower()
        if not token or len(token) < 2 or token in stopwords:
            continue
        if token in seen:
            continue
        seen.append(token)
        if len(seen) >= max_keywords:
            break
    return seen


async def _call_openrouter(prompt: str, model: Optional[str] = None) -> str:
    if not OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "openrouter_not_configured",
                "message": "OPENROUTER_API_KEY is not set on the server.",
            },
        )
    if httpx is None:
        raise HTTPException(
            status_code=500,
            detail={"error": "httpx_missing", "message": "httpx is not installed."},
        )

    payload = {
        "model": model or OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    if SITE_URL:
        headers["HTTP-Referer"] = SITE_URL
    if SITE_TITLE:
        headers["X-Title"] = SITE_TITLE
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
        )
    if resp.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "openrouter_upstream_error",
                "status": resp.status_code,
                "message": resp.text[:500],
            },
        )
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "openrouter_bad_response",
                "message": f"Unexpected OpenRouter payload: {exc}",
            },
        )


async def _call_groq(prompt: str, model: Optional[str] = None) -> str:
    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "groq_not_configured",
                "message": "GROQ_API_KEY is not set on the server.",
            },
        )
    if httpx is None:
        raise HTTPException(
            status_code=500,
            detail={"error": "httpx_missing", "message": "httpx is not installed."},
        )

    payload = {
        "model": model or GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
        )
    if resp.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "groq_upstream_error",
                "status": resp.status_code,
                "message": resp.text[:500],
            },
        )
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "groq_bad_response",
                "message": f"Unexpected Groq payload: {exc}",
            },
        )


# ---------------------------------------------------------------------------
# Static visa data
# ---------------------------------------------------------------------------

DEFAULT_VISAS: List[Dict[str, Any]] = [
    {
        "code": "E-7",
        "name": "특정활동",
        "category": "취업",
        "summary": "한국 산업 수요에 맞는 특정 직업에 종사하기 위한 비자.",
    },
    {
        "code": "D-8",
        "name": "기업투자",
        "category": "투자",
        "summary": "외국인 투자기업의 경영, 관리 또는 생산기술 분야 종사자에게 발급되는 비자.",
    },
    {
        "code": "D-10",
        "name": "구직",
        "category": "구직",
        "summary": "국내 기업 구직 활동을 위한 단기 체류 비자.",
    },
    {
        "code": "F-2",
        "name": "거주",
        "category": "장기체류",
        "summary": "장기 거주 자격을 부여받은 외국인을 위한 거주 비자.",
    },
    {
        "code": "F-5",
        "name": "영주",
        "category": "영주",
        "summary": "영주권자에게 발급되는 영주 비자.",
    },
]


_VISAS_CACHE: Optional[Dict[str, Any]] = None


def _candidate_visa_paths() -> List[str]:
    """Search order for the authoritative visa JSON file.

    1. `VISA_DATA_PATH` env var (absolute path, for explicit Railway
       configuration).
    2. `backend/data/visas.json` (committed override, e.g. for tests).
    3. `<repo-root>/visa_data.json` (works for local dev and any deploy
       whose build context includes the repo root).
    """
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(here)
    paths: List[str] = []
    explicit = os.environ.get("VISA_DATA_PATH", "").strip()
    if explicit:
        paths.append(explicit)
    paths.extend(
        [
            os.path.join(here, "data", "visas.json"),
            os.path.join(repo_root, "visa_data.json"),
        ]
    )
    return paths


def _coerce_visa_list(raw: Any) -> Optional[List[Dict[str, Any]]]:
    """Accept the common shapes for a visa data file.

    Supported:
    - a JSON list of records;
    - an object with a list under one of: visas, data, records, items.
    """
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        for key in ("visas", "data", "records", "items"):
            value = raw.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return None


def _classify_source(path: str) -> str:
    """Tag where a discovered visa file came from for response metadata."""
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(here)
    if path == os.path.join(here, "data", "visas.json"):
        return "backend-data"
    if path == os.path.join(repo_root, "visa_data.json"):
        return "repo-root"
    return "explicit"


def _load_visas() -> Dict[str, Any]:
    """Load and cache the visa list.

    Returns a dict with `visas` and either a `source_type` tag (real data
    loaded) or a `warning` describing why the DEFAULT_VISAS fallback was
    used. The file is read once per process and cached in module-level
    state. `source` always exposes only a short tag, not an absolute
    path, to avoid leaking the runtime layout.
    """
    global _VISAS_CACHE
    if _VISAS_CACHE is not None:
        return _VISAS_CACHE

    last_error: Optional[str] = None
    for path in _candidate_visa_paths():
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            last_error = f"failed to read {path}: {exc}"
            logger.warning(last_error)
            continue
        records = _coerce_visa_list(raw)
        if records is None:
            last_error = (
                f"{path} did not contain a recognizable visa list shape"
            )
            logger.warning(last_error)
            continue
        source_type = _classify_source(path)
        logger.info(
            "Loaded %d visa records (source_type=%s) from %s",
            len(records),
            source_type,
            path,
        )
        _VISAS_CACHE = {
            "visas": records,
            "source": source_type,
            "source_type": source_type,
        }
        return _VISAS_CACHE

    warning = (
        "using fallback DEFAULT_VISAS because no visa data file was found"
        if last_error is None
        else f"using fallback DEFAULT_VISAS because {last_error}"
    )
    _VISAS_CACHE = {
        "visas": DEFAULT_VISAS,
        "source": "fallback",
        "source_type": "fallback",
        "warning": warning,
    }
    return _VISAS_CACHE


def _reset_visas_cache_for_tests() -> None:
    """Test hook only — clears the module-level cache."""
    global _VISAS_CACHE
    _VISAS_CACHE = None


# ---------------------------------------------------------------------------
# Manual grounding (narrow, deterministic)
# ---------------------------------------------------------------------------
#
# This is intentionally a single-file lookup, not a full RAG pipeline. Each
# supported (visa_code, procedure_type) pair must be backed by a verified
# entry in the stay_manual_grounding_2026_05.json fixture. Currently grounded:
#   - ("D-2", "체류기간 연장허가")
#   - ("D-4", "체류기간 연장허가")  # 어학연수생(D-4-1, D-4-7) only
#   - ("E-7", "체류기간 연장허가")
# Anything else falls through to the ungrounded path so behavior is unchanged
# for questions outside the verified scope.

_STAY_MANUAL_GROUNDING_FILE = "stay_manual_grounding_2026_05.json"
_GROUNDING_CACHE: Optional[Dict[str, Any]] = None


def _stay_manual_grounding_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "data", "manual_grounding", _STAY_MANUAL_GROUNDING_FILE)


def _load_stay_manual_grounding() -> Optional[Dict[str, Any]]:
    """Load the stay manual grounding fixture once per process."""
    global _GROUNDING_CACHE
    if _GROUNDING_CACHE is not None:
        return _GROUNDING_CACHE
    path = _stay_manual_grounding_path()
    if not os.path.isfile(path):
        logger.info("stay manual grounding fixture missing at %s", path)
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            _GROUNDING_CACHE = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("failed to read %s: %s", path, exc)
        return None
    return _GROUNDING_CACHE


def _reset_grounding_cache_for_tests() -> None:
    global _GROUNDING_CACHE
    _GROUNDING_CACHE = None


# Valid top-level main codes the normalizer recognizes. Used as a parsing
# oracle to disambiguate contiguous letter+digit inputs like 'd101' (D-10-1
# vs D-1-0-1) or 'd42k' (D-4-2K vs D-42-K). Two-digit forms like F-10 and
# E-10 are included to preserve the existing regression-guard behavior even
# though F-10 is not a real Korean visa category.
_VALID_MAIN_CODES: frozenset = frozenset(
    [
        "A-1", "A-2", "A-3",
        "B-1", "B-2",
        "C-1", "C-3", "C-4",
        "D-1", "D-2", "D-3", "D-4", "D-5", "D-6", "D-7", "D-8", "D-9", "D-10",
        "E-1", "E-2", "E-3", "E-4", "E-5", "E-6", "E-7", "E-8", "E-9", "E-10",
        "F-1", "F-2", "F-3", "F-4", "F-5", "F-6", "F-10",
        "G-1",
        "H-1", "H-2",
    ]
)


def _normalize_visa_code(code: Optional[str]) -> Optional[str]:
    """Normalize a visa code to the canonical 'A-N' or 'A-N-SUB' form.

    Examples (main codes):
        'd2', 'D2', 'd-2', 'D 2' -> 'D-2'
        'd10', 'D10', 'd-10', 'D 10' -> 'D-10'
        'K-ETA', 'k-eta' -> 'K-ETA' (no digits, pass through)

    Examples (sub-codes):
        'D-2-1', 'd2-1' -> 'D-2-1'
        'D-10-1', 'D10-1', 'd101' -> 'D-10-1'
        'D-4-2K', 'D4-2K', 'd42k' -> 'D-4-2K'
        'F-6-1', 'F6-1', 'f61' -> 'F-6-1'
        'E-7-4', 'E7-4', 'e74' -> 'E-7-4'

    For contiguous inputs (no separator between main and sub), the parser
    uses a static list of known main codes (_VALID_MAIN_CODES) to choose
    the longest valid main-code prefix. This is the only way to tell
    'd10' (main code D-10) apart from 'd101' (sub-code D-10-1) without
    explicit separators.

    Codes that do not start with letter+digits (e.g. K-ETA, K-STAR,
    REGION-S) pass through after strip+upper. Empty/None returns None.
    """
    if not isinstance(code, str):
        return None
    cleaned = code.strip().upper()
    if not cleaned:
        return None
    import re

    # Letter-only prefixed codes with no digits anywhere (K-ETA, K-STAR,
    # REGION-S) keep their canonical form after upper-casing.
    if not re.search(r"\d", cleaned):
        return cleaned

    # Must start with a single letter followed (optionally via separator)
    # by a digit. Anything else (e.g. a bare number, weird inputs) falls
    # through unchanged.
    head = re.match(r"^([A-Z])[\s\-]?(\d.*)$", cleaned)
    if not head:
        return cleaned
    letter = head.group(1)
    body = head.group(2)

    # Capture the first contiguous digit run, then whatever remains.
    digit_run = re.match(r"^(\d+)(.*)$", body)
    leading_digits = digit_run.group(1)
    tail = digit_run.group(2)
    # Strip any leading separator(s) between main digits and the sub part.
    tail = re.sub(r"^[\s\-]+", "", tail)

    # Choose the longest valid main-code prefix from the leading digits.
    # _VALID_MAIN_CODES is bounded to 1-2 digit forms, so iterate from 2
    # down to 1 to prefer 'D-10' over 'D-1' when both are valid.
    main_digits = leading_digits
    sub_from_digits = ""
    for prefix_len in range(min(len(leading_digits), 2), 0, -1):
        candidate = f"{letter}-{leading_digits[:prefix_len]}"
        if candidate in _VALID_MAIN_CODES:
            main_digits = leading_digits[:prefix_len]
            sub_from_digits = leading_digits[prefix_len:]
            break

    sub_raw = sub_from_digits + tail
    # Internal separators in the sub-code segment collapse to a single hyphen.
    sub_normalized = re.sub(r"[\s\-]+", "-", sub_raw)
    sub_normalized = sub_normalized.strip("-")

    if sub_normalized:
        return f"{letter}-{main_digits}-{sub_normalized}"
    return f"{letter}-{main_digits}"


def _split_visa_code(normalized: Optional[str]) -> tuple:
    """Split a normalized code into (top_visa_code, visa_sub_code).

    'D-4-2K' -> ('D-4', 'D-4-2K')
    'D-10-1' -> ('D-10', 'D-10-1')
    'D-2'    -> ('D-2', None)
    'K-ETA'  -> ('K-ETA', None)  (only one '-' segment after the letter)
    None     -> (None, None)

    A sub-code is recognized when the normalized form has three or more
    hyphen-separated segments where the first looks like 'L' and the
    second looks like a number — i.e. 'L-NN-...'. This keeps non-digit
    compound codes (K-ETA, REGION-S) from being mis-split.
    """
    if not isinstance(normalized, str) or not normalized:
        return None, None
    parts = normalized.split("-")
    if len(parts) >= 3 and len(parts[0]) == 1 and parts[1].isdigit():
        top = f"{parts[0]}-{parts[1]}"
        return top, normalized
    return normalized, None


# Visa codes for which a deterministic grounding entry exists. Used to
# bound the text-detection regex so we never claim detection for a code
# that has no backing grounding entry.
_GROUNDED_VISA_CODES: tuple = ("D-2", "D-4", "E-7")


def _detect_visa_code(payload_code: Optional[str], visa_data: Optional[Dict[str, Any]], text: str) -> Optional[str]:
    """Best-effort visa code detection (top-level only).

    Backwards-compatible wrapper around _detect_visa_codes that returns
    just the top-level visa_code, for callers that do not need sub-code
    routing. New code should call _detect_visa_codes directly.
    """
    top, _sub = _detect_visa_codes(payload_code, visa_data, text)
    return top


def _detect_visa_codes(
    payload_code: Optional[str],
    visa_data: Optional[Dict[str, Any]],
    text: str,
) -> tuple:
    """Return ``(top_visa_code, visa_sub_code)``.

    Priority: explicit ``visa_code`` -> ``visa_data.code`` -> regex match in
    text. Explicit payload values are normalized so ``d2``, ``D2``, ``d-2``
    all resolve to ``D-2`` and ``d42k``, ``D4-2K``, ``D-4-2K`` all resolve
    to ``D-4-2K`` (top ``D-4``, sub ``D-4-2K``).

    Sub-code detection is intentionally **payload-only**. Free-text
    detection still returns ``(top, None)`` even if the prompt mentions a
    sub-code in passing — sub-code routing is a binding declaration about
    *which* document list applies and must come from the caller, not from
    a free-text guess.

    Text detection is restricted to visa codes that currently have a
    verified grounding entry; codes outside that set still resolve from
    explicit payload fields but are not inferred from free-text alone.
    """
    import re

    for candidate in (payload_code, (visa_data or {}).get("code") if visa_data else None):
        if isinstance(candidate, str) and candidate.strip():
            normalized = _normalize_visa_code(candidate)
            return _split_visa_code(normalized)
    if not text:
        return None, None
    # Match "D-2", "D2", "유학(D-2)" etc. (and equivalents for D-4 / E-7),
    # case-insensitive. The 1-9 digit class avoids accidental two-digit
    # matches like 'D-22' or 'E-71'. The (?!-?\d) lookahead also avoids
    # claiming 'D-4' for a 'D-4-2' substring.
    for letter, digit in (("D", "2"), ("D", "4"), ("E", "7")):
        pattern = rf"\b{letter}[\s-]?{digit}\b(?!-?\d)"
        if re.search(pattern, text, flags=re.IGNORECASE):
            return f"{letter}-{digit}", None
    return None, None


def _detect_task_type(text: str) -> Optional[str]:
    """Detect the procedure the user is asking about from the prompt text.

    Currently only the "extension" task is recognized, because that is the
    only grounding we ship. Korean and English wording are both checked.
    """
    import re

    if not text:
        return None
    korean_signals = ("체류기간 연장", "체류 연장", "비자 연장", "연장 신청", "연장허가", "연장")
    if any(signal in text for signal in korean_signals):
        return "extension"
    # English: word-boundary match on extend/extension/renew/renewal so that
    # "extend my D-2 visa" is recognized without false-positives like
    # "extension cord".
    if re.search(r"\b(extend|extension|renew|renewal)\b", text, flags=re.IGNORECASE):
        return "extension"
    return None


def _select_grounding(
    visa_code: Optional[str],
    task_type: Optional[str],
    visa_sub_code: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Return the grounding record for the request, or None.

    The selector is sub-code-aware:

    1. If ``visa_sub_code`` is set, prefer an entry whose
       ``visa_sub_code`` matches exactly.
    2. Otherwise fall back to a "general" entry (``visa_sub_code`` is
       null) **only** when that general entry explicitly lists the
       requested sub-code in ``sub_codes_covered``. A general entry that
       does not declare coverage is treated as not covering the sub-code,
       so e.g. an E-7-4 request never silently inherits the general E-7
       document list.
    3. If ``visa_sub_code`` is not provided, only entries with
       ``visa_sub_code`` null are eligible.

    Codes outside _GROUNDED_VISA_CODES return None so unrelated visa
    categories — including any sub-code whose top-level is not yet
    grounded (D-10, F-6) — are unaffected.
    """
    if task_type != "extension":
        return None
    if visa_code not in _GROUNDED_VISA_CODES:
        return None
    bundle = _load_stay_manual_grounding()
    if not bundle:
        return None
    entries = bundle.get("groundings", []) or []

    if visa_sub_code:
        # 1. Exact sub-code match wins.
        for entry in entries:
            if (
                entry.get("visa_code") == visa_code
                and entry.get("procedure_type") == "체류기간 연장허가"
                and entry.get("visa_sub_code") == visa_sub_code
            ):
                return entry
        # 2. Fall back to a general entry only if it explicitly covers this sub-code.
        for entry in entries:
            if (
                entry.get("visa_code") == visa_code
                and entry.get("procedure_type") == "체류기간 연장허가"
                and entry.get("visa_sub_code") in (None, "")
            ):
                covered = entry.get("sub_codes_covered") or []
                if isinstance(covered, list) and visa_sub_code in covered:
                    return entry
        return None

    # 3. No sub-code supplied: only general entries are eligible.
    for entry in entries:
        if (
            entry.get("visa_code") == visa_code
            and entry.get("procedure_type") == "체류기간 연장허가"
            and entry.get("visa_sub_code") in (None, "")
        ):
            return entry
    return None


def _answer_language_instruction(lang: Optional[str]) -> str:
    """Map a request lang hint to a one-line answer-language instruction.

    The grounding content (제출서류, 출처) is Korea-specific regardless of
    answer language. Only the language the model writes the answer in
    varies.
    """
    normalized = (lang or "").strip().lower()
    if normalized == "ko":
        return "- 한국어로 답하십시오."
    if normalized == "en":
        return "- Answer in English."
    return "- Answer in the same language as the user's question."


def _build_grounded_prompt(
    user_prompt: str,
    grounding: Dict[str, Any],
    bundle: Dict[str, Any],
    lang: Optional[str] = None,
) -> str:
    """Inject Korea-specific manual context into the user prompt.

    The wording explicitly instructs the model to stay within Korean
    immigration scope and to cite the manual, which guards against generic
    global-immigration boilerplate (USCIS, Home Office, etc.) and keeps the
    answer aligned with the source. The answer language is taken from the
    request `lang` field — Korea-specific grounding is preserved regardless.
    """
    docs = grounding.get("required_documents", []) or []
    caveats = grounding.get("caveats", []) or []
    excerpt = grounding.get("source_excerpt", "") or ""
    source_title = bundle.get("source_title", "외국인체류 안내매뉴얼")
    source_date = bundle.get("source_date", "2026.5")
    issuing_body = bundle.get("issuing_body", "법무부 출입국·외국인정책본부")
    page_range = grounding.get("page_range")
    page_label = f", pp. {page_range}" if page_range else ""

    docs_block = "\n".join(f"- {item}" for item in docs)
    caveats_block = "\n".join(f"- {item}" for item in caveats)
    answer_language_line = _answer_language_instruction(lang)

    section_label = grounding.get("section") or grounding.get("visa_code", "")
    procedure_label = grounding.get("procedure_type", "체류기간 연장허가")
    return (
        "당신은 대한민국 출입국·외국인정책본부의 공식 매뉴얼을 근거로 답하는 한국 비자 안내 도우미입니다.\n"
        "아래 '참고 자료' 범위 안에서만 답하고, 다른 나라의 이민 절차나 일반적인 글로벌 이민 안내로"
        " 확장하지 마십시오. 모호한 표현 대신 한국의 출입국 제도를 구체적으로 적시하고,"
        " 매뉴얼에 없는 항목을 임의로 추가하지 마십시오. 본 매뉴얼 발췌에 포함되지 않은 다른 체류자격(비자)의"
        " 제출서류를 끌어와 답변에 섞지 마십시오.\n\n"
        f"[참고 자료] {source_title} ({source_date}) — {issuing_body}{page_label}\n"
        f"섹션: {section_label} / {procedure_label}\n\n"
        "제출서류 (매뉴얼 발췌):\n"
        f"{docs_block}\n\n"
        "유의사항:\n"
        f"{caveats_block}\n\n"
        "원문 발췌:\n"
        f"{excerpt}\n\n"
        "[사용자 질문]\n"
        f"{user_prompt}\n\n"
        "[답변 지침]\n"
        f"{answer_language_line}\n"
        "- 위 제출서류와 유의사항을 명시적으로 인용하십시오.\n"
        f"- 출처를 다음과 같이 명시하십시오: {source_title} ({source_date}), {issuing_body}.\n"
        "- 관할 출입국·외국인청/사무소/출장소가 개별 사안에 따라 서류를 추가하거나 면제할 수 있다는 점을 명시하십시오."
    )


def _grounding_source_summary(grounding: Dict[str, Any], bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Public-facing grounding metadata returned to the client.

    Keep this conservative: include only fields needed for UI attribution
    and downstream verification, not the full prompt-building payload.
    """
    return {
        "source_file": bundle.get("source_file"),
        "source_title": bundle.get("source_title"),
        "source_date": bundle.get("source_date"),
        "issuing_body": bundle.get("issuing_body"),
        "visa_code": grounding.get("visa_code"),
        "procedure_type": grounding.get("procedure_type"),
        "section": grounding.get("section"),
        "page_range": grounding.get("page_range"),
        "source_verification_status": grounding.get("source_verification_status"),
        "source_confidence": grounding.get("source_confidence"),
        "verification_note": grounding.get("verification_note"),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
async def root() -> Dict[str, Any]:
    """Service-info page for humans who hit the bare backend URL.

    The Paradiso backend is API-only; the human-facing frontend is
    served elsewhere (currently GitHub Pages). Without this route,
    FastAPI returns a bare `{"detail":"Not Found"}` for `GET /`, which
    is confusing for anyone (especially mobile users) who opens the
    Railway URL directly. Returns a small JSON descriptor instead.
    """
    return {
        "service": "paradiso-backend",
        "status": "ok",
        "message": (
            "Paradiso backend is running. "
            "Use /health, /api/visas, /api/ask."
        ),
        "frontend": FRONTEND_URL or None,
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "paradiso-backend",
        "version": app.version,
        "providers": _providers_configured(),
    }


@app.get("/api/visas")
async def list_visas() -> Dict[str, Any]:
    """Return the visa catalog.

    Response shape preserves backwards-compatibility with frontend
    consumers that read either a bare array or `{data: [...]}`:

    - `data`: list of visa records (frontend's `parse()` reads this)
    - `visas`: same list under the explicit name used by newer code
    - `count`: convenience integer
    - `warning`: present only when DEFAULT_VISAS fallback is in use
    """
    cached = _load_visas()
    visas = cached["visas"]
    payload: Dict[str, Any] = {
        "count": len(visas),
        "data": visas,
        "visas": visas,
        "source": cached.get("source", "unknown"),
        "source_type": cached.get("source_type", "unknown"),
    }
    if "warning" in cached:
        payload["warning"] = cached["warning"]
    return payload


@app.post("/api/ask", response_model=AskResponse)
async def ask(req: AskRequest) -> AskResponse:
    prompt = (req.message or req.query or req.question or "").strip()
    if not prompt:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "empty_prompt",
                "message": "Provide a non-empty 'message', 'query', or 'question'.",
            },
        )

    visa_code_detected, visa_sub_code_detected = _detect_visa_codes(
        req.visa_code, req.visa_data, prompt
    )
    task_type_detected = _detect_task_type(prompt)
    grounding = _select_grounding(
        visa_code_detected, task_type_detected, visa_sub_code_detected
    )
    grounding_sources: List[Dict[str, Any]] = []
    final_prompt = prompt
    if grounding is not None:
        bundle = _load_stay_manual_grounding() or {}
        final_prompt = _build_grounded_prompt(prompt, grounding, bundle, lang=req.lang)
        grounding_sources = [_grounding_source_summary(grounding, bundle)]

    if OPENROUTER_API_KEY:
        answer = await _call_openrouter(final_prompt, model=req.model)
        return AskResponse(
            answer=answer,
            provider="openrouter",
            model=req.model or OPENROUTER_MODEL,
            grounding_used=bool(grounding),
            grounding_sources=grounding_sources,
            visa_code_detected=visa_code_detected,
            visa_sub_code_detected=visa_sub_code_detected,
            task_type_detected=task_type_detected,
        )
    if GROQ_API_KEY:
        answer = await _call_groq(final_prompt, model=req.model)
        return AskResponse(
            answer=answer,
            provider="groq",
            model=req.model or GROQ_MODEL,
            grounding_used=bool(grounding),
            grounding_sources=grounding_sources,
            visa_code_detected=visa_code_detected,
            visa_sub_code_detected=visa_sub_code_detected,
            task_type_detected=task_type_detected,
        )

    raise HTTPException(
        status_code=503,
        detail={
            "error": "no_llm_provider_configured",
            "message": (
                "No LLM provider is configured. Set OPENROUTER_API_KEY or "
                "GROQ_API_KEY in the backend environment."
            ),
            "grounding_used": bool(grounding),
            "grounding_sources": grounding_sources,
            "visa_code_detected": visa_code_detected,
            "visa_sub_code_detected": visa_sub_code_detected,
            "task_type_detected": task_type_detected,
        },
    )


@app.post("/api/jobcodekeywords", response_model=JobCodeKeywordsResponse)
async def job_code_keywords(req: JobCodeKeywordsRequest) -> JobCodeKeywordsResponse:
    keywords = _extract_keywords(req.query)
    return JobCodeKeywordsResponse(query=req.query, keywords=keywords)


# ---------------------------------------------------------------------------
# Entrypoint helper for local runs
# ---------------------------------------------------------------------------

if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(
        "paradiso_backend:app",
        host="0.0.0.0",
        port=port,
        reload=bool(os.environ.get("RELOAD")),
    )
