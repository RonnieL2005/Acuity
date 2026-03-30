import unittest

from services.macro_engine.relevance import score_market_relevance
from services.macro_engine.schema import FactorMapping, RawMarket


class RelevanceTests(unittest.TestCase):
    def test_direct_signal_scores_above_proxy(self) -> None:
        market = RawMarket(
            market_id="m1",
            event_id="e1",
            title="Fed cut in September?",
            description="Macro market",
            tags=["rates"],
            category="macro",
            probability=0.58,
            liquidity=50_000,
            volume=50_000,
        )
        direct = FactorMapping("fed_policy", "Fed Policy", "direct", ["fed cut"], "direct")
        proxy = FactorMapping("fed_policy", "Fed Policy", "proxy", ["yield"], "proxy")

        direct_score = score_market_relevance(market, direct)
        proxy_score = score_market_relevance(market, proxy)

        self.assertGreater(direct_score.final_score, proxy_score.final_score)
        self.assertTrue(direct_score.keep)

    def test_low_liquidity_market_is_discarded(self) -> None:
        market = RawMarket(
            market_id="m2",
            event_id="e2",
            title="CPI above 3%?",
            description="Inflation print",
            tags=["inflation"],
            category="macro",
            probability=0.52,
            liquidity=100,
            volume=100,
        )
        mapping = FactorMapping("inflation_stickiness", "Inflation Stickiness", "direct", ["cpi"], "direct")
        score = score_market_relevance(market, mapping)
        self.assertFalse(score.keep)
        self.assertIn("liquidity", score.reason.lower())


if __name__ == "__main__":
    unittest.main()
