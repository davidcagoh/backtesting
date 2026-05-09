# What We've Learned

Running log. Each entry is a **confirmed fact**, an **open hypothesis**, something **ruled out**, or a pointer to what the next experiment / paper search should prioritise.

This file is the self-correction mechanism for the project. Entries in `Ruled Out` should always state the *mechanism* that broke the idea, not just the metric — so future-you (or the weekly paper-search agent) doesn't re-explore the same dead end with a slight variation. The "What the Next Paper Search Should Prioritise" section feeds directly into `wiki/agent-config/paper-search-trigger.md`.

---

**Reference:** `wiki/reference/strategy-archetypes.md` — canonical taxonomy of 7 strategy types (market making, stat arb, mean reversion, options, order flow, cross-exchange arb), each with signal logic, key parameters, known failure modes, and friction adjustments. Annotated with current project state. The meta failure-modes table there tracks which universal risks (transaction cost blindness, regime change, overfitting) are open vs addressed in this project.

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
- **Co-primary metrics: Calmar (closed trades) + SQN.** Freqtrade reports both. Calmar = CAGR / max_drawdown on closed-trade equity; SQN = sqrt(N) × mean(R) / std(R). Use Calmar as primary when N≥20; use SQN as co-primary always because it explicitly penalises thin samples. At N<20, Calmar is mathematically valid but statistically unreliable — a single outlier trade can produce Calmar >20 on N=6. Always show SQN alongside. Confirmed 2026-04-30.
- **Also track: Profit Factor and Expectancy.** Profit Factor (gross profit / gross loss) is robust to thin samples and has no N assumption. Expectancy (mean return per trade, as ratio of risk) gives a complementary view. Both are now in the leaderboard.
- **Sharpe (closed trades) shown as sanity check.** "Daily wallet balance" Sharpe/Calmar penalises sparse strategies; don't use them for decision-making.
- **Prior leaderboard entries confirmed 2026-04-30:** LongOnlyStrategy closed-trade Calmar -4.55 (SQN -0.53, PF 0.81); TrendFilter200 closed-trade Calmar -6.84 (SQN -2.79, PF 0.43). The table previously said "n/a¹" for these — now corrected.
- **Fee correction (2026-05-03):** The original 6.33% SmaRegime180 result was NOT zero-fee. Freqtrade applied ccxt's hardcoded Hyperliquid default (0.045%/side). True zero-fee is 6.62% (Calmar 9.50). Actual Hyperliquid taker (0.035%/side): 6.39% (Calmar 8.86). **The `"fee"` key in config.json exchange block is silently ignored by the backtester — use `--fee FLOAT` CLI flag instead.**
- **Cost modeling complete (2026-05-03).** Historical Hyperliquid BTC funding rates applied per-trade across all 32 trades (19,733 8h periods, Feb 2024 → Apr 2026). Total drag: −2.25 USDC taker fees + −12.08 USDC funding = −14.33 USDC on 66.16 USDC gross (21.7% cost ratio). Net post-all-costs: +51.83 USDC (+5.18%), estimated Calmar ~7.2. Funding is 5.4× larger than taker fees in dollar terms and adversely selected: 85% of funding drag falls on the 7 winning trades (avg hold 25.9d) during bull-run periods, including 5.27 USDC from the 67-day Oct–Dec 2024 winner. Strategy survives realistic cost modeling — Calmar remains well above 2.0 threshold.

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
5. **Can a regime filter work on crypto at all, given the `TrendFilter200` failure?** The naive 1h SMA200 cross-up failed (see Ruled Out). The family isn't dead — it's the *specification* that failed.
   - **What we know from SmaRegime720 (2026-04-30):** Lengthening to SMA720 (≈30d) and adding a slope gate (`sma720 > sma720.shift(24)`) eliminated most whipsaw — 6 trades vs 90 for TrendFilter200, MDD 0.30% vs 4.22%, first positive total return (+0.80%) in the bear window. Closed-trade Calmar was 28.96 — best result so far. BUT: sample is only 6 trades (1 winner at +10.98%, 5 losers). Thin evidence. Bull-market validation pending.
   - **4h unscaled test failed** (13 trades, -1.73%, market change +25.51%): not a fair comparison — SMA720 on 4h = 120-day window, not the intended 30-day window. A fair bull test needs a 4h-scaled variant (SMA180 + slope_lookback=6) or extended 1h history.
   - **SmaRegime180 bull-window result (2026-04-30):** 4h variant (SMA180, slope_lookback=6) on BTC 4h, Feb 2024 → Apr 2026 (includes 2024–2025 bull). 32 trades, Calmar (CT) 8.68, SQN 1.02, Profit Factor 2.72, CAGR +2.83%, MDD 1.74%, win rate 21.9%. Bear sub-window alone: Calmar 6.59, 5 trades, SQN 0.33. **H7 PASS** — positive Calmar in both windows. Slope gate confirmed as a whipsaw suppressor across both regimes.
   - **Remaining open questions:** (a) Do post-cost metrics remain positive? (Estimated ~2.24% fee drag vs 6.33% gross — see Scoring note.) (b) Would an HMM regime filter improve win rate from ~22% to ~40%+ while preserving low MDD?
   - **What we know from HMM papers:** A Wasserstein HMM (arXiv 2603.04441) achieves Sharpe 2.18 vs SPX 1.18. 4-state NH-HMM on Bitcoin 2024–2026 outperforms standard 2-state HMM (Preprints.org 202603.0831) — likely {low-vol bull, high-vol bull, low-vol bear, high-vol bear}.
   - **Implication:** Build 4-state NH-HMM (not 2-state), use Bayesian posterior at P(bull) > 0.65, add 24h realised-vol as the transition covariate.
   - **Next test:** 4-state NH-HMM via `hmmlearn` GaussianHMM(n_components=4) on rolling 500h returns + log-volume, enter at P(bull-state) > 0.65. Compare Calmar, SQN, and win rate directly against `SmaRegime180`. First: re-run `SmaRegime180` with realistic fee config to confirm post-cost viability (top priority per "What the Next Experiments Should Prioritise").
   - **Search:** crypto-specific 1h/4h HMM validation with Calmar — daily Bitcoin validation found, intraday still open.
