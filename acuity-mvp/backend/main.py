from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from connectors.polymarket.client import PolymarketClient
from models import MacroFactorsResponse, SimulationRequest, SimulationResponse
from services.macro_engine.engine import MacroProbabilityEngine
from services.risk_engine.analytics import evaluate_debt_waterfall, summarize_simulation
from services.scenario_engine.simulation import run_correlated_lbo_simulation
from workers.oracle_mock import get_macro_volatility_snapshot


# FastAPI entrypoint for the Acuity backend. This layer stays thin:
# it orchestrates macro signal construction, simulation, and response shaping.
app = FastAPI(title="Acuity MVP", version="0.1.0")
macro_engine = MacroProbabilityEngine(
    connector=PolymarketClient(debug_dir="/Users/nate/Acq/Acuity/acuity-mvp/backend/debug_samples/polymarket")
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/macro/factors", response_model=MacroFactorsResponse)
def get_macro_factors() -> MacroFactorsResponse:
    # If Polymarket is temporarily unavailable, return neutral defaults instead of failing the UI.
    try:
        signals = macro_engine.build_factor_signals()
    except Exception:
        signals = macro_engine.build_factor_signals(markets=[])

    return MacroFactorsResponse(
        factors=[
            {
                "factor_key": signal.factor_key,
                "factor_name": signal.factor_name,
                "value": signal.value,
                "confidence": signal.confidence,
                "explanation": signal.explanation,
                "contributing_markets": signal.contributing_markets,
                "contributing_details": [detail.to_dict() for detail in signal.contributing_details],
                "excluded_candidates": [detail.to_dict() for detail in signal.excluded_details],
                "mapping_reason": signal.mapping_reason,
                "trend": signal.trend,
            }
            for signal in sorted(signals.values(), key=lambda item: item.confidence, reverse=True)
        ]
    )


@app.post("/simulate", response_model=SimulationResponse)
def simulate(request: SimulationRequest) -> SimulationResponse:
    # The oracle mock supplies the volatility regime; the macro engine supplies directional factor views.
    oracle_snapshot = get_macro_volatility_snapshot(request.base_interest_rate)
    try:
        factor_signals = macro_engine.build_factor_signals()
    except Exception:
        factor_signals = macro_engine.build_factor_signals(markets=[])

    simulation = run_correlated_lbo_simulation(
        base_interest_rate=request.base_interest_rate,
        base_exit_multiple=request.base_exit_multiple,
        base_exit_ebitda=request.base_exit_ebitda,
        entry_ebitda=request.entry_ebitda,
        entry_multiple=request.entry_multiple,
        initial_debt=request.initial_debt,
        hold_period_years=request.hold_period_years,
        iterations=request.iterations,
        macro_volatility_scale=float(oracle_snapshot["volatility_scale"]),
        factor_signals=factor_signals,
    )

    waterfall = evaluate_debt_waterfall(
        annual_ebitda_path=simulation["annual_ebitda_path"],
        initial_debt=request.initial_debt,
        interest_rates=simulation["interest_rates"],
    )

    return summarize_simulation(
        irrs=simulation["irrs"],
        exit_equity_values=simulation["exit_equity_values"],
        prob_covenant_breach=float(waterfall["prob_covenant_breach"]),
        macro_volatility_regime=str(oracle_snapshot["regime"]),
        tagged_inputs=request.tagged_inputs,
        macro_factors=factor_signals,
        simulation_debug=simulation["assumption_debug"],
    )
