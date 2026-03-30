# Macro Layer Note

This note is intended to help reviewers and co-authors understand the current system
without reading every file in sequence.

## File Tree

```text
backend/
  main.py
  config/
    factors.yaml
  connectors/
    polymarket/
      client.py
  debug_samples/
    polymarket/
  docs/
    macro_layer_note.md
  models/
    __init__.py
    api.py
  services/
    macro_engine/
      aggregation.py
      engine.py
      mapping.py
      relevance.py
      schema.py
    risk_engine/
      analytics.py
    scenario_engine/
      simulation.py
  tests/
```

## Data Flow

1. `connectors/polymarket/client.py` fetches live Gamma events and CLOB reads, normalizes fields, and can write raw debug samples.
2. `services/macro_engine/mapping.py` maps markets into factor candidates with direct or proxy rules.
3. `services/macro_engine/relevance.py` scores each candidate and records keep or reject reasons.
4. `services/macro_engine/aggregation.py` combines kept candidates into factor-level signals and preserves excluded candidates for auditability.
5. `services/scenario_engine/simulation.py` applies factor-driven assumption shifts and runs the Monte Carlo engine.
6. `services/risk_engine/analytics.py` summarizes outputs and packages factor explainability plus assumption-debug data for the API.
7. `main.py` exposes `/macro/factors` and `/simulate`, and the dashboard consumes both through the frontend client.

## Live Polymarket Assumptions

- Gamma `events` pagination accepts `limit` and `offset`.
- Event payloads can contain inactive or closed child markets even when the parent event is active.
- `outcomes`, `outcomePrices`, and `clobTokenIds` may arrive as JSON-encoded strings rather than arrays.
- CLOB `/book` levels currently arrive as objects with `price` and `size`.
- Best ask must be computed as the minimum ask price from the book payload, not the first ask entry.

## Known Limitations

- Factor mapping is deterministic and regex-driven, so coverage quality depends on the taxonomy in `config/factors.yaml`.
- `/macro/factors` falls back to neutral defaults if live Polymarket reads fail.
- The simulation uses a fixed correlation matrix embedded in `services/scenario_engine/simulation.py`.
- Factor adjustments are simple linear shifts intended for transparency, not calibration.

## Highest-Risk Areas

- Upstream Polymarket field changes, especially Gamma string-encoded arrays and CLOB schema drift.
- Over- or under-mapping political and proxy markets into macro factors.
- Using event-level liquidity or price fields when market-level fields are sparse or stale.
