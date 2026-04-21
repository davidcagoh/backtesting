# Hyperliquid - things to note
- USDC as the quote currency
- Check `freqtrade_hyperliquid_download-data/data_content_futures.txt` or `..._spot.txt` for available pairs and timerange

# Backtesting command

```shell
freqtrade backtesting \
  -c /Users/ectan/Coding-new/Trading/freqtrade/user_data/config.json \
  --data-dir /Users/ectan/Coding-new/Trading/freqtrade_hyperliquid_download-data/user_data/data/hyperliquid \
  --data-format-ohlcv feather \
  -s LongOnlyStrategy -i 5m \
  -p BTC/USDC:USDC \
  --eps --max-open-trades 1
```

