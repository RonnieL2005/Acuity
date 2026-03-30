from __future__ import annotations

from typing import Iterable

from connectors.polymarket.client import PolymarketClient
from services.macro_engine.aggregation import aggregate_factor_signals
from services.macro_engine.mapping import map_market_to_factors
from services.macro_engine.relevance import score_market_relevance
from services.macro_engine.schema import FactorSignal, MarketFactorDetail, RawMarket
from utils.config import load_factor_catalog


class MacroProbabilityEngine:
    # Deterministic macro-signal pipeline:
    # Polymarket markets -> mapping -> relevance scoring -> factor aggregation.
    def __init__(
        self,
        connector: PolymarketClient | None = None,
        *,
        factor_catalog: dict | None = None,
    ) -> None:
        self.connector = connector or PolymarketClient()
        self.factor_catalog = factor_catalog or load_factor_catalog()

    def build_factor_signals(self, *, markets: Iterable[RawMarket] | None = None) -> dict[str, FactorSignal]:
        candidate_markets = list(markets) if markets is not None else self.connector.fetch_active_markets()

        scored_entries = []
        rejected_entries = []
        for market in candidate_markets:
            # Keep rejected candidates as first-class audit data so signal construction is inspectable.
            for mapping in map_market_to_factors(market, self.factor_catalog):
                score = score_market_relevance(market, mapping)
                if score.keep:
                    scored_entries.append((market, mapping, score))
                else:
                    rejected_entries.append((market, mapping, score))

        aggregated = aggregate_factor_signals(scored_entries, rejected_entries)
        return self._with_defaults(aggregated, rejected_entries)

    def _with_defaults(
        self,
        aggregated: dict[str, FactorSignal],
        rejected_entries: list[tuple[RawMarket, object, object]],
    ) -> dict[str, FactorSignal]:
        # Every configured factor gets a response, even if that response is a neutral "no signal".
        completed = dict(aggregated)
        rejected_by_factor: dict[str, list[MarketFactorDetail]] = {}
        for market, mapping, score in rejected_entries:
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

        for factor_key in self.factor_catalog.get("factors", {}):
            if factor_key in completed:
                continue
            completed[factor_key] = FactorSignal(
                factor_key=factor_key,
                factor_name=factor_key.replace("_", " ").title(),
                value=0.5,
                confidence=0.0,
                contributing_markets=[],
                explanation="No sufficiently relevant Polymarket signal was available.",
                trend=None,
                contributing_details=[],
                excluded_details=sorted(
                    rejected_by_factor.get(factor_key, []),
                    key=lambda item: item.relevance_score,
                    reverse=True,
                ),
                mapping_reason="No kept candidate passed mapping and relevance filters.",
            )
        return completed


def build_factor_signals(
    connector: PolymarketClient | None = None,
    *,
    markets: Iterable[RawMarket] | None = None,
) -> dict[str, FactorSignal]:
    engine = MacroProbabilityEngine(connector=connector)
    return engine.build_factor_signals(markets=markets)
