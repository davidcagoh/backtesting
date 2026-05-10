# Backtesting Wiki

Crypto strategy backtesting setup built on [Freqtrade](https://www.freqtrade.io/en/stable/), targeting Hyperliquid (USDC-quoted) markets. Revived 2026-04 as a possible base for actively trading personal crypto holdings.

**Last updated:** 2026-05-10 (late session)

**Current state:** Six experiments completed 2026-05-10. (5) **Pre-registered kill criteria for SmaRegime180** — see `decisions/004-kill-criteria-sma-regime-180.md`. Hard kills (MDD > 5.5%, six straight stops, 365d return ≤ 0 for 30d, walk-forward Calmar < 2). Continuous shrinkage formula (Davies–Ravagnani) ties live position size to rolling 180d PF, Calmar, and bull/bear ratio. Mandatory quarterly walk-forward review. (6) **CEX bull-window validation** — Binance BTC/USDT:USDT 4h, 2019-10 → 2026-05 (6.7y, 92 trades, 2 bull + 2 bear cycles). Full-window Calmar **7.23**, SQN **1.73**, PF **2.85**, MDD 2.22%, win rate 21.7% — matches Hyperliquid result within noise. Sub-windows: 2020-21 bull Calmar 14.04, 2022 bear Calmar −5.23 (PF 0.00 but MDD 0.28% — strategy correctly stays flat in deep bears), 2023-24 bull Calmar 21.13, 2025 bear Calmar 3.59. **SmaRegime180 graduates to paper-trade candidate.** See `results/2026-05-10-sma-regime-180-cex-bull-validation.md`.

**Earlier 2026-05-10 experiments:** (1) **Rolling-window HMM refit** (`HmmRegime4Rolling`) on BTC: SQN 0.59 (vs look-ahead's 1.38), win rate 37.7%, return +1.15%. **Look-ahead absorbed ~50% of the alpha**; demotes HmmRegime4 to upper-bound. (2) **Multi-asset HmmRegime4Rolling** on 7 majors: −5.62%, only HYPE/BTC profitable. HMM does not generalise without per-coin tuning. (3) **FundingCarry** threshold-gated long-only on 7 majors: catastrophic −30.16%, all losers stopped at −10%. Naive carry fails in bear. (4) **HmmCarry conjunction** (HMM bull AND funding-negative) on 7 majors: −19.59%, MDD 23.86%. **Worse than HMM alone** — signals are anti-complementary, not independent (HMM is reactive, funding is forward-looking; intersection picks worst moments). Only HYPE/ETH showed expected tightening; BTC win rate collapsed 41.1% → 7.7%. Open items: (1) Reverse-sign HmmCarry (positive funding as bull confirmation); (2) Per-coin funding-sign learning; (3) Lead-lag conjunction (funding-negative *before* HMM-bull turns on); (4) Per-coin HMM hyperparameter sweep with DSR gate; (5) Bull-window CEX backtest as training-set check.

---

## Contents

- [learnings.md](learnings.md) — confirmed facts, open hypotheses, ruled-out directions, search priorities
- `reference/`
  - [strategy-archetypes.md](reference/strategy-archetypes.md) — canonical reference: 7 strategy archetypes from IMC Prosperity podium writeups, annotated with current project state. Stable reference; findings live in `results/` and `learnings.md`.
- `decisions/`
  - [001-drop-external-data-repo.md](decisions/001-drop-external-data-repo.md) — removed the `freqtrade_hyperliquid_download-data` gitlink
  - [002-hyperliquid-deep-history.md](decisions/002-hyperliquid-deep-history.md) — accept the 5000-candle API cap; reconstruct from S3 only if needed
  - [003-baseline-eval.md](decisions/003-baseline-eval.md) — baseline used by `scripts/run_eval.sh` and the Session Start Routine
  - [004-kill-criteria-sma-regime-180.md](decisions/004-kill-criteria-sma-regime-180.md) — pre-registered hard-kill thresholds + continuous-shrinkage formula for SmaRegime180
- `experiments/` — backtest runs and results
- `results/` — per-strategy report cards (one file per run)
- `papers/` — summaries of relevant research (populated by the weekly paper-search agent)
- `logs/` — weekly paper-search run logs
- `agent-config/paper-search-trigger.md` — master prompt for the weekly paper-search RemoteTrigger

---

## Papers

Research summaries added by the weekly paper-search agent. Sorted newest-first. Primary sort: direct applicability to Freqtrade strategy on Hyperliquid perps.

| Paper | Venue | Date | Priority addressed | File |
|-------|-------|------|--------------------|------|
| Slippage-at-Risk (SaR): A Forward-Looking Liquidity Risk Framework for Perpetual Futures Exchanges | arXiv 2603.09164 | Mar 2026 | P3 — Slippage on Hyperliquid (real order-book data) | [slippage-at-risk-hyperliquid-2026.md](papers/slippage-at-risk-hyperliquid-2026.md) |
| Evaluating Structured Strategy Backtests: Peer Benchmarks, Regime Timing, and Live Performance | arXiv 2604.18821 | Apr 2026 | P3 — Backtest-vs-live divergence | [backtest-regime-timing-live-performance-2026.md](papers/backtest-regime-timing-live-performance-2026.md) |
| Markov and HMM for Regime Detection in Cryptocurrency Markets: Evidence from Bitcoin (2024–2026) | Preprints.org 202603.0831 | Mar 2026 | P2 — Regime detection (crypto-specific HMM) | [hmm-regime-detection-bitcoin-2026.md](papers/hmm-regime-detection-bitcoin-2026.md) |
| Explainable Regime Aware Investing | arXiv 2603.04441 | Mar 2026 | P2 — Regime detection | [wasserstein-hmm-regime-investing-2026.md](papers/wasserstein-hmm-regime-investing-2026.md) |
| Who Sets the Range? Funding Mechanics and 4h Context in Crypto Markets | arXiv 2601.06084 | Dec 2025 | P1+P2+P4 — Carry timing + HMM covariate + mean-reversion trigger | [funding-mechanics-4h-context-crypto-2026.md](papers/funding-mechanics-4h-context-crypto-2026.md) |
| The Two-Tiered Structure of Cryptocurrency Funding Rate Markets | MDPI Mathematics 14(2):346 | Jan 2026 | P1+P3 — Funding rate carry + execution costs | [two-tiered-funding-rate-markets-2026.md](papers/two-tiered-funding-rate-markets-2026.md) |
| Trends and Reversion in Financial Markets on Time Scales from Minutes to Decades | arXiv 2501.16772 | Jan 2025 | P4 — Mean-reversion boundary at 1h–4h | [trends-reversion-timescale-2025.md](papers/trends-reversion-timescale-2025.md) |
| Exploring Risk and Return Profiles of Funding Rate Arbitrage on CEX and DEX | Blockchain: Research and Applications (Elsevier) | Aug 2025 | P1 — DEX carry return profile | [dex-carry-funding-rate-arbitrage-2025.md](papers/dex-carry-funding-rate-arbitrage-2025.md) |
| Predictability of Funding Rates | SSRN 5576424 | Oct 2025 | P1 — Funding rate carry signal | [funding-rate-predictability-inan-2025.md](papers/funding-rate-predictability-inan-2025.md) |

---

## Strategy Leaderboard

Primary sort: **Calmar (closed trades)**. Co-primary: **SQN** (System Quality Number — penalises thin samples; use this when N<30). All metrics are closed-trade unless noted. See `wiki/decisions/003-baseline-eval.md` for the evaluation baseline. CT = closed trades.

| Strategy | Calmar (CT) | SQN | Profit Factor | Sharpe (CT) | CAGR | MDD | Trades | Data | Report |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| `SmaRegime720` (1h SMA720 + slope gate) | **28.96**² | 0.69 | 3.68 | 0.20 | +1.66% | 0.30% | 6 | BTC 1h, bear, 2025-10-29→2026-04-24 | [2026-04-30](results/2026-04-30-sma-regime-720.md) |
| `HmmRegime4` (look-ahead, 4-state GaussianHMM, 1h) | 26.35⁴ | 1.38⁴ | 1.58 | 1.23 | +5.26% | 1.03% | 74 | BTC 1h, bear, 2025-11-04→2026-05-09 | [2026-05-09](results/2026-05-09-hmm-regime-4.md) |
| `HmmRegime4Rolling` (walk-forward refit, 1h) | 12.11 | 0.59 | 1.31 | 0.51 | +2.56% | 1.10% | 53 | BTC 1h, bear, 2025-11-25→2026-05-09 | [2026-05-10](results/2026-05-10-hmm-regime-4-rolling.md) |
| `SmaRegime180` (4h SMA180 + slope gate) | **8.68**³ | 1.02 | 2.72 | 0.14 | +2.83% | 1.74% | 32 | BTC 4h, full, 2024-02-12→2026-04-24 | [2026-04-30](results/2026-04-30-sma-regime-180.md) |
| `SmaRegime180` cross-cycle (Binance perp)⁶ | **7.23** | **1.73** | 2.85 | 0.13 | +2.84% | 2.22% | 92 | BTC 4h, 2019-10→2026-05 | [2026-05-10](results/2026-05-10-sma-regime-180-cex-bull-validation.md) |
| `LongOnlyStrategy` (placeholder SMA cross) | -4.55 | -0.53 | 0.81 | -0.36 | -1.61% | 1.86% | 49 | BTC 1h, bear, 2025-10-06→2026-04-24 | — |
| `TrendFilter200` (1h SMA200 regime filter) | -6.84 | -2.79 | 0.43 | -2.54 | -5.44% | 4.22% | 90 | BTC 1h, bear, 2025-10-06→2026-04-24 | [2026-04-24](results/2026-04-24-trend-filter-200.md) |
| `HmmRegime4Rolling` 7-asset portfolio | -4.43 | -0.59 | 0.91 | -1.53 | -12.02% | 14.70% | 504 | 7 majors 1h, bear, 2025-11-25→2026-05-09 | [2026-05-10](results/2026-05-10-hmm-regime-4-multi-asset.md) |
| `FundingCarry` 7-asset portfolio | -7.35 | -3.60 | 0.28 | -2.57 | — | 42.14% | 47 | 7 majors 1h, bear, 2025-11-04→2026-05-09 | [2026-05-10](results/2026-05-10-funding-carry.md) |
| `HmmCarry` (conjunction) 7-asset portfolio⁵ | -9.51 | — | 0.55 | -2.09 | — | 23.86% | 278 | 7 majors 1h, bear, 2025-11-25→2026-05-09 | [2026-05-10](results/2026-05-10-hmm-carry-conjunction.md) |

² Calmar unreliable at N=6 (SQN 0.69). SmaRegime180 (N=32, SQN 1.02) is the more meaningful data point for this family.

³ Uses ccxt default 0.045%/side fee (not zero-fee as previously documented). Actual Hyperliquid taker (0.035%/side): Calmar 8.86 (+6.39%). Post-all-costs (taker + historical funding): est. Calmar ~7.2 (+5.18%). See [2026-04-30 result card](results/2026-04-30-sma-regime-180.md) for full breakdown.

⁴ Calmar inflated by tiny MDD denominator (1.03%). **Look-ahead, upper-bound only.** Honest walk-forward version (`HmmRegime4Rolling`, SQN 0.59) is the comparable number — look-ahead absorbed ~50% of the alpha (return +2.65% → +1.15%, win rate 45.9% → 37.7%). HmmRegime4Rolling is the row to rank against SmaRegime180 (SQN 0.59 vs 1.02 — SmaRegime180 wins on co-primary). Multi-asset run on 7 majors is decisively negative (−5.62%) — HMM does not generalise without per-coin tuning.

⁵ Conjunction of HmmRegime4Rolling (bull_prob > 0.65) and FundingCarry (funding_roll < threshold). Hypothesis: independent signals → tighter filter. Result: signals are anti-complementary in this window — conjunction is *worse* than HMM alone (−19.59% vs −5.62%). HMM is reactive; funding is forward-looking; intersection picks late-cycle bull lag with early-cycle bear lead. Only HYPE/ETH showed expected tightening; BTC win rate collapsed 41.1% → 7.7%. See result card for reverse-sign and per-coin follow-ups.

⁶ Cross-cycle out-of-sample validation. 6.7y of Binance BTC perp 4h covering 2 bull + 2 bear cycles. Sub-window decomposition: 2020-21 bull Calmar 14.04, 2022 bear Calmar −5.23 (PF 0.00 but MDD 0.28% — strategy correctly stays flat), 2023-24 bull Calmar 21.13, 2025 bear Calmar 3.59. Win rate 21.7% identical to Hyperliquid (21.9%). **SmaRegime180 graduates to paper-trade candidate** under decisions/004 kill criteria. Worst regime is 2022-style deep bear: PF goes to 0 but slope-gate filter caps DD at 0.28%. Continuous-shrinkage formula would have shrunk size to ~10% through 2022 without hard-killing.

**H7 status (updated 2026-05-10):** `SmaRegime180` passes the cross-cycle validation on Binance perp 2019-26. Calmar 7.23 (close to Hyperliquid 8.68), win rate 21.7% (vs 21.9%), bull-window Calmars 14.04 and 21.13, 2022 bear is contained-failure (Calmar −5.23 but MDD 0.28%). H7 inflation is real but bounded — strategy is regime-flattered by ~20% on the original Hyperliquid window, not collapsing. Slope-gate family validated across 4 regime transitions.

**Fee correction (2026-05-03):** The original 6.33% run was NOT zero-fee — Freqtrade applied ccxt's hardcoded Hyperliquid default (0.045%/side). True zero-fee baseline is 6.62% (Calmar 9.50). Actual Hyperliquid taker (0.035%/side, via `--fee` CLI flag) gives 6.39% (Calmar 8.86). The `"fee"` key in config.json exchange block is silently ignored by the backtester.

**Cost modeling complete (2026-05-03):** Historical funding rates applied per-trade (19,733 periods). Total cost: −2.25 USDC taker + −12.08 USDC funding = −14.33 USDC on 66.16 USDC gross = 21.7% drag. Net post-all-costs: +51.83 USDC (+5.18%), estimated Calmar ~7.2. Funding is 5.4× larger than taker fees and adversely selected: 85% of funding drag falls on the 7 winning trades (avg hold 25.9d) during bull-run periods. Strategy survives realistic cost modeling.

**Benchmark:** market change -37.20% (bear window), +61.43% (full 4h window). Long-only trend strategies will underperform buy-and-hold in strong bulls — evaluate on risk-adjusted return (Calmar, SQN), not absolute return.

Rows added here whenever a new strategy is backtested. Link the Report column to the relevant `wiki/results/<date>-<strategy>.md` file.

---

## Repository Layout

| Path | Role |
|------|------|
| `freqtrade/` | Fresh clone of the upstream Freqtrade repo (gitignored — it has its own `.git`). Ships a Hyperliquid adapter. |
| `user_data/config.json` | Minimal Hyperliquid config (dry_run, futures/isolated, USDC stake, Feather format). No keys committed — fill `walletAddress` / `privateKey` only for live trading, not needed for backtesting. |
| `user_data/strategies/LongOnlyStrategy.py` | SMA-cross placeholder strategy so the original `notes.md` command still runs. Replace with real logic. |
| `user_data/data/hyperliquid/` | Where `scripts/download_hyperliquid.py` writes Feather OHLCV files (futures land under `futures/`). |
| `scripts/download_hyperliquid.py` | Custom Hyperliquid OHLCV downloader + funding-rate history collector. Required because freqtrade's built-in `download-data` is disabled for Hyperliquid. Use `--funding --coins BTC` to fetch 8-hourly funding rates. Output: `user_data/data/hyperliquid/funding/<COIN>-funding.parquet`. Supports incremental updates (resumes from last saved timestamp). |
| `scripts/generate_leaderboard_chart.py` | Reads `wiki/_index.md` leaderboard table + backtest ZIPs; writes `wiki/assets/leaderboard.png`. Requires `pip install matplotlib`. Auto-called by `run_eval.sh`. |
| `wiki/assets/leaderboard.png` | Generated chart — Calmar, Sharpe, Win Rate, MDD bars + equity curves. Committed to repo so it renders in `README.md` on GitHub. |
| `README.md` | Repo root readme. Embeds the leaderboard chart; links to this wiki for full details. |
| `notes.md` | Original crib sheet (preserved). |

The old `freqtrade_hyperliquid_download-data` gitlink was removed — see `decisions/001`.

---

## Setup (first run on this machine)

```shell
cd freqtrade
python3 -m venv .venv
source .venv/bin/activate
pip install -e .        # or: pip install -r requirements.txt
# talib may need a system install first: brew install ta-lib
```

> The install step needs explicit approval in agent sessions — it executes freqtrade's setup code. Run it manually.

## Download data

**Use the custom script at `scripts/download_hyperliquid.py`** — freqtrade's built-in `download-data` is disabled for Hyperliquid (`ohlcv_has_history=False` in the adapter). The script hits `https://api.hyperliquid.xyz/info` directly and writes Feather files into freqtrade's expected layout. See `decisions/002` for why.

Run from the wrapper repo root (`backtesting/`):

```shell
./freqtrade/.venv/bin/python scripts/download_hyperliquid.py \
  --pairs BTC/USDC:USDC ETH/USDC:USDC \
  --timeframes 1h 4h
```

Cap: ~5000 candles per (pair, timeframe). That's ~208 days at 1h, ~833 days at 4h — Hyperliquid API ceiling, not a tooling limitation.

## Backtest

```shell
./freqtrade/.venv/bin/freqtrade backtesting \
  --userdir user_data \
  -c user_data/config.json \
  --data-format-ohlcv feather \
  -s LongOnlyStrategy -i 1h \
  -p BTC/USDC:USDC \
  --eps --max-open-trades 1
```

Flag notes:
- `--data-format-ohlcv feather` — data is stored as Feather.
- `--eps` — `--enable-position-stacking`, allows re-entry.
- `-p BTC/USDC:USDC` — futures pair notation (base/quote:settle).

---

## Useful Freqtrade Docs

- Strategy 101: https://www.freqtrade.io/en/stable/strategy-101/
- Exchanges → Hyperliquid: https://www.freqtrade.io/en/stable/exchanges/#hyperliquid
- Historical data note (upstream Hyperliquid): https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data
