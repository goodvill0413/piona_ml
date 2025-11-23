import pandas as pd
import numpy as np

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(period).mean()
    avg_loss = pd.Series(loss).rolling(period).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    return 100 - (100 / (1 + rs))

def calculate_macd(series, short=12, long=26, signal=9):
    exp1 = series.ewm(span=short, adjust=False).mean()
    exp2 = series.ewm(span=long, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd - signal_line

def add_technical_indicators(df):
    df["SMA_20"] = df["close"].rolling(20).mean()
    df["SMA_60"] = df["close"].rolling(60).mean()
    df["RSI"] = calculate_rsi(df["close"])
    df["MACD"] = calculate_macd(df["close"])
    df["Momentum"] = df["close"] / df["close"].shift(5) - 1
    df.fillna(0, inplace=True)
    return df
