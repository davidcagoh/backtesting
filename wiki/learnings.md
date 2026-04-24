# What We've Learned

Running log. Each entry is a **confirmed fact**, an **open question**, or something **ruled out**.

---

## Confirmed Facts

- **Freqtrade** is the open-source framework this project is built on — live trading bot + backtester. We only care about the backtester for now.
- **Hyperliquid uses USDC as the quote currency.** Freqtrade pair notation for futures is `BTC/USDC:USDC` (base/quote:settle).
- **Freqtrade now ships a Hyperliquid adapter** (`freqtrade/exchange/hyperliquid.py` on current main). Last year when Ethan set this up, it didn't exist — that's why he had to source data externally.
- **Freqtrade's `download-data` is fully disabled for Hyperliquid**, not just capped. `ohlcv_has_history=False` in the adapter triggers a hard refusal: "Hyperliquid does not support downloading trades or ohlcv data." Confirmed 2026-04-24.
- **We have a working direct-API downloader:** `scripts/download_hyperliquid.py` hits `/info candleSnapshot` and writes Feather in freqtrade's layout. Verified end-to-end — 5001 rows of 1h BTC/USDC:USDC data landed, `freqtrade backtesting` consumed them, 49 trades over ~200 days.
- **5000 candles is the hard public ceiling**, not a pagination cap. Hyperliquid API returns at most 5000 per call and doesn't expose older data via any public endpoint.
- **Hyperliquid publishes no bulk OHLCV to S3.** Official docs: "No other historical data sets are provided via S3 (e.g. candles or spot asset data)." Only L2 book snapshots (`s3://hyperliquid-archive/market_data/`) and asset contexts are available.
- **This is why Ethan's data source was irrecoverable** — there is no canonical public dump. Whatever he used was either a third-party paid aggregator or a one-off community archive.
- **Default data format in this repo is Feather.** Backtests must pass `--data-format-ohlcv feather` (also set in `config.json` as `dataformat_ohlcv`).
- **5000 candles is plenty for longer timeframes.** 1h = ~208 days, 4h = ~833 days, 1d = essentially the full life of the exchange. Only sub-hour strategies hit the constraint.

---

## Open Questions

Ordered by how much the answer would change what we do next.

1. **What's the current bottleneck on backtest speed?** Goal for this revisit was "make backtesting faster" — but a full backtest on 5000 1h candles returns in seconds. May already be fast enough; re-check only once real strategies and bigger sweeps are in play.
2. **What timeframe does the target strategy need?** Determines whether the 5000-candle cap matters. If 1h+, ignore the cap. If 1m / 5m and we want multi-month history, we need to accrete candles over time (rerun the script daily) or reconstruct from S3.
3. **Is Freqtrade's Hyperliquid execution adapter mature enough to go live?** Separate question from backtesting — relevant if this becomes the path to trading real capital. Check the freqtrade changelog and Hyperliquid-specific warnings in docs.

---

## Ruled Out

- **Hunting for Ethan's original data source.** Confirmed there's no canonical public bulk OHLCV for Hyperliquid. Whatever he used was ad hoc and isn't worth the time to retrace — we'd rather use `download-data` or reconstruct from S3. See `decisions/002`.
- **Maintaining `freqtrade_hyperliquid_download-data` as a separate repo.** It existed because freqtrade didn't support Hyperliquid; now it does. See `decisions/001`.

---

## What to Focus on Next

Setup and baseline are done (2026-04-24). Remaining:

1. **Pick a real strategy.** `LongOnlyStrategy` is a placeholder SMA cross that lost 0.89% on BTC 1h over ~200 days — not a signal, just a smoke test. Replace with whatever strategies Ethan/you actually want to evaluate.
2. **Profile.** `cProfile` or `python -X importtime` around `freqtrade backtesting` on a representative run. Identify the hot path before optimizing. The "make backtesting faster" goal from the project brief is still unverified — may already be fast enough.
3. **Expand data.** Add more pairs / timeframes to `scripts/download_hyperliquid.py` invocations. Consider a cron that re-runs it so fresh candles land daily (start building deep history by accretion).
4. **Live-trading readiness** (separate track): review freqtrade's Hyperliquid live-execution notes, unified-account warnings, stoploss-on-exchange behavior. Only relevant once backtest results are trustworthy.
