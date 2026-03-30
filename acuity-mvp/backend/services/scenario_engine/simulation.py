from __future__ import annotations

import numpy as np

from services.macro_engine.schema import FactorSignal


def run_correlated_lbo_simulation(
    *,
    base_interest_rate: float,
    base_exit_multiple: float,
    base_exit_ebitda: float,
    entry_ebitda: float,
    entry_multiple: float,
    initial_debt: float,
    hold_period_years: int,
    iterations: int,
    macro_volatility_scale: float,
    factor_signals: dict[str, FactorSignal] | None = None,
) -> dict[str, np.ndarray | float | dict[str, object]]:
    np.random.seed(42)

    # We snapshot assumptions before and after macro adjustments so the simulation remains debuggable.
    base_assumptions = _build_assumption_snapshot(
        base_interest_rate=base_interest_rate,
        base_exit_multiple=base_exit_multiple,
        base_exit_ebitda=base_exit_ebitda,
        macro_volatility_scale=macro_volatility_scale,
    )
    adjusted_inputs = _apply_factor_shifts(
        base_interest_rate=base_interest_rate,
        base_exit_multiple=base_exit_multiple,
        base_exit_ebitda=base_exit_ebitda,
        macro_volatility_scale=macro_volatility_scale,
        factor_signals=factor_signals or {},
    )

    # Correlated draws already exist here; the next upgrade path is to externalize this matrix into config.
    correlation_matrix = np.array(
        [
            [1.0, -0.45, -0.30],
            [-0.45, 1.0, 0.55],
            [-0.30, 0.55, 1.0],
        ]
    )
    cholesky = np.linalg.cholesky(correlation_matrix)
    uncorrelated = np.random.normal(size=(3, iterations))
    correlated = cholesky @ uncorrelated

    rate_shocks = correlated[0]
    multiple_shocks = correlated[1]
    ebitda_shocks = correlated[2]

    interest_rates = np.clip(
        adjusted_inputs["base_interest_rate"] + rate_shocks * (0.0125 * adjusted_inputs["macro_volatility_scale"]),
        0.01,
        0.25,
    )
    exit_multiples = np.clip(
        adjusted_inputs["base_exit_multiple"] + multiple_shocks * (1.10 * adjusted_inputs["macro_volatility_scale"]),
        4.0,
        20.0,
    )
    exit_ebitdas = np.clip(
        adjusted_inputs["base_exit_ebitda"] + ebitda_shocks * (2.0 * adjusted_inputs["macro_volatility_scale"]),
        0.25 * adjusted_inputs["base_exit_ebitda"],
        3.0 * adjusted_inputs["base_exit_ebitda"],
    )

    purchase_price = entry_ebitda * entry_multiple
    initial_equity = max(purchase_price - initial_debt, 1e-6)

    annual_ebitda_path = np.linspace(entry_ebitda, 1.0, hold_period_years + 1)[1:, None] * exit_ebitdas
    annual_ebitda_path = annual_ebitda_path / max(adjusted_inputs["base_exit_ebitda"], 1e-6)

    cash_available_for_debt = np.maximum(annual_ebitda_path * 0.45, 0.0)
    cumulative_paydown = np.minimum(initial_debt, np.cumsum(cash_available_for_debt, axis=0))
    ending_debt = np.maximum(initial_debt - cumulative_paydown[-1], 0.0)

    exit_enterprise_values = exit_ebitdas * exit_multiples
    exit_equity_values = np.maximum(exit_enterprise_values - ending_debt, 0.0)
    irrs = np.where(
        exit_equity_values > 0.0,
        (exit_equity_values / initial_equity) ** (1.0 / hold_period_years) - 1.0,
        -1.0,
    )

    return {
        "interest_rates": interest_rates,
        "exit_multiples": exit_multiples,
        "exit_ebitdas": exit_ebitdas,
        "annual_ebitda_path": annual_ebitda_path,
        "ending_debt": ending_debt,
        "exit_equity_values": exit_equity_values,
        "irrs": irrs,
        "initial_equity": initial_equity,
        "assumption_debug": _build_assumption_debug(
            base_assumptions=base_assumptions,
            adjusted_inputs=adjusted_inputs,
            correlation_matrix=correlation_matrix,
        ),
    }


