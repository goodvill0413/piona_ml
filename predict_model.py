import os, json, joblib, pandas as pd
from utils_indicators import add_technical_indicators

MODEL_PATH = r"D:\piona_ml\backup\model.pkl"
RESULT_PATH = r"D:\piona_ml\result.json"
DATA_PATH = r"D:\piona_ml\data"

def predict(symbol="005930"):
    model = joblib.load(MODEL_PATH)
    path = os.path.join(DATA_PATH, f"{symbol}.csv")
    
    if not os.path.exists(path):
        print("⚠️ 데이터 없음, 더미데이터 사용")
        df = pd.DataFrame({
            "close": [71000, 71200, 71500, 71700, 72000],
            "open": [70500]*5, "high": [72500]*5, "low": [70000]*5, "volume": [1000000]*5
        })
    else:
        df = pd.read_csv(path)

    df = add_technical_indicators(df)
    features = ["SMA_20", "SMA_60", "RSI", "MACD", "Momentum"]
    X = df[features].iloc[-1:].values

    try:
        prob = model.predict_proba(X)[0]
        # 클래스 이름 확인
        classes = model.classes_
        if 1 in classes:
            idx = list(classes).index(1)
            ml_score = round(prob[idx] * 100, 2)
        else:
            ml_score = 0.0
    except Exception as e:
        print(f"⚠️ 예측 중 오류 발생: {e}")
        ml_score = 0.0

    result = {symbol: {"ml_score": ml_score}}
    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ 예측 완료: {RESULT_PATH} / 점수 {ml_score}")

if __name__ == "__main__":
    predict()