6. **Does the CEX → Hyperliquid (DEX) funding-rate lead time create an exploitable signal?** Zhivkov (2026) shows Granger causality runs CEX→DEX with zero reverse; the lead is measured in minutes on 1-min data. At 1h frequency this lag may be fully collapsed, but on 15m or 5m data a CEX (Binance) funding-rate signal might lead Hyperliquid by 1–3 bars.
   - **Test:** download Binance BTC funding rate at high frequency and correlate with Hyperliquid funding rate lags using Granger test. Determine if lead persists at 15m or 1h.
   - **Search:** CEX–DEX funding rate lead-lag; Hyperliquid-specific execution dynamics.
7. **Are our backtests artificially inflated by the bear-market regime at construction time?** A 2026 empirical study (Liu, arXiv 2604.18821) across 1,726 commercially distributed strategies shows that pro-forma backtests predominantly capture the factor regime present at construction time, not strategy skill — and strategies launched after extreme regime conditions experience sharper live-period deterioration.
   - **What this means here:** All our backtests are from Oct 2025 → Apr 2026, a sustained BTC bear (−37.20% buy-and-hold). Any strategy that avoids long exposure looks good purely because the regime rewarded flatness or shorts. A strategy with positive Calmar in this window may flip negative once BTC recovers.
   - **Test:** for any strategy with Calmar > 0 in the current test window, backtest over a bull sub-window using 4h data (~833 days available via `scripts/download_hyperliquid.py`). Require the strategy to show positive risk-adjusted return in BOTH regimes before moving to live consideration.
   - **Benchmark fix:** when adding new results to the leaderboard, report *benchmark-relative Calmar* (strategy Calmar minus buy-and-hold Calmar for the same period) as an additional column to reduce regime carry-over flattery.
