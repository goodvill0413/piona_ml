import os
import json
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

class IchimokuInflectionAnalysis:
    """
    일목균형표 변곡일 분석 클래스
    KIS 자동매매 시스템과 통합하여 변곡일 기반 매매 신호 생성
    """
    
    def __init__(self, inflection_data_path=None):
        """변곡일 데이터 로드"""
        if inflection_data_path is None:
            # 기본 경로 설정 (uploaded files에서 가져올 수 있도록)
            inflection_data_path = "/mnt/user-data/uploads/inflection_points.json"
        
        with open(inflection_data_path, "r", encoding="utf-8") as f:
            self.inflection_data = json.load(f)
        
        # 변곡일 정의
        self.inflection_points = [9, 13, 26, 33, 42, 51, 65, 77, 88]
    
    def calculate_ichimoku_indicators(self, df):
        """
        일목균형표 기본 지표 계산
        """
        # 전환선 (과거 9일 고가+저가)/2
        period9_high = df['high'].rolling(window=9).max()
        period9_low = df['low'].rolling(window=9).min()
        df['tenkan_sen'] = (period9_high + period9_low) / 2
        
        # 기준선 (과거 26일 고가+저가)/2  
        period26_high = df['high'].rolling(window=26).max()
        period26_low = df['low'].rolling(window=26).min()
        df['kijun_sen'] = (period26_high + period26_low) / 2
        
        # 선행스팬 1 = (전환선 + 기준선) / 2, 26일 선행
        df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(26)
        
        # 선행스팬 2 = (과거 52일 고가+저가)/2, 26일 선행
        period52_high = df['high'].rolling(window=52).max()
        period52_low = df['low'].rolling(window=52).min()
        df['senkou_span_b'] = ((period52_high + period52_low) / 2).shift(26)
        
        # 후행스팬 = 종가를 26일 과거로
        df['chikou_span'] = df['close'].shift(-26)
        
        return df
    
    def find_significant_points(self, df, point_type='low'):
        """
        의미있는 고점/저점 찾기
        point_type: 'low' 또는 'high'
        """
        if point_type == 'low':
            # 저점 찾기 (최근 20일 중 가장 낮은 지점들)
            rolling_min = df['low'].rolling(window=20, center=True).min()
            significant_points = df[df['low'] == rolling_min].copy()
        else:
            # 고점 찾기 (최근 20일 중 가장 높은 지점들)
            rolling_max = df['high'].rolling(window=20, center=True).max()
            significant_points = df[df['high'] == rolling_max].copy()
        
        return significant_points.dropna()
    
    def calculate_inflection_signals(self, df, symbol="005930"):
        """
        현재 시점 기준 변곡일 신호 계산
        """
        signals = {
            "symbol": symbol,
            "current_price": float(df['close'].iloc[-1]) if len(df) > 0 else 0,
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "inflection_signals": {}
        }
        
        if len(df) < 88:  # 최소 88일 데이터 필요
            signals["inflection_signals"]["warning"] = "데이터 부족: 최소 88일 필요"
            return signals
        
        # 일목균형표 지표 계산
        df = self.calculate_ichimoku_indicators(df)
        
        # 최근 저점 찾기 (88일 내)
        recent_lows = self.find_significant_points(df.tail(88), 'low')
        
        if len(recent_lows) > 0:
            latest_low_date = recent_lows.index[-1]
            days_since_low = len(df) - df.index.get_loc(latest_low_date) - 1
            
            # 각 변곡일별 분석
            for inflection_day in self.inflection_points:
                signal_strength = self.analyze_inflection_point(
                    df, latest_low_date, days_since_low, inflection_day
                )
                signals["inflection_signals"][f"D+{inflection_day}"] = signal_strength
        
        return signals
    
    def analyze_inflection_point(self, df, low_date, days_since_low, target_day):
        """
        특정 변곡일 분석
        """
        analysis = {
            "days_since_low": days_since_low,
            "target_day": target_day,
            "status": "pending",
            "signal_strength": 0,
            "recommendations": []
        }
        
        if days_since_low < target_day - 3:
            analysis["status"] = "approaching"
            analysis["signal_strength"] = 0
            analysis["recommendations"].append(f"{target_day}일 변곡 접근 중 - 관찰 필요")
            
        elif target_day - 3 <= days_since_low <= target_day + 3:
            # 변곡일 구간에 진입
            analysis["status"] = "active"
            
            # 변곡일별 구체적 분석
            if target_day == 13:
                strength = self.analyze_13_inflection(df, low_date, days_since_low)
            elif target_day == 26:
                strength = self.analyze_26_inflection(df, low_date, days_since_low)
            elif target_day == 42:
                strength = self.analyze_42_inflection(df, low_date, days_since_low)
            elif target_day == 51:
                strength = self.analyze_51_inflection(df, low_date, days_since_low)
            elif target_day in [65, 77]:
                strength = self.analyze_major_inflection(df, low_date, days_since_low, target_day)
            else:
                strength = self.analyze_general_inflection(df, low_date, days_since_low, target_day)
                
            analysis["signal_strength"] = strength
            
        elif days_since_low > target_day + 3:
            analysis["status"] = "passed"
            analysis["signal_strength"] = self.analyze_inflection_result(df, low_date, target_day)
        
        return analysis
    
    def analyze_13_inflection(self, df, low_date, days_since_low):
        """13일 변곡 분석: 조정 끝 신호"""
        strength = 0
        current_idx = len(df) - 1
        
        # 전환선/기준선 골든크로스 확인
        if current_idx >= 1:
            if (df['tenkan_sen'].iloc[current_idx] > df['kijun_sen'].iloc[current_idx] and
                df['tenkan_sen'].iloc[current_idx-1] <= df['kijun_sen'].iloc[current_idx-1]):
                strength += 30  # 골든크로스 발생
        
        # 후행스팬이 전환선을 위로 통과했는지 확인
        if current_idx >= 26:
            chikou_current = df['close'].iloc[current_idx-26]
            tenkan_current = df['tenkan_sen'].iloc[current_idx-26]
            if chikou_current > tenkan_current:
                strength += 20
                
        # 가격 상승 확인
        if df['close'].iloc[current_idx] > df['close'].iloc[current_idx-5]:
            strength += 15
            
        return min(strength, 100)
    
    def analyze_26_inflection(self, df, low_date, days_since_low):
        """26일 변곡 분석: 정배열 진입"""
        strength = 0
        current_idx = len(df) - 1
        
        # 구름대 위 진입 확인
        current_price = df['close'].iloc[current_idx]
        if (current_idx >= 26 and 
            current_price > df['senkou_span_a'].iloc[current_idx] and
            current_price > df['senkou_span_b'].iloc[current_idx]):
            strength += 40  # 정배열 진입
            
        # 26일 신고가 갱신 확인
        if current_price == df['close'].tail(26).max():
            strength += 30
            
        # 구름 색깔 변화 확인 (양운으로 전환)
        if (df['senkou_span_a'].iloc[current_idx] > df['senkou_span_b'].iloc[current_idx]):
            strength += 30
            
        return min(strength, 100)
    
    def analyze_42_inflection(self, df, low_date, days_since_low):
        """42일 변곡 분석: 3파 시작 조건"""
        strength = 0
        current_idx = len(df) - 1
        
        # 60일 신고가 갱신 확인
        current_price = df['close'].iloc[current_idx]
        if current_price == df['close'].tail(60).max():
            strength += 50  # 60일 신고가 달성
            
        # 선행스팬2 상승 확인
        if (current_idx >= 1 and 
            df['senkou_span_b'].iloc[current_idx] > df['senkou_span_b'].iloc[current_idx-5]):
            strength += 30
            
        # 거래량 증가 확인
        if df['volume'].iloc[current_idx] > df['volume'].tail(10).mean():
            strength += 20
            
        return min(strength, 100)
        
    def analyze_51_inflection(self, df, low_date, days_since_low):
        """51일 변곡 분석: 불가항력 변곡"""
        strength = 0
        current_idx = len(df) - 1
        
        # 강력한 상승 추세 확인
        recent_trend = (df['close'].iloc[current_idx] / df['close'].iloc[current_idx-10] - 1) * 100
        if recent_trend > 5:  # 10일간 5% 이상 상승
            strength += 40
            
        # 구름대 두께 확인 (정배열이 안정적인가)
        cloud_thickness = abs(df['senkou_span_a'].iloc[current_idx] - df['senkou_span_b'].iloc[current_idx])
        if cloud_thickness > df['close'].iloc[current_idx] * 0.02:  # 구름이 충분히 두꺼움
            strength += 35
            
        # 후행스팬이 명확히 구름 위에 있는가
        if (current_idx >= 26 and 
            df['close'].iloc[current_idx-26] > max(df['senkou_span_a'].iloc[current_idx-26], 
                                                   df['senkou_span_b'].iloc[current_idx-26])):
            strength += 25
            
        return min(strength, 100)
    
    def analyze_major_inflection(self, df, low_date, days_since_low, target_day):
        """65일, 77일 등 대변곡 분석"""
        strength = 0
        current_idx = len(df) - 1
        
        if target_day in [65, 77]:
            # 고점 경계 구간 - 소멸 갭 주의
            recent_high = df['high'].tail(5).max()
            if df['close'].iloc[current_idx] < recent_high * 0.95:  # 5% 이상 하락
                strength = -50  # 매도 신호
            else:
                # 지속 상승 중
                volume_surge = df['volume'].iloc[current_idx] > df['volume'].tail(20).mean() * 2
                if volume_surge:
                    strength = -30  # 대량거래 경고
                else:
                    strength = 20   # 지속 관찰
        
        return max(min(strength, 100), -100)
    
    def analyze_general_inflection(self, df, low_date, days_since_low, target_day):
        """기타 변곡일 분석"""
        strength = 0
        current_idx = len(df) - 1
        
        # 기본적인 추세 분석
        price_change = (df['close'].iloc[current_idx] / df['close'].iloc[current_idx-5] - 1) * 100
        if price_change > 2:
            strength += 20
        elif price_change < -2:
            strength -= 20
            
        return max(min(strength, 100), -100)
    
    def analyze_inflection_result(self, df, low_date, target_day):
        """변곡일 통과 후 결과 분석"""
        low_idx = df.index.get_loc(low_date)
        target_idx = min(low_idx + target_day, len(df) - 1)
        
        if target_idx < len(df):
            # 변곡일 이후 성과 측정
            price_at_inflection = df['close'].iloc[target_idx]
            current_price = df['close'].iloc[-1]
            performance = (current_price / price_at_inflection - 1) * 100
            
            if performance > 5:
                return 80  # 성공적인 변곡
            elif performance > 0:
                return 40  # 소폭 상승
            else:
                return -20  # 실패한 변곡
        
        return 0

    def generate_combined_signal(self, inflection_analysis, ml_prediction):
        """
        변곡일 분석과 ML 예측을 결합한 최종 신호 생성
        """
        combined_signal = {
            "symbol": inflection_analysis["symbol"],
            "ml_score": ml_prediction.get("ml_score", 0),
            "inflection_score": 0,
            "combined_score": 0,
            "action": "HOLD",
            "confidence": "LOW",
            "reasons": []
        }
        
        # 변곡일 신호 점수 계산
        active_signals = [
            signal for signal in inflection_analysis["inflection_signals"].values() 
            if isinstance(signal, dict) and signal.get("status") == "active"
        ]
        
        if active_signals:
            avg_strength = sum(signal["signal_strength"] for signal in active_signals) / len(active_signals)
            combined_signal["inflection_score"] = avg_strength
        
        # 최종 점수 결합 (ML 60% + 변곡일 40%)
        ml_score = ml_prediction.get("ml_score", 0)
        inflection_score = combined_signal["inflection_score"]
        
        combined_signal["combined_score"] = (ml_score * 0.6) + (inflection_score * 0.4)
        
        # 매매 액션 결정
        final_score = combined_signal["combined_score"]
        if final_score >= 70:
            combined_signal["action"] = "STRONG_BUY"
            combined_signal["confidence"] = "HIGH"
        elif final_score >= 50:
            combined_signal["action"] = "BUY"
            combined_signal["confidence"] = "MEDIUM"
        elif final_score <= -50:
            combined_signal["action"] = "SELL"
            combined_signal["confidence"] = "MEDIUM"
        elif final_score <= -70:
            combined_signal["action"] = "STRONG_SELL"
            combined_signal["confidence"] = "HIGH"
        else:
            combined_signal["action"] = "HOLD"
            combined_signal["confidence"] = "LOW"
        
        return combined_signal

if __name__ == "__main__":
    # 테스트용 실행
    analyzer = IchimokuInflectionAnalysis()
    
    # 샘플 데이터로 테스트 (실제로는 KIS API에서 가져온 데이터 사용)
    print("📊 일목균형표 변곡일 분석 모듈 로드 완료")
    print("🔄 KIS 시스템과 통합 준비 완료")
