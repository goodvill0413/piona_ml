import os
import json
import joblib
import pandas as pd
from sklearn.metrics import classification_report
from utils_indicators import add_technical_indicators

MODEL_PATH = r"D:\piona_ml\backup\model.pkl"
DATA_PATH = r"D:\piona_ml\data"
RESULT_PATH = r"D:\piona_ml\result.json"
REPORT_PATH = r"D:\piona_ml\ml_report.txt"

def generate_report(symbol="005930"):
    if not os.path.exists(MODEL_PATH):
        print("❌ 모델 파일이 없습니다. 먼저 train_model.py를 실행하세요.")
        return

    model = joblib.load(MODEL_PATH)
    path = os.path.join(DATA_PATH, f"{symbol}.csv")
    if not os.path.exists(path):
        print("⚠️ 데이터 없음 — 더미 데이터로 리포트 생성 중...")
        dates = pd.date_range(end=pd.Timestamp.today(), periods=200)
        df = pd.DataFrame({
            "date": dates,
            "open": 70000 + (pd.Series(range(200)) * 5),
            "high": 71000 + (pd.Series(range(200)) * 5),
            "low": 69000 + (pd.Series(range(200)) * 5),
            "close": 70500 + (pd.Series(range(200)) * 5),
            "volume": 1000000
        })
    else:
        df = pd.read_csv(path)

    df = add_technical_indicators(df)
    df["future_return"] = df["close"].shift(-5) / df["close"] - 1
    df["label"] = 0
    df.loc[df["future_return"] > 0.03, "label"] = 1
    df.loc[df["future_return"] < -0.03, "label"] = -1
    df.dropna(inplace=True)

    features = ["SMA_20", "SMA_60", "RSI", "MACD", "Momentum"]
    X, y = df[features], df["label"]

    preds = model.predict(X)
    report = classification_report(y, preds, digits=3)
    feature_importances = dict(zip(features, model.feature_importances_))

    result_json = {}
    if os.path.exists(RESULT_PATH):
        with open(RESULT_PATH, "r", encoding="utf-8") as f:
            result_json = json.load(f)
    ml_score = result_json.get(symbol, {}).get("ml_score", "N/A")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("📘 피오나 ML 리포트\n")
        f.write(f"대상 종목: {symbol}\n")
        f.write(f"ML 예측 점수: {ml_score}\n\n")
        f.write("=== [정확도 리포트] ===\n")
        f.write(report + "\n")
        f.write("=== [피처 중요도] ===\n")
        for k, v in feature_importances.items():
            f.write(f"{k:10s}: {v:.4f}\n")
        f.write("\n✅ 리포트 생성 완료.\n")

    print(f"✅ ML 리포트 생성 완료 → {REPORT_PATH}")

if __name__ == "__main__":
    generate_report()