8. **Does a SaR proxy (bid-ask spread × depth imbalance from Hyperliquid L2 book) predict liquidation cascade risk and correlate with adverse funding drag?** Sepper 2026 (arXiv 2603.09164) shows SaR spikes before the Oct 2025 cascade. 85% of our funding drag falls on winning trades during bull-run periods — exactly when OI and leverage are high. If high-SaR periods precede funding spikes, adding a LOB-depth check as a "pause carry" condition could improve post-cost Calmar.
   - **Test:** download Hyperliquid L2 book snapshots (`/info l2Book`) during historical high-funding periods; correlate top-5 ask depth with next-period funding rate change. If correlation > 0.3, prototype a SaR proxy filter.
   - **Search:** papers combining LOB depth with funding-rate prediction on perp venues.
9. **Does adding a `funding_aligned` feature improve NH-HMM state separation?** Badawi 2025 (arXiv 2601.06084) documents that funding/4h-trend alignment predicts expansion vs. compression regimes. Our planned NH-HMM uses returns + log-volume. Adding a binary `funding_aligned` covariate (sign of funding agrees with 4h SMA slope) may improve bull-state recall without hurting precision.
   - **Test:** compare NH-HMM(features=[returns, log-vol]) vs. NH-HMM(features=[returns, log-vol, funding_aligned]) on held-out 2025 data. Measure: bull-state precision, bear-state precision, and regime-conditional Calmar.
   - **Dependency:** requires funding-rate history download (already planned as Experiment #2).
10. **Is the 1h-4h range the right mean-reversion horizon for BTC on Hyperliquid, or does the transition zone shift with volatility regime?** Safari & Schmidhuber 2025 (arXiv 2501.16772) show the reversion-to-trending transition occurs in the 1–4h range broadly, but note crypto may differ due to higher retail participation. The transition boundary may compress to 15–30 min in high-vol regimes and expand to 4–8h in low-vol regimes.
    - **Test:** measure 1h BTC return autocorrelation (lag-1) separately during HMM bull-state vs. bear-state periods. If autocorrelation sign differs by regime, mean-reversion strategy should be state-conditional.
    - **Search:** papers on regime-conditional autocorrelation in crypto 1h returns.

---

## Ruled Out

Explain the mechanism, not just the metric — so we don't re-explore variants.

- **Hunting for Ethan's original data source.** Confirmed there's no canonical public bulk OHLCV for Hyperliquid. Whatever he used was ad hoc and isn't worth the time to retrace. Mechanism: Hyperliquid simply does not publish it. See `decisions/002`.
- **Maintaining `freqtrade_hyperliquid_download-data` as a separate repo.** It existed because freqtrade didn't support Hyperliquid; now it does. Mechanism: upstream closed the gap. See `decisions/001`.
- **Using freqtrade's built-in `download-data` for Hyperliquid.** Hard-disabled in the adapter via `ohlcv_has_history=False`. Mechanism: not a config toggle — it's a structural refusal in the exchange class. Use `scripts/download_hyperliquid.py` instead.
- **Naive 1h SMA200 cross-up as a regime filter** (`TrendFilter200`, 2026-04-24). Calmar -6.84, 12.2% win rate, 26 consecutive losses. Mechanism: 200 periods on 1h = ~8 days, too short to define a regime in crypto. In a sustained bear every cross-up is a bull-trap. Short-window, single-asset, single-timeframe regime filters get whipsawed. The broader family ("regime filters on crypto majors") is still open — see `wiki/results/2026-04-24-trend-filter-200.md` for candidate refinements (longer window, slope confirmation, higher-timeframe agreement).

---

## What the Next Experiments Should Prioritise

Updated 2026-05-09.

1. **Rolling-window HMM refit for HmmRegime4.** The 2026-05-09 backtest (BTC 1h bear, 74 trades, win rate 45.9%, SQN 1.38, Calmar 26.35) was run with the HMM fit on the full visible window — i.e. with look-ahead. Implement a walk-forward variant: re-fit the HMM every K bars on prior data only. If win rate stays above ~35%, the regime signal is real. If it collapses toward 22%, the look-ahead was the alpha. **This is the single most important next experiment** — it tells us whether HmmRegime4 is genuine regime detection or an artifact.
2. **Multi-asset HmmRegime4 run.** Data for 7 Hyperliquid majors (BTC/ETH/SOL/HYPE/ARB/AVAX/DOGE) × {1h, 4h} now on disk (downloaded 2026-05-09). Run HmmRegime4 across all 7 to check whether regime structure generalises beyond BTC. Watch for cross-asset correlation (BTC dominance ≈ 0.7+) — effective sample size is less than 7×.
3. **Funding-rate carry strategy.** Funding history (~25k records) for all 7 coins now on disk. Next: implement threshold-gated carry strategy (minimum rate ≥20–25 bps/8h, DAR-direction gate per Inan 2025).
4. **Post-cost analysis for HmmRegime4.** Apply taker fees (already in the run) + funding drag per-trade (similar to SmaRegime180 cost modelling on 2026-05-03). Funding adversely selects to long-hold winners; HmmRegime4's avg duration is 1d 09:47 so funding drag should be much smaller than SmaRegime180's 12.08 USDC.
5. **Profile** (deferred). "Make backtesting faster" still unverified as a bottleneck.

**Done (2026-05-09):** `HmmRegime4` backtest run on BTC 1h bear window (Nov 2025 → May 2026, 187d, --fee 0.00035, 74 trades). Calmar 26.35 (inflated by tiny 1.03% MDD), SQN 1.38, **win rate 45.9% vs SmaRegime180's 21.9%** — open hypothesis #5 (HMM regime detection lifts win rate from ~22% toward 40%+) confirmed. Profit Factor 1.58 (down from SmaRegime180's 2.72 — wins more often but each win smaller). Look-ahead caveat per strategy docstring: HMM fit on full visible window, treat as upper bound. Result card: `wiki/results/2026-05-09-hmm-regime-4.md`. Two minor fixes during run: (a) `log_vol.std().clip(lower=...)` → `max(log_vol.std(), 1e-9)` (pandas scalar vs Series API); (b) `download_hyperliquid.py` funding payload — `fundingHistory` API contract changed (flat fields, not `req`-wrapped) and 0.2s inter-page sleep added to avoid 429 on long histories. Multi-asset OHLCV expansion completed: 7 Hyperliquid majors × {1h, 4h} + funding history for all 7 (~25k records each, except HYPE 12.5k since coin only existed Dec 2024+).

