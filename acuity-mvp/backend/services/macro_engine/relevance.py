from __future__ import annotations

import math

from services.macro_engine.schema import FactorMapping, RawMarket, RelevanceScore


DENYLIST_TERMS = {"sports", "movie", "award", "celebrity"}
MINIMUM_LIQUIDITY = 1_000.0
KEEP_THRESHOLD = 0.35


def score_market_relevance(market: RawMarket, mapping: FactorMapping) -> RelevanceScore:
    # Relevance is a weighted heuristic, not a prediction model.
    # The output explains whether a candidate is kept and why.
    text = f"{market.title} {market.description} {' '.join(market.tags)}".lower()
    if any(term in text for term in DENYLIST_TERMS):
        return RelevanceScore(
            market_id=market.market_id,
            factor_key=mapping.factor_key,
            macro_relevance=0.0,
            liquidity_score=0.0,
            clarity_score=0.0,
            noise_penalty=1.0,
            final_score=0.0,
            keep=False,
            reason="Discarded by denylist category.",
        )

    macro_relevance = 1.0 if mapping.mapping_type == "direct" else 0.6
    liquidity_base = max(market.liquidity, market.volume, market.microstructure.bid_depth + market.microstructure.ask_depth)
    liquidity_score = min(math.log10(max(liquidity_base, 1.0)) / 4.0, 1.0)
    clarity_score = min(1.0, 0.35 + 0.15 * len(mapping.matched_terms) + (0.2 if mapping.mapping_type == "direct" else 0.0))

    ambiguous_terms = ("championship", "award", "episode", "meme", "viral")
    noise_penalty = 0.15 if mapping.mapping_type == "proxy" else 0.05
    if any(term in text for term in ambiguous_terms):
        noise_penalty += 0.3
    if "?" in market.title and len(mapping.matched_terms) <= 1:
        noise_penalty += 0.1
    noise_penalty = min(noise_penalty, 1.0)

    final_score = (
        0.45 * macro_relevance
        + 0.25 * liquidity_score
        + 0.20 * clarity_score
        - 0.10 * noise_penalty
    )

    keep = liquidity_base >= MINIMUM_LIQUIDITY and final_score >= KEEP_THRESHOLD
    if liquidity_base < MINIMUM_LIQUIDITY:
        reason = "Discarded for insufficient liquidity."
    elif keep:
        reason = "Kept as a sufficiently liquid macro signal."
    else:
        reason = "Discarded because the signal is too noisy."

    return RelevanceScore(
        market_id=market.market_id,
        factor_key=mapping.factor_key,
        macro_relevance=macro_relevance,
        liquidity_score=liquidity_score,
        clarity_score=clarity_score,
        noise_penalty=noise_penalty,
        final_score=max(0.0, min(final_score, 1.0)),
        keep=keep,
        reason=reason,
    )
