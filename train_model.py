"""
ML 모델 학습 스크립트
"""
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import logging
from pathlib import Path

from config import DATA_DIR, MODEL_PATH, ML_CONFIG
from utils_indicators import add_technical_indicators, validate_dataframe

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_data():
    """
    데이터 디렉토리에서 모든 CSV 파일 로드

    Returns:
        pd.DataFrame: 통합된 데이터프레임

    Raises:
        FileNotFoundError: 데이터 파일이 없을 때
    """
    all_data = []

    if not DATA_DIR.exists():
        logger.warning(f"데이터 디렉토리가 없습니다: {DATA_DIR}")
        return create_dummy_data()

    csv_files = list(DATA_DIR.glob("*.csv"))

    if not csv_files:
        logger.warning("CSV 파일이 없습니다. 더미 데이터 생성 중...")
        return create_dummy_data()

    for file in csv_files:
        try:
            df = pd.read_csv(file)
            logger.info(f"로드: {file.name} ({len(df)}행)")
            all_data.append(df)
        except Exception as e:
            logger.error(f"{file.name} 로드 실패: {e}")

    if not all_data:
        logger.warning("유효한 데이터가 없습니다. 더미 데이터 생성 중...")
        return create_dummy_data()

    combined_df = pd.concat(all_data, ignore_index=True)
    logger.info(f"총 데이터: {len(combined_df)}행")

    return combined_df


def create_dummy_data():
    """
    테스트용 더미 데이터 생성

    Returns:
        pd.DataFrame: 더미 데이터
    """
    logger.info("더미 데이터 생성 중...")

    # 충분한 학습 데이터 생성 (100개)
    np.random.seed(42)
    base_price = 100
    prices = [base_price]

    # 랜덤 워크 생성
    for _ in range(99):
        change = np.random.normal(0.001, 0.02)  # 평균 0.1% 상승, 표준편차 2%
        prices.append(prices[-1] * (1 + change))

    return pd.DataFrame({
        "close": prices,
        "volume": np.random.randint(2000, 3000, 100),
        "high": [p * 1.01 for p in prices],
        "low": [p * 0.99 for p in prices],
        "open": [p * 0.995 for p in prices]
    })


def prepare_training_data(df):
    """
    학습 데이터 준비

    Args:
        df: 원본 데이터프레임

    Returns:
        tuple: (X, y) 피처와 타겟
    """
    try:
        # 기술적 지표 추가
        df = add_technical_indicators(df)

        # 미래 수익률 계산 (5일 후)
        df["future_return"] = df["close"].shift(-5) / df["close"] - 1

        # 레이블 생성 (3% 이상 상승 = 1, 그 외 = 0)
        df["label"] = (df["future_return"] > 0.03).astype(int)

        # 결측치 제거
        df = df.dropna()

        if len(df) < 10:
            raise ValueError("학습 데이터가 부족합니다 (최소 10개 필요)")

        # 피처 선택
        feature_columns = ["SMA_5", "SMA_20", "SMA_60", "RSI", "MACD", "Momentum"]

        X = df[feature_columns]
        y = df["label"]

        logger.info(f"학습 데이터 준비 완료: {len(X)}개 샘플, {len(feature_columns)}개 피처")

        return X, y

    except Exception as e:
        logger.error(f"학습 데이터 준비 실패: {e}")
        raise


def train_model():
    """
    ML 모델 학습 및 저장
    """
    try:
        logger.info("="*60)
        logger.info("ML 모델 학습 시작")
        logger.info("="*60)

        # 데이터 로드
        df = load_data()

        # 학습 데이터 준비
        X, y = prepare_training_data(df)

        # 학습/테스트 분할
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=ML_CONFIG["test_size"],
            random_state=ML_CONFIG["random_state"]
        )

        logger.info(f"학습 세트: {len(X_train)}개, 테스트 세트: {len(X_test)}개")

        # 모델 학습
        model = RandomForestClassifier(
            n_estimators=ML_CONFIG["n_estimators"],
            max_depth=ML_CONFIG["max_depth"],
            min_samples_split=ML_CONFIG["min_samples_split"],
            random_state=ML_CONFIG["random_state"]
        )

        model.fit(X_train, y_train)

        # 모델 평가
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        logger.info(f"학습 완료! 정확도: {accuracy:.2%}")
        logger.info("\n분류 리포트:")
        logger.info("\n" + classification_report(y_test, y_pred))

        # 피처 중요도
        feature_importance = dict(zip(X.columns, model.feature_importances_))
        logger.info("\n피처 중요도:")
        for feature, importance in sorted(feature_importance.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {feature:15s}: {importance:.4f}")

        # 모델 저장
        MODEL_PATH.parent.mkdir(exist_ok=True)
        joblib.dump(model, MODEL_PATH)

        logger.info(f"\n✅ 모델 저장 완료: {MODEL_PATH}")
        logger.info("="*60)

        return model

    except Exception as e:
        logger.error(f"모델 학습 실패: {e}")
        raise


if __name__ == "__main__":
    train_model()
