# What We've Learned

Running log. Each entry is a **confirmed fact**, an **open hypothesis**, something **ruled out**, or a pointer to what the next experiment / paper search should prioritise.

This file is the self-correction mechanism for the project. Entries in `Ruled Out` should always state the *mechanism* that broke the idea, not just the metric — so future-you (or the weekly paper-search agent) doesn't re-explore the same dead end with a slight variation. The "What the Next Paper Search Should Prioritise" section feeds directly into `wiki/agent-config/paper-search-trigger.md`.

---

## Confirmed Facts

### Infrastructure
- **Freqtrade** is the open-source framework this project is built on — live trading bot + backtester. We only care about the backtester for now.
- **Hyperliquid uses USDC as the quote currency.** Freqtrade pair notation for futures is `BTC/USDC:USDC` (base/quote:settle).
- **Freqtrade now ships a Hyperliquid adapter** (`freqtrade/exchange/hyperliquid.py` on current main). Last year when Ethan set this up, it didn't exist — that's why he had to source data externally.
- **Default data format in this repo is Feather.** Backtests must pass `--data-format-ohlcv feather` (also set in `config.json` as `dataformat_ohlcv`).

### Data sourcing
- **Freqtrade's `download-data` is fully disabled for Hyperliquid**, not just capped. `ohlcv_has_history=False` in the adapter triggers a hard refusal: "Hyperliquid does not support downloading trades or ohlcv data." Confirmed 2026-04-24.
- **We have a working direct-API downloader:** `scripts/download_hyperliquid.py` hits `/info candleSnapshot` and writes Feather in freqtrade's layout. Verified end-to-end — 5001 rows of 1h BTC/USDC:USDC data landed, `freqtrade backtesting` consumed them, 49 trades over ~200 days.
- **5000 candles is the hard public ceiling**, not a pagination cap. Hyperliquid API returns at most 5000 per call and doesn't expose older data via any public endpoint.
- **Hyperliquid publishes no bulk OHLCV to S3.** Official docs: "No other historical data sets are provided via S3 (e.g. candles or spot asset data)." Only L2 book snapshots (`s3://hyperliquid-archive/market_data/`) and asset contexts are available.
- **5000 candles is plenty for longer timeframes.** 1h = ~208 days, 4h = ~833 days, 1d = essentially the full life of the exchange. Only sub-hour strategies hit the constraint.

### Scoring
- **Primary metric is Calmar ratio (CAGR / MDD).** Sharpe is always displayed alongside as a sanity check — a high-Calmar / low-Sharpe strategy is usually a lucky tail, not a real edge. Decided 2026-04-24; do not score-shop mid-project.

---

## Open Hypotheses

Ordered by how much the answer would change what we do next. Each should have a concrete test and a search direction if one exists.

1. **What's the current bottleneck on backtest speed?** Goal for this revisit was "make backtesting faster" — but a full backtest on 5000 1h candles returns in seconds. May already be fast enough; re-check only once real strategies and bigger sweeps are in play.
   - **Test:** `cProfile` or `python -X importtime` around a multi-pair sweep once we have one.
2. **What timeframe does the target strategy need?** Determines whether the 5000-candle cap matters. If 1h+, ignore the cap. If 1m / 5m and we want multi-month history, we need to accrete candles over time (rerun the script daily) or reconstruct from S3.
   - **Test:** pick a first real strategy; its timeframe answers the question.
3. **Is Freqtrade's Hyperliquid execution adapter mature enough to go live?** Separate track from backtesting; relevant only once a strategy is trustworthy.
   - **Test:** read freqtrade changelog entries tagged `hyperliquid`; check issue tracker for open execution bugs.
4. **Do crypto-specific factors (funding rates, perp basis, on-chain flow) add orthogonal signal to price-only strategies?** Unexplored.
   - **Test:** build a simple funding-rate carry signal once a price-only baseline exists.
   - **Search:** crypto carry / funding-rate strategies, perp basis trading.

---

## Ruled Out

Explain the mechanism, not just the metric — so we don't re-explore variants.

- **Hunting for Ethan's original data source.** Confirmed there's no canonical public bulk OHLCV for Hyperliquid. Whatever he used was ad hoc and isn't worth the time to retrace. Mechanism: Hyperliquid simply does not publish it. See `decisions/002`.
- **Maintaining `freqtrade_hyperliquid_download-data` as a separate repo.** It existed because freqtrade didn't support Hyperliquid; now it does. Mechanism: upstream closed the gap. See `decisions/001`.
- **Using freqtrade's built-in `download-data` for Hyperliquid.** Hard-disabled in the adapter via `ohlcv_has_history=False`. Mechanism: not a config toggle — it's a structural refusal in the exchange class. Use `scripts/download_hyperliquid.py` instead.

---

## What the Next Experiments Should Prioritise

Updated 2026-04-24. Baseline is verified (`LongOnlyStrategy` on 1h BTC/USDC:USDC, ~200 days, -0.89% / placeholder). Real work hasn't started yet.

1. **Pick a real strategy.** `LongOnlyStrategy` is a placeholder SMA cross — not a signal, just a smoke test. Replace with a strategy whose thesis we can actually evaluate on Calmar + Sharpe.
2. **Expand data.** Add more pairs / timeframes to `scripts/download_hyperliquid.py` invocations once a strategy demands it. Consider a cron that re-runs daily so we accrete deep history at sub-hour timeframes.
3. **Profile only if a real sweep is slow.** The "make backtesting faster" goal from the project brief is still unverified — don't optimise prematurely.
4. **Live-trading readiness** (separate track): only relevant once backtest results are trustworthy.

---

## What the Next Paper Search Should Prioritise

Updated 2026-04-24. This section is the source text for the weekly paper-search agent's prompt — keep it current.

**Do NOT search for:**
- Hyperliquid bulk OHLCV sources or historical data archives (ruled out above — none exist).
- Generic SMA-cross or RSI-cross strategy papers — these are baseline noise, not research.

**Priority 1 — Crypto perp-specific factors (OPEN).**
Funding rates, perp basis, open-interest imbalance, liquidation-cascade detection. These don't exist in equity factor literature — the substrate is crypto-native and most quant-finance papers skip it. Search for empirical studies on funding-rate carry, basis trading on perpetual swaps, and liquidation-cascade early-warning signals.

**Priority 2 — Regime detection for 24/7 markets (OPEN).**
Equity-market regime-switching models (HMM, SJM, Wasserstein HMM) assume clean calendar structure: overnight gaps, weekends, close auctions. Crypto has none of these. Search for regime models specifically adapted to continuous-trading markets, or evidence that equity-derived models transfer cleanly.

**Priority 3 — Backtest-realistic execution on perps (OPEN).**
Slippage and funding-cost modelling for Hyperliquid-style perp markets. Freqtrade's default execution model was built for spot exchanges. Search for empirical slippage studies on decentralised perp venues, and for any published backtest-vs-live divergence analyses on perps.

**Priority 4 — Mean-reversion at 1h–4h timeframes in crypto majors (OPEN).**
Our baseline data is 1h and 4h. Search for crypto-specific evidence on mean-reversion horizons and whether the retail-overreaction mechanism that drives it in Chinese A-shares has a crypto analogue (likely yes — retail-heavy, 24/7, high leverage).
