# D:\piona_ml\fetch_data_creon_simple.py
"""
CREON Plus API로 88일 데이터 수집 (pandas 없는 버전)
순수 Python만 사용
"""
import win32com.client
import csv
import os
from datetime import datetime
import time

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
    
    def get_stock_data(self, symbol, days=88):
        """
        주가 데이터 수집
        
        Args:
            symbol: 종목코드 (예: "005930")
            days: 수집할 일수 (기본 88일)
        
        Returns:
            list: [{'date': ..., 'open': ..., 'high': ..., 'low': ..., 'close': ..., 'volume': ...}, ...]
        """
        if not self.connected:
            print("❌ CREON API 연결되지 않음")
            return None
        
        try:
            print(f"📊 {symbol} 데이터 수집 중... ({days}일)")
            
            # 종목코드 형식 확인 (A 접두사 추가)
            stock_code = symbol if symbol.startswith('A') else f"A{symbol}"
            print(f"   🔖 사용할 종목코드: {stock_code}")
            
            # 차트 데이터 요청 설정
            self.cp_stock_chart.SetInputValue(0, stock_code)  # 종목코드
            self.cp_stock_chart.SetInputValue(1, ord('2'))    # 기간 요청
            self.cp_stock_chart.SetInputValue(4, days)        # 조회 개수
            self.cp_stock_chart.SetInputValue(5, [0, 1, 2, 3, 4, 8])  # 날짜,시가,고가,저가,종가,거래량
            self.cp_stock_chart.SetInputValue(6, ord('D'))    # 일봉
            
            # 데이터 요청
            ret = self.cp_stock_chart.BlockRequest()
            print(f"   📡 API 요청 결과 코드: {ret}")
            
            # 결과 데이터 수집
            count = self.cp_stock_chart.GetHeaderValue(3)
            print(f"   📊 수신된 데이터 개수: {count}건")
            
            # 에러 체크
            if count == 0:
                error_code = self.cp_stock_chart.GetHeaderValue(0)
                error_msg = self.cp_stock_chart.GetHeaderValue(1)
                print(f"   ⚠️ 에러 코드: {error_code}")
                print(f"   ⚠️ 에러 메시지: {error_msg}")
            
            data_list = []
            
            for i in range(count):
                date_val = self.cp_stock_chart.GetDataValue(0, i)
                date_str = self._convert_date(date_val)
                
                row = {
                    'date': date_str,
                    'open': self.cp_stock_chart.GetDataValue(1, i),
                    'high': self.cp_stock_chart.GetDataValue(2, i),
                    'low': self.cp_stock_chart.GetDataValue(3, i),
                    'close': self.cp_stock_chart.GetDataValue(4, i),
                    'volume': self.cp_stock_chart.GetDataValue(5, i)
                }
                data_list.append(row)
            
            # 날짜순 정렬 (오래된 것부터)
            data_list.sort(key=lambda x: x['date'])
            
            print(f"✅ {symbol} 데이터 수집 완료: {len(data_list)}건")
            return data_list
            
        except Exception as e:
            print(f"❌ {symbol} 데이터 수집 실패: {e}")
            return None
    
    def _convert_date(self, date_int):
        """CREON 날짜 형식(YYYYMMDD) → YYYY-MM-DD 변환"""
        date_str = str(date_int)
        year = date_str[:4]
        month = date_str[4:6]
        day = date_str[6:8]
        return f"{year}-{month}-{day}"
    
    def save_to_csv(self, symbol, data_list, data_dir="D:\\piona_ml\\data"):
        """데이터를 CSV로 저장"""
        if not data_list:
            print(f"⚠️ {symbol} 저장할 데이터 없음")
            return
        
        os.makedirs(data_dir, exist_ok=True)
        
        filename = f"{symbol}_88days.csv"
        filepath = os.path.join(data_dir, filename)
        
        # CSV 저장
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            fieldnames = ['date', 'open', 'high', 'low', 'close', 'volume']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(data_list)
        
        print(f"💾 {symbol} 저장 완료 → {filepath}")
        
        # 데이터 샘플 출력 (최근 5일)
        print(f"\n📈 {symbol} 데이터 샘플 (최근 5일):")
        for row in data_list[-5:]:
            print(f"  {row['date']}: 종가 {row['close']:>10,}원, 거래량 {row['volume']:>12,}주")
    
    def is_connected(self):
        """연결 상태 반환"""
        return self.connected


def main():
    """메인 실행 함수"""
    print("="*60)
    print("CREON Plus 데이터 수집 시작 (pandas 없는 버전)")
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
    for idx, symbol in enumerate(symbols, 1):
        print(f"\n🔄 [{idx}/{len(symbols)}] {symbol} 처리 중...")
        
        # 88일 데이터 수집
        data_list = fetcher.get_stock_data(symbol, days=88)
        
        if data_list:
            # CSV 저장
            fetcher.save_to_csv(symbol, data_list)
        
        # API 호출 제한 준수
        if idx < len(symbols):
            time.sleep(0.5)
    
    print("\n" + "="*60)
    print("✅ 전체 데이터 수집 완료!")
    print("="*60)
    print("\n💡 다음 단계:")
    print("   1. data 폴더에 CSV 파일 확인")
    print("   2. ichimoku_inflection_analysis.py로 변곡점 분석")
    print("   3. ML 모델 학습 및 예측")


if __name__ == "__main__":
    main()
