CREATE TABLE firms (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE deals (
    id BIGSERIAL PRIMARY KEY,
    firm_id BIGINT NOT NULL REFERENCES firms(id),
    name TEXT NOT NULL,
    entry_ebitda NUMERIC(14,2),
    entry_multiple NUMERIC(8,2),
    initial_debt NUMERIC(14,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE simulations (
    id BIGSERIAL PRIMARY KEY,
    deal_id BIGINT NOT NULL REFERENCES deals(id),
    iteration_count INTEGER NOT NULL,
    hold_period_years INTEGER NOT NULL,
    base_interest_rate NUMERIC(8,5) NOT NULL,
    base_exit_multiple NUMERIC(8,2) NOT NULL,
    base_exit_ebitda NUMERIC(14,2) NOT NULL,
    macro_volatility_regime TEXT NOT NULL,
    tagged_input_snapshot JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE risk_scores (
    id BIGSERIAL PRIMARY KEY,
    simulation_id BIGINT NOT NULL UNIQUE REFERENCES simulations(id),
    mean_irr NUMERIC(8,4) NOT NULL,
    prob_irr_less_than_10 NUMERIC(8,4) NOT NULL,
    prob_covenant_breach NUMERIC(8,4) NOT NULL,
    mean_exit_equity_value NUMERIC(14,2) NOT NULL,
    p5_exit_equity_value NUMERIC(14,2) NOT NULL,
    p95_exit_equity_value NUMERIC(14,2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
