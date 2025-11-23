"""
PIONA ML 프로젝트 설정 파일
"""
import os
from pathlib import Path

# 프로젝트 루트 디렉토리 (크로스 플랫폼 호환)
BASE_DIR = Path(__file__).parent.absolute()

# 데이터 디렉토리
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = BASE_DIR / "backup"

# 파일 경로
MODEL_PATH = BACKUP_DIR / "model.pkl"
MODEL_ENHANCED_PATH = BACKUP_DIR / "model_enhanced.pkl"
INFLECTION_PATH = BASE_DIR / "inflection_points.json"
RESULT_PATH = BASE_DIR / "result.json"
RESULT_ENHANCED_PATH = BASE_DIR / "result_enhanced.json"
REPORT_PATH = BASE_DIR / "ml_report.txt"

# 환경 변수 파일
ENV_FILE = BASE_DIR / ".env"
ENV_REAL_FILE = BASE_DIR / ".env_real"

# 주요 종목 리스트
DEFAULT_SYMBOLS = ["005930", "000660", "373220"]  # 삼성전자, SK하이닉스, LG에너지솔루션

# 일목균형표 변곡일
INFLECTION_DAYS = [9, 13, 26, 33, 42, 51, 65, 77, 88]

# ML 모델 설정
ML_CONFIG = {
    "n_estimators": 100,
    "max_depth": 10,
    "min_samples_split": 5,
    "random_state": 42,
    "test_size": 0.2
}

# 기술적 지표 설정
INDICATOR_CONFIG = {
    "sma_periods": [5, 20, 60],
    "rsi_period": 14,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "bb_period": 20,
    "bb_std": 2
}

# 데이터 수집 설정
DATA_COLLECTION = {
    "default_days": 88,
    "chart_type": "D",  # 일봉
    "api_delay": 0.2  # API 호출 간 대기 시간 (초)
}

# 디렉토리 생성
DATA_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)
