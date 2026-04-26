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
4. **Do crypto-specific factors (funding rates, perp basis, on-chain flow) add orthogonal signal to price-only strategies?** Partially explored — see papers below.
   - **What we know:** Funding rates on BTC perps (Binance, Bybit) are one-step-ahead predictable via DAR models but predictability is time-varying (Inan 2025). Roughly 60% of apparent DEX carry is eaten by transaction costs + spread reversals (Zhivkov 2026). **NEW (Aug 2025):** Empirical carry-only strategies on DEX perps (Drift, ApolloX) yield extremely high Sharpe ratios (23.55, 6.50) vs. negative on CEX (Binance −7.34, Bitmex −7.93) over the same period; DEX carry exhibits *no correlation* with spot HODL — pure diversifier (see `dex-carry-funding-rate-arbitrage-2025.md`). The CEX negativity confirms that our bear-market test window compressed CEX funding rates; DEX venues retained premia due to less-sophisticated arbitrage. A carry strategy therefore needs: (a) minimum funding-rate threshold (≥20–25 bps per 8h per Zhivkov), (b) DAR forecast confirming persistence (Inan), (c) DEX venue preference over CEX for Sharpe. Leverage on carry raises risk non-linearly; test unleveraged first.
   - **Test:** implement a funding-rate threshold + DAR-direction gated carry strategy. Requires adding funding-rate data fetching to `scripts/download_hyperliquid.py` (Hyperliquid API exposes current funding rate; build a collector). Then backtest with and without DAR gate; compare Sharpe/Calmar.
   - **Search:** Hyperliquid-specific fee schedule and taker cost; open-interest imbalance or liquidation-cascade signals as carry-timing overlays — still open.
5. **Can a regime filter work on crypto at all, given the `TrendFilter200` failure?** The naive 1h SMA200 cross-up failed (see Ruled Out). The family isn't dead — it's the *specification* that failed. Open question whether any of: (a) longer regime window (1h SMA720 ≈ 30d), (b) slope-confirmed entries (`sma.diff(24) > 0`), (c) higher-timeframe agreement (daily SMA200 filtering 1h execution), (d) probabilistic regime via HMM, fixes the whipsaw problem.
   - **What we know:** A Wasserstein HMM on a cross-asset daily universe achieves Sharpe 2.18 vs SPX 1.18 and MDD −5.43% vs −14.62% (arXiv 2603.04441). **NEW (Mar 2026):** Non-homogeneous HMM (NH-HMM) with Bayesian estimation on Bitcoin 2024–2026 outperforms standard 2-state HMM; a **4-state** model wins on BIC — likely {low-vol bull, high-vol bull, low-vol bear, high-vol bear}. Adding transition-probability covariates (volume, VIX, on-chain) materially improves regime forecasting in crisis periods (see `hmm-regime-detection-bitcoin-2026.md`).
   - **Implication for (d):** Build 4-state NH-HMM (not 2-state), use Bayesian posterior for probabilistic entry at P(bull) > 0.65, add 24h realised-vol as the transition covariate.
   - **Test:** implement (a) first — cheapest change, same file. Then the 4-state NH-HMM — replace SMA filter with `hmmlearn` GaussianHMM(n_components=4) on rolling 500h returns + log-volume, enter when P(identified-bull-state) > 0.65. (c) needs daily data downloaded.
   - **Search:** crypto-specific 1h/4h HMM validation with Calmar — daily Bitcoin validation found, intraday still open.
6. **Does the CEX → Hyperliquid (DEX) funding-rate lead time create an exploitable signal?** Zhivkov (2026) shows Granger causality runs CEX→DEX with zero reverse; the lead is measured in minutes on 1-min data. At 1h frequency this lag may be fully collapsed, but on 15m or 5m data a CEX (Binance) funding-rate signal might lead Hyperliquid by 1–3 bars.
   - **Test:** download Binance BTC funding rate at high frequency and correlate with Hyperliquid funding rate lags using Granger test. Determine if lead persists at 15m or 1h.
   - **Search:** CEX–DEX funding rate lead-lag; Hyperliquid-specific execution dynamics.
7. **Are our backtests artificially inflated by the bear-market regime at construction time?** A 2026 empirical study (Liu, arXiv 2604.18821) across 1,726 commercially distributed strategies shows that pro-forma backtests predominantly capture the factor regime present at construction time, not strategy skill — and strategies launched after extreme regime conditions experience sharper live-period deterioration.
   - **What this means here:** All our backtests are from Oct 2025 → Apr 2026, a sustained BTC bear (−37.20% buy-and-hold). Any strategy that avoids long exposure looks good purely because the regime rewarded flatness or shorts. A strategy with positive Calmar in this window may flip negative once BTC recovers.
   - **Test:** for any strategy with Calmar > 0 in the current test window, backtest over a bull sub-window using 4h data (~833 days available via `scripts/download_hyperliquid.py`). Require the strategy to show positive risk-adjusted return in BOTH regimes before moving to live consideration.
   - **Benchmark fix:** when adding new results to the leaderboard, report *benchmark-relative Calmar* (strategy Calmar minus buy-and-hold Calmar for the same period) as an additional column to reduce regime carry-over flattery.

---

## Ruled Out

Explain the mechanism, not just the metric — so we don't re-explore variants.

