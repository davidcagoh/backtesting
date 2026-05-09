# Backtesting Wiki

Crypto strategy backtesting setup built on [Freqtrade](https://www.freqtrade.io/en/stable/), targeting Hyperliquid (USDC-quoted) markets. Revived 2026-04 as a possible base for actively trading personal crypto holdings.

**Last updated:** 2026-05-09

**Current state:** Automated research loop live. Weekly paper-search agent (`trig_013s3hXkiYrSnYh2Qes1KPws`, Sun 04:00 ET) scheduled and verified end-to-end on 2026-04-24. Five strategies on the leaderboard. `SmaRegime180` (4h, 32 trades, Feb 2024 → Apr 2026) passes H7 bull-window validation and full cost modeling: post-all-costs return +5.18%, est. Calmar ~7.2. **New (2026-05-09):** `HmmRegime4` backtest run on BTC 1h bear window (Nov 2025 → May 2026, 187d, 74 trades, taker fees). Result: Calmar 26.35 (inflated by tiny MDD), SQN 1.38, **win rate 45.9% vs SmaRegime180's 21.9%** — open hypothesis #5 partially closed. Caveat: HMM fit on full visible window (look-ahead) — next priority is rolling-window refit. Multi-asset OHLCV expansion: 7 Hyperliquid majors (BTC/ETH/SOL/HYPE/ARB/AVAX/DOGE) × {1h, 4h} now downloaded. Funding history (~25k records each) for all 7 coins now on disk. `download_hyperliquid.py` patched: `fundingHistory` API contract changed (flat fields, not `req`-wrapped). Open items: (1) Rolling-window HMM refit to address look-ahead; (2) Multi-asset HmmRegime4 run; (3) Threshold-gated carry strategy (data ready); (4) Calmar unreliable at small MDD denominators — SQN co-primary.

---

## Contents

- [learnings.md](learnings.md) — confirmed facts, open hypotheses, ruled-out directions, search priorities
- `reference/`
  - [strategy-archetypes.md](reference/strategy-archetypes.md) — canonical reference: 7 strategy archetypes from IMC Prosperity podium writeups, annotated with current project state. Stable reference; findings live in `results/` and `learnings.md`.
- `decisions/`
  - [001-drop-external-data-repo.md](decisions/001-drop-external-data-repo.md) — removed the `freqtrade_hyperliquid_download-data` gitlink
  - [002-hyperliquid-deep-history.md](decisions/002-hyperliquid-deep-history.md) — accept the 5000-candle API cap; reconstruct from S3 only if needed
  - [003-baseline-eval.md](decisions/003-baseline-eval.md) — baseline used by `scripts/run_eval.sh` and the Session Start Routine
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
| `HmmRegime4` (4-state GaussianHMM, 1h) | **26.35**⁴ | 1.38 | 1.58 | 1.23 | +5.26% | 1.03% | 74 | BTC 1h, bear, 2025-11-04→2026-05-09 | [2026-05-09](results/2026-05-09-hmm-regime-4.md) |
| `SmaRegime180` (4h SMA180 + slope gate) | **8.68**³ | 1.02 | 2.72 | 0.14 | +2.83% | 1.74% | 32 | BTC 4h, full, 2024-02-12→2026-04-24 | [2026-04-30](results/2026-04-30-sma-regime-180.md) |
| `LongOnlyStrategy` (placeholder SMA cross) | -4.55 | -0.53 | 0.81 | -0.36 | -1.61% | 1.86% | 49 | BTC 1h, bear, 2025-10-06→2026-04-24 | — |
| `TrendFilter200` (1h SMA200 regime filter) | -6.84 | -2.79 | 0.43 | -2.54 | -5.44% | 4.22% | 90 | BTC 1h, bear, 2025-10-06→2026-04-24 | [2026-04-24](results/2026-04-24-trend-filter-200.md) |

² Calmar unreliable at N=6 (SQN 0.69). SmaRegime180 (N=32, SQN 1.02) is the more meaningful data point for this family.

³ Uses ccxt default 0.045%/side fee (not zero-fee as previously documented). Actual Hyperliquid taker (0.035%/side): Calmar 8.86 (+6.39%). Post-all-costs (taker + historical funding): est. Calmar ~7.2 (+5.18%). See [2026-04-30 result card](results/2026-04-30-sma-regime-180.md) for full breakdown.

⁴ Calmar inflated by tiny MDD denominator (1.03%). SQN 1.38 is the more honest comparison vs SmaRegime180 (SQN 1.02). **Look-ahead caveat:** HMM is fit on the full visible window — treat as upper bound on signal quality, not a clean OOS result. Win-rate 45.9% vs SmaRegime180's 21.9% is the headline finding (open hypothesis #5 partially closed). Next: rolling-window HMM refit. See [2026-05-09 result card](results/2026-05-09-hmm-regime-4.md).

**H7 status:** `SmaRegime180` passes — positive Calmar in both bear-only sub-window (6.59) and full bull+bear window (8.68). The slope-gate SMA family is not ruled out. Next: cost modeling + NH-HMM comparison.

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
