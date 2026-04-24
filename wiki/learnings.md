# What We've Learned

Running log. Each entry is a **confirmed fact**, an **open question**, or something **ruled out**.

---

## Confirmed Facts

- **Freqtrade** is the open-source framework this project is built on — live trading bot + backtester. We only care about the backtester for now.
- **Hyperliquid uses USDC as the quote currency.** Freqtrade pair notation for futures is `BTC/USDC:USDC` (base/quote:settle).
- **Freqtrade now ships a Hyperliquid adapter** (`freqtrade/exchange/hyperliquid.py` on current main). Last year when Ethan set this up, it didn't exist — that's why he had to source data externally.
- **Freqtrade's `download-data` works with Hyperliquid, but is capped at ~5000 candles per timeframe** because the Hyperliquid API itself only returns 5000. The adapter has `"ohlcv_has_history": False` — no downloader can backfill deep history.
- **Hyperliquid publishes no bulk OHLCV to S3.** Official docs: "No other historical data sets are provided via S3 (e.g. candles or spot asset data)." Only L2 book snapshots (`s3://hyperliquid-archive/market_data/`) and asset contexts are available.
- **This is why Ethan's data source was irrecoverable** — there is no canonical public dump. Whatever he used was either a third-party paid aggregator or a one-off community archive.
- **Default data format in this repo is Feather.** Backtests must pass `--data-format-ohlcv feather` (also set in `config.json` as `dataformat_ohlcv`).
- **5000 candles is plenty for longer timeframes.** 1h = ~208 days, 4h = ~833 days, 1d = essentially the full life of the exchange. Only sub-hour strategies hit the constraint.

---

## Open Questions

Ordered by how much the answer would change what we do next.

1. **What's the current bottleneck on backtest speed?** The stated goal for this revisit is "make backtesting faster" — but we haven't profiled anything. Could be Feather IO, strategy evaluation, or the pair × timerange sweep size. Profile before optimizing.
2. **What timeframe does the target strategy need?** Determines whether the 5000-candle cap matters. If 1h+, ignore the cap. If 1m / 5m and we want multi-month history, we need to accumulate over time or reconstruct from S3.
3. **Is Freqtrade's Hyperliquid execution adapter mature enough to go live?** Separate question from backtesting — relevant if this becomes the path to trading real capital. Check the freqtrade changelog and Hyperliquid-specific warnings in docs.
4. **Do we want to fork freqtrade or stay on upstream?** Upstream now covers Hyperliquid, so there's less reason to fork. Probably stay upstream.

---

## Ruled Out

- **Hunting for Ethan's original data source.** Confirmed there's no canonical public bulk OHLCV for Hyperliquid. Whatever he used was ad hoc and isn't worth the time to retrace — we'd rather use `download-data` or reconstruct from S3. See `decisions/002`.
- **Maintaining `freqtrade_hyperliquid_download-data` as a separate repo.** It existed because freqtrade didn't support Hyperliquid; now it does. See `decisions/001`.

---

## What to Focus on Next

1. **Install freqtrade locally** (needs user approval — see setup in `_index.md`). Confirm `freqtrade --version` runs.
2. **Download data.** `freqtrade download-data --exchange hyperliquid --timeframes 1h -p BTC/USDC:USDC` — start small, confirm the Feather files land in `user_data/data/hyperliquid/`.
3. **Reproduce a backtest.** Run the updated command in `_index.md`. This is the baseline — no "make it faster" work before this passes.
4. **Profile.** `python -X importtime` or `cProfile` wrapped around `freqtrade backtesting` on a representative run. Identify the hot path.
5. **Then** decide whether to optimize (vectorization, caching, narrower data, parallel pair sweeps) or pivot toward live-trading evaluation.