- **Hunting for Ethan's original data source.** Confirmed there's no canonical public bulk OHLCV for Hyperliquid. Whatever he used was ad hoc and isn't worth the time to retrace. Mechanism: Hyperliquid simply does not publish it. See `decisions/002`.
- **Maintaining `freqtrade_hyperliquid_download-data` as a separate repo.** It existed because freqtrade didn't support Hyperliquid; now it does. Mechanism: upstream closed the gap. See `decisions/001`.
- **Using freqtrade's built-in `download-data` for Hyperliquid.** Hard-disabled in the adapter via `ohlcv_has_history=False`. Mechanism: not a config toggle — it's a structural refusal in the exchange class. Use `scripts/download_hyperliquid.py` instead.
- **Naive 1h SMA200 cross-up as a regime filter** (`TrendFilter200`, 2026-04-24). Calmar -6.84, 12.2% win rate, 26 consecutive losses. Mechanism: 200 periods on 1h = ~8 days, too short to define a regime in crypto. In a sustained bear every cross-up is a bull-trap. Short-window, single-asset, single-timeframe regime filters get whipsawed. The broader family ("regime filters on crypto majors") is still open — see `wiki/results/2026-04-24-trend-filter-200.md` for candidate refinements (longer window, slope confirmation, higher-timeframe agreement).

---

## What the Next Experiments Should Prioritise

Updated 2026-04-24. Baseline is verified (`LongOnlyStrategy` on 1h BTC/USDC:USDC, ~200 days, -0.89% / placeholder). Real work hasn't started yet.

1. **Pick a real strategy.** `LongOnlyStrategy` is a placeholder SMA cross — not a signal, just a smoke test. Replace with a strategy whose thesis we can actually evaluate on Calmar + Sharpe.
2. **Expand data.** Add more pairs / timeframes to `scripts/download_hyperliquid.py` invocations once a strategy demands it. Consider a cron that re-runs daily so we accrete deep history at sub-hour timeframes.
3. **Profile only if a real sweep is slow.** The "make backtesting faster" goal from the project brief is still unverified — don't optimise prematurely.
4. **Live-trading readiness** (separate track): only relevant once backtest results are trustworthy.

---

## What the Next Paper Search Should Prioritise

Updated 2026-04-26. This section is the source text for the weekly paper-search agent's prompt — keep it current.

**Do NOT search for:**
- Hyperliquid bulk OHLCV sources or historical data archives (ruled out above — none exist).
- Generic SMA-cross or RSI-cross strategy papers — these are baseline noise, not research.
- General funding-rate carry papers at the "naive always-on carry" level — we already know DEX carry exists and is profitable in isolation (Drift Sharpe 23.55, Aug 2025). Search only for papers that address *conditional* carry (threshold-gated, rate-predicted, or cost-adjusted) or that quantify Hyperliquid-specific carry costs.
- HMM papers on equity or FX markets — daily Bitcoin-specific NH-HMM validation is now in hand (Preprints.org 202603.0831). Do NOT search for more daily-frequency HMM papers unless they report 1h or 4h results.

**Priority 1 — Funding-rate carry on DEX perps: Hyperliquid-specific threshold (NARROWED further).**
We now have strong empirical backing that DEX carry is profitable (Sharpe 23.55 on Drift, ~zero correlation with spot, Aug 2025). The remaining open question is narrow: what is the exact break-even funding-rate threshold on *Hyperliquid specifically*, accounting for (a) Hyperliquid's taker fee schedule, (b) the funding interval (8h), and (c) the DAR forecast uncertainty window? Search for: Hyperliquid fee structure publications; open-interest imbalance or liquidation-cascade signals as carry-timing overlays; any study combining funding-rate forecasting (DAR) with carry threshold gating.

**Priority 2 — Regime detection for 24/7 markets: intraday validation still open (NARROWED).**
Daily Bitcoin HMM validation is found (4-state NH-HMM, Preprints.org 202603.0831). The remaining gap: does an NH-HMM trained on *1h or 4h* crypto data produce actionable regime labels? Search for: (a) papers that apply HMM/regime-switching directly to crypto *intraday* (1h, 4h) data and report regime-conditional Calmar or Sharpe; (b) papers on feature selection for HMM transition covariates in crypto (volume, funding rate as covariates).

**Priority 3 — Backtest-realistic execution on perps (OPEN — slippage sub-component).**
The backtest-vs-live divergence angle is now addressed (Liu 2026, arXiv 2604.18821): backtests reflect regime at launch, not skill. The remaining gap is the *execution model* gap: Freqtrade's default backtest assumes zero slippage. Search for: empirical slippage studies on Hyperliquid or similar on-chain perp venues (order-book depth, taker impact, spread costs); papers comparing Freqtrade or similar backtester assumed fills vs. actual fill quality on perps.

**Priority 4 — Mean-reversion at 1h–4h timeframes in crypto majors (OPEN — unchanged).**
Our baseline data is 1h and 4h. Search for crypto-specific evidence on mean-reversion horizons and whether the retail-overreaction mechanism that drives it in Chinese A-shares has a crypto analogue (likely yes — retail-heavy, 24/7, high leverage). No strong paper found yet — this priority is unchanged. Also search for: crypto intraday momentum reversal (within 1–4h), short-horizon mean-reversion after funding-rate extremes.
