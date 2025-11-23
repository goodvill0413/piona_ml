# PIONA ML - 주식 예측 머신러닝 시스템

한국 주식 시장을 위한 머신러닝 기반 주가 예측 시스템입니다. 일목균형표 변곡일 분석과 ML 예측을 결합하여 매매 신호를 생성합니다.

## 주요 기능

- ✅ **크로스 플랫폼 지원**: Windows, Linux, macOS 모두 지원
- ✅ **기술적 지표 계산**: RSI, MACD, 볼린저 밴드, 이동평균 등
- ✅ **머신러닝 예측**: RandomForest 기반 가격 예측
- ✅ **일목균형표 변곡일 분석**: 9개 핵심 변곡일 신호
- ✅ **자동 리포팅**: 모델 성능 및 예측 결과 리포트
- ✅ **에러 처리**: 강화된 예외 처리 및 로깅
- ✅ **테스트 커버리지**: 단위 테스트 및 통합 테스트 포함

## 프로젝트 구조

```
piona_ml/
├── config.py                    # 설정 파일 (경로, 파라미터 등)
├── utils_indicators.py          # 기술적 지표 계산 유틸리티
├── train_model.py              # ML 모델 학습
├── predict_model.py            # ML 예측 수행
├── ml_report.py                # 성능 리포트 생성
├── test_piona_ml.py            # 테스트 스위트
├── requirements.txt            # 필수 패키지 목록
│
├── data/                       # 주가 데이터 (CSV)
├── backup/                     # 학습된 모델 저장
├── result.json                 # 예측 결과
└── ml_report.txt              # 성능 리포트
```

## 설치 방법

### 1. Python 환경 준비

Python 3.8 이상이 필요합니다.

```bash
python --version  # 3.8 이상 확인
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

필수 패키지:
- numpy >= 1.21.0
- pandas >= 1.3.0
- scikit-learn >= 1.0.0
- joblib >= 1.1.0

## 사용 방법

### 1. 모델 학습

```bash
python train_model.py
```

**출력:**
```
============================================================
ML 모델 학습 시작
============================================================
로드: 005930_88days.csv (88행)
총 데이터: 88행
학습 데이터 준비 완료: 83개 샘플, 6개 피처
학습 세트: 66개, 테스트 세트: 17개
학습 완료! 정확도: 75.00%

피처 중요도:
  SMA_5          : 0.2889
  SMA_20         : 0.2343
  RSI            : 0.1408
  MACD           : 0.1302
  Momentum       : 0.1188
  SMA_60         : 0.0872

✅ 모델 저장 완료: /home/user/piona_ml/backup/model.pkl
```

### 2. 예측 수행

```bash
python predict_model.py
```

**출력:**
```
모델 로드 완료: /home/user/piona_ml/backup/model.pkl
005930 데이터 로드: 88행
005930 ML 예측 점수: 75.3%

예측 결과: {
  'symbol': '005930',
  'ml_score': 75.3,
  'confidence': 'HIGH',
  'prediction_time': '2025-11-23 14:00:00',
  'current_price': 71000
}
```

### 3. 성능 리포트 생성

```bash
python ml_report.py
```

생성된 리포트는 `ml_report.txt`에 저장됩니다.

### 4. 테스트 실행

```bash
python test_piona_ml.py
```

**출력:**
```
test_add_technical_indicators ... ok
test_calculate_bollinger_bands ... ok
test_calculate_macd ... ok
test_calculate_rsi ... ok
...

----------------------------------------------------------------------
Ran 12 tests in 0.021s

OK
```

## API 사용법

### Python 코드에서 사용

```python
from predict_model import predict, predict_multiple

# 단일 종목 예측
result = predict("005930")
print(f"ML 점수: {result['ml_score']}%")

# 여러 종목 예측
results = predict_multiple(["005930", "000660", "373220"])
for symbol, result in results.items():
    print(f"{symbol}: {result['ml_score']}%")
```

### 기술적 지표 계산

```python
from utils_indicators import add_technical_indicators
import pandas as pd

