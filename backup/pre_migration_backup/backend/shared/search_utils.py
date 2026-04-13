import re
from typing import Iterable

from django.db.models import Q, QuerySet


QUERY_PARAM_ALIASES = ("search", "q", "query")


def get_search_query(query_params, aliases: Iterable[str] = QUERY_PARAM_ALIASES) -> str:
    for key in aliases:
        value = (query_params.get(key) or "").strip()
        if value:
            return value
    return ""


def normalize_query_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def parse_limit_offset(query_params, *, default_limit: int = 50, max_limit: int = 200) -> tuple[int, int]:
    limit_raw = query_params.get("limit")
    offset_raw = query_params.get("offset")

    try:
        limit = int(limit_raw) if limit_raw is not None else default_limit
    except (TypeError, ValueError):
        limit = default_limit
    try:
        offset = int(offset_raw) if offset_raw is not None else 0
    except (TypeError, ValueError):
        offset = 0

    limit = max(1, min(limit, max_limit))
    offset = max(0, offset)
    return limit, offset


def resolve_sort_order(query_params, *, allowed_fields: set[str], default_field: str, default_dir: str = "desc") -> str:
    sort_by = (query_params.get("sort_by") or default_field).strip()
    sort_dir = (query_params.get("sort_dir") or default_dir).strip().lower()
    if sort_by not in allowed_fields:
        sort_by = default_field
    prefix = "-" if sort_dir != "asc" else ""
    return f"{prefix}{sort_by}"


def _collapse_repeated_chars(token: str) -> str:
    # Basic typo tolerance: "deveeloper" -> "developer"
    return re.sub(r"(.)\1+", r"\1", token)


def _token_variants(token: str) -> list[str]:
    token = token.strip().lower()
    variants = {token}
    collapsed = _collapse_repeated_chars(token)
    if collapsed:
        variants.add(collapsed)
    if len(token) >= 4:
        variants.add(token[:-1])  # trailing char typo
    if len(token) >= 3:
        variants.add(token[:3])  # prefix fallback
    return [v for v in variants if v]


def _build_token_q(fields: Iterable[str], token_variants: list[str]) -> Q:
    token_q = Q()
    for field in fields:
        for variant in token_variants:
            token_q |= Q(**{f"{field}__icontains": variant})
    return token_q


def apply_keyword_search(
    qs: QuerySet,
    *,
    query: str,
    fields: Iterable[str],
    typo_tolerant: bool = True,
) -> tuple[QuerySet, str]:
    normalized = normalize_query_text(query)
    if not normalized:
        return qs, "none"

    tokens = [t for t in normalized.split(" ") if t]
    if not tokens:
        return qs, "none"

    strict_qs = qs
    for token in tokens:
        strict_qs = strict_qs.filter(_build_token_q(fields, [token]))

    if strict_qs.exists() or not typo_tolerant:
        return strict_qs, "strict"

    relaxed_qs = qs
    for token in tokens:
        relaxed_qs = relaxed_qs.filter(_build_token_q(fields, _token_variants(token)))
    return relaxed_qs, "relaxed"
