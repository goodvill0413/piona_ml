# ===========================================
# 📊 KIS API 실제 과거 데이터 수집 (더미 없음)
# ===========================================
import os
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time

# -------------------------------------------
# 1️⃣ 환경설정
# -------------------------------------------
env_path = os.path.join("D:\\piona_ml", ".env")
load_dotenv(env_path)

APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")
ACCESS_TOKEN_PATH = r"D:\piona_ml\access_token_real.json"
DATA_DIR = r"D:\piona_ml\data"
BASE_URL = "https://openapi.koreainvestment.com:9443"

def load_access_token():
    """액세스 토큰 로드"""
    try:
        with open(ACCESS_TOKEN_PATH, "r", encoding="utf-8") as f:
            token_data = json.load(f)
        return token_data["access_token"]
    except Exception as e:
        print(f"❌ 토큰 로드 실패: {e}")
        return None

def fetch_historical_data(symbol, period_days=120):
    """
    KIS API를 통한 과거 데이터 수집
    period_days: 수집할 일수 (기본 100일)
    """
    access_token = load_access_token()
    if not access_token:
        print("❌ 유효한 토큰이 없습니다.")
        return None
    
    print(f"📊 {symbol} {period_days}일 과거 데이터 수집 시작...")
    
    # 종료일 (오늘)
    end_date = datetime.now().strftime("%Y%m%d")
    
    # 시작일 (100일 전)
    start_date = (datetime.now() - timedelta(days=period_days + 30)).strftime("%Y%m%d")
    
    url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-price"
    
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {access_token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": "FHKST01010400",  # 국내주식 기간별시세
    }
    
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",  # 시장구분코드
        "FID_INPUT_ISCD": symbol,       # 종목코드
        "FID_PERIOD_DIV_CODE": "D",     # 기간구분코드 (D:일봉)
        "FID_ORG_ADJ_PRC": "0",        # 수정주가구분코드
    }
    
    all_data = []
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"❌ API 요청 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return None
        
        data = response.json()
        
        if "output" not in data:
            print(f"❌ 응답 데이터 형식 오류: {data}")
            return None
        
        # 데이터 파싱
        for item in data["output"]:
            try:
                record = {
                    "date": pd.to_datetime(item["stck_bsop_date"]).strftime("%Y-%m-%d"),
                    "open": float(item["stck_oprc"]),
                    "high": float(item["stck_hgpr"]),
                    "low": float(item["stck_lwpr"]),
                    "close": float(item["stck_clpr"]),
                    "volume": int(item["acml_vol"])
                }
                all_data.append(record)
            except (ValueError, KeyError) as e:
                print(f"⚠️ 데이터 파싱 오류: {e}, 항목: {item}")
                continue
        
        if not all_data:
            print(f"❌ {symbol} 수집된 데이터 없음")
            return None
        
        # DataFrame 생성 (날짜 오름차순 정렬)
        df = pd.DataFrame(all_data)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        
        # 최신 100일만 유지
        df = df.tail(period_days)
        
        print(f"✅ {symbol} 데이터 수집 완료: {len(df)}일")
        print(f"   기간: {df['date'].min()} ~ {df['date'].max()}")
        print(f"   현재가: {df['close'].iloc[-1]:,}원")
        
        return df
        
    except Exception as e:
        print(f"❌ {symbol} 데이터 수집 실패: {e}")
        return None

