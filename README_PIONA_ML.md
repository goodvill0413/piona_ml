# 🚀 PIONA ML - CREON + ML 통합 시스템

## 📋 개요

CREON Plus API로 88일 데이터를 수집하여 변곡점 분석 및 ML 예측을 수행하고,
최종 신호를 KIS 자동매매 시스템에 전달하는 분석 시스템입니다.

## 🎯 시스템 구조

```
[CREON API] - piona_ml 폴더
   ↓ 88일 데이터 수집
[변곡점 분석] - ichimoku_inflection_analysis.py
   ↓ 9, 13, 26, 33, 42, 51, 65, 77, 88일 변곡
[ML 예측] - train_model.py + predict_model.py
   ↓ 변곡점 40% + ML 60%
[result.json] - 최종 신호 저장
   ↓
[KIS 자동매매] - piona_trader 폴더
   ↓ 모의투자 실행
```

## 📁 폴더 구조

```
D:\piona_ml\
├── fetch_data_creon.py          ← CREON API 88일 데이터 수집
├── ichimoku_inflection_analysis.py  ← 변곡점 분석
├── train_model.py               ← ML 모델 학습
├── predict_model.py             ← ML 예측
├── ml_report.py                 ← 정확도 리포트
├── data\
│   ├── 005930_88days.csv       ← CREON 데이터
│   ├── 000660_88days.csv
│   └── 373220_88days.csv
├── backup\
│   └── model.pkl               ← 학습된 모델
└── result.json                 ← 최종 신호 (KIS가 읽음)
```

## 🔧 필수 요구사항

### 1. CREON Plus 설정
- ✅ Windows 환경
- ✅ 32bit Python 환경
- ✅ CREON Plus 설치 및 로그인
- ✅ 관리자 권한 실행

### 2. Python 패키지
```bash
pip install pywin32 pandas numpy scikit-learn joblib
```

### 3. pywin32 설치 후 필수 작업
```bash
python -m pywin32_postinstall -install
```

## 🚀 사용 방법

### 1단계: CREON 데이터 수집

```bash
cd D:\piona_ml
python fetch_data_creon.py
```

**결과:**
```
📊 005930 데이터 수집 중... (88일)
✅ 005930 데이터 수집 완료: 88건
💾 005930 저장 완료 → D:\piona_ml\data\005930_88days.csv
```

### 2단계: 변곡점 분석

```python
# ichimoku_inflection_analysis.py 사용
from ichimoku_inflection_analysis import IchimokuInflectionAnalysis
import pandas as pd

# 분석기 생성
analyzer = IchimokuInflectionAnalysis()

# 데이터 로드
df = pd.read_csv("data/005930_88days.csv")

# 변곡점 분석
signals = analyzer.calculate_inflection_signals(df, "005930")

print(f"변곡점 신호: {signals}")
```

### 3단계: ML 학습

```bash
python train_model.py
```

**결과:**
```
✅ 학습 완료: D:\piona_ml\backup\model.pkl
정확도: 72.5%
```

### 4단계: ML 예측

```bash
python predict_model.py
```

**결과:**
```
✅ 예측 완료: D:\piona_ml\result.json
{
  "005930": {
    "ml_score": 75.3,
    "inflection_score": 85.0,
    "combined_score": 79.2,
    "action": "STRONG_BUY"
  }
}
```

### 5단계: KIS 자동매매 실행

```bash
cd D:\piona_trader
python main.py --mode full
```

KIS 트레이더가 `result.json`을 읽어서 자동 매매 실행!

## 📊 변곡점 분석 상세

### 9개 핵심 변곡일
```
9일  - 초단기 전환
13일 - 조정 끝 신호
26일 - 정배열 진입
33일 - 중기 추세 확인
42일 - 3파 시작 조건
51일 - 불가항력 변곡 ⭐
65일 - 대변곡 (고점 주의)
77일 - 대변곡 (소멸갭 주의)
88일 - 장기 추세 전환
```

### 변곡점 신호 강도
```python
if signal_strength >= 70:
    "STRONG_BUY"  # 강력 매수
elif signal_strength >= 50:
    "BUY"         # 매수
elif signal_strength <= -50:
    "SELL"        # 매도
```

