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
        return "60m" # will resample to 4H
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

def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def macd(series: pd.Series, fast=12, slow=26, signal=9):
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def bollinger(series: pd.Series, window=20, num_std=2):
    ma = series.rolling(window).mean()
    std = series.rolling(window).std()
    upper = ma + num_std * std
    lower = ma - num_std * std
    return ma, upper, lower

def detect_double_top_bottom(df: pd.DataFrame, lookback: int = 30, tol: float = 0.0005):
    if len(df) < lookback:
        return None
    recent = df.tail(lookback)
    highs = recent["High"]
    lows = recent["Low"]
    top_level = highs.nlargest(2)
    bottom_level = lows.nsmallest(2)
    pattern = None
    ref = recent["Close"].iloc[-1]
    if len(top_level) >= 2 and abs(top_level.iloc[0] - top_level.iloc[1]) <= tol * ref:
        pattern = "double_top"
    if len(bottom_level) >= 2 and abs(bottom_level.iloc[0] - bottom_level.iloc[1]) <= tol * ref:
        pattern = "double_bottom"
    return pattern

def detect_breakout(df: pd.DataFrame, window: int = 20):
    if len(df) < window + 1:
        return None
    recent = df.tail(window + 1)
    prior = recent.iloc[:-1]
    last = recent.iloc[-1]
    if last["Close"] > prior["High"].max():
        return "bull_breakout"
    if last["Close"] < prior["Low"].min():
        return "bear_breakout"
    return None

def score_signal(df: pd.DataFrame):
    close = df["Close"]
    rsi14 = rsi(close, 14)
    macd_line, signal_line, _ = macd(close)
    ema20 = ema(close, 20)
    ema50 = ema(close, 50)
    ema200 = ema(close, 200)
    atr14 = atr(df, 14)
    _, bb_up, bb_low = bollinger(close, 20, 2)

    price = float(close.iloc[-1])
    _rsi = float(rsi14.iloc[-1])
    _macd = float(macd_line.iloc[-1])
    _signal = float(signal_line.iloc[-1])
    _ema20 = float(ema20.iloc[-1])
    _ema50 = float(ema50.iloc[-1])
    _ema200 = float(ema200.iloc[-1])
    _atr = float(atr14.iloc[-1])
    _bb_up = float(bb_up.iloc[-1])
    _bb_low = float(bb_low.iloc[-1])

    score = 0.0
    reasons = []

    if _rsi < 30:
        score += 1; reasons.append(f"RSI oversold ({_rsi:.1f})")
    elif _rsi > 70:
        score -= 1; reasons.append(f"RSI overbought ({_rsi:.1f})")

    if _macd > _signal:
        score += 1; reasons.append("MACD > Signal")
    else:
        score -= 1; reasons.append("MACD < Signal")

    if price > _ema20 > _ema50 > _ema200:
        score += 1; reasons.append("EMA20>50>200 uptrend")
    elif price < _ema20 < _ema50 < _ema200:
        score -= 1; reasons.append("EMA20<50<200 downtrend")

    if price <= _bb_low:
        score += 0.5; reasons.append("Near/Below lower Bollinger")
    elif price >= _bb_up:
        score -= 0.5; reasons.append("Near/Above upper Bollinger")

    patt = detect_double_top_bottom(df)
    if patt == "double_bottom":
        score += 1; reasons.append("Double bottom")
    elif patt == "double_top":
        score -= 1; reasons.append("Double top")

    brk = detect_breakout(df)
    if brk == "bull_breakout":
        score += 1; reasons.append("Bullish breakout")
    elif brk == "bear_breakout":
        score -= 1; reasons.append("Bearish breakout")

    direction = "HOLD"
    if score >= 2:
        direction = "BUY"
    elif score <= -2:
        direction = "SELL"

    return dict(
        price=price,
        rsi=_rsi,
        macd=_macd,
        macd_signal=_signal,
        ema20=_ema20,
        ema50=_ema50,
        ema200=_ema200,
        atr=_atr,
        score=score,
        direction=direction,
        reasons=reasons
    )
    
def sl_tp_from_atr(entry: float, direction: str, atr_val: float, sl_mult: float, tp_mult: float, pv: float):
    if direction == "BUY":
        sl = entry - sl_mult * atr_val
        tp = entry + tp_mult * atr_val
        sl_pips = (entry - sl) / pv
        tp_pips = (tp - entry) / pv
    elif direction == "SELL":
        sl = entry + sl_mult * atr_val
        tp = entry - tp_mult * atr_val
        sl_pips = (sl - entry) / pv
        tp_pips = (entry - tp) / pv
    else:
        return None, None, 0.0, 0.0, 0.0

    rr = tp_pips / sl_pips if sl_pips > 0 else 0.0
    return round(sl, 5), round(tp, 5), float(sl_pips), float(tp_pips), float(rr)
    
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
    if direction in ("BUY", "SELL"):
        sl, tp, sl_pips, tp_pips, rr = sl_tp_from_atr(
            entry, direction, atr_val, cfg["risk"]["atr_sl_mult"], cfg["risk"]["atr_tp_mult"], pv
        )

    abs_score = abs(res["score"])
    if abs_score <= 1.5:
        conf = 50 + 10 * abs_score
    elif abs_score <= 2.5:
        conf = 70 + 15 * (abs_score - 2)
    else:
        conf = min(95, 85 + 5 * (abs_score - 3))

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
