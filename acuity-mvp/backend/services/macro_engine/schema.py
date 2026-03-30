from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class MarketMicrostructure:
    best_bid: float = 0.0
    best_ask: float = 0.0
    spread: float = 0.0
    bid_depth: float = 0.0
    ask_depth: float = 0.0
    midpoint: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(slots=True)
class RawMarket:
    market_id: str
    event_id: str
    title: str
    description: str
    outcomes: list[str] = field(default_factory=list)
    outcome_prices: list[float] = field(default_factory=list)
    token_ids: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    category: str = ""
    probability: float = 0.5
    liquidity: float = 0.0
    volume: float = 0.0
    spread: float = 0.0
    end_date: str = ""
    clob_token_id: str = ""
    market_slug: str = ""
    image_url: str = ""
    microstructure: MarketMicrostructure = field(default_factory=MarketMicrostructure)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["microstructure"] = self.microstructure.to_dict()
        return payload


@dataclass(slots=True)
class FactorMapping:
    factor_key: str
    factor_name: str
    mapping_type: str
    matched_terms: list[str]
    explanation: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class RelevanceScore:
    market_id: str
    factor_key: str
    macro_relevance: float
    liquidity_score: float
    clarity_score: float
    noise_penalty: float
    final_score: float
    keep: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class MarketFactorDetail:
    market_id: str
    event_id: str
    title: str
    probability: float
    mapping_type: str
    mapping_reason: str
    matched_terms: list[str]
    relevance_score: float
    relevance_reason: str
    keep: bool
    liquidity: float
    volume: float
    spread: float
    weight: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class FactorSignal:
    factor_key: str
    factor_name: str
    value: float
    confidence: float
    contributing_markets: list[str]
    explanation: str
    trend: str | None = None
    contributing_details: list[MarketFactorDetail] = field(default_factory=list)
    excluded_details: list[MarketFactorDetail] = field(default_factory=list)
    mapping_reason: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
