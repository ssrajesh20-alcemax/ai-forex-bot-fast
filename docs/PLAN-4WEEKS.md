# AI Forex Bot – 4-Week Build Plan

## Week 1: Core & Alerts
- FastAPI /analyze for 7 pairs (GBPUSD, EURUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD) and 5m/15m/4H
- Indicators: RSI(14), MACD(12,26,9), EMA(20/50/200), ATR(14), Bollinger(20,2)
- Patterns: double top/bottom, 20-bar breakout
- SL/TP: ATR-based (JPY pip=0.01; others 0.0001)
- Confidence threshold start: 75%; RR >= 1.5
- Telegram alerts; local JSONL/CSV logging

## Week 2: Automation & Risk Filters (n8n + Calendar + Sheets)
- n8n cron every 1–5 minutes → call /analyze → apply filters → alert + log
- Economic calendar block: Trading Economics/FXStreet; block ±30m around red events
- Sentiment modifiers: Dukascopy/MyFxBook/FXSSI as ±0.3~0.5
- Google Sheets logging per alert; daily Telegram summary

## Week 3: Backtesting & Tuning
- Backtest yfinance data (5m/15m) for 1–2 years
- Tune thresholds: RSI bands, MACD weight, ATR multipliers, EMA spans, confidence_min
- Guardrails: session filter (London/NY), ATR regime filter (skip bottom 20%), duplicate-signal suppression

## Week 4: Paper-Trade & Version Freeze
- Run paper-trading for a week with summaries
- Reliability: retries, auto-restart checks
- Freeze "v1 stable" config; prepare to add crypto/gold later
