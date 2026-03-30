import unittest

from services.macro_engine.engine import MacroProbabilityEngine
from services.macro_engine.schema import RawMarket


class StubConnector:
    def fetch_active_markets(self):
        return [
            RawMarket(
                market_id="fed-1",
                event_id="evt-1",
                title="Will the Fed cut rates by September?",
                description="FOMC path and rate cuts.",
                tags=["macro", "rates"],
                category="macro",
                probability=0.68,
                liquidity=45_000,
                volume=80_000,
                end_date="2026-06-15T00:00:00Z",
            ),
            RawMarket(
                market_id="oil-1",
                event_id="evt-2",
                title="Will Brent oil trade above $95?",
                description="Oil shock pricing",
                tags=["energy"],
                category="macro",
                probability=0.42,
                liquidity=30_000,
                volume=40_000,
                end_date="2026-05-01T00:00:00Z",
            ),
            RawMarket(
                market_id="sports-1",
                event_id="evt-3",
                title="Who will win the Super Bowl?",
                description="Sports market",
                tags=["sports"],
                category="sports",
                probability=0.50,
                liquidity=100_000,
                volume=100_000,
            ),
        ]


class MacroEngineE2ETests(unittest.TestCase):
    def test_build_factor_signals_from_mocked_polymarket_feed(self) -> None:
        engine = MacroProbabilityEngine(connector=StubConnector())
        signals = engine.build_factor_signals()

        self.assertIn("fed_policy", signals)
        self.assertIn("oil_shock", signals)
        self.assertGreater(signals["fed_policy"].confidence, 0.0)
        self.assertEqual(signals["recession_risk"].confidence, 0.0)


if __name__ == "__main__":
    unittest.main()
