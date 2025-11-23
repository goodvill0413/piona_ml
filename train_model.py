import os, json, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
from dotenv import load_dotenv

# 🌿 환경파일 강제 로드
load_dotenv("D:\\piona_trader\\.env")

DATA_DIR = "D:\\piona_ml\\data"
MODEL_PATH = "D:\\piona_ml\\backup\\model.pkl"
os.makedirs("D:\\piona_ml\\backup", exist_ok=True)

def load_data():
    all_data = []
    for file in os.listdir(DATA_DIR):
        if file.endswith(".csv"):
            df = pd.read_csv(os.path.join(DATA_DIR, file))
            all_data.append(df)
    if not all_data:
        print("⚠️ 데이터 없음, 더미데이터 생성 중...")
        return pd.DataFrame({
            "close": [100, 101, 99, 102, 103],
            "volume": [2000, 2300, 2100, 2500, 2600],
            "high": [101, 102, 100, 103, 104],
            "low": [99, 99, 98, 100, 101],
            "label": [1, 0, 0, 1, 1]
        })
    return pd.concat(all_data)

def train_model():
    df = load_data()
    X = df[["close", "volume", "high", "low"]]
    y = df["label"] if "label" in df.columns else (df["close"].pct_change().shift(-1) > 0).astype(int)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    joblib.dump(model, MODEL_PATH)
    print(f"✅ 학습 완료: {MODEL_PATH}")

if __name__ == "__main__":
    train_model()