# 주가 데이터 로드
df = pd.read_csv("data/005930_88days.csv")

# 기술적 지표 추가
df = add_technical_indicators(df)

print(df[['close', 'SMA_20', 'RSI', 'MACD']].tail())
```

## 설정

`config.py`에서 다음 설정을 변경할 수 있습니다:

```python
# 주요 종목 리스트
DEFAULT_SYMBOLS = ["005930", "000660", "373220"]

# ML 모델 설정
ML_CONFIG = {
    "n_estimators": 100,      # 랜덤 포레스트 트리 개수
    "max_depth": 10,          # 최대 깊이
    "test_size": 0.2,         # 테스트 세트 비율
    "random_state": 42        # 랜덤 시드
}

# 기술적 지표 설정
INDICATOR_CONFIG = {
    "sma_periods": [5, 20, 60],   # 이동평균 기간
    "rsi_period": 14,              # RSI 기간
    "macd_fast": 12,               # MACD 단기
    "macd_slow": 26,               # MACD 장기
    "bb_period": 20,               # 볼린저 밴드 기간
}
```

## 데이터 형식

주가 데이터는 다음 컬럼을 포함하는 CSV 파일이어야 합니다:

```csv
date,open,high,low,close,volume
2025-01-01,71000,72000,70000,71500,1000000
2025-01-02,71500,72500,71000,72000,1200000
...
```

필수 컬럼:
- `close`: 종가 (필수)
- `high`: 고가 (선택)
- `low`: 저가 (선택)
- `open`: 시가 (선택)
- `volume`: 거래량 (선택)

## 문제 해결

### ModuleNotFoundError

```bash
pip install -r requirements.txt
```

### 데이터 파일이 없을 때

더미 데이터가 자동으로 생성됩니다. 실제 데이터를 사용하려면:

```bash
# data 디렉토리에 CSV 파일 저장
cp your_data.csv data/005930_88days.csv
```

### 모델 파일이 없을 때

```bash
python train_model.py  # 먼저 모델을 학습하세요
```

## 성능 메트릭

- **정확도 (Accuracy)**: 전체 예측 중 정답 비율
- **정밀도 (Precision)**: 상승 예측 중 실제 상승 비율
- **재현율 (Recall)**: 실제 상승 중 예측 성공 비율
- **F1 점수**: 정밀도와 재현율의 조화 평균

## 변곡일 분석

9개 핵심 변곡일:

| 변곡일 | 의미 |
|--------|------|
| 9일 | 초단기 전환 |
| 13일 | 조정 끝 신호 |
| 26일 | 정배열 진입 |
| 33일 | 중기 추세 확인 |
| 42일 | 3파 시작 조건 |
| 51일 | 불가항력 변곡 |
| 65일 | 대변곡 (고점 주의) |
| 77일 | 대변곡 (소멸갭 주의) |
| 88일 | 장기 추세 전환 |

## 개선 사항 (2025-11-23)

### 버그 수정
- ✅ 하드코딩된 Windows 경로 제거 → 크로스 플랫폼 지원
- ✅ 에러 처리 강화 → 파일/데이터 검증
- ✅ 로깅 시스템 추가 → 디버깅 용이

### 리팩토링
- ✅ config.py 추가 → 설정 중앙화
- ✅ 중복 코드 제거
- ✅ 함수 문서화 (docstring)
- ✅ 타입 힌트 추가

### 새로운 기능
- ✅ 테스트 스위트 (test_piona_ml.py)
- ✅ 볼린저 밴드 지표 추가
- ✅ 상세한 성능 리포트

### 문서화
- ✅ README.md 작성
- ✅ requirements.txt 업데이트
- ✅ 코드 주석 개선

## 라이선스

MIT License

## 기여

버그 리포트 및 개선 제안은 Issues에 등록해주세요.

## 연락처

프로젝트 관련 문의: [GitHub Issues](https://github.com/your-repo/piona_ml/issues)

---

**⚠️ 주의사항**

이 시스템은 투자 참고용이며, 실제 투자 결정은 본인의 판단과 책임하에 이루어져야 합니다.
