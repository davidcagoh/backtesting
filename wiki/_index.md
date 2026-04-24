# Backtesting Wiki

Crypto strategy backtesting scaffolding built on [Freqtrade](https://www.freqtrade.io/en/stable/), targeting Hyperliquid (USDC-quoted) markets. Dormant since ~2025; being revisited in 2026-04 as a potential base for actively trading personal crypto holdings.

**Last updated:** 2026-04-24

---

## Contents

- [learnings.md](learnings.md) — confirmed facts, open questions, ruled-out directions
- `decisions/` — engineering/design decisions (empty)
- `experiments/` — backtest runs and results (empty)

---

## Repository Layout

This repo is a wrapper around two **git-linked subprojects** (tracked as gitlinks, but no `.gitmodules` — they're standalone clones that happen to live here):

| Path | Role | Upstream |
|------|------|----------|
| `freqtrade/` | Clone of the Freqtrade starter. Strategy code, config, and the `freqtrade` CLI live here. | github.com/freqtrade/freqtrade |
| `freqtrade_hyperliquid_download-data/` | Holds OHLCV data for Hyperliquid under `user_data/data/hyperliquid/`. Freqtrade has no native Hyperliquid downloader yet, so data came from an external source (exact provenance lost). | unknown — third-party Hyperliquid dump |
| `notes.md` | Original crib sheet: Hyperliquid quote = USDC, pair lists in `data_content_{spot,futures}.txt`, canonical `freqtrade backtesting` command. | — |

> **State as of 2026-04-24:** both subproject directories are empty on this machine. The gitlink SHAs are recorded but the working trees need to be re-cloned before anything runs.

---

## Current Status

- **What works (historically):** A `LongOnlyStrategy` backtested on `BTC/USDC:USDC` 5m candles on Hyperliquid via the command in `notes.md`.
- **What's missing now:** Subproject working trees aren't checked out locally. Paths in `notes.md` point to `/Users/ectan/...` (original author's machine) — need path fixes for this environment.
- **Why we're back:** Considering using this to backtest strategies against real personal crypto allocations. Speed of iteration is the first bottleneck worth attacking.

---

## Canonical Backtest Command

From `notes.md` — paths are Ethan's original; rewrite for your machine before running:

```shell
freqtrade backtesting \
  -c /Users/ectan/Coding-new/Trading/freqtrade/user_data/config.json \
  --data-dir /Users/ectan/Coding-new/Trading/freqtrade_hyperliquid_download-data/user_data/data/hyperliquid \
  --data-format-ohlcv feather \
  -s LongOnlyStrategy -i 5m \
  -p BTC/USDC:USDC \
  --eps --max-open-trades 1
```

Flags worth remembering:
- `--data-format-ohlcv feather` — data is stored as Feather, not the Freqtrade default JSON/parquet.
- `--eps` — enable position-stacking (`--enable-position-stacking`), needed when the strategy might re-enter.
- `-p BTC/USDC:USDC` — the `:USDC` suffix is Freqtrade's futures-pair notation (settlement currency).

---

## Useful Freqtrade Docs

- Strategy 101: https://www.freqtrade.io/en/stable/strategy-101/
- Main docs: https://www.freqtrade.io/en/stable/
