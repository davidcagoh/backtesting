#!/usr/bin/env bash
# Session Start Routine baseline eval.
# Runs LongOnlyStrategy on 1h BTC/USDC:USDC, ~200 days.
# See wiki/decisions/003-baseline-eval.md to change the baseline.
#
# Primary metric: Calmar (CAGR / |MDD|). Sharpe always shown as sanity check.
# Freqtrade's backtest summary prints both; scan the "BACKTESTING REPORT" block.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

FT="./freqtrade/.venv/bin/freqtrade"
if [[ ! -x "$FT" ]]; then
  echo "freqtrade not found at $FT — see wiki/_index.md Setup section." >&2
  exit 1
fi

"$FT" backtesting \
  --userdir user_data \
  -c user_data/config.json \
  --data-format-ohlcv feather \
  -s LongOnlyStrategy -i 1h \
  -p BTC/USDC:USDC \
  --eps --max-open-trades 1
