"""
ML 모델 예측 스크립트
"""
import json
import joblib
import pandas as pd
import logging
from datetime import datetime

from config import MODEL_PATH, RESULT_PATH, DATA_DIR, DEFAULT_SYMBOLS
from utils_indicators import add_technical_indicators

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_model():
    """
    저장된 ML 모델 로드

    Returns:
        sklearn model: 로드된 모델

    Raises:
        FileNotFoundError: 모델 파일이 없을 때
    """
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"모델 파일이 없습니다: {MODEL_PATH}\n"
            "먼저 train_model.py를 실행하여 모델을 학습하세요."
        )

    try:
        model = joblib.load(MODEL_PATH)
        logger.info(f"모델 로드 완료: {MODEL_PATH}")
        return model
    except Exception as e:
        logger.error(f"모델 로드 실패: {e}")
        raise


def load_stock_data(symbol):
    """
    종목 데이터 로드

    Args:
        symbol: 종목 코드

    Returns:
        pd.DataFrame: 주가 데이터
    """
    data_file = DATA_DIR / f"{symbol}.csv"

    if not data_file.exists():
        # _88days.csv 형태도 체크
        data_file = DATA_DIR / f"{symbol}_88days.csv"

    if not data_file.exists():
        logger.warning(f"{symbol} 데이터 파일이 없습니다. 더미 데이터 사용")
        return create_dummy_stock_data(symbol)

    try:
        df = pd.read_csv(data_file)
        logger.info(f"{symbol} 데이터 로드: {len(df)}행")
        return df
    except Exception as e:
        logger.error(f"{symbol} 데이터 로드 실패: {e}")
        return create_dummy_stock_data(symbol)


def create_dummy_stock_data(symbol):
    """
    더미 주가 데이터 생성

    Args:
        symbol: 종목 코드

    Returns:
        pd.DataFrame: 더미 데이터
    """
    # 종목별 기본 가격 설정
    base_prices = {
        "005930": 71000,  # 삼성전자
        "000660": 120000,  # SK하이닉스
        "373220": 400000   # LG에너지솔루션
    }

    base_price = base_prices.get(symbol, 50000)

    return pd.DataFrame({
        "close": [base_price * (1 + i*0.01) for i in range(5)],
        "open": [base_price * (1 + i*0.01) * 0.99 for i in range(5)],
        "high": [base_price * (1 + i*0.01) * 1.02 for i in range(5)],
        "low": [base_price * (1 + i*0.01) * 0.98 for i in range(5)],
        "volume": [1000000] * 5
    })


def predict(symbol="005930"):
    """
    특정 종목에 대한 예측 수행

    Args:
        symbol: 종목 코드

    Returns:
        dict: 예측 결과
    """
    try:
        # 모델 로드
        model = load_model()

        # 데이터 로드
        df = load_stock_data(symbol)

        # 기술적 지표 추가
        df = add_technical_indicators(df, validate=False)

        # 피처 선택
        features = ["SMA_5", "SMA_20", "SMA_60", "RSI", "MACD", "Momentum"]

        # 최신 데이터로 예측
        X = df[features].iloc[-1:].values

        # 예측 수행
        prob = model.predict_proba(X)[0]

        # 클래스 확인 (1 = 상승)
        classes = model.classes_
        if 1 in classes:
            idx = list(classes).index(1)
            ml_score = round(prob[idx] * 100, 2)
        else:
            ml_score = 50.0

        logger.info(f"{symbol} ML 예측 점수: {ml_score}%")

        return {
            "symbol": symbol,
            "ml_score": ml_score,
            "confidence": "HIGH" if ml_score > 70 or ml_score < 30 else "MEDIUM",
            "prediction_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_price": float(df["close"].iloc[-1]) if "close" in df.columns else 0
        }

    except Exception as e:
        logger.error(f"{symbol} 예측 실패: {e}")
        return {
            "symbol": symbol,
            "ml_score": 50.0,
            "confidence": "LOW",
            "error": str(e),
            "prediction_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


def predict_multiple(symbols=None):
    """
    여러 종목 예측

    Args:
        symbols: 종목 코드 리스트 (기본값: DEFAULT_SYMBOLS)

    Returns:
        dict: 전체 예측 결과
    """
    if symbols is None:
        symbols = DEFAULT_SYMBOLS

    logger.info("="*60)
    logger.info(f"ML 예측 시작: {len(symbols)}개 종목")
    logger.info("="*60)

    results = {}

    for symbol in symbols:
        result = predict(symbol)
        results[symbol] = result

    # 결과 저장
    try:
        with open(RESULT_PATH, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"\n✅ 예측 결과 저장: {RESULT_PATH}")
    except Exception as e:
        logger.error(f"결과 저장 실패: {e}")

    logger.info("="*60)

    return results


if __name__ == "__main__":
    # 단일 종목 예측
    result = predict()
    print(f"\n예측 결과: {result}")

    # 또는 여러 종목 예측
    # results = predict_multiple()
    # for symbol, result in results.items():
    #     print(f"{symbol}: {result['ml_score']}%")
