# D:\piona_ml\analyze_inflection_005930.py
"""
삼성전자(005930) 변곡점 분석
88일 데이터로 현재 위치 추정
"""
import csv
from datetime import datetime

# 변곡일 정의
INFLECTION_POINTS = [9, 13, 26, 33, 42, 51, 65, 77, 88]

def load_data(filepath):
    """CSV 데이터 로드"""
    data = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'date': row['date'],
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': int(row['volume'])
            })
    return data

def find_significant_lows(data, window=20):
    """의미있는 저점 찾기"""
    lows = []
    
    for i in range(window, len(data) - window):
        current_low = data[i]['low']
        is_local_min = True
        
        # 전후 window 범위 내에서 가장 낮은지 확인
        for j in range(i - window, i + window + 1):
            if j != i and data[j]['low'] < current_low:
                is_local_min = False
                break
        
        if is_local_min:
            lows.append({
                'index': i,
                'date': data[i]['date'],
                'price': current_low
            })
    
    return lows

def analyze_inflection(data, symbol="005930"):
    """변곡점 분석"""
    print("="*60)
    print(f"📊 {symbol} 변곡점 분석")
    print("="*60)
    
    # 현재 정보
    current = data[-1]
    print(f"\n📅 분석 기준일: {current['date']}")
    print(f"💰 현재가: {current['close']:,.0f}원")
    print(f"📊 데이터 기간: {len(data)}일")
    
    # 최근 저점 찾기
    print(f"\n{'='*60}")
    print("🔍 최근 의미있는 저점 찾기")
    print("="*60)
    
    lows = find_significant_lows(data)
    
    if not lows:
        print("⚠️ 저점을 찾을 수 없습니다.")
        return
    
    # 가장 최근 저점
    latest_low = lows[-1]
    days_since_low = len(data) - 1 - latest_low['index']
    
    print(f"\n📉 가장 최근 저점:")
    print(f"   날짜: {latest_low['date']}")
    print(f"   가격: {latest_low['price']:,.0f}원")
    print(f"   경과일: {days_since_low}일 전")
    
    # 저점 대비 현재 상승률
    price_change = ((current['close'] - latest_low['price']) / latest_low['price']) * 100
    print(f"   상승률: {price_change:+.2f}%")
    
    # 변곡점 분석
    print(f"\n{'='*60}")
    print("📊 변곡점 위치 분석")
    print("="*60)
    
    for inflection_day in INFLECTION_POINTS:
        distance = days_since_low - inflection_day
        
        if distance < -5:
            status = "🔵 아직 멀리 있음"
        elif -5 <= distance <= -3:
            status = "🟡 접근 중"
        elif -3 < distance < 3:
            status = "🔴 변곡 구간! (매우 중요)"
        elif 3 <= distance <= 5:
            status = "🟢 방금 지나감"
        else:
            status = "⚪ 지나감"
        
        print(f"D+{inflection_day:2d}일 변곡: 현재 D+{days_since_low} ({distance:+3d}일) {status}")
    
    # 상세 분석
    print(f"\n{'='*60}")
    print("🎯 상세 변곡점 분석")
    print("="*60)
    
    for inflection_day in INFLECTION_POINTS:
        distance = days_since_low - inflection_day
        
        if abs(distance) <= 3:
            analyze_specific_inflection(data, inflection_day, days_since_low, latest_low)
    
    # 추천 액션
    print(f"\n{'='*60}")
    print("💡 추천 액션")
    print("="*60)
    
    recommend_action(days_since_low, price_change, data)

