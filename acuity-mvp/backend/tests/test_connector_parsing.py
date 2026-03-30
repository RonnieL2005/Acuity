import unittest

from connectors.polymarket.client import PolymarketClient


class ConnectorParsingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = PolymarketClient()

    def test_parses_json_encoded_sequences(self) -> None:
        self.assertEqual(self.client._as_string_list('["Yes","No"]'), ["Yes", "No"])
        self.assertEqual(self.client._as_float_list('["0.125","0.875"]'), [0.125, 0.875])
        self.assertEqual(self.client._as_string_list('["1","2"]'), ["1", "2"])

    def test_extracts_best_prices_from_object_book(self) -> None:
        bids = [{"price": "0.12", "size": "10"}, {"price": "0.11", "size": "20"}]
        asks = [{"price": "0.99", "size": "10"}, {"price": "0.13", "size": "20"}]
        self.assertEqual(self.client._best_price(bids, side="bid"), 0.12)
        self.assertEqual(self.client._best_price(asks, side="ask"), 0.13)

    def test_filters_inactive_markets(self) -> None:
        self.assertTrue(self.client._is_active_market({"active": True, "closed": False, "archived": False}))
        self.assertFalse(self.client._is_active_market({"active": True, "closed": True, "archived": False}))


if __name__ == "__main__":
    unittest.main()
