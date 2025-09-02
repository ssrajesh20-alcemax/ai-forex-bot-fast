import pandas as pd
import numpy as np
import yfinance as yf

def pip_value(pair: str) -> float:
    return 0.01 if "JPY" in pair.upper() else 0.0001

def tf_to_interval(tf: str) -> str:
    tf = tf.lower()
    if tf == "5m":
        return "5m"
    if tf == "15m":
        return "15m"
    if tf == "4h":
        return "60m"  # will resample to 4H
    raise ValueError("Unsupported timeframe (use 5m, 15m, 4h)")

def symbol_to_yf(pair: str) -> str:
    return pair.upper() + "=X"

def fetch_bars(pair: str, tf: str, lookback: str = "7d") -> pd.DataFrame:
    symbol = symbol_to_yf(pair)
    interval = tf_to_interval(tf)
    df = yf.download(symbol, period=lookback, interval=interval, progress=False)
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.rename(columns={
        "open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume",
        "Open": "Open", "High": "High", "Low": "Low", "Close": "Close", "Volume": "Volume"
    })
    df = df.dropna()
    if tf.lower() == "4h":
        df = df.resample("4H").agg({
            "Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"
        }).dropna()
    return df

def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["High"] - df["Low"]
    high_close = np.abs(df["High"] - df["Close"].shift())
    low_close = np.abs(df["Low"] - df["Close"].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    return true_range.rolling(period).mean()

def score_signal(df: pd.DataFrame) -> dict:
    close = df["Close"]
    rsi_val = rsi(close).iloc[-1]
    sma_20 = close.rolling(20).mean().iloc[-1]
    sma_50 = close.rolling(50).mean().iloc[-1]
    current_price = close.iloc[-1]
    atr_val = atr(df).iloc[-1]
    
    score = 0
    reasons = []
    
    # RSI signals
    if rsi_val < 30:
        score += 2
        reasons.append("RSI oversold")
    elif rsi_val > 70:
        score -= 2
        reasons.append("RSI overbought")
    
    # Moving average signals
    if current_price > sma_20 > sma_50:
        score += 1
        reasons.append("Bullish MA alignment")
    elif current_price < sma_20 < sma_50:
        score -= 1
        reasons.append("Bearish MA alignment")
    
    # Determine direction based on score
    if score >= 2:
        direction = "BUY"
    elif score <= -2:
        direction = "SELL"
    else:
        direction = "HOLD"
    
    return {
        "score": score,
        "direction": direction,
        "price": current_price,
        "atr": atr_val,
        "reasons": reasons
    }

def sl_tp_from_atr(entry: float, direction: str, atr_val: float, sl_mult: float, tp_mult: float, pip_value: float) -> tuple:
    if direction == "BUY":
        sl = entry - (atr_val * sl_mult)
        tp = entry + (atr_val * tp_mult)
    else:  # SELL
        sl = entry + (atr_val * sl_mult)
        tp = entry - (atr_val * tp_mult)
    
    sl_pips = abs(entry - sl) / pip_value
    tp_pips = abs(tp - entry) / pip_value
    rr = tp_pips / sl_pips if sl_pips > 0 else 0
    
    return sl, tp, sl_pips, tp_pips, rr

def analyze_pair_tf(pair: str, tf: str, cfg: dict) -> dict:
    lookback = "14d" if tf.lower() != "4h" else "90d"
    df = fetch_bars(pair, tf, lookback=lookback)
    if df is None or df.empty or len(df) < 60:
        return {"pair": pair, "timeframe": tf, "error": "not_enough_data"}
    
    res = score_signal(df)
    entry = res["price"]
    direction = res["direction"]
    atr_val = res["atr"]
    pv = pip_value(pair)
    sl = tp = None
    sl_pips = tp_pips = rr = 0.0
    
    # Calculate confidence based on absolute score
    abs_score = abs(res["score"])
    if abs_score <= 1.5:
        conf = 50 + 10 * abs_score
    elif abs_score <= 2.5:
        conf = 70 + 15 * (abs_score - 2)
    else:
        conf = min(95, 85 + 5 * (abs_score - 3))
    
    # STRONG SIGNAL THRESHOLD GUARDS - CRITICAL SAFETY FILTERS
    # Define minimum thresholds for strong signals
    MIN_SCORE_THRESHOLD = 2.0  # Minimum absolute score for BUY/SELL
    MIN_CONFIDENCE_THRESHOLD = 70.0  # Minimum confidence percentage
    MIN_RR_THRESHOLD = 1.5  # Minimum risk-reward ratio
    
    # Calculate risk metrics if we have a potential BUY/SELL signal
    if direction in ("BUY", "SELL"):
        sl, tp, sl_pips, tp_pips, rr = sl_tp_from_atr(
            entry, direction, atr_val, cfg["risk"]["atr_sl_mult"], cfg["risk"]["atr_tp_mult"], pv
        )
    
    # ENFORCE THRESHOLD GUARDS - Override direction if thresholds not met
    if direction in ("BUY", "SELL"):
        # Check all three critical thresholds
        if (abs_score < MIN_SCORE_THRESHOLD or 
            conf < MIN_CONFIDENCE_THRESHOLD or 
            rr < MIN_RR_THRESHOLD):
            
            # Override to HOLD with clear reason
            direction = "HOLD"
            
            # Add threshold violation reasons
            threshold_reasons = []
            if abs_score < MIN_SCORE_THRESHOLD:
                threshold_reasons.append(f"Score {abs_score:.1f} below threshold {MIN_SCORE_THRESHOLD}")
            if conf < MIN_CONFIDENCE_THRESHOLD:
                threshold_reasons.append(f"Confidence {conf:.1f}% below threshold {MIN_CONFIDENCE_THRESHOLD}%")
            if rr < MIN_RR_THRESHOLD:
                threshold_reasons.append(f"Risk-reward {rr:.2f} below threshold {MIN_RR_THRESHOLD}")
            
            # Update reasons to include threshold failures
            res["reasons"] = res["reasons"] + ["THRESHOLD GUARD: " + "; ".join(threshold_reasons)]
    
    # If signal is still weak after all checks, provide clear feedback
    if direction == "HOLD" and abs_score < 1.0:
        direction = "No strong signal"
    
    return {
        "pair": pair,
        "timeframe": tf,
        "direction": direction,
        "entry": round(entry, 5),
        "stop_loss": sl,
        "take_profit": tp,
        "sl_pips": round(sl_pips, 1),
        "tp_pips": round(tp_pips, 1),
        "rr": round(rr, 2),
        "confidence": round(conf, 1),
        "reasons": res["reasons"]
    }

def analyze(pairs: list, tf: str, cfg: dict) -> list:
    results = []
    for p in pairs:
        try:
            results.append(analyze_pair_tf(p, tf, cfg))
        except Exception as e:
            results.append({"pair": p, "timeframe": tf, "error": str(e)})
    return results
