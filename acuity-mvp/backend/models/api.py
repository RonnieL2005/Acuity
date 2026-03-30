from typing import List

from pydantic import BaseModel, Field


# API-facing models only. These are the contracts consumed by the frontend and external reviewers.
class TaggedCellInput(BaseModel):
    tag: str = Field(..., examples=["base_interest_rate"])
    address: str = Field(..., examples=["Inputs!B7"])
    value: float = Field(..., examples=[0.055])


class MarketExplanationResponse(BaseModel):
    market_id: str
    event_id: str
    title: str
    probability: float
    mapping_type: str
    mapping_reason: str
    matched_terms: List[str] = Field(default_factory=list)
    relevance_score: float
    relevance_reason: str
    keep: bool
    liquidity: float
    volume: float
    spread: float
    weight: float = 0.0


class FactorSignalResponse(BaseModel):
    factor_key: str
    factor_name: str
    value: float
    confidence: float
    explanation: str
    contributing_markets: List[str] = Field(default_factory=list)
    contributing_details: List[MarketExplanationResponse] = Field(default_factory=list)
    excluded_candidates: List[MarketExplanationResponse] = Field(default_factory=list)
    mapping_reason: str = ""
    trend: str | None = None


class MacroFactorsResponse(BaseModel):
    factors: List[FactorSignalResponse]


class SimulationAssumptionsResponse(BaseModel):
    interest_rate_mean: float
    interest_rate_std: float
    exit_multiple_mean: float
    exit_multiple_std: float
    exit_ebitda_mean: float
    exit_ebitda_std: float
    macro_volatility_scale: float


class MacroAdjustmentResponse(BaseModel):
    interest_rate_mean: float
    interest_rate_std: float
    exit_multiple_mean: float
    exit_multiple_std: float
    exit_ebitda_mean: float
    exit_ebitda_std: float


class SimulationDebugResponse(BaseModel):
    base_assumptions: SimulationAssumptionsResponse
    macro_adjustments: MacroAdjustmentResponse
    adjusted_assumptions: SimulationAssumptionsResponse
    factor_intensities: dict[str, float] = Field(default_factory=dict)
    correlation_matrix: List[List[float]] = Field(default_factory=list)


class SimulationRequest(BaseModel):
    deal_name: str = Field(..., examples=["Project Atlas"])
    firm_name: str = Field(..., examples=["North Peak Capital"])
    base_interest_rate: float = Field(..., ge=0.0, examples=[0.055])
    base_exit_multiple: float = Field(..., gt=0.0, examples=[10.5])
    base_exit_ebitda: float = Field(..., gt=0.0, examples=[18.0])
    entry_ebitda: float = Field(default=12.0, gt=0.0)
    entry_multiple: float = Field(default=10.0, gt=0.0)
    initial_debt: float = Field(default=60.0, ge=0.0)
    hold_period_years: int = Field(default=5, ge=1, le=10)
    iterations: int = Field(default=10000, ge=1000, le=50000)
    tagged_inputs: List[TaggedCellInput] = Field(default_factory=list)


class SimulationResponse(BaseModel):
    mean_irr: float
    prob_irr_less_than_10: float
    prob_covenant_breach: float
    mean_exit_equity_value: float
    p5_exit_equity_value: float
    p95_exit_equity_value: float
    macro_volatility_regime: str
    tagged_inputs: List[TaggedCellInput]
    macro_factors: List[FactorSignalResponse] = Field(default_factory=list)
    simulation_debug: SimulationDebugResponse
