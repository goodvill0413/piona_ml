# D:\piona_ml\fetch_data_creon.py
"""
CREON Plus API로 88일 이상 과거 데이터 수집
변곡점 분석 및 ML 학습용 데이터 생성
"""
import win32com.client
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import os

class CreonDataFetcher:
    """CREON Plus API 데이터 수집 클래스"""
    
    def __init__(self):
        self.connected = False
        self.cp_code_mgr = None
        self.cp_stock_chart = None
        
        print("🔌 CREON Plus 연결 시도...")
        self.connect()
    
    def connect(self):
        """CREON Plus API 연결"""
        try:
            # COM 객체 생성
            self.cp_code_mgr = win32com.client.Dispatch("CpUtil.CpCodeMgr")
            self.cp_stock_chart = win32com.client.Dispatch("CpSysDib.StockChart")
            
            # 연결 상태 확인
            cp_cybos = win32com.client.Dispatch("CpUtil.CpCybos")
            if cp_cybos.IsConnect == 1:
                self.connected = True
                server_type = "실서버" if cp_cybos.ServerType == 1 else "모의서버"
                print(f"✅ CREON Plus 연결 성공! ({server_type})")
            else:
                print("❌ CREON Plus 로그인 필요")
                self.connected = False
                
        except Exception as e:
            print(f"❌ CREON Plus 연결 실패: {e}")
            print("💡 해결 방법:")
            print("   1. CREON Plus가 실행되어 있는지 확인")
            print("   2. Python을 관리자 권한으로 실행")
            print("   3. 32bit Python 환경 확인")
            self.connected = False
    
    def get_stock_data(self, symbol, days=88, chart_type='D'):
        """
        주가 데이터 수집
        
        Args:
            symbol: 종목코드 (예: "005930")
            days: 수집할 일수 (기본 88일)
            chart_type: 'D'(일봉), 'm'(분봉), 'T'(틱)
        
        Returns:
            DataFrame: date, open, high, low, close, volume
        """
        if not self.connected:
            print("❌ CREON API 연결되지 않음")
            return None
        
        try:
            print(f"📊 {symbol} 데이터 수집 중... ({days}일)")
            
            # 차트 데이터 요청 설정
            self.cp_stock_chart.SetInputValue(0, symbol)      # 종목코드
            self.cp_stock_chart.SetInputValue(1, ord('2'))    # 기간 요청
            self.cp_stock_chart.SetInputValue(4, days)        # 조회 개수
            self.cp_stock_chart.SetInputValue(5, [0, 1, 2, 3, 4, 8])  # 날짜,시가,고가,저가,종가,거래량
            self.cp_stock_chart.SetInputValue(6, chart_type)  # 차트 타입
            
            # 데이터 요청
            self.cp_stock_chart.BlockRequest()
            
            # 결과 데이터 수집
            count = self.cp_stock_chart.GetHeaderValue(3)
            
            dates = []
            opens = []
            highs = []
            lows = []
            closes = []
            volumes = []
            
            for i in range(count):
                date_val = self.cp_stock_chart.GetDataValue(0, i)
                dates.append(self._convert_date(date_val))
                opens.append(self.cp_stock_chart.GetDataValue(1, i))
                highs.append(self.cp_stock_chart.GetDataValue(2, i))
                lows.append(self.cp_stock_chart.GetDataValue(3, i))
                closes.append(self.cp_stock_chart.GetDataValue(4, i))
                volumes.append(self.cp_stock_chart.GetDataValue(5, i))
            
            # DataFrame 생성
            df = pd.DataFrame({
                'date': dates,
                'open': opens,
                'high': highs,
                'low': lows,
                'close': closes,
                'volume': volumes
            })
            
            # 날짜순 정렬 (오래된 것부터)
            df = df.sort_values('date').reset_index(drop=True)
            
            print(f"✅ {symbol} 데이터 수집 완료: {len(df)}건")
            return df
            
        except Exception as e:
            print(f"❌ {symbol} 데이터 수집 실패: {e}")
            return None
    
    def _convert_date(self, date_int):
        """CREON 날짜 형식(YYYYMMDD) → datetime 변환"""
        date_str = str(date_int)
        return pd.to_datetime(date_str, format='%Y%m%d')
    
    def get_multiple_stocks(self, symbols, days=88):
        """
        여러 종목 데이터 일괄 수집
        
        Args:
            symbols: 종목코드 리스트
            days: 수집할 일수
        
        Returns:
            dict: {symbol: DataFrame}
        """
        results = {}
        
        for symbol in symbols:
            df = self.get_stock_data(symbol, days)
            if df is not None:
                results[symbol] = df
            
            # API 호출 제한 대응 (0.2초 대기)
            time.sleep(0.2)
        
        return results
    
    def save_to_csv(self, symbol, df, data_dir="D:\\piona_ml\\data"):
        """데이터를 CSV로 저장"""
        os.makedirs(data_dir, exist_ok=True)
        
        filename = f"{symbol}_88days.csv"
        filepath = os.path.join(data_dir, filename)
        
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        print(f"💾 {symbol} 저장 완료 → {filepath}")
    
    def is_connected(self):
        """연결 상태 반환"""
        return self.connected


def main():
    """메인 실행 함수"""
    print("="*60)
    print("CREON Plus 데이터 수집 시작")
    print("="*60)
    
    # CREON 연결
    fetcher = CreonDataFetcher()
    
    if not fetcher.is_connected():
        print("❌ CREON 연결 실패. 프로그램 종료")
        return
    
    # 수집할 종목 리스트
    symbols = ["005930", "000660", "373220"]  # 삼성전자, SK하이닉스, LG에너지솔루션
    
    print(f"\n📋 수집 대상: {len(symbols)}개 종목")
    print(f"📊 수집 기간: 88일")
    print()
    
    # 데이터 수집
    for symbol in symbols:
        print(f"\n🔄 [{symbols.index(symbol)+1}/{len(symbols)}] {symbol} 처리 중...")
        
        # 88일 데이터 수집
        df = fetcher.get_stock_data(symbol, days=88)
        
        if df is not None:
            # CSV 저장
            fetcher.save_to_csv(symbol, df)
            
            # 데이터 샘플 출력
            print(f"\n📈 {symbol} 데이터 샘플 (최근 5일):")
            print(df.tail(5).to_string(index=False))
        
        # API 호출 제한 준수
        time.sleep(0.5)
    
    print("\n" + "="*60)
    print("✅ 전체 데이터 수집 완료!")
    print("="*60)


if __name__ == "__main__":
    main()
