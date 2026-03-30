from __future__ import annotations

import re
from typing import Any

from services.macro_engine.schema import FactorMapping, RawMarket
from utils.config import load_factor_catalog


REJECT_CATEGORIES = {
    "sports",
    "nba",
    "nfl",
    "mlb",
    "soccer",
    "entertainment",
    "celebrity",
    "movie",
    "tv",
}


def map_market_to_factors(
    market: RawMarket,
    factor_catalog: dict[str, Any] | None = None,
) -> list[FactorMapping]:
    # Rule-based mapping is intentionally transparent: co-authors can review keywords/patterns
    # directly instead of inferring behavior from a learned model.
    if _is_rejected_market(market):
        return []

    catalog = factor_catalog or load_factor_catalog()
    factor_defs: dict[str, Any] = catalog.get("factors", {})
    haystack = " ".join(
        [market.title.lower(), market.description.lower(), " ".join(tag.lower() for tag in market.tags)]
    )

    mappings: list[FactorMapping] = []
    for factor_key, definition in factor_defs.items():
        direct_matches = _collect_matches(
            haystack,
            definition.get("direct_keywords", []),
            definition.get("direct_patterns", []),
        )
        proxy_matches = _collect_matches(
            haystack,
            definition.get("proxy_keywords", []),
            definition.get("proxy_patterns", []),
        )

        if direct_matches:
            mappings.append(
                FactorMapping(
                    factor_key=factor_key,
                    factor_name=factor_key.replace("_", " ").title(),
                    mapping_type="direct",
                    matched_terms=sorted(direct_matches),
                    explanation=f"Direct macro match via {', '.join(sorted(direct_matches)[:3])}.",
                )
            )
        elif proxy_matches:
            mappings.append(
                FactorMapping(
                    factor_key=factor_key,
                    factor_name=factor_key.replace("_", " ").title(),
                    mapping_type="proxy",
                    matched_terms=sorted(proxy_matches),
                    explanation=f"Proxy macro match via {', '.join(sorted(proxy_matches)[:3])}.",
                )
            )

    return mappings


def _collect_matches(text: str, keywords: list[str], patterns: list[str]) -> set[str]:
    matches = {keyword for keyword in keywords if keyword.lower() in text}
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            matches.add(pattern)
    return matches


def _is_rejected_market(market: RawMarket) -> bool:
    category = market.category.lower()
    if any(blocked in category for blocked in REJECT_CATEGORIES):
        return True

    tag_text = " ".join(market.tags).lower()
    if any(blocked in tag_text for blocked in REJECT_CATEGORIES):
        return True

    title = market.title.lower()
    return any(title.startswith(prefix) for prefix in ("who will win", "final score", "box office"))