def fetch_all_symbols_data(symbols=None, period_days=100):
    """모든 종목의 과거 데이터 수집"""
    if symbols is None:
        symbols = ["005930", "000660", "373220"]  # 삼성전자, SK하이닉스, LG에너지솔루션
    
    print("🚀 전체 종목 과거 데이터 수집 시작!")
    print("=" * 50)
    
    os.makedirs(DATA_DIR, exist_ok=True)
    
    success_count = 0
    
    for i, symbol in enumerate(symbols):
        print(f"\n📈 [{i+1}/{len(symbols)}] {symbol} 처리 중...")
        
        df = fetch_historical_data(symbol, period_days)
        
        if df is not None:
            # CSV 파일로 저장 (기존 파일 덮어쓰기)
            save_path = os.path.join(DATA_DIR, f"{symbol}.csv")
            df.to_csv(save_path, index=False, encoding="utf-8-sig")
            print(f"💾 저장 완료: {save_path}")
            success_count += 1
        else:
            print(f"❌ {symbol} 수집 실패")
        
        # API 요청 간격 (과도한 요청 방지)
        if i < len(symbols) - 1:
            print("⏳ API 대기 중... (1초)")
            time.sleep(1)
    
    print("\n" + "=" * 50)
    print(f"✅ 전체 수집 완료: {success_count}/{len(symbols)} 성공")
    
    # 수집된 데이터 요약
    print("\n📊 수집 데이터 요약:")
    for symbol in symbols:
        file_path = os.path.join(DATA_DIR, f"{symbol}.csv")
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            print(f"   {symbol}: {len(df)}일, 최신가: {df['close'].iloc[-1]:,}원")
    
    return success_count

def update_with_realtime_data():
    """실시간 데이터로 기존 과거 데이터 업데이트"""
    print("\n🔄 실시간 데이터로 업데이트 중...")
    
    symbols = ["005930", "000660", "373220"]
    
    for symbol in symbols:
        # 기존 과거 데이터 로드
        historical_path = os.path.join(DATA_DIR, f"{symbol}.csv")
        realtime_path = os.path.join(DATA_DIR, f"{symbol}_realtime.csv")
        
        if not os.path.exists(historical_path):
            print(f"⚠️ {symbol} 과거 데이터 없음, 실시간 데이터로 오늘 데이터 생성")
            continue
        
        if not os.path.exists(realtime_path):
            print(f"⚠️ {symbol} 실시간 데이터 없음")
            continue
        
        try:
            # 과거 데이터 로드
            df_historical = pd.read_csv(historical_path)
            df_historical['date'] = pd.to_datetime(df_historical['date'])
            
            # 실시간 데이터 로드
            df_realtime = pd.read_csv(realtime_path, names=['time', 'price', 'volume', 'foreign'])
            
            if len(df_realtime) == 0:
                continue
            
            # 오늘 날짜 확인
            today = datetime.now().date()
            latest_historical_date = df_historical['date'].max().date()
            
            # 오늘 데이터가 없으면 실시간 데이터로 추가
            if today > latest_historical_date:
                today_data = {
                    'date': today,
                    'open': df_realtime['price'].iloc[0],
                    'high': df_realtime['price'].max(),
                    'low': df_realtime['price'].min(),
                    'close': df_realtime['price'].iloc[-1],
                    'volume': df_realtime['volume'].iloc[-1]
                }
                
                # 새 데이터 추가
                new_row = pd.DataFrame([today_data])
                new_row['date'] = pd.to_datetime(new_row['date'])
                df_updated = pd.concat([df_historical, new_row], ignore_index=True)
                
                # 저장
                df_updated.to_csv(historical_path, index=False, encoding="utf-8-sig")
                print(f"✅ {symbol} 오늘 데이터 추가: {today_data['close']:,}원")
            else:
                # 오늘 데이터가 있으면 실시간 가격으로 업데이트
                df_historical.loc[df_historical['date'].dt.date == today, 'close'] = df_realtime['price'].iloc[-1]
                df_historical.loc[df_historical['date'].dt.date == today, 'volume'] = df_realtime['volume'].iloc[-1]
                df_historical.to_csv(historical_path, index=False, encoding="utf-8-sig")
                print(f"✅ {symbol} 오늘 데이터 업데이트: {df_realtime['price'].iloc[-1]:,}원")
                
        except Exception as e:
            print(f"❌ {symbol} 실시간 업데이트 실패: {e}")

if __name__ == "__main__":
    print("📊 KIS API 실제 과거 데이터 수집기")
    print("=" * 40)
    
    # 1. 과거 데이터 수집 (100일)
    success_count = fetch_all_symbols_data(period_days=120)
    
    # 2. 실시간 데이터로 업데이트
    if success_count > 0:
        update_with_realtime_data()
    
    print("\n🎯 데이터 준비 완료!")
    print("이제 predict_model_enhanced_complete.py를 다시 실행하세요!")
