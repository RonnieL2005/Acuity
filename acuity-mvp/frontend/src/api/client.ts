export type TaggedCellInput = {
  tag: string;
  address: string;
  value: number;
};

export type SimulationRequest = {
  deal_name: string;
  firm_name: string;
  base_interest_rate: number;
  base_exit_multiple: number;
  base_exit_ebitda: number;
  entry_ebitda: number;
  entry_multiple: number;
  initial_debt: number;
  hold_period_years: number;
  iterations: number;
  tagged_inputs: TaggedCellInput[];
};

export type MarketExplanation = {
  market_id: string;
  event_id: string;
  title: string;
  probability: number;
  mapping_type: string;
  mapping_reason: string;
  matched_terms: string[];
  relevance_score: number;
  relevance_reason: string;
  keep: boolean;
  liquidity: number;
  volume: number;
  spread: number;
  weight: number;
};

export type FactorSignal = {
  factor_key: string;
  factor_name: string;
  value: number;
  confidence: number;
  explanation: string;
  contributing_markets: string[];
  contributing_details: MarketExplanation[];
  excluded_candidates: MarketExplanation[];
  mapping_reason: string;
  trend: string | null;
};

export type SimulationAssumptions = {
  interest_rate_mean: number;
  interest_rate_std: number;
  exit_multiple_mean: number;
  exit_multiple_std: number;
  exit_ebitda_mean: number;
  exit_ebitda_std: number;
  macro_volatility_scale: number;
};

export type MacroAdjustmentSet = {
  interest_rate_mean: number;
  interest_rate_std: number;
  exit_multiple_mean: number;
  exit_multiple_std: number;
  exit_ebitda_mean: number;
  exit_ebitda_std: number;
};

export type SimulationDebug = {
  base_assumptions: SimulationAssumptions;
  macro_adjustments: MacroAdjustmentSet;
  adjusted_assumptions: SimulationAssumptions;
  factor_intensities: Record<string, number>;
  correlation_matrix: number[][];
};

export type SimulationResponse = {
  mean_irr: number;
  prob_irr_less_than_10: number;
  prob_covenant_breach: number;
  mean_exit_equity_value: number;
  p5_exit_equity_value: number;
  p95_exit_equity_value: number;
  macro_volatility_regime: string;
  tagged_inputs: TaggedCellInput[];
  macro_factors: FactorSignal[];
  simulation_debug: SimulationDebug;
};

export type MacroFactorsResponse = {
  factors: FactorSignal[];
};

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  (typeof window !== "undefined" && window.location.hostname === "localhost"
    ? "http://localhost:8000"
    : `${window.location.origin.replace(/\/$/, "")}`);

// Thin frontend client for the two backend surfaces:
// 1. full simulation output
// 2. standalone macro factor inspection
export async function runSimulation(payload: SimulationRequest): Promise<SimulationResponse> {
  const response = await fetch(`${API_BASE_URL}/simulate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(`Simulation failed with status ${response.status}`);
  }

  return response.json();
}

export async function fetchMacroFactors(): Promise<MacroFactorsResponse> {
  const response = await fetch(`${API_BASE_URL}/macro/factors`);

  if (!response.ok) {
    throw new Error(`Macro factor fetch failed with status ${response.status}`);
  }

  return response.json();
}
