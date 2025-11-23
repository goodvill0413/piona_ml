import os
import requests
import json
from dotenv import load_dotenv

# 🌿 1. 환경변수 로드 (.env 파일에서 APP_KEY, APP_SECRET 읽기)
env_path = os.path.join("D:\\piona_ml", ".env")
load_dotenv(env_path)

APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")
ACCESS_TOKEN_PATH = r"D:\piona_ml\access_token_real.json"

# 🌿 2. access_token 읽기
def load_access_token():
    if not os.path.exists(ACCESS_TOKEN_PATH):
        print("❌ access_token_real.json 파일이 없습니다. 새로 발급 필요.")
        return None
    with open(ACCESS_TOKEN_PATH, "r", encoding="utf-8") as f:
        token_data = json.load(f)
    return token_data.get("access_token")

# 🌿 3. 실서버 토큰 발급 함수
def issue_real_token():
    print("🚀 실서버 토큰 발급 시도 중...")
    url = "https://openapi.koreainvestment.com:9443/oauth2/tokenP"
    headers = {"Content-Type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET
    }
    res = requests.post(url, headers=headers, data=json.dumps(body))
    if res.status_code == 200:
        data = res.json()
        with open(ACCESS_TOKEN_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 토큰 발급 성공! 저장 경로: {ACCESS_TOKEN_PATH}")
        return data["access_token"]
    else:
        print(f"❌ 발급 실패 [{res.status_code}]")
        print(res.text)
        return None

# 🌿 4. 현재가 조회
def get_current_price(symbol):
    access_token = load_access_token()
    if not access_token:
        access_token = issue_real_token()
    if not access_token:
        print("❌ 토큰이 없어 조회 불가")
        return

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
    print(f"📡 상태 코드: {res.status_code}")
    print(res.text)

# 🌿 5. 실행부
if __name__ == "__main__":
    token = issue_real_token()      # 토큰 발급
    get_current_price("005930")     # 삼성전자 현재가 조회