def analyze_specific_inflection(data, target_day, current_day, latest_low):
    """특정 변곡일 상세 분석"""
    print(f"\n📌 {target_day}일 변곡 상세 분석:")
    
    if target_day == 9:
        print("   의미: 초단기 전환점")
        print("   특징: 단기 조정 마무리 신호")
        
    elif target_day == 13:
        print("   의미: 조정 종료 신호")
        print("   특징: 전환선/기준선 골든크로스 가능")
        print("   액션: 단기 매수 진입 타이밍")
        
    elif target_day == 26:
        print("   의미: 정배열 진입")
        print("   특징: 구름대 돌파 시도")
        print("   액션: 본격 상승 시작 가능")
        
    elif target_day == 33:
        print("   의미: 중기 추세 확인")
        print("   특징: 상승 추세 지속 여부 판단")
        
    elif target_day == 42:
        print("   의미: 3파 시작 조건")
        print("   특징: 60일 신고가 돌파 가능")
        print("   액션: 적극 매수 구간")
        
    elif target_day == 51:
        print("   의미: 불가항력 변곡 ⭐")
        print("   특징: 강력한 상승 추세 확정")
        print("   액션: 추격 매수도 가능한 구간")
        
    elif target_day == 65:
        print("   의미: 대변곡 (고점 주의)")
        print("   특징: 과열 구간 진입")
        print("   액션: 익절 타이밍 고려")
        
    elif target_day == 77:
        print("   의미: 대변곡 (소멸갭 주의)")
        print("   특징: 고점 경계 구간")
        print("   액션: 분할 익절 추천")
        
    elif target_day == 88:
        print("   의미: 장기 추세 전환")
        print("   특징: 새로운 사이클 시작")

def recommend_action(days_since_low, price_change, data):
    """추천 액션 생성"""
    current_price = data[-1]['close']
    recent_high = max([d['high'] for d in data[-20:]])
    recent_low = min([d['low'] for d in data[-20:]])
    
    # 가격 위치 (최근 20일 기준)
    price_position = (current_price - recent_low) / (recent_high - recent_low) * 100
    
    print(f"\n📈 가격 위치 분석:")
    print(f"   최근 20일 저점: {recent_low:,.0f}원")
    print(f"   최근 20일 고점: {recent_high:,.0f}원")
    print(f"   현재 위치: {price_position:.1f}% (저점 대비)")
    
    # 변곡점 기반 추천
    print(f"\n💡 변곡점 기반 추천:")
    
    if 11 <= days_since_low <= 15:
        print("   🟢 13일 변곡 구간 → 단기 매수 타이밍!")
    elif 24 <= days_since_low <= 28:
        print("   🟢 26일 변곡 구간 → 정배열 진입, 매수!")
    elif 40 <= days_since_low <= 44:
        print("   🟢 42일 변곡 구간 → 3파 시작, 적극 매수!")
    elif 49 <= days_since_low <= 53:
        print("   🟢 51일 불가항력 변곡 → 강력 매수!")
    elif 63 <= days_since_low <= 67:
        print("   🟡 65일 대변곡 → 고점 주의, 익절 고려")
    elif 75 <= days_since_low <= 79:
        print("   🔴 77일 대변곡 → 과열, 분할 익절!")
    elif 86 <= days_since_low <= 90:
        print("   🔴 88일 변곡 통과 → 새 사이클, 관망")
    else:
        print(f"   ⚪ D+{days_since_low} → 다음 변곡 대기 중")
    
    # 가격 기반 추천
    print(f"\n💰 가격 기반 추천:")
    if price_change > 10:
        print(f"   저점 대비 {price_change:.1f}% 상승 → 단기 과열 주의")
    elif price_change > 5:
        print(f"   저점 대비 {price_change:.1f}% 상승 → 정상 상승 중")
    elif price_change > 0:
        print(f"   저점 대비 {price_change:.1f}% 상승 → 초기 상승 단계")
    else:
        print(f"   저점 대비 {price_change:.1f}% → 저점 재테스트 중")

def main():
    filepath = "D:\\piona_ml\\data\\005930_88days.csv"
    
    try:
        data = load_data(filepath)
        analyze_inflection(data, "005930")
        
    except FileNotFoundError:
        print(f"❌ 파일을 찾을 수 없습니다: {filepath}")
        print("💡 먼저 fetch_data_creon_simple.py를 실행하세요!")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()