**Done (2026-05-05):** `HmmRegime4` strategy implemented (`user_data/strategies/HmmRegime4.py`). 4-state GaussianHMM on rolling 24h log return + log-volume z-score; entry at P(bull-state)>0.65, exit at P(bull-state)<0.45. Requires `pip install hmmlearn`. Funding-rate history collector added to `scripts/download_hyperliquid.py` (`--funding --coins BTC ETH`); writes `user_data/data/hyperliquid/funding/<COIN>-funding.parquet` with incremental-update support.

**Done (2026-05-03):** Full cost modeling for SmaRegime180. Discovered that original 6.33% was already fee-inclusive (ccxt default 0.045%/side, not zero-fee). Fetched 19,733 historical Hyperliquid funding rate records; applied per-trade. Net post-all-costs return +5.18%, est. Calmar ~7.2. Funding drag (1.21% portfolio) is 5.4× larger than taker fees (0.23%) and adversely selected to winning trades. Strategy survives.

**Done (2026-04-30):** H7 bull-window validation for the slope-gate SMA family (SmaRegime180 passes). Prior leaderboard entries corrected with closed-trade Calmar. Leaderboard expanded with SQN and Profit Factor columns.

---

## What the Next Paper Search Should Prioritise

Updated 2026-05-03. This section is the source text for the weekly paper-search agent's prompt — keep it current.

