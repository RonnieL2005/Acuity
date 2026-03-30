from __future__ import annotations


def get_macro_volatility_snapshot(base_interest_rate: float) -> dict[str, float | str]:
    if base_interest_rate >= 0.07:
        return {"regime": "stressed", "volatility_scale": 1.35}
    if base_interest_rate >= 0.05:
        return {"regime": "elevated", "volatility_scale": 1.1}
    return {"regime": "benign", "volatility_scale": 0.9}
