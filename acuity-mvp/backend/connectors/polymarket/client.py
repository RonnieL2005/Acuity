from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from services.macro_engine.schema import MarketMicrostructure, RawMarket
from utils.cache import TTLCache


class PolymarketClient:
    # Read-only connector for Polymarket market data. It normalizes Gamma + CLOB responses
    # so the macro engine never needs to know Polymarket-specific field quirks.
    def __init__(
        self,
        *,
        gamma_base_url: str = "https://gamma-api.polymarket.com",
        clob_base_url: str = "https://clob.polymarket.com",
        cache_ttl_seconds: int = 300,
        timeout_seconds: int = 10,
        retries: int = 3,
        debug_dir: str | None = None,
    ) -> None:
        self.gamma_base_url = gamma_base_url.rstrip("/")
        self.clob_base_url = clob_base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.retries = retries
        self.cache = TTLCache[Any](ttl_seconds=cache_ttl_seconds)
        self.debug_dir = Path(debug_dir) if debug_dir else None

    def fetch_active_markets(self, *, limit: int = 200, page_size: int = 100) -> list[RawMarket]:
        # Gamma paginates at the event level, but active events may still contain closed child markets.
        markets: list[RawMarket] = []
        offset = 0

        while len(markets) < limit:
            requested = min(page_size, limit - len(markets))
            payload = self._get_json(
                f"{self.gamma_base_url}/events",
                {
                    "closed": "false",
                    "archived": "false",
                    "active": "true",
                    "limit": str(requested),
                    "offset": str(offset),
                },
            )
            events = payload if isinstance(payload, list) else payload.get("events", [])
            if not events:
                break

            for event in events:
                markets.extend(self._extract_event_markets(event))

            offset += len(events)
            if len(events) < requested:
                break

        return markets[:limit]

    def fetch_market_microstructure(self, clob_token_id: str) -> MarketMicrostructure:
        # Order book and spread come from CLOB because Gamma snapshots are not always sufficient.
        if not clob_token_id:
            return MarketMicrostructure()

        book = self._get_json(f"{self.clob_base_url}/book", {"token_id": clob_token_id})
        spread_payload = self._get_json(f"{self.clob_base_url}/spread", {"token_id": clob_token_id})

        bids = book.get("bids") or []
        asks = book.get("asks") or []
        best_bid = self._best_price(bids, side="bid")
        best_ask = self._best_price(asks, side="ask")
        spread = self._safe_float(spread_payload.get("spread"))
        if spread == 0.0 and best_bid and best_ask:
            spread = max(best_ask - best_bid, 0.0)

        return MarketMicrostructure(
            best_bid=best_bid,
            best_ask=best_ask,
            spread=spread,
            bid_depth=self._side_depth(bids),
            ask_depth=self._side_depth(asks),
            midpoint=self._midpoint(best_bid, best_ask),
        )

    def fetch_price_history(
        self,
        clob_token_id: str,
        *,
        interval: str = "1d",
        fidelity: int = 60,
    ) -> list[dict[str, float | str]]:
        if not clob_token_id:
            return []

        payload = self._get_json(
            f"{self.clob_base_url}/prices-history",
            {"market": clob_token_id, "interval": interval, "fidelity": str(fidelity)},
        )
        history = payload.get("history") or payload.get("prices") or []
        return [
            {
                "timestamp": str(point.get("t") or point.get("timestamp") or ""),
                "price": self._safe_float(point.get("p") or point.get("price")),
            }
            for point in history
        ]

    def _extract_event_markets(self, event: dict[str, Any]) -> list[RawMarket]:
        event_tags = self._collect_tags(event)
        extracted: list[RawMarket] = []

        for market in event.get("markets", []):
            if not self._is_active_market(market):
                continue

            token_ids = self._as_string_list(
                market.get("clobTokenIds") or market.get("clobTokenId") or market.get("tokenIds")
            )
            outcomes = self._as_string_list(market.get("outcomes"))
            outcome_prices = self._as_float_list(market.get("outcomePrices"))
            tags = sorted({*event_tags, *self._collect_tags(market)})
            micro = self._extract_embedded_microstructure(market)

            # Prefer market-level fields, then fall back to event-level fields where Gamma is sparse.
            extracted.append(
                RawMarket(
                    market_id=str(
                        market.get("id")
                        or market.get("conditionId")
                        or market.get("questionID")
                        or market.get("slug")
                        or ""
                    ),
                    event_id=str(event.get("id") or ""),
                    title=str(market.get("question") or market.get("title") or event.get("title") or ""),
                    description=str(
                        market.get("description")
                        or event.get("description")
                        or event.get("title")
                        or ""
                    ),
                    outcomes=outcomes,
                    outcome_prices=outcome_prices,
                    token_ids=token_ids,
                    tags=tags,
                    category=str(
                        market.get("category")
                        or event.get("category")
                        or event.get("slug")
                        or ""
                    ).lower(),
                    probability=self._primary_probability(
                        probability=market.get("probability"),
                        last_trade_price=market.get("lastTradePrice"),
                        outcome_prices=outcome_prices,
                        midpoint=micro.midpoint,
                    ),
                    liquidity=self._safe_float(
                        market.get("liquidityNum")
                        or market.get("liquidityClob")
                        or market.get("liquidity")
                        or event.get("liquidityClob")
                        or event.get("liquidity")
                    ),
                    volume=self._safe_float(
                        market.get("volumeNum")
                        or market.get("volumeClob")
                        or market.get("volume")
                        or event.get("volumeClob")
                        or event.get("volume")
                    ),
                    spread=self._safe_float(market.get("spread")) or micro.spread,
                    end_date=str(
                        market.get("endDate")
                        or market.get("endDateIso")
                        or market.get("end_date_iso")
                        or event.get("endDate")
                        or event.get("endDateIso")
                        or ""
                    ),
                    clob_token_id=token_ids[0] if token_ids else "",
                    market_slug=str(market.get("slug") or ""),
                    image_url=str(event.get("image") or market.get("image") or ""),
                    microstructure=micro,
                )
            )

        return [market for market in extracted if market.market_id and market.title]

    def _get_json(self, url: str, params: dict[str, str]) -> Any:
        query = urlencode(params)
        cache_key = f"{url}?{query}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                request = Request(
                    f"{url}?{query}",
                    headers={"Accept": "application/json", "User-Agent": "acuity-mvp/0.1"},
                )
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                    self._write_debug_sample(url, payload)
                    return self.cache.set(cache_key, payload)
            except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                time.sleep(0.25 * (attempt + 1))

        raise RuntimeError(f"Failed to fetch Polymarket payload from {url}") from last_error

    @staticmethod
    def _collect_tags(payload: dict[str, Any]) -> list[str]:
        raw_tags = payload.get("tags") or payload.get("tagSlugs") or []
        tags: list[str] = []
        for tag in raw_tags:
            if isinstance(tag, dict):
                value = tag.get("slug") or tag.get("name") or tag.get("label")
            else:
                value = tag
            if value:
                tags.append(str(value).lower())
        return tags

    @staticmethod
    def _extract_embedded_microstructure(market: dict[str, Any]) -> MarketMicrostructure:
        best_bid = PolymarketClient._safe_float(market.get("bestBid"))
        best_ask = PolymarketClient._safe_float(market.get("bestAsk"))
        return MarketMicrostructure(
            best_bid=best_bid,
            best_ask=best_ask,
            spread=PolymarketClient._safe_float(market.get("spread")),
            bid_depth=PolymarketClient._safe_float(market.get("bidDepth")),
            ask_depth=PolymarketClient._safe_float(market.get("askDepth")),
            midpoint=PolymarketClient._midpoint(best_bid, best_ask),
        )

    @staticmethod
    def _safe_float(value: Any) -> float:
        try:
            if isinstance(value, list):
                value = value[0] if value else 0.0
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _side_depth(levels: list[Any]) -> float:
        return sum(PolymarketClient._level_size(level) for level in levels)

    @staticmethod
    def _midpoint(best_bid: float, best_ask: float) -> float:
        if best_bid > 0.0 and best_ask > 0.0:
            return (best_bid + best_ask) / 2.0
        return 0.0

    @staticmethod
    def _parse_sequence(value: Any) -> list[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                loaded = json.loads(value)
            except json.JSONDecodeError:
                return [value]
            return loaded if isinstance(loaded, list) else [loaded]
        return [value]

    @staticmethod
    def _as_string_list(value: Any) -> list[str]:
        return [str(item) for item in PolymarketClient._parse_sequence(value) if str(item)]

    @staticmethod
    def _as_float_list(value: Any) -> list[float]:
        return [PolymarketClient._safe_float(item) for item in PolymarketClient._parse_sequence(value)]

    @staticmethod
    def _primary_probability(
        *,
        probability: Any,
        last_trade_price: Any,
        outcome_prices: list[float],
        midpoint: float,
    ) -> float:
        explicit_probability = PolymarketClient._safe_float(probability)
        if explicit_probability > 0.0:
            return explicit_probability

        trade_price = PolymarketClient._safe_float(last_trade_price)
        if trade_price > 0.0:
            return trade_price

        if outcome_prices:
            return outcome_prices[0]

        if midpoint > 0.0:
            return midpoint

        return 0.5

    @staticmethod
    def _level_price(level: Any) -> float:
        if isinstance(level, dict):
            return PolymarketClient._safe_float(level.get("price"))
        if isinstance(level, list) and level:
            return PolymarketClient._safe_float(level[0])
        return 0.0

    @staticmethod
    def _level_size(level: Any) -> float:
        if isinstance(level, dict):
            return PolymarketClient._safe_float(level.get("size"))
        if isinstance(level, list) and len(level) >= 2:
            return PolymarketClient._safe_float(level[1])
        return 0.0

    @staticmethod
    def _best_price(levels: list[Any], *, side: str) -> float:
        prices = [PolymarketClient._level_price(level) for level in levels]
        prices = [price for price in prices if price > 0.0]
        if not prices:
            return 0.0
        return max(prices) if side == "bid" else min(prices)

    @staticmethod
    def _is_active_market(market: dict[str, Any]) -> bool:
        return bool(market.get("active", True)) and not bool(market.get("closed", False)) and not bool(
            market.get("archived", False)
        )

    def _write_debug_sample(self, url: str, payload: Any) -> None:
        # Persisting representative raw payloads makes upstream schema drift easier to inspect.
        if self.debug_dir is None:
            return

        self.debug_dir.mkdir(parents=True, exist_ok=True)
        sample_name = url.rstrip("/").split("/")[-1] or "payload"
        target = self.debug_dir / f"{sample_name}.json"
        try:
            with target.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
        except OSError:
            return