## 🎯 최종 신호 생성 로직

```python
# 변곡점 분석 점수
inflection_score = analyze_inflection(data)  # 0~100

# ML 예측 점수
ml_score = ml_model.predict(data)  # 0~100

# 최종 점수 (가중 평균)
combined_score = (ml_score * 0.6) + (inflection_score * 0.4)

# 매매 신호
if combined_score >= 70:
    action = "STRONG_BUY"  # 강력 매수
elif combined_score >= 50:
    action = "BUY"          # 매수
elif combined_score <= 30:
    action = "SELL"         # 매도
else:
    action = "HOLD"         # 관망
```

## ⚙️ 자동화 설정

### 배치 파일 생성 (run_piona_ml.bat)
```batch
@echo off
cd /d D:\piona_ml
echo [%date% %time%] CREON 데이터 수집 시작

REM 1. 데이터 수집
python fetch_data_creon.py

REM 2. ML 예측
python predict_model.py

REM 3. 결과 확인
type result.json

echo [%date% %time%] 분석 완료
pause
```

### Windows 작업 스케줄러
- 매일 오전 8:50 실행 (장 시작 전)
- `run_piona_ml.bat` 실행

## 🔍 문제 해결

### CREON 연결 실패
```
❌ CREON Plus 연결 실패
```

**해결 방법:**
1. CREON Plus 실행 확인
2. 로그인 상태 확인
3. 32bit Python 환경 확인
4. 관리자 권한으로 실행

### pywin32 오류
```
ImportError: No module named 'win32com'
```

**해결 방법:**
```bash
pip install pywin32
python -m pywin32_postinstall -install
```

### 데이터 부족 경고
```
⚠️ 데이터 부족: 최소 88일 필요
```

**해결 방법:**
- `fetch_data_creon.py` 실행
- days 파라미터 확인 (88 이상)

## 📈 성능 모니터링

### ML 리포트 확인
```bash
python ml_report.py
```

**출력 예시:**
```
📘 피오나 ML 리포트
대상 종목: 005930
ML 예측 점수: 75.3

=== [정확도 리포트] ===
              precision    recall  f1-score   support
        -1       0.680     0.650     0.664        80
         0       0.720     0.750     0.735       120
         1       0.740     0.720     0.730       100

=== [피처 중요도] ===
SMA_20    : 0.2850
SMA_60    : 0.2340
RSI       : 0.1920
MACD      : 0.1650
Momentum  : 0.1240
```

## 🔄 KIS 트레이더 연동

### result.json 구조
```json
{
  "005930": {
    "symbol": "005930",
    "ml_score": 75.3,
    "inflection_score": 85.0,
    "combined_score": 79.2,
    "action": "STRONG_BUY",
    "confidence": "HIGH",
    "analysis_date": "2025-11-15"
  }
}
```

### KIS 트레이더에서 읽기
```python
# piona_trader/modules/strategy.py 수정

import json

def read_ml_signal(symbol):
    """ML 신호 읽기"""
    with open("D:\\piona_ml\\result.json", "r") as f:
        signals = json.load(f)
    
    return signals.get(symbol, {})

# 매매 결정
ml_signal = read_ml_signal("005930")
if ml_signal.get("action") == "STRONG_BUY":
    # 매수 실행
    trader.buy(symbol, 1)
```

## ⚠️ 주의사항

1. **CREON은 데이터 수집만!**
   - 실제 매매는 KIS로!
   - CREON은 모의투자 지원 안 함

2. **API 호출 제한**
   - CREON: 초당 5회 제한
   - 종목 간 0.2초 대기

3. **32bit Python 필수**
   - CREON COM 객체는 32bit만 지원

4. **관리자 권한 필수**
   - COM 객체 등록 위해 필요

## 📞 지원

문제 발생 시:
1. CREON Plus 재시작
2. Python 재시작 (관리자 권한)
3. pywin32 재설치

---

**🎉 이제 88일 변곡점 분석이 가능합니다!**

CREON으로 정확한 분석 → KIS로 안전한 모의투자! 🚀
