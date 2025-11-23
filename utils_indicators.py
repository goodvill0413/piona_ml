"""
기술적 지표 계산 유틸리티
"""
import pandas as pd
import numpy as np
from config import INDICATOR_CONFIG


def validate_dataframe(df, required_columns=None):
    """
    DataFrame 유효성 검증

    Args:
        df: 검증할 DataFrame
        required_columns: 필수 컬럼 리스트

    Returns:
        bool: 유효성 여부

    Raises:
        ValueError: DataFrame이 유효하지 않을 때
    """
    if df is None or df.empty:
        raise ValueError("DataFrame이 비어있습니다.")

    if required_columns:
        missing = set(required_columns) - set(df.columns)
        if missing:
            raise ValueError(f"필수 컬럼 누락: {missing}")

    return True


def calculate_rsi(series, period=None):
    """
    RSI (Relative Strength Index) 계산

    Args:
        series: 가격 Series
        period: RSI 기간 (기본값: config에서 로드)

    Returns:
        pd.Series: RSI 값
    """
    if period is None:
        period = INDICATOR_CONFIG["rsi_period"]

    try:
        delta = series.diff()
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        avg_gain = pd.Series(gain).rolling(period).mean()
        avg_loss = pd.Series(loss).rolling(period).mean()

        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))

        return rsi
    except Exception as e:
        raise ValueError(f"RSI 계산 오류: {e}")


def calculate_macd(series, fast=None, slow=None, signal=None):
    """
    MACD (Moving Average Convergence Divergence) 계산

    Args:
        series: 가격 Series
        fast: 단기 EMA 기간
        slow: 장기 EMA 기간
        signal: 시그널선 기간

    Returns:
        pd.Series: MACD 히스토그램
    """
    if fast is None:
        fast = INDICATOR_CONFIG["macd_fast"]
    if slow is None:
        slow = INDICATOR_CONFIG["macd_slow"]
    if signal is None:
        signal = INDICATOR_CONFIG["macd_signal"]

    try:
        exp1 = series.ewm(span=fast, adjust=False).mean()
        exp2 = series.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()

        return macd - signal_line
    except Exception as e:
        raise ValueError(f"MACD 계산 오류: {e}")


def calculate_bollinger_bands(series, period=None, std_dev=None):
    """
    볼린저 밴드 계산

    Args:
        series: 가격 Series
        period: 이동평균 기간
        std_dev: 표준편차 배수

    Returns:
        tuple: (upper_band, middle_band, lower_band)
    """
    if period is None:
        period = INDICATOR_CONFIG["bb_period"]
    if std_dev is None:
        std_dev = INDICATOR_CONFIG["bb_std"]

    try:
        middle = series.rolling(period).mean()
        std = series.rolling(period).std()

        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        return upper, middle, lower
    except Exception as e:
        raise ValueError(f"볼린저 밴드 계산 오류: {e}")


def add_technical_indicators(df, validate=True):
    """
    기술적 지표 일괄 추가

    Args:
        df: OHLCV 데이터가 포함된 DataFrame
        validate: 데이터 검증 여부

    Returns:
        pd.DataFrame: 지표가 추가된 DataFrame
    """
    if validate:
        validate_dataframe(df, required_columns=["close"])

    try:
        # 이동평균선
        for period in INDICATOR_CONFIG["sma_periods"]:
            df[f"SMA_{period}"] = df["close"].rolling(period).mean()

        # RSI
        df["RSI"] = calculate_rsi(df["close"])

        # MACD
        df["MACD"] = calculate_macd(df["close"])

        # 모멘텀
        df["Momentum"] = df["close"] / df["close"].shift(5) - 1

        # 볼린저 밴드
        upper, middle, lower = calculate_bollinger_bands(df["close"])
        df["BB_upper"] = upper
        df["BB_middle"] = middle
        df["BB_lower"] = lower
        df["BB_position"] = (df["close"] - lower) / (upper - lower)

        # 결측치 처리
        df.fillna(0, inplace=True)

        return df
    except Exception as e:
        raise ValueError(f"기술적 지표 계산 오류: {e}")
