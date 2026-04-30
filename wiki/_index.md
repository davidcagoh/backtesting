# Backtesting Wiki

Crypto strategy backtesting setup built on [Freqtrade](https://www.freqtrade.io/en/stable/), targeting Hyperliquid (USDC-quoted) markets. Revived 2026-04 as a possible base for actively trading personal crypto holdings.

**Last updated:** 2026-04-30

**Current state:** Automated research loop live. Weekly paper-search agent (`trig_013s3hXkiYrSnYh2Qes1KPws`, Sun 04:00 ET) scheduled and verified end-to-end on 2026-04-24 — it reads `wiki/learnings.md` priorities, writes to `wiki/papers/`, updates `wiki/learnings.md` with narrowed next-round priorities, commits and pushes. Three strategies on the leaderboard; `SmaRegime720` is the first to show positive total return (+0.80%) and closed-trade Calmar (28.96) in a bear window, but the sample is thin (6 trades) and bull-market validation is pending. Two metric notes: (1) Calmar (daily wallet balance) is misleading for sparse strategies — use closed-trade Calmar going forward; (2) any strategy with positive Calmar in the bear window still needs a bull-window test (H7) before live consideration.

---

## Contents

- [learnings.md](learnings.md) — confirmed facts, open hypotheses, ruled-out directions, search priorities
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
| Evaluating Structured Strategy Backtests: Peer Benchmarks, Regime Timing, and Live Performance | arXiv 2604.18821 | Apr 2026 | P3 — Backtest-vs-live divergence | [backtest-regime-timing-live-performance-2026.md](papers/backtest-regime-timing-live-performance-2026.md) |
| Markov and HMM for Regime Detection in Cryptocurrency Markets: Evidence from Bitcoin (2024–2026) | Preprints.org 202603.0831 | Mar 2026 | P2 — Regime detection (crypto-specific HMM) | [hmm-regime-detection-bitcoin-2026.md](papers/hmm-regime-detection-bitcoin-2026.md) |
| Explainable Regime Aware Investing | arXiv 2603.04441 | Mar 2026 | P2 — Regime detection | [wasserstein-hmm-regime-investing-2026.md](papers/wasserstein-hmm-regime-investing-2026.md) |
| The Two-Tiered Structure of Cryptocurrency Funding Rate Markets | MDPI Mathematics 14(2):346 | Jan 2026 | P1+P3 — Funding rate carry + execution costs | [two-tiered-funding-rate-markets-2026.md](papers/two-tiered-funding-rate-markets-2026.md) |
| Exploring Risk and Return Profiles of Funding Rate Arbitrage on CEX and DEX | Blockchain: Research and Applications (Elsevier) | Aug 2025 | P1 — DEX carry return profile | [dex-carry-funding-rate-arbitrage-2025.md](papers/dex-carry-funding-rate-arbitrage-2025.md) |
| Predictability of Funding Rates | SSRN 5576424 | Oct 2025 | P1 — Funding rate carry signal | [funding-rate-predictability-inan-2025.md](papers/funding-rate-predictability-inan-2025.md) |

---

## Strategy Leaderboard

Primary sort: **Calmar (closed trades)** (CAGR / |MDD|, computed on closed-trade returns only). Sharpe (closed trades) shown as sanity check. Prior entries used daily-wallet-balance Calmar — see note below. See `wiki/decisions/003-baseline-eval.md` for the evaluation baseline.

| Strategy | Calmar (CT) | Sharpe (CT) | CAGR | MDD | Trades | Data | Report |
|---|---:|---:|---:|---:|---:|---|---|
| `SmaRegime720` (1h SMA720 + slope gate) | **28.96** | 0.20 | +1.66% | 0.30% | 6 | BTC 1h, 2025-10-29 → 2026-04-24 | [2026-04-30](results/2026-04-30-sma-regime-720.md) |
| `LongOnlyStrategy` (placeholder SMA cross) | n/a¹ | n/a¹ | -1.61% | 1.86% | 49 | BTC 1h, 2025-10-06 → 2026-04-24 | — |
| `TrendFilter200` (1h SMA200 regime filter) | n/a¹ | n/a¹ | -5.44% | 4.22% | 90 | BTC 1h, 2025-10-06 → 2026-04-24 | [2026-04-24](results/2026-04-24-trend-filter-200.md) |

¹ Prior entries recorded daily-wallet-balance Calmar (-4.55 and -6.84 respectively). Re-run with `--export trades` to get closed-trade Calmar.

**Benchmark (buy-and-hold):** market change -37.20% on the same Oct 2025–Apr 2026 window. Every strategy beats buy-and-hold by a lot, but the baseline is a sustained bear — a zero-activity (flat) strategy would also score highly. Any strategy with positive Calmar here still needs a bull-window test (H7) before live consideration.

**Metric note:** Freqtrade's "Calmar (daily wallet balance)" penalises sparse strategies by including zero-return flat/cash days in the distribution. Use "Calmar (closed trades)" going forward. CT = closed trades.

Rows added here whenever a new strategy is backtested. Link the Report column to the relevant `wiki/results/<date>-<strategy>.md` file.

---

## Repository Layout

| Path | Role |
|------|------|
| `freqtrade/` | Fresh clone of the upstream Freqtrade repo (gitignored — it has its own `.git`). Ships a Hyperliquid adapter. |
| `user_data/config.json` | Minimal Hyperliquid config (dry_run, futures/isolated, USDC stake, Feather format). No keys committed — fill `walletAddress` / `privateKey` only for live trading, not needed for backtesting. |
| `user_data/strategies/LongOnlyStrategy.py` | SMA-cross placeholder strategy so the original `notes.md` command still runs. Replace with real logic. |
| `user_data/data/hyperliquid/` | Where `scripts/download_hyperliquid.py` writes Feather OHLCV files (futures land under `futures/`). |
| `scripts/download_hyperliquid.py` | Custom Hyperliquid OHLCV downloader. Required because freqtrade's built-in `download-data` is disabled for Hyperliquid. |
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
