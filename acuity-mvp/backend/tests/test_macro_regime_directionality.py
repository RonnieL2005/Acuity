import unittest

import numpy as np

from services.macro_engine.schema import FactorSignal
from services.scenario_engine.simulation import run_correlated_lbo_simulation


def build_signal(factor_key: str, value: float, confidence: float) -> FactorSignal:
    return FactorSignal(
        factor_key=factor_key,
        factor_name=factor_key.replace("_", " ").title(),
        value=value,
        confidence=confidence,
        contributing_markets=[],
        explanation="mock",
    )


class MacroRegimeDirectionalityTests(unittest.TestCase):
    def test_regimes_move_outputs_in_expected_direction(self) -> None:
        base = run_correlated_lbo_simulation(
            base_interest_rate=0.055,
            base_exit_multiple=10.5,
            base_exit_ebitda=18.0,
            entry_ebitda=12.0,
            entry_multiple=10.0,
            initial_debt=60.0,
            hold_period_years=5,
            iterations=5000,
            macro_volatility_scale=1.0,
            factor_signals={},
        )
        easing = run_correlated_lbo_simulation(
            base_interest_rate=0.055,
            base_exit_multiple=10.5,
            base_exit_ebitda=18.0,
            entry_ebitda=12.0,
            entry_multiple=10.0,
            initial_debt=60.0,
            hold_period_years=5,
            iterations=5000,
            macro_volatility_scale=1.0,
            factor_signals={"fed_policy": build_signal("fed_policy", 0.8, 0.9)},
        )
        recession = run_correlated_lbo_simulation(
            base_interest_rate=0.055,
            base_exit_multiple=10.5,
            base_exit_ebitda=18.0,
            entry_ebitda=12.0,
            entry_multiple=10.0,
            initial_debt=60.0,
            hold_period_years=5,
            iterations=5000,
            macro_volatility_scale=1.0,
            factor_signals={
                "recession_risk": build_signal("recession_risk", 0.9, 0.9),
                "credit_stress": build_signal("credit_stress", 0.85, 0.9),
            },
        )

        self.assertLess(float(np.mean(easing["interest_rates"])), float(np.mean(base["interest_rates"])))
        self.assertGreater(float(np.mean(easing["exit_multiples"])), float(np.mean(base["exit_multiples"])))
        self.assertGreater(float(np.mean(easing["exit_equity_values"])), float(np.mean(base["exit_equity_values"])))

        self.assertGreater(float(np.mean(recession["interest_rates"])), float(np.mean(base["interest_rates"])))
        self.assertLess(float(np.mean(recession["exit_multiples"])), float(np.mean(base["exit_multiples"])))
        self.assertLess(float(np.mean(recession["exit_ebitdas"])), float(np.mean(base["exit_ebitdas"])))
        self.assertLess(float(np.mean(recession["exit_equity_values"])), float(np.mean(base["exit_equity_values"])))


if __name__ == "__main__":
    unittest.main()
