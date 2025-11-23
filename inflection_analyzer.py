"""
일목균형표 변곡점 분석기 (pandas 없는 순수 Python 버전)
신창환 이론의 9대 변곡점 분석
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

class IchimokuInflectionAnalyzer:
    """일목균형표 변곡점 분석기"""
    
    def __init__(self):
        self.inflection_points = {
            9: "단기 조정",
            13: "조정 끝 신호", 
            26: "정배열 진입",
            33: "대세 상승",
            42: "강세 지속",
            51: "불가항력 변곡",
            65: "추세 전환 주의",
            77: "장기 변곡",
            88: "대세 전환"
        }
    
    def calculate_ichimoku(self, data: List[Dict]) -> Dict:
        """
        일목균형표 지표 계산
        
        Args:
            data: [{'date': datetime, 'open': float, 'high': float, 'low': float, 'close': float, 'volume': int}, ...]
        
        Returns:
            {'conversion': float, 'base': float, 'span_a': float, 'span_b': float, 'lagging': float}
        """
        if len(data) < 52:
            return None
        
        # 전환선 (9일)
        highs_9 = [d['high'] for d in data[-9:]]
        lows_9 = [d['low'] for d in data[-9:]]
        conversion = (max(highs_9) + min(lows_9)) / 2
        
        # 기준선 (26일)
        highs_26 = [d['high'] for d in data[-26:]]
        lows_26 = [d['low'] for d in data[-26:]]
        base = (max(highs_26) + min(lows_26)) / 2
        
        # 선행스팬 A (전환선 + 기준선) / 2
        span_a = (conversion + base) / 2
        
        # 선행스팬 B (52일)
        highs_52 = [d['high'] for d in data[-52:]]
        lows_52 = [d['low'] for d in data[-52:]]
        span_b = (max(highs_52) + min(lows_52)) / 2
        
        # 후행스팬 (26일 전 종가)
        lagging = data[-26]['close'] if len(data) >= 26 else data[0]['close']
        
        current_price = data[-1]['close']
        
        return {
            'conversion': conversion,
            'base': base,
            'span_a': span_a,
            'span_b': span_b,
            'lagging': lagging,
            'current_price': current_price,
            'cloud_top': max(span_a, span_b),
            'cloud_bottom': min(span_a, span_b),
            'cloud_thickness': abs(span_a - span_b)
        }
    
    def find_lowest_point(self, data: List[Dict], lookback_days: int = 120) -> Tuple[datetime, float]:
        """
        최근 lookback_days 일 내의 최저점 찾기
        
        Returns:
            (최저점 날짜, 최저가)
        """
        recent_data = data[-lookback_days:] if len(data) > lookback_days else data
        
        lowest = min(recent_data, key=lambda x: x['low'])
        return lowest['date'], lowest['low']
    
    def days_since_low(self, current_date: datetime, low_date: datetime) -> int:
        """저점 이후 경과일수 계산"""
        delta = current_date - low_date
        return delta.days
    
    def check_golden_cross(self, ichimoku: Dict) -> bool:
        """전환선이 기준선 위에 있는지 확인"""
        return ichimoku['conversion'] > ichimoku['base']
    
    def check_above_cloud(self, ichimoku: Dict) -> bool:
        """가격이 구름대 위에 있는지 확인"""
        return ichimoku['current_price'] > ichimoku['cloud_top']
    
    def check_lagging_above_price(self, data: List[Dict]) -> bool:
        """후행스팬이 26일 전 가격 위에 있는지 확인"""
        if len(data) < 26:
            return False
        
        current_close = data[-1]['close']
        price_26_days_ago = data[-26]['close']
        
        return current_close > price_26_days_ago
    
    def analyze_9_inflection(self, data: List[Dict], low_date: datetime, days_since: int) -> Dict:
        """
        9일 변곡 분석: 9일 신고가 = 전환선 상승
        
        신창환 이론 핵심:
        - 저점 후 9일째에 9일 신고가를 돌파하면 전환선이 상승한다
        - 전환선 상승 = 골든크로스 가능성 증가
        """
        ichimoku = self.calculate_ichimoku(data)
        if not ichimoku:
            return {'signal': 'insufficient_data', 'strength': 0, 'details': {}}
        
        signal_strength = 0
        details = {}
        
        # 9일 근처인지 확인 (±2일)
        if 7 <= days_since <= 11:
            signal_strength += 20
            details['timing'] = 'near_9_days'
            
            # 9일 신고가 돌파 확인
            recent_9days = data[-9:] if len(data) >= 9 else data
            high_9 = max(d['high'] for d in recent_9days[:-1])  # 오늘 제외한 9일 최고가
            current_high = data[-1]['high']
            
            if current_high > high_9:
                signal_strength += 40  # 9일 신고가 돌파! 매우 중요
                details['new_high_9'] = 'confirmed'
                details['breakout_pct'] = f"{((current_high - high_9) / high_9 * 100):.2f}%"
        
        # 전환선이 상승 중인지 확인
        if len(data) >= 10:
            prev_conversion = (max(d['high'] for d in data[-10:-1]) + min(d['low'] for d in data[-10:-1])) / 2
            if ichimoku['conversion'] > prev_conversion:
                signal_strength += 25
                details['conversion_trend'] = 'rising'
        
        # 전환선이 10일 이평 위에 있는지 (속도 지표)
        if len(data) >= 10:
            ma10 = sum(d['close'] for d in data[-10:]) / 10
            if ichimoku['conversion'] > ma10:
                signal_strength += 15
                details['speed'] = 'fast'  # 빠른 상승
        
        return {
            'signal': 'bullish' if signal_strength >= 60 else 'neutral',
            'strength': signal_strength,
            'details': details,
            'recommendation': '9일 신고가 돌파! 전환선 상승 시작' if signal_strength >= 60 else '9일 변곡 대기'
        }
    
    def analyze_13_inflection(self, data: List[Dict], low_date: datetime, days_since: int) -> Dict:
        """
        13일 변곡 분석: 조정 끝 신호
        
        신창환 이론 핵심:
        - 13일 전후에 골든크로스 발생하면 26일까지 상승 확률 높음!
        - 전환선 > 기준선 = 대세 상승 확정
        """
        ichimoku = self.calculate_ichimoku(data)
        if not ichimoku:
            return {'signal': 'insufficient_data', 'strength': 0, 'details': {}}
        
        signal_strength = 0
        details = {}
        
        # 13일 근처인지 확인 (±2일)
        if 11 <= days_since <= 15:
            signal_strength += 25
            details['timing'] = 'near_13_days'
        
        # 골든크로스 확인 (가장 중요!)
        if self.check_golden_cross(ichimoku):
            signal_strength += 40  # 골든크로스 = 강력한 신호
            details['golden_cross'] = 'confirmed'
            details['target'] = '26일까지 상승 기대'
            
            # 골든크로스 직후인지 확인 (더 강력)
            if len(data) >= 2:
                prev_conv = (max(d['high'] for d in data[-10:-1]) + min(d['low'] for d in data[-10:-1])) / 2
                prev_base = (max(d['high'] for d in data[-27:-1]) + min(d['low'] for d in data[-27:-1])) / 2
                
                if prev_conv <= prev_base and ichimoku['conversion'] > ichimoku['base']:
                    signal_strength += 20  # 방금 골든크로스!
                    details['cross_timing'] = 'just_crossed'
        
        # 13일 신고가 확인
        if len(data) >= 13:
            high_13 = max(d['high'] for d in data[-13:-1])
            if data[-1]['high'] > high_13:
                signal_strength += 20
                details['new_high_13'] = 'confirmed'
        
        # 후행스팬 위치
        if self.check_lagging_above_price(data):
            signal_strength += 15
            details['lagging_span'] = 'bullish'
        
        return {
            'signal': 'strong_bullish' if signal_strength >= 70 else 'bullish' if signal_strength >= 50 else 'neutral',
            'strength': signal_strength,
            'details': details,
            'recommendation': '13일 골든크로스! 26일까지 GO!' if signal_strength >= 70 else '조정 종료, 상승 준비' if signal_strength >= 50 else '추가 확인 필요'
        }
    
    def analyze_26_inflection(self, data: List[Dict], low_date: datetime, days_since: int) -> Dict:
        """
        26일 변곡 분석: 정배열 진입
        
        특징:
        - 구름대 위 진입
        - 26일 신고가
        - 완전한 정배열
        """
        ichimoku = self.calculate_ichimoku(data)
        if not ichimoku:
            return {'signal': 'insufficient_data', 'strength': 0, 'details': {}}
        
        signal_strength = 0
        details = {}
        
        # 26일 근처인지 확인 (±3일)
        if 23 <= days_since <= 29:
            signal_strength += 25
            details['timing'] = 'near_26_days'
        
        # 구름대 위 확인
        if self.check_above_cloud(ichimoku):
            signal_strength += 35
            details['cloud_position'] = 'above'
            details['cloud_thickness'] = f"{ichimoku['cloud_thickness']:.2f}"
        
        # 26일 신고가 확인
        if len(data) >= 26:
            highs_26 = [d['high'] for d in data[-26:]]
            if data[-1]['high'] >= max(highs_26):
                signal_strength += 25
                details['new_high'] = 'confirmed'
        
        # 완전한 정배열
        if (ichimoku['conversion'] > ichimoku['base'] and 
            ichimoku['current_price'] > ichimoku['conversion'] and
            ichimoku['span_a'] > ichimoku['span_b']):
            signal_strength += 15
            details['perfect_alignment'] = 'yes'
        
        return {
            'signal': 'strong_bullish' if signal_strength >= 70 else 'bullish' if signal_strength >= 50 else 'neutral',
            'strength': signal_strength,
            'details': details,
            'recommendation': '본격 상승 구간 진입' if signal_strength >= 70 else '상승 추세 지속' if signal_strength >= 50 else '추가 확인'
        }
    
    def analyze_33_inflection(self, data: List[Dict], low_date: datetime, days_since: int) -> Dict:
        """
        33일 변곡 분석: 대세 상승
        
        특징:
        - 강력한 상승세
        - 높은 거래량
        - 구름대 두꺼워짐
        """
        ichimoku = self.calculate_ichimoku(data)
        if not ichimoku:
            return {'signal': 'insufficient_data', 'strength': 0, 'details': {}}
        
        signal_strength = 0
        details = {}
        
        # 33일 근처인지 확인 (±3일)
        if 30 <= days_since <= 36:
            signal_strength += 20
            details['timing'] = 'near_33_days'
        
        # 저점 대비 상승률
        low_price = min(d['low'] for d in data[-days_since:])
        current_price = data[-1]['close']
        gain_pct = ((current_price - low_price) / low_price) * 100
        details['gain_from_low'] = f"{gain_pct:.2f}%"
        
        if gain_pct > 15:
            signal_strength += 30
        elif gain_pct > 10:
            signal_strength += 20
        
        # 구름대 두께 (강력한 지지)
        if ichimoku['cloud_thickness'] > current_price * 0.03:  # 3% 이상
            signal_strength += 25
            details['cloud_support'] = 'strong'
        
        # 거래량 지속 증가
        if len(data) >= 10:
            recent_volume = sum(d['volume'] for d in data[-5:]) / 5
            previous_volume = sum(d['volume'] for d in data[-10:-5]) / 5
            
            if recent_volume > previous_volume * 1.5:
                signal_strength += 25
                details['volume_trend'] = 'strongly_increasing'
        
        return {
            'signal': 'strong_bullish' if signal_strength >= 70 else 'bullish',
            'strength': signal_strength,
            'details': details,
            'recommendation': '대세 상승 구간, 홀딩 유지' if signal_strength >= 70 else '상승 추세 지속 중'
        }
    
    def analyze_42_inflection(self, data: List[Dict], low_date: datetime, days_since: int) -> Dict:
        """
        42일 변곡 분석: 3파 시작 조건
        
        신창환 이론:
        - 42일 = 26일 + 16일 (피보나치)
        - 3파동 시작 가능성
        - 60일 신고가 돌파 시 강력한 상승
        """
        ichimoku = self.calculate_ichimoku(data)
        if not ichimoku:
            return {'signal': 'insufficient_data', 'strength': 0, 'details': {}}
        
        signal_strength = 0
        details = {}
        
        # 42일 근처인지 확인 (±3일)
        if 39 <= days_since <= 45:
            signal_strength += 20
            details['timing'] = 'near_42_days'
        
        # 60일 신고가 돌파 확인 (중요!)
        if len(data) >= 60:
            high_60 = max(d['high'] for d in data[-60:-1])
            current_high = data[-1]['high']
            
            if current_high > high_60:
                signal_strength += 40  # 60일 신고가 = 강력!
                details['new_high_60'] = 'confirmed'
                details['breakout_pct'] = f"{((current_high - high_60) / high_60 * 100):.2f}%"
        
        # 3파 시작 조건: 26일 변곡 이후 안정적 상승
        if len(data) >= 26:
            # 최근 16일간 (42-26) 안정적 상승인지 확인
            recent_16 = data[-16:]
            rising_days = sum(1 for i in range(1, len(recent_16)) if recent_16[i]['close'] > recent_16[i-1]['close'])
            
            if rising_days >= 10:  # 16일 중 10일 이상 상승
                signal_strength += 25
                details['stable_rise'] = f"{rising_days}/16 days"
        
        # 거래량 폭발 (3파 특징)
        if len(data) >= 10:
            recent_volume = sum(d['volume'] for d in data[-5:]) / 5
            previous_volume = sum(d['volume'] for d in data[-10:-5]) / 5
            
            if recent_volume > previous_volume * 2:  # 2배 이상
                signal_strength += 15
                details['volume_surge'] = 'explosive'
        
        return {
            'signal': 'very_strong_bullish' if signal_strength >= 80 else 'strong_bullish' if signal_strength >= 60 else 'bullish',
            'strength': signal_strength,
            'details': details,
            'recommendation': '3파 시작! 60일 신고가 돌파!' if signal_strength >= 80 else '3파 준비 중' if signal_strength >= 60 else '42일 변곡 진행 중'
        }
    
    def analyze_51_inflection(self, data: List[Dict], low_date: datetime, days_since: int) -> Dict:
        """
        51일 변곡 분석: 불가항력 변곡
        
        특징:
        - 매우 강력한 상승
        - 장기 추세 확립
        - 조정 시 매수 기회
        """
        ichimoku = self.calculate_ichimoku(data)
        if not ichimoku:
            return {'signal': 'insufficient_data', 'strength': 0, 'details': {}}
        
        signal_strength = 0
        details = {}
        
        # 51일 근처인지 확인 (±4일)
        if 47 <= days_since <= 55:
            signal_strength += 20
            details['timing'] = 'near_51_days'
        
        # 저점 대비 상승률
        recent_data = data[-days_since:] if days_since <= len(data) else data
        low_price = min(d['low'] for d in recent_data)
        current_price = data[-1]['close']
        gain_pct = ((current_price - low_price) / low_price) * 100
        details['gain_from_low'] = f"{gain_pct:.2f}%"
        
        if gain_pct > 30:
            signal_strength += 35
        elif gain_pct > 20:
            signal_strength += 25
        
        # 구름대 매우 두꺼움
        if ichimoku['cloud_thickness'] > current_price * 0.05:  # 5% 이상
            signal_strength += 25
            details['cloud_support'] = 'very_strong'
        
        # 후행스팬 강세
        if self.check_lagging_above_price(data):
            signal_strength += 20
            details['lagging_span'] = 'very_bullish'
        
        return {
            'signal': 'very_strong_bullish' if signal_strength >= 80 else 'strong_bullish',
            'strength': signal_strength,
            'details': details,
            'recommendation': '불가항력 상승, 조정 시 매수 기회' if signal_strength >= 80 else '강력한 상승 추세'
        }
    
    def analyze_all_inflections(self, data: List[Dict]) -> Dict:
        """
        현재 시점의 모든 변곡점 분석
        
        Returns:
            {
                'current_date': datetime,
                'low_date': datetime,
                'days_since_low': int,
                'current_price': float,
                'ichimoku': Dict,
                'inflections': {
                    9: {...},
                    13: {...},
                    ...
                },
                'active_signals': [...]
            }
        """
        if len(data) < 52:
            return {'error': '최소 52일 데이터 필요'}
        
        # 최저점 찾기
        low_date, low_price = self.find_lowest_point(data)
        current_date = data[-1]['date']
        days_since = self.days_since_low(current_date, low_date)
        
        # 일목균형표 계산
        ichimoku = self.calculate_ichimoku(data)
        
        # 각 변곡점 분석
        inflections = {}
        
        if days_since >= 7:
            inflections[9] = self.analyze_9_inflection(data, low_date, days_since)
        
        if days_since >= 11:
            inflections[13] = self.analyze_13_inflection(data, low_date, days_since)
        
        if days_since >= 23:
            inflections[26] = self.analyze_26_inflection(data, low_date, days_since)
        
        if days_since >= 30:
            inflections[33] = self.analyze_33_inflection(data, low_date, days_since)
        
        if days_since >= 39:
            inflections[42] = self.analyze_42_inflection(data, low_date, days_since)
        
        if days_since >= 47:
            inflections[51] = self.analyze_51_inflection(data, low_date, days_since)
        
        # 활성 신호 (strength >= 60인 것들)
        active_signals = []
        for day, analysis in inflections.items():
            if analysis['strength'] >= 60:
                active_signals.append({
                    'inflection_point': day,
                    'description': self.inflection_points[day],
                    'signal': analysis['signal'],
                    'strength': analysis['strength'],
                    'recommendation': analysis['recommendation']
                })
        
        return {
            'current_date': current_date,
            'low_date': low_date,
            'low_price': low_price,
            'days_since_low': days_since,
            'current_price': data[-1]['close'],
            'gain_from_low': ((data[-1]['close'] - low_price) / low_price * 100),
            'ichimoku': ichimoku,
            'inflections': inflections,
            'active_signals': active_signals
        }


def print_analysis_report(analysis: Dict):
    """분석 결과를 보기 좋게 출력"""
    
    print("=" * 70)
    print("일목균형표 변곡점 분석 리포트")
    print("=" * 70)
    print()
    
    print(f"📅 현재 날짜: {analysis['current_date'].strftime('%Y-%m-%d')}")
    print(f"📉 최저점 날짜: {analysis['low_date'].strftime('%Y-%m-%d')}")
    print(f"📈 저점 이후 경과: {analysis['days_since_low']}일")
    print(f"💰 현재가: {analysis['current_price']:,.0f}원")
    print(f"📊 저점 대비 수익률: {analysis['gain_from_low']:.2f}%")
    print()
    
    print("-" * 70)
    print("일목균형표 지표")
    print("-" * 70)
    ichi = analysis['ichimoku']
    print(f"전환선 (9일): {ichi['conversion']:,.0f}원")
    print(f"기준선 (26일): {ichi['base']:,.0f}원")
    print(f"선행스팬A: {ichi['span_a']:,.0f}원")
    print(f"선행스팬B: {ichi['span_b']:,.0f}원")
    print(f"구름대 상단: {ichi['cloud_top']:,.0f}원")
    print(f"구름대 하단: {ichi['cloud_bottom']:,.0f}원")
    print(f"구름대 두께: {ichi['cloud_thickness']:,.0f}원 ({ichi['cloud_thickness']/ichi['current_price']*100:.2f}%)")
    print()
    
    print("-" * 70)
    print("변곡점 분석")
    print("-" * 70)
    
    for day, inflection_analysis in analysis['inflections'].items():
        print(f"\n🔹 {day}일 변곡점 - {analysis['inflections'][day].get('description', '')}")
        print(f"   신호: {inflection_analysis['signal']}")
        print(f"   강도: {inflection_analysis['strength']}/100")
        print(f"   추천: {inflection_analysis['recommendation']}")
        
        if inflection_analysis.get('details'):
            print("   세부사항:")
            for key, value in inflection_analysis['details'].items():
                print(f"      - {key}: {value}")
    
    print()
    print("=" * 70)
    print("🎯 활성 매매 신호 (강도 60 이상)")
    print("=" * 70)
    
    if analysis['active_signals']:
        for i, signal in enumerate(analysis['active_signals'], 1):
            print(f"\n{i}. {signal['inflection_point']}일 변곡점 - {signal['description']}")
            print(f"   신호: {signal['signal']} (강도: {signal['strength']}/100)")
            print(f"   💡 {signal['recommendation']}")
    else:
        print("\n현재 활성 신호 없음")
    
    print()
    print("=" * 70)


# 테스트 코드
if __name__ == "__main__":
    # 샘플 데이터 생성 (실제로는 KIS API나 CREON Plus에서 가져와야 함)
    from datetime import datetime, timedelta
    import random
    
    def generate_sample_data(days=120):
        """테스트용 샘플 데이터 생성"""
        data = []
        base_price = 50000
        current_price = base_price
        start_date = datetime.now() - timedelta(days=days)
        
        for i in range(days):
            date = start_date + timedelta(days=i)
            
            # 60일차에 저점, 그 후 상승
            if i < 60:
                trend = -0.5
            else:
                trend = 1.5
            
            change = random.uniform(-2, 2) + trend
            current_price = current_price * (1 + change/100)
            
            high = current_price * random.uniform(1.005, 1.02)
            low = current_price * random.uniform(0.98, 0.995)
            open_price = current_price * random.uniform(0.99, 1.01)
            volume = random.randint(100000, 500000)
            
            data.append({
                'date': date,
                'open': open_price,
                'high': high,
                'low': low,
                'close': current_price,
                'volume': volume
            })
        
        return data
    
    # 분석 실행
    print("샘플 데이터로 테스트 중...\n")
    
    analyzer = IchimokuInflectionAnalyzer()
    sample_data = generate_sample_data(120)
    
    analysis = analyzer.analyze_all_inflections(sample_data)
    print_analysis_report(analysis)
