import unittest

from services.macro_engine.aggregation import aggregate_factor_signals
from services.macro_engine.schema import FactorMapping, RawMarket, RelevanceScore


class AggregationTests(unittest.TestCase):
    def test_aggregates_and_deduplicates_markets(self) -> None:
        market = RawMarket(
            market_id="dup-market",
            event_id="evt",
            title="Fed cuts twice this year?",
            description="Rates market",
            tags=["fed"],
            category="macro",
            probability=0.70,
            liquidity=60_000,
            volume=70_000,
            end_date="2026-04-20T00:00:00Z",
        )
        mapping = FactorMapping("fed_policy", "Fed Policy", "direct", ["fed"], "direct")
        high_score = RelevanceScore("dup-market", "fed_policy", 1.0, 1.0, 0.9, 0.1, 0.8, True, "keep")
        low_score = RelevanceScore("dup-market", "fed_policy", 1.0, 0.8, 0.7, 0.2, 0.5, True, "keep")

        aggregated = aggregate_factor_signals(
            [
                (market, mapping, high_score),
                (market, mapping, low_score),
            ]
        )

        signal = aggregated["fed_policy"]
        self.assertEqual(signal.contributing_markets, ["Fed cuts twice this year?"])
        self.assertAlmostEqual(signal.value, 0.70, places=3)
        self.assertGreater(signal.confidence, 0.0)


if __name__ == "__main__":
    unittest.main()
