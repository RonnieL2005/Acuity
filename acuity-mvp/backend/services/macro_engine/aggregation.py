from __future__ import annotations

from datetime import datetime, timezone

from services.macro_engine.schema import FactorMapping, FactorSignal, MarketFactorDetail, RawMarket, RelevanceScore


def aggregate_factor_signals(
    market_entries: list[tuple[RawMarket, FactorMapping, RelevanceScore]],
    rejected_entries: list[tuple[RawMarket, FactorMapping, RelevanceScore]] | None = None,
) -> dict[str, FactorSignal]:
    # Multiple market candidates collapse into one factor-level signal while preserving
    # both the included contributors and the rejected alternatives for review.
    deduped: dict[tuple[str, str], tuple[RawMarket, FactorMapping, RelevanceScore]] = {}
    for market, mapping, score in market_entries:
        key = (mapping.factor_key, market.market_id)
        current = deduped.get(key)
        if current is None or score.final_score > current[2].final_score:
            deduped[key] = (market, mapping, score)

    grouped: dict[str, list[tuple[RawMarket, FactorMapping, RelevanceScore]]] = {}
    for entry in deduped.values():
        grouped.setdefault(entry[1].factor_key, []).append(entry)

    rejected_by_factor: dict[str, list[MarketFactorDetail]] = {}
    for market, mapping, score in rejected_entries or []:
        rejected_by_factor.setdefault(mapping.factor_key, []).append(
            MarketFactorDetail(
                market_id=market.market_id,
                event_id=market.event_id,
                title=market.title,
                probability=market.probability,
                mapping_type=mapping.mapping_type,
                mapping_reason=mapping.explanation,
                matched_terms=mapping.matched_terms,
                relevance_score=score.final_score,
                relevance_reason=score.reason,
                keep=score.keep,
                liquidity=market.liquidity,
                volume=market.volume,
                spread=market.spread,
            )
        )

    factor_signals: dict[str, FactorSignal] = {}
    for factor_key, entries in grouped.items():
        weighted_value = 0.0
        total_weight = 0.0
        confidence_components: list[float] = []
        contributing_markets: list[str] = []
        contribution_details: list[MarketFactorDetail] = []
        factor_name = entries[0][1].factor_name

        for market, mapping, score in entries:
            weight = score.final_score * _liquidity_weight(market) * _recency_weight(market.end_date)
            weighted_value += market.probability * weight
            total_weight += weight
            confidence_components.append((score.final_score + _recency_weight(market.end_date)) / 2.0)
            contributing_markets.append(market.title)
            contribution_details.append(
                MarketFactorDetail(
                    market_id=market.market_id,
                    event_id=market.event_id,
                    title=market.title,
                    probability=market.probability,
                    mapping_type=mapping.mapping_type,
                    mapping_reason=mapping.explanation,
                    matched_terms=mapping.matched_terms,
                    relevance_score=score.final_score,
                    relevance_reason=score.reason,
                    keep=score.keep,
                    liquidity=market.liquidity,
                    volume=market.volume,
                    spread=market.spread,
                    weight=weight,
                )
            )

        normalized_details = [
            MarketFactorDetail(**{**detail.to_dict(), "weight": (detail.weight / total_weight) if total_weight else 0.0})
            for detail in contribution_details
        ]
        value = weighted_value / total_weight if total_weight else 0.5
        confidence = sum(confidence_components) / len(confidence_components) if confidence_components else 0.0
        factor_signals[factor_key] = FactorSignal(
            factor_key=factor_key,
            factor_name=factor_name,
            value=max(0.0, min(value, 1.0)),
            confidence=max(0.0, min(confidence, 1.0)),
            contributing_markets=contributing_markets,
            explanation=f"Aggregated from {len(entries)} relevant market(s).",
            trend=_trend_label(value),
            contributing_details=sorted(normalized_details, key=lambda item: item.weight, reverse=True),
            excluded_details=sorted(
                rejected_by_factor.get(factor_key, []),
                key=lambda item: item.relevance_score,
                reverse=True,
            ),
            mapping_reason=entries[0][1].explanation,
        )

    return factor_signals


def _liquidity_weight(market: RawMarket) -> float:
    liquidity = max(market.liquidity, market.volume, 1.0)
    return min(liquidity / 50_000.0, 1.0)


def _recency_weight(end_date: str) -> float:
    if not end_date:
        return 0.6

    try:
        target = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
    except ValueError:
        return 0.6

    days_out = abs((target - datetime.now(timezone.utc)).days)
    if days_out <= 30:
        return 1.0
    if days_out <= 180:
        return 0.8
    return 0.55


def _trend_label(value: float) -> str:
    if value >= 0.65:
        return "up"
    if value <= 0.35:
        return "down"
    return "flat"
