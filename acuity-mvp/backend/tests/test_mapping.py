import unittest

from services.macro_engine.mapping import map_market_to_factors
from services.macro_engine.schema import RawMarket


class MappingTests(unittest.TestCase):
    def test_maps_direct_fed_market(self) -> None:
        market = RawMarket(
            market_id="1",
            event_id="evt-1",
            title="Will the Fed cut rates by September?",
            description="FOMC pricing for a rate cut this year.",
            tags=["macro", "rates"],
            category="politics",
            probability=0.62,
            liquidity=10_000,
            volume=25_000,
        )

        mappings = map_market_to_factors(market)
        factor_keys = {mapping.factor_key for mapping in mappings}
        self.assertIn("fed_policy", factor_keys)
        self.assertEqual(next(item for item in mappings if item.factor_key == "fed_policy").mapping_type, "direct")

    def test_rejects_sports_market(self) -> None:
        market = RawMarket(
            market_id="2",
            event_id="evt-2",
            title="Who will win the NBA Finals?",
            description="Championship market",
            tags=["sports", "nba"],
            category="sports",
            probability=0.50,
            liquidity=50_000,
            volume=60_000,
        )

        self.assertEqual(map_market_to_factors(market), [])


if __name__ == "__main__":
    unittest.main()