def _apply_factor_shifts(
    *,
    base_interest_rate: float,
    base_exit_multiple: float,
    base_exit_ebitda: float,
    macro_volatility_scale: float,
    factor_signals: dict[str, FactorSignal],
) -> dict[str, float | dict[str, float]]:
    # Scenario logic consumes generic factor signals only.
    # It deliberately knows nothing about Polymarket as a data source.
    def intensity(key: str) -> float:
        signal = factor_signals.get(key)
        if signal is None:
            return 0.0
        return (signal.value - 0.5) * signal.confidence

    fed_policy = intensity("fed_policy")
    recession_risk = max(intensity("recession_risk"), 0.0)
    oil_shock = max(intensity("oil_shock"), 0.0)
    multiple_compression = max(intensity("exit_multiple_compression"), 0.0)
    credit_stress = max(intensity("credit_stress"), 0.0)

    adjusted_rate = base_interest_rate - 0.012 * fed_policy + 0.010 * credit_stress
    adjusted_multiple = base_exit_multiple + 0.7 * fed_policy - 1.0 * multiple_compression - 0.4 * recession_risk
    adjusted_ebitda = base_exit_ebitda * (1.0 - 0.12 * recession_risk - 0.08 * oil_shock)
    adjusted_volatility = macro_volatility_scale * (
        1.0 + 0.30 * recession_risk + 0.25 * credit_stress + 0.20 * oil_shock
    )

    return {
        "base_interest_rate": max(adjusted_rate, 0.01),
        "base_exit_multiple": max(adjusted_multiple, 4.0),
        "base_exit_ebitda": max(adjusted_ebitda, 0.25),
        "macro_volatility_scale": max(adjusted_volatility, 0.25),
        "factor_intensities": {
            "fed_policy": fed_policy,
            "recession_risk": recession_risk,
            "oil_shock": oil_shock,
            "exit_multiple_compression": multiple_compression,
            "credit_stress": credit_stress,
        },
    }


def _build_assumption_snapshot(
    *,
    base_interest_rate: float,
    base_exit_multiple: float,
    base_exit_ebitda: float,
    macro_volatility_scale: float,
) -> dict[str, float]:
    return {
        "interest_rate_mean": base_interest_rate,
        "interest_rate_std": 0.0125 * macro_volatility_scale,
        "exit_multiple_mean": base_exit_multiple,
        "exit_multiple_std": 1.10 * macro_volatility_scale,
        "exit_ebitda_mean": base_exit_ebitda,
        "exit_ebitda_std": 2.0 * macro_volatility_scale,
        "macro_volatility_scale": macro_volatility_scale,
    }


def _build_assumption_debug(
    *,
    base_assumptions: dict[str, float],
    adjusted_inputs: dict[str, float | dict[str, float]],
    correlation_matrix: np.ndarray,
) -> dict[str, object]:
    # This block is returned to the API so authors can inspect exactly what changed and why.
    adjusted_assumptions = _build_assumption_snapshot(
        base_interest_rate=float(adjusted_inputs["base_interest_rate"]),
        base_exit_multiple=float(adjusted_inputs["base_exit_multiple"]),
        base_exit_ebitda=float(adjusted_inputs["base_exit_ebitda"]),
        macro_volatility_scale=float(adjusted_inputs["macro_volatility_scale"]),
    )
    return {
        "base_assumptions": base_assumptions,
        "macro_adjustments": {
            key: adjusted_assumptions[key] - base_assumptions[key]
            for key in (
                "interest_rate_mean",
                "interest_rate_std",
                "exit_multiple_mean",
                "exit_multiple_std",
                "exit_ebitda_mean",
                "exit_ebitda_std",
            )
        },
        "adjusted_assumptions": adjusted_assumptions,
        "factor_intensities": adjusted_inputs["factor_intensities"],
        "correlation_matrix": correlation_matrix.tolist(),
    }
