# What We've Learned

Running log. Each entry is a **confirmed fact**, an **open question**, or something **ruled out**.

---

## Confirmed Facts

- **Freqtrade** is the open-source framework this project is built on — covers both a live trading bot and a strategy backtester. We only care about the backtester for now.
- **Hyperliquid uses USDC as the quote currency.** Freqtrade pair notation for futures is `BTC/USDC:USDC` (base/quote:settle).
- **Freqtrade has no built-in Hyperliquid downloader.** For other exchanges it ships a download pipeline; Hyperliquid data was sourced externally (provenance not recorded — Ethan doesn't remember).
- **Data format on disk is Feather**, not the Freqtrade default. Backtests must pass `--data-format-ohlcv feather`.
- **Available pairs and timerange** are enumerated in `freqtrade_hyperliquid_download-data/data_content_spot.txt` and `data_content_futures.txt`.
- **The two subdirectories here are gitlinks**, not submodules (no `.gitmodules`). They're standalone clones co-located in this wrapper repo. Currently not checked out on this machine.

---

## Open Questions

Ordered by how much the answer would change what we do next.

1. **Where did the Hyperliquid OHLCV data actually come from?** Needs to be re-findable so we can refresh it and extend to more pairs. Ethan couldn't remember; search history / shell history / browser history on his machine may have it.
2. **What's the current bottleneck on backtest speed?** The stated goal for this revisit is "make backtesting faster" — but we haven't profiled anything yet. Could be data IO (Feather load), could be strategy evaluation, could be pair × timerange sweep size.
3. **Is Freqtrade's Hyperliquid execution adapter mature enough to go live?** Separate from backtesting — relevant only if this becomes the path to trading real capital.
4. **Which strategies beyond `LongOnlyStrategy` exist in this repo?** Need to check `freqtrade/user_data/strategies/` once the subproject is re-cloned.
5. **Do we want to fork Freqtrade or stay on upstream?** Affects whether Hyperliquid downloader work gets upstreamed or kept local.

---

## Ruled Out

[Nothing yet]

---

## What to Focus on Next

Before any "make backtesting faster" work:

1. **Rehydrate the workspace.** Clone the two subprojects back into this wrapper so `freqtrade/` and `freqtrade_hyperliquid_download-data/` have working trees. Fix the `/Users/ectan/...` paths in `notes.md` / config.
2. **Reproduce the canonical backtest.** Run the command in `notes.md` and confirm it completes. This is the baseline — no optimization makes sense without it.
3. **Profile.** Time a representative backtest. Identify whether speed complaints are real and where time is going.
4. **Then** decide whether to optimize (vectorization, caching, narrower data, parallel pair sweeps) or move on to live-trading questions.
