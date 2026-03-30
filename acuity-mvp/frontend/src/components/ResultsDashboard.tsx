import React from "react";
import { FactorSignal, SimulationResponse } from "../api/client";

type ResultsDashboardProps = {
  result: SimulationResponse | null;
  macroFactors: FactorSignal[];
};

const formatPercent = (value: number) => `${value.toFixed(1)}%`;
const formatMoney = (value: number) => `$${value.toFixed(1)}M`;
const formatProbability = (value: number) => `${(value * 100).toFixed(0)}%`;
const formatDelta = (value: number, digits = 2) => `${value >= 0 ? "+" : ""}${value.toFixed(digits)}`;

export default function ResultsDashboard({ result, macroFactors }: ResultsDashboardProps) {
  // Show the highest-confidence factors first so the dashboard emphasizes the clearest macro signals.
  const visibleFactors = macroFactors
    .filter((factor) => factor.confidence > 0)
    .sort((left, right) => right.confidence - left.confidence)
    .slice(0, 6);

  return (
    <aside className="rounded-3xl border border-slate-800 bg-gradient-to-br from-slate-900 to-slate-950 p-6">
      <h2 className="text-xl font-medium">Risk Output</h2>
      {!result ? (
        <p className="mt-4 text-sm text-slate-400">Run a simulation to populate the IRR and covenant metrics.</p>
      ) : (
        <div className="mt-6 space-y-4">
          <MetricCard label="Mean IRR" value={formatPercent(result.mean_irr)} />
          <MetricCard label="Probability IRR < 10%" value={formatPercent(result.prob_irr_less_than_10)} />
          <MetricCard label="Probability Covenant Breach" value={formatPercent(result.prob_covenant_breach)} />
          <MetricCard label="Mean Exit Equity" value={formatMoney(result.mean_exit_equity_value)} />
          <MetricCard
            label="Exit Equity Range (P5 / P95)"
            value={`${formatMoney(result.p5_exit_equity_value)} / ${formatMoney(result.p95_exit_equity_value)}`}
          />
          <MetricCard label="Macro Volatility Regime" value={result.macro_volatility_regime} />
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
            <p className="text-sm text-slate-400">Assumption Adjustments</p>
            <div className="mt-3 space-y-2 text-sm text-slate-300">
              <AssumptionRow
                label="Interest Rate Mean / Std"
                base={`${(result.simulation_debug.base_assumptions.interest_rate_mean * 100).toFixed(2)}% / ${(result.simulation_debug.base_assumptions.interest_rate_std * 100).toFixed(2)}%`}
                delta={`${formatDelta(result.simulation_debug.macro_adjustments.interest_rate_mean * 100)} pts / ${formatDelta(result.simulation_debug.macro_adjustments.interest_rate_std * 100)} pts`}
                adjusted={`${(result.simulation_debug.adjusted_assumptions.interest_rate_mean * 100).toFixed(2)}% / ${(result.simulation_debug.adjusted_assumptions.interest_rate_std * 100).toFixed(2)}%`}
              />
              <AssumptionRow
                label="Exit Multiple Mean / Std"
                base={`${result.simulation_debug.base_assumptions.exit_multiple_mean.toFixed(2)}x / ${result.simulation_debug.base_assumptions.exit_multiple_std.toFixed(2)}x`}
                delta={`${formatDelta(result.simulation_debug.macro_adjustments.exit_multiple_mean)}x / ${formatDelta(result.simulation_debug.macro_adjustments.exit_multiple_std)}x`}
                adjusted={`${result.simulation_debug.adjusted_assumptions.exit_multiple_mean.toFixed(2)}x / ${result.simulation_debug.adjusted_assumptions.exit_multiple_std.toFixed(2)}x`}
              />
              <AssumptionRow
                label="EBITDA Mean / Std"
                base={`${formatMoney(result.simulation_debug.base_assumptions.exit_ebitda_mean)} / ${formatMoney(result.simulation_debug.base_assumptions.exit_ebitda_std)}`}
                delta={`${formatDelta(result.simulation_debug.macro_adjustments.exit_ebitda_mean)}M / ${formatDelta(result.simulation_debug.macro_adjustments.exit_ebitda_std)}M`}
                adjusted={`${formatMoney(result.simulation_debug.adjusted_assumptions.exit_ebitda_mean)} / ${formatMoney(result.simulation_debug.adjusted_assumptions.exit_ebitda_std)}`}
              />
            </div>
          </div>
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
            <p className="text-sm text-slate-400">Macro Probability Layer</p>
            {visibleFactors.length === 0 ? (
              <p className="mt-2 text-sm text-slate-500">No priced macro signals available.</p>
            ) : (
              <div className="mt-3 space-y-3">
                {visibleFactors.map((factor) => (
                  <div key={factor.factor_key} className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-3">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-medium text-slate-100">{factor.factor_name}</p>
                      <p className="text-sm text-cyan-300">{formatProbability(factor.value)}</p>
                    </div>
                    <div className="mt-1 flex items-center justify-between gap-3 text-xs text-slate-400">
                      <span>Confidence {formatProbability(factor.confidence)}</span>
                      <span>{factor.trend ?? "stable"}</span>
                    </div>
                    <p className="mt-2 text-xs text-slate-500">{factor.mapping_reason || factor.explanation}</p>
                    {factor.contributing_details[0] ? (
                      <div className="mt-2 text-xs text-slate-400">
                        <p>
                          Top market: {factor.contributing_details[0].title} ({formatProbability(factor.contributing_details[0].probability)})
                        </p>
                        <p>
                          Relevance {formatProbability(factor.contributing_details[0].relevance_score)} | Weight {formatProbability(factor.contributing_details[0].weight)}
                        </p>
                      </div>
                    ) : null}
                    {factor.excluded_candidates.length > 0 ? (
                      <p className="mt-2 text-[11px] text-slate-500">
                        Excluded candidates: {factor.excluded_candidates.length}. Top reject reason: {factor.excluded_candidates[0].relevance_reason}
                      </p>
                    ) : null}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </aside>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
      <p className="text-sm text-slate-400">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-cyan-300">{value}</p>
    </div>
  );
}

function AssumptionRow({ label, base, delta, adjusted }: { label: string; base: string; delta: string; adjusted: string }) {
  return (
    <div className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-3">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{label}</p>
      <p className="mt-2 text-xs text-slate-400">Base {base}</p>
      <p className="mt-1 text-xs text-amber-300">Adjustment {delta}</p>
      <p className="mt-1 text-sm text-cyan-300">Final {adjusted}</p>
    </div>
  );
}
