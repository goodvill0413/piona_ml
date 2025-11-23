import os, json, requests
from dotenv import load_dotenv
from datetime import datetime

env_path = os.path.join("D:\\piona_ml", ".env")
load_dotenv(env_path)

APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")

ACCESS_TOKEN_PATH = r"D:\piona_ml\access_token_real.json"
DATA_DIR = r"D:\piona_ml\data"

def load_access_token():
    with open(ACCESS_TOKEN_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["access_token"]

def fetch_price(symbol):
    access_token = load_access_token()
    url = "https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/quotations/inquire-price"
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {access_token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": "FHKST01010100",
    }
    params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": symbol}
    res = requests.get(url, headers=headers, params=params)
    data = res.json().get("output", {})
    if "stck_prpr" not in data:
        print(f"❌ {symbol} 수집 실패: {res.text}")
        return None

    record = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": symbol,
        "price": float(data["stck_prpr"]),
        "volume": int(data["acml_vol"]),
        "foreign": float(data["hts_frgn_ehrt"]),
    }
    print(f"✅ {symbol} 수집: {record}")
    return record

def save_record(record):
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, f"{record['symbol']}_realtime.csv")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{record['time']},{record['price']},{record['volume']},{record['foreign']}\n")

if __name__ == "__main__":
    symbols = ["005930", "000660", "373220"]  # 삼성전자, SK하이닉스, LG에너지솔루션
    for s in symbols:
        r = fetch_price(s)
        if r:
            save_record(r)
