# AI Forex Bot – Free Data Stack and Accuracy Boosters

## Market Price and Redundancy
- yfinance (primary historical/intraday)
- Alpha Vantage (500 calls/day) and Twelve Data (800 calls/day) as fallbacks
- Tip: cache last fetch per minute; resample 1h to 4H

## Sentiment and Positioning
- Dukascopy SWFX, MyFxBook, FXSSI
- Use as small confidence modifiers: ±0.3 to ±0.5; do not overweight

## Economic Calendar
- Trading Economics (free tier) and FXStreet
- Block signals ±30 minutes around high-impact events for USD/EUR/GBP/JPY/AUD/CAD/CHF

## Volatility and Regime
- ATR percentile: skip bottom 20% (chop); widen SL/TP in top 20%
- Session filter: prefer London/NY hours (IST-friendly)

## Confluence Boosters
- Multi-timeframe confirm: allow 5m/15m buys only if 1h EMA20 > EMA50 (+0.5), sell if < (-0.5)
- Market structure: swing highs/lows, daily/weekly pivots (computed)
- Candles: engulfing/pin/inside as small adjustments near key levels

## Breadth & Correlation
- DXY proxy (UUP via yfinance): if DXY strong up and USD-weak signal, -0.3 unless high confluence
- Cross-check EURUSD vs GBPUSD: strong contradiction → -0.3

## Data Quality
- If latest price differs across sources beyond ~0.5–1.0×ATR per pip, mark suspect and skip

## Additional integration notes:
- Use n8n for low/no-code automation, scheduling, calling /analyze, Google Sheets logging, Telegram summaries, and calendar blocks.
- Only upgrade to paid tiers when system is profit-producing.
