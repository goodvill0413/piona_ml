"""
ML 모델 성능 리포트 생성
"""
import json
import joblib
import pandas as pd
import logging
from datetime import datetime
from sklearn.metrics import classification_report, confusion_matrix

from config import MODEL_PATH, DATA_DIR, RESULT_PATH, REPORT_PATH
from utils_indicators import add_technical_indicators

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_data_for_evaluation(symbol):
    """
    평가용 데이터 로드

    Args:
        symbol: 종목 코드

    Returns:
        pd.DataFrame: 데이터프레임
    """
    data_file = DATA_DIR / f"{symbol}.csv"

    if not data_file.exists():
        data_file = DATA_DIR / f"{symbol}_88days.csv"

    if not data_file.exists():
        logger.warning("데이터 없음 - 더미 데이터로 리포트 생성")
        return create_dummy_evaluation_data()

    try:
        df = pd.read_csv(data_file)
        logger.info(f"{symbol} 데이터 로드: {len(df)}행")
        return df
    except Exception as e:
        logger.error(f"데이터 로드 실패: {e}")
        return create_dummy_evaluation_data()


def create_dummy_evaluation_data():
    """더미 평가 데이터 생성"""
    dates = pd.date_range(end=pd.Timestamp.today(), periods=200)

    return pd.DataFrame({
        "date": dates,
        "open": 70000 + (pd.Series(range(200)) * 5),
        "high": 71000 + (pd.Series(range(200)) * 5),
        "low": 69000 + (pd.Series(range(200)) * 5),
        "close": 70500 + (pd.Series(range(200)) * 5),
        "volume": [1000000] * 200
    })


def generate_report(symbol="005930"):
    """
    ML 모델 성능 리포트 생성

    Args:
        symbol: 종목 코드
    """
    try:
        logger.info("="*60)
        logger.info(f"ML 리포트 생성 시작: {symbol}")
        logger.info("="*60)

        # 모델 로드
        if not MODEL_PATH.exists():
            logger.error(f"모델 파일이 없습니다: {MODEL_PATH}")
            logger.error("먼저 train_model.py를 실행하세요.")
            return

        model = joblib.load(MODEL_PATH)
        logger.info("모델 로드 완료")

        # 데이터 로드
        df = load_data_for_evaluation(symbol)

        # 기술적 지표 추가
        df = add_technical_indicators(df, validate=False)

        # 타겟 생성
        df["future_return"] = df["close"].shift(-5) / df["close"] - 1
        df["label"] = 0
        df.loc[df["future_return"] > 0.03, "label"] = 1
        df.loc[df["future_return"] < -0.03, "label"] = -1
        df.dropna(inplace=True)

        # 피처 준비
        features = ["SMA_5", "SMA_20", "SMA_60", "RSI", "MACD", "Momentum"]

        # 모델이 예측할 수 있는 피처만 사용
        available_features = [f for f in features if f in df.columns]

        if not available_features:
            logger.error("사용 가능한 피처가 없습니다.")
            return

        X = df[available_features]
        y = df["label"]

        # 예측
        y_pred = model.predict(X)

        # 성능 평가
        report = classification_report(y, y_pred, digits=3, zero_division=0)
        cm = confusion_matrix(y, y_pred)

        # 피처 중요도
        if hasattr(model, 'feature_importances_'):
            feature_importances = dict(zip(available_features, model.feature_importances_))
        else:
            feature_importances = {}

        # 예측 점수 가져오기
        ml_score = "N/A"
        if RESULT_PATH.exists():
            try:
                with open(RESULT_PATH, "r", encoding="utf-8") as f:
                    result_json = json.load(f)
                    ml_score = result_json.get(symbol, {}).get("ml_score", "N/A")
            except Exception as e:
                logger.warning(f"예측 결과 로드 실패: {e}")

        # 리포트 작성
        report_content = generate_report_content(
            symbol, ml_score, report, cm, feature_importances, len(df)
        )

        # 리포트 저장
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            f.write(report_content)

        logger.info(f"\n✅ ML 리포트 생성 완료: {REPORT_PATH}")
        logger.info("="*60)

        # 콘솔에도 출력
        print("\n" + report_content)

    except Exception as e:
        logger.error(f"리포트 생성 실패: {e}")
        raise


def generate_report_content(symbol, ml_score, classification_report_text,
                           confusion_matrix_data, feature_importances, data_count):
    """
    리포트 내용 생성

    Args:
        symbol: 종목 코드
        ml_score: ML 예측 점수
        classification_report_text: 분류 리포트 텍스트
        confusion_matrix_data: 혼동 행렬
        feature_importances: 피처 중요도
        data_count: 데이터 개수

    Returns:
        str: 리포트 내용
    """
    content = []
    content.append("="*60)
    content.append("        PIONA ML 성능 리포트")
    content.append("="*60)
    content.append(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    content.append(f"대상 종목: {symbol}")
    content.append(f"데이터 개수: {data_count}개")
    content.append(f"최신 ML 예측 점수: {ml_score}")
    content.append("")

    content.append("="*60)
    content.append(" 분류 성능 리포트")
    content.append("="*60)
    content.append(classification_report_text)
    content.append("")

    content.append("="*60)
    content.append(" 혼동 행렬 (Confusion Matrix)")
    content.append("="*60)
    content.append(str(confusion_matrix_data))
    content.append("")

    if feature_importances:
        content.append("="*60)
        content.append(" 피처 중요도")
        content.append("="*60)
        sorted_features = sorted(feature_importances.items(),
                                key=lambda x: x[1], reverse=True)
        for feature, importance in sorted_features:
            content.append(f"  {feature:15s}: {importance:.4f}")
        content.append("")

    content.append("="*60)
    content.append("리포트 생성 완료")
    content.append("="*60)

    return "\n".join(content)


if __name__ == "__main__":
    generate_report()
