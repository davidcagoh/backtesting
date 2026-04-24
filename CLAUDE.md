# CLAUDE.md

## Project context

This is a crypto strategy backtesting setup built on [Freqtrade](https://www.freqtrade.io/en/stable/). Mostly a wrapper repo: real work lives in two git-linked subprojects.

- `freqtrade/` — clone of the Freqtrade starter. Strategies, config, CLI.
- `freqtrade_hyperliquid_download-data/` — external OHLCV dump for Hyperliquid (Freqtrade has no built-in Hyperliquid downloader). Feather format, under `user_data/data/hyperliquid/`.
- `notes.md` — the canonical backtest command and Hyperliquid quirks (USDC quote, pair lists in `data_content_{spot,futures}.txt`).
- `wiki/` — project knowledge base. Read `wiki/_index.md` and `wiki/learnings.md` before substantive work; update them when facts change.

**Current state (2026-04-24):** both subproject directories are empty on disk (gitlinks recorded, working trees not cloned). Original author paths in `notes.md` point at `/Users/ectan/...` and need rewriting for this machine. Goal of the current revisit: evaluate whether this is fast enough / mature enough to back real trading of personal crypto holdings. Don't start "speed optimization" work without first rehydrating and reproducing the baseline backtest — see `wiki/learnings.md` → "What to Focus on Next".

Use the **wiki** skill (`/wiki`) to add papers, decisions, or experiment results as they come up.

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
