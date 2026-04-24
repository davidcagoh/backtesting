"""
Download Hyperliquid perp OHLCV directly from the public `/info` endpoint and
write Feather files in freqtrade's expected layout.

Freqtrade's native `freqtrade download-data` is disabled for Hyperliquid
(`ohlcv_has_history=False` in the adapter). The Hyperliquid public API serves
at most ~5000 recent candles per (coin, interval) via `candleSnapshot` — that
is the hard public ceiling. This script fetches that window and drops the
result where freqtrade looks for it.

Output layout:
    user_data/data/hyperliquid/futures/<PAIR_FS>-<TIMEFRAME>-futures.feather
where PAIR_FS is e.g. `BTC_USDC_USDC` for the freqtrade pair `BTC/USDC:USDC`.

Usage:
    python scripts/download_hyperliquid.py \\
        --pairs BTC/USDC:USDC ETH/USDC:USDC \\
        --timeframes 1h 4h \\
        --data-dir user_data/data/hyperliquid
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests


API_URL = "https://api.hyperliquid.xyz/info"
MAX_CANDLES = 5000  # Hyperliquid public cap; not a pagination limit
INTERVAL_TO_MS: dict[str, int] = {
    "1m": 60_000,
    "3m": 180_000,
    "5m": 300_000,
    "15m": 900_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
    "2h": 7_200_000,
    "4h": 14_400_000,
    "8h": 28_800_000,
    "12h": 43_200_000,
    "1d": 86_400_000,
    "3d": 259_200_000,
    "1w": 604_800_000,
}

logger = logging.getLogger("download_hyperliquid")


@dataclass(frozen=True)
class DownloadRequest:
    pair: str            # freqtrade form: "BTC/USDC:USDC"
    timeframe: str       # e.g. "1h"

    @property
    def coin(self) -> str:
        base, _rest = self.pair.split("/", 1)
        return base

    @property
    def filename_stem(self) -> str:
        return self.pair.replace("/", "_").replace(":", "_")


def fetch_candles(coin: str, interval: str) -> list[dict]:
    """
    Pull up to MAX_CANDLES recent candles for the given perp.
    """
    if interval not in INTERVAL_TO_MS:
        raise ValueError(f"Unsupported interval: {interval}")
    end_ms = int(time.time() * 1000)
    start_ms = end_ms - INTERVAL_TO_MS[interval] * MAX_CANDLES
    payload = {
        "type": "candleSnapshot",
        "req": {
            "coin": coin,
            "interval": interval,
            "startTime": start_ms,
            "endTime": end_ms,
        },
    }
    resp = requests.post(API_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected response shape for {coin}/{interval}: {data!r}")
    return data


def candles_to_frame(candles: list[dict]) -> pd.DataFrame:
    """
    Convert Hyperliquid candleSnapshot rows into the freqtrade OHLCV schema:
    date (datetime64[ms], UTC-naive), open, high, low, close, volume (floats).
    """
    if not candles:
        return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
    df = pd.DataFrame(candles)
    df = df.rename(columns={"t": "date", "o": "open", "h": "high", "l": "low",
                            "c": "close", "v": "volume"})
    df["date"] = pd.to_datetime(df["date"], unit="ms", utc=True).astype("datetime64[ms, UTC]")
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = df[col].astype(float)
    df = (df[["date", "open", "high", "low", "close", "volume"]]
          .sort_values("date")
          .drop_duplicates(subset=["date"])
          .reset_index(drop=True))
    return df


def write_feather(df: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_feather(out_path, compression="lz4", compression_level=9)


def download_one(req: DownloadRequest, data_dir: Path) -> Path:
    logger.info("fetching %s %s", req.pair, req.timeframe)
    candles = fetch_candles(req.coin, req.timeframe)
    df = candles_to_frame(candles)
    if df.empty:
        raise RuntimeError(f"No candles returned for {req.pair} {req.timeframe}")
    out_path = data_dir / "futures" / f"{req.filename_stem}-{req.timeframe}-futures.feather"
    write_feather(df, out_path)
    logger.info("wrote %d rows → %s (range %s → %s)",
                len(df), out_path, df["date"].iloc[0], df["date"].iloc[-1])
    return out_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--pairs", nargs="+", required=True,
                        help="Freqtrade pair strings, e.g. BTC/USDC:USDC")
    parser.add_argument("--timeframes", nargs="+", required=True,
                        help=f"Any of: {', '.join(INTERVAL_TO_MS)}")
    parser.add_argument("--data-dir", default="user_data/data/hyperliquid", type=Path,
                        help="Where freqtrade looks for Hyperliquid data")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = parse_args(argv)
    failures: list[tuple[str, str, str]] = []
    for pair in args.pairs:
        for tf in args.timeframes:
            req = DownloadRequest(pair=pair, timeframe=tf)
            try:
                download_one(req, args.data_dir)
            except Exception as exc:
                logger.exception("failed: %s %s", pair, tf)
                failures.append((pair, tf, str(exc)))
    if failures:
        logger.error("%d failure(s): %s", len(failures), failures)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
