import os
import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime

DATA_DIR = r"D:\piona_ml\data"
BACKUP_DIR = r"D:\piona_ml\backup"
MODEL_PATH = os.path.join(BACKUP_DIR, "model_real.pkl")

def load_data():
    """실시간 CSV 파일 읽기"""
    dfs = []
    for file in os.listdir(DATA_DIR):
        if file.endswith("_realtime.csv"):
            path = os.path.join(DATA_DIR, file)
            df = pd.read_csv(path, names=["time", "price", "volume", "foreign"])
            df["symbol"] = file.replace("_realtime.csv", "")
            dfs.append(df)
    if not dfs:
        print("⚠️ 실데이터 없음. 데이터 수집 먼저 실행하세요.")
        return None
    return pd.concat(dfs, ignore_index=True)

def feature_engineering(df):
    """기초 지표 계산"""
    df["price_change"] = df["price"].pct_change().fillna(0)
    df["vol_change"] = df["volume"].pct_change().fillna(0)
    df["foreign_diff"] = df["foreign"].diff().fillna(0)
    df["target"] = (df["price_change"].shift(-1) > 0).astype(int)  # 다음 틱 상승여부
    return df.dropna()

def train_model(df):
    """RandomForest 기반 간단한 학습"""
    features = ["price", "volume", "foreign", "price_change", "vol_change", "foreign_diff"]
    X = df[features]
    y = df["target"]

    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X, y)

    os.makedirs(BACKUP_DIR, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    print(f"✅ 학습 완료: {MODEL_PATH}")
    print(f"📊 데이터 크기: {len(df)}행, 피처 {len(features)}개")
    return model

if __name__ == "__main__":
    print("🚀 실데이터 기반 모델 학습 시작...")
    df = load_data()
    if df is not None:
        df = feature_engineering(df)
        model = train_model(df)
        print("🎯 최신 모델 저장 완료.")
