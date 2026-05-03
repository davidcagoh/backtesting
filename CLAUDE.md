# CLAUDE.md

## Project context

This is a crypto strategy backtesting setup built on [Freqtrade](https://www.freqtrade.io/en/stable/). Mostly a wrapper repo: real work lives in two git-linked subprojects.

- `freqtrade/` — clone of the Freqtrade starter. Strategies, config, CLI.
- `notes.md` — the canonical backtest command and Hyperliquid quirks (USDC quote, pair lists in `data_content_{spot,futures}.txt`).
- `wiki/` — project knowledge base. Read `wiki/_index.md` and `wiki/learnings.md` before substantive work; update them when facts change. `wiki/reference/` holds stable canonical references (e.g. strategy-archetypes.md).

**Current state (2026-05-03):** Four strategies on the leaderboard. `SmaRegime180` (4h SMA180 + slope gate) passes H7 and full cost modeling: post-all-costs return +5.18%, est. Calmar ~7.2. Fee gotcha: original 6.33% used ccxt's default 0.045%/side (NOT zero-fee); use `--fee 0.00035` CLI flag for actual Hyperliquid taker — the `"fee"` key in config.json exchange block is silently ignored by the backtester. Historical funding drag (−12.08 USDC) is 5.4× larger than taker fees and adversely selected to winning trades. Next: 4-state NH-HMM regime filter. See `wiki/_index.md` leaderboard for current rankings.

**Data sourcing:** Freqtrade's `download-data` is **disabled** for Hyperliquid (`ohlcv_has_history=False`) and Hyperliquid publishes no bulk OHLCV. Use `scripts/download_hyperliquid.py` — it hits `/info candleSnapshot` directly and writes Feather in freqtrade's layout. Hard cap: 5000 candles per (pair, timeframe). See `wiki/decisions/002`.

Use the **wiki** skill (`/wiki`) to add papers, decisions, or experiment results as they come up.

---

## Session Start Routine

At the start of every session, automatically run these four steps and report a brief status — no need to ask first:

1. **Sync wiki:** `git pull origin main` to pick up anything the weekly paper-search agent pushed (scheduled Sunday 4 AM ET — see `wiki/agent-config/paper-search-trigger.md`).
2. **Read state:** Read `wiki/_index.md` and `wiki/learnings.md` — these are the authoritative project state and search priorities. Do this before any substantive work.
3. **Run baseline eval:** `./scripts/run_eval.sh` — runs `LongOnlyStrategy` on 1h BTC/USDC:USDC (~200 days). Primary metric is **Calmar**; also displays **Sharpe**, CAGR, MDD, trade count. If Calmar changes materially from the last recorded value in `wiki/_index.md` leaderboard, something regressed. See `wiki/decisions/003-baseline-eval.md` to change the baseline.
4. **Report:** 4–6 bullets: what the agent added since last session, eval results (Calmar + Sharpe at minimum), open tasks worth doing today.

---

## Behavioral guidelines

Guidelines to reduce common LLM coding mistakes.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