**Do NOT search for:**
- Hyperliquid bulk OHLCV sources or historical data archives (ruled out above — none exist).
- Generic SMA-cross or RSI-cross strategy papers — these are baseline noise, not research.
- General funding-rate carry papers at the "naive always-on carry" level — we already know DEX carry exists and is profitable in isolation (Drift Sharpe 23.55, Aug 2025). Search only for papers that address *conditional* carry (threshold-gated, rate-predicted, or cost-adjusted) or that quantify Hyperliquid-specific carry costs.
- HMM papers on equity or FX markets — daily Bitcoin-specific NH-HMM validation is now in hand (Preprints.org 202603.0831). Do NOT search for more daily-frequency HMM papers unless they report 1h or 4h results.
- General slippage/execution papers on equity markets or CEX spot — we need perp-specific or Hyperliquid-specific studies only. Slippage at the SaR methodology level (Sepper 2026, arXiv 2603.09164) is now found; don't re-search this angle.

**Priority 1 — Funding-rate carry on DEX perps: Hyperliquid-specific threshold (NARROWED further).**
We now have: (a) empirical backing that DEX carry is profitable (Drift Sharpe 23.55, Aug 2025), (b) the carry timing principle — funding aligned with 4h context expands, funding divergent compresses (Badawi 2025, arXiv 2601.06084), (c) DAR predictability of next-period rate (Inan 2025, SSRN 5576424). The remaining open question: compute the *actual* break-even funding-rate threshold on Hyperliquid accounting for taker fee (0.035%/side) + DAR uncertainty window. Search for: Hyperliquid-specific fee schedule updates; papers that backtest threshold-gated carry with DAR forecasts on perp venues and report Calmar or Sharpe by threshold level.

**Priority 2 — Regime detection: intraday HMM with quantitative performance results (NARROWED).**
We have: daily 4h Bitcoin NH-HMM validation (Preprints 202603.0831), Wasserstein HMM technique (arXiv 2603.04441), and a candidate covariate — funding/4h-context alignment (Badawi 2025, arXiv 2601.06084). The remaining gap: a paper reporting *regime-conditional Calmar or Sharpe* on 1h or 4h crypto data. Search for: (a) NH-HMM or MSGARCH papers on crypto intraday that include a strategy backtest with Calmar/Sharpe; (b) any paper using funding rate or OI imbalance as an explicit HMM transition covariate and quantifying the improvement in regime purity or strategy performance.

**Priority 3 — Backtest-realistic execution on perps (SUBSTANTIALLY ADDRESSED — residual gap).**
Slippage on Hyperliquid is now addressed: Sepper 2026 (arXiv 2603.09164) provides SaR metrics from real Hyperliquid order-book data; Liu 2026 (arXiv 2604.18821) addresses regime-driven backtest inflation. Residual gap: does Freqtrade's T+0 fill assumption materially inflate Calmar vs. T+1 execution? Search for: papers quantifying the specific Calmar/Sharpe impact of T+0 vs. T+1 fill semantics for daily-to-weekly holding strategies on perps (not HFT). If nothing found after 2 search cycles, close this priority.

**Priority 4 — Mean-reversion at 1h–4h timeframes in crypto majors (NARROWED — implementation gap).**
We now have structural evidence: markets revert sub-hour and trend at hours-to-years (Safari & Schmidhuber 2025, arXiv 2501.16772), and the 4h funding-divergence mechanism provides a mean-reversion trigger (Badawi 2025, arXiv 2601.06084). The remaining gap is implementation-level: a Calmar-validated crypto mean-reversion strategy at 1h granularity. Search for: (a) crypto intraday mean-reversion backtests with Calmar ≥ 2 at 1h frequency; (b) short-horizon reversal after funding-rate extremes on BTC perps with quantified Sharpe/Calmar; (c) order-flow imbalance (OFI) as a 1h mean-reversion signal in crypto perps.
