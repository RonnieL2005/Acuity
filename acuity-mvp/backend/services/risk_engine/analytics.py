from __future__ import annotations

import numpy as np

from models.api import (
    FactorSignalResponse,
    MacroAdjustmentResponse,
    MarketExplanationResponse,
    SimulationAssumptionsResponse,
    SimulationDebugResponse,
    SimulationResponse,
)
from services.macro_engine.schema import FactorSignal


def evaluate_debt_waterfall(
    *,
    annual_ebitda_path: np.ndarray,
    initial_debt: float,
    interest_rates: np.ndarray,
) -> dict[str, np.ndarray | float]:
    years, iterations = annual_ebitda_path.shape
    required_amortization = initial_debt / years if years else 0.0
    debt_balance = np.full(iterations, initial_debt, dtype=float)
    minimum_cash = np.full(iterations, 1.0, dtype=float)

    fccr_schedule = np.zeros((years, iterations), dtype=float)
    breach_matrix = np.zeros((years, iterations), dtype=bool)

    for year in range(years):
        interest_expense = debt_balance * interest_rates
        fixed_charges = interest_expense + required_amortization + minimum_cash
        ebitda = annual_ebitda_path[year]
        fccr = np.divide(
            ebitda - 0.15 * ebitda,
            np.maximum(fixed_charges, 1e-6),
        )
        fccr_schedule[year] = fccr
        breach_matrix[year] = fccr < 1.15

        paydown_capacity = np.maximum(ebitda * 0.40 - interest_expense, 0.0)
        debt_balance = np.maximum(debt_balance - np.minimum(paydown_capacity, required_amortization), 0.0)

    breached_runs = breach_matrix.any(axis=0)
    prob_covenant_breach = float(np.mean(breached_runs) * 100.0)

    return {
        "fccr_schedule": fccr_schedule,
        "breached_runs": breached_runs,
        "prob_covenant_breach": prob_covenant_breach,
    }


def summarize_simulation(
    *,
    irrs: np.ndarray,
    exit_equity_values: np.ndarray,
    prob_covenant_breach: float,
    macro_volatility_regime: str,
    tagged_inputs: list,
    macro_factors: dict[str, FactorSignal],
    simulation_debug: dict[str, object],
) -> SimulationResponse:
    # Response shaping happens here so API payload construction stays separate from simulation math.
    return SimulationResponse(
        mean_irr=float(np.mean(irrs) * 100.0),
        prob_irr_less_than_10=float(np.mean(irrs < 0.10) * 100.0),
        prob_covenant_breach=float(prob_covenant_breach),
        mean_exit_equity_value=float(np.mean(exit_equity_values)),
        p5_exit_equity_value=float(np.percentile(exit_equity_values, 5)),
        p95_exit_equity_value=float(np.percentile(exit_equity_values, 95)),
        macro_volatility_regime=macro_volatility_regime,
        tagged_inputs=tagged_inputs,
        macro_factors=[
            FactorSignalResponse(
                factor_key=signal.factor_key,
                factor_name=signal.factor_name,
                value=round(signal.value, 4),
                confidence=round(signal.confidence, 4),
                explanation=signal.explanation,
                contributing_markets=signal.contributing_markets,
                contributing_details=[
                    MarketExplanationResponse(**detail.to_dict()) for detail in signal.contributing_details
                ],
                excluded_candidates=[
                    MarketExplanationResponse(**detail.to_dict()) for detail in signal.excluded_details
                ],
                mapping_reason=signal.mapping_reason,
                trend=signal.trend,
            )
            for signal in sorted(macro_factors.values(), key=lambda item: item.confidence, reverse=True)
        ],
        simulation_debug=SimulationDebugResponse(
            base_assumptions=SimulationAssumptionsResponse(**simulation_debug["base_assumptions"]),
            macro_adjustments=MacroAdjustmentResponse(**simulation_debug["macro_adjustments"]),
            adjusted_assumptions=SimulationAssumptionsResponse(**simulation_debug["adjusted_assumptions"]),
            factor_intensities=simulation_debug["factor_intensities"],
            correlation_matrix=simulation_debug["correlation_matrix"],
        ),
    )
