import os, json, time, requests, pandas as pd
from dotenv import load_dotenv

# 🌿 환경파일 강제 로드 (항상 piona_trader 기준)
load_dotenv("D:\\piona_trader\\.env")

APP_KEY = os.getenv("APP_KEY")
APP_SECRET = os.getenv("APP_SECRET")
ACCESS_TOKEN_PATH = "D:\\piona_trader\\access_token.json"
BASE_URL = "https://openapivts.koreainvestment.com:29443"  # PAPER 모드

def load_token():
    with open(ACCESS_TOKEN_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["access_token"]

def get_realtime_price(symbol):
    """KIS 모의투자 실시간 시세 조회"""
    url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"
    headers = {
        "authorization": f"Bearer {load_token()}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": "FHKST01010100"
    }
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": symbol}
    resp = requests.get(url, headers=headers, params=params)

    if resp.status_code != 200:
        print(f"❌ {symbol} API 오류: {resp.status_code}")
        return None

    data = resp.json().get("output", {})
    if not data:
        print(f"⚠️ {symbol} 데이터 없음")
        return None

    df = pd.DataFrame([{
        "date": time.strftime("%Y-%m-%d"),
        "symbol": symbol,
        "close": float(data["stck_prpr"]),
        "high": float(data["stck_hgpr"]),
        "low": float(data["stck_lwpr"]),
        "open": float(data["stck_oprc"]),
        "volume": int(data["acml_vol"])
    }])
    return df

if __name__ == "__main__":
    os.makedirs("D:\\piona_ml\\data", exist_ok=True)
    symbols = ["005930", "000660", "373220"]

    for sym in symbols:
        print(f"📊 {sym} 현재가 수집 중...")
        df = get_realtime_price(sym)
        if df is not None:
            save_path = f"D:\\piona_ml\\data\\{sym}.csv"
            df.to_csv(save_path, index=False, encoding="utf-8-sig")
            print(f"✅ {sym} 저장 완료 → {save_path}")
        time.sleep(1)

    print("\n🎯 전체 수집 완료!")
