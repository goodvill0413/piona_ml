# ===========================================
# 📘 PIONA ML + 일목균형표 변곡일 통합 예측 시스템
# ===========================================
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import joblib
from sklearn.ensemble import RandomForestClassifier
import warnings
warnings.filterwarnings('ignore')

# -------------------------------------------
# 1️⃣ 기본 설정 및 경로
# -------------------------------------------
BASE_DIR = r"D:\piona_ml"
DATA_DIR = os.path.join(BASE_DIR, "data")
BACKUP_DIR = os.path.join(BASE_DIR, "backup")
MODEL_PATH = os.path.join(BACKUP_DIR, "model_enhanced.pkl")
INFLECTION_PATH = os.path.join(BASE_DIR, "inflection_points.json")
RESULT_PATH = os.path.join(BASE_DIR, "result_enhanced.json")

# -------------------------------------------
# 2️⃣ 일목균형표 변곡일 분석 클래스 (통합 버전)
# -------------------------------------------
class IchimokuInflectionAnalysis:
    """일목균형표 변곡일 분석을 ML과 통합한 클래스"""
    
    def __init__(self, inflection_data_path=None):
        """변곡일 데이터 로드"""
        if inflection_data_path and os.path.exists(inflection_data_path):
            with open(inflection_data_path, "r", encoding="utf-8") as f:
                self.inflection_data = json.load(f)
        else:
            self.inflection_data = {}
        
        # 변곡일 정의 (9개 핵심 변곡)
        self.inflection_points = [9, 13, 26, 33, 42, 51, 65, 77, 88]
        
    def calculate_ichimoku_indicators(self, df):
        """일목균형표 5대 지표 계산"""
        if len(df) < 88:
            print(f"⚠️ 데이터 부족: {len(df)}일 (최소 88일 필요)")
            return df
            
        # 전환선 (9일)
        df['tenkan_sen'] = (df['high'].rolling(9).max() + df['low'].rolling(9).min()) / 2
        
        # 기준선 (26일)
        df['kijun_sen'] = (df['high'].rolling(26).max() + df['low'].rolling(26).min()) / 2
        
        # 선행스팬1 (전환선+기준선)/2, 26일 선행
        df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(26)
        
        # 선행스팬2 (52일), 26일 선행
        df['senkou_span_b'] = ((df['high'].rolling(52).max() + df['low'].rolling(52).min()) / 2).shift(26)
        
        # 후행스팬 (종가 26일 과거)
        df['chikou_span'] = df['close'].shift(-26)
        
        return df
    
    def find_significant_lows(self, df, window=20):
        """의미있는 저점 찾기"""
        if len(df) < window * 2:
            return pd.DataFrame()
            
        rolling_min = df['low'].rolling(window=window, center=True).min()
        significant_lows = df[df['low'] == rolling_min].copy()
        return significant_lows.dropna()
    
    def analyze_inflection_signals(self, df, symbol="005930"):
        """변곡일 신호 분석"""
        signals = {
            "symbol": symbol,
            "current_price": float(df['close'].iloc[-1]) if len(df) > 0 else 0,
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "inflection_signals": {},
            "overall_score": 0,
            "recommendation": "HOLD"
        }
        
        if len(df) < 88:
            signals["inflection_signals"]["warning"] = "데이터 부족"
            return signals
        
        # 일목균형표 계산
        df = self.calculate_ichimoku_indicators(df)
        
        # 최근 88일 내 저점 찾기
        recent_data = df.tail(88).copy()
        recent_lows = self.find_significant_lows(recent_data)
        
        if len(recent_lows) == 0:
            signals["inflection_signals"]["warning"] = "의미있는 저점 없음"
            return signals
        
        # 가장 최근 저점 기준 분석
        latest_low_idx = recent_lows.index[-1]
        days_since_low = len(df) - df.index.get_loc(latest_low_idx) - 1
        
        total_score = 0
        active_signals = 0
        
        # 각 변곡일별 분석
        for inflection_day in self.inflection_points:
            signal = self.analyze_single_inflection(df, latest_low_idx, days_since_low, inflection_day)
            signals["inflection_signals"][f"D+{inflection_day}"] = signal
            
            if signal["status"] == "active":
                total_score += signal["signal_strength"]
                active_signals += 1
        
        # 전체 점수 계산
        if active_signals > 0:
            signals["overall_score"] = total_score / active_signals
        else:
            signals["overall_score"] = 0
        
        # 매매 추천 결정
        if signals["overall_score"] >= 70:
            signals["recommendation"] = "STRONG_BUY"
        elif signals["overall_score"] >= 50:
            signals["recommendation"] = "BUY"
        elif signals["overall_score"] <= -50:
            signals["recommendation"] = "SELL"
        elif signals["overall_score"] <= -70:
            signals["recommendation"] = "STRONG_SELL"
        else:
            signals["recommendation"] = "HOLD"
        
        return signals
    
    def analyze_single_inflection(self, df, low_idx, days_since_low, target_day):
        """개별 변곡일 분석"""
        signal = {
            "days_since_low": days_since_low,
            "target_day": target_day,
            "status": "pending",
            "signal_strength": 0,
            "description": ""
        }
        
        current_idx = len(df) - 1
        
        # 변곡일 구간 진입 여부 확인
        if target_day - 5 <= days_since_low <= target_day + 5:
            signal["status"] = "active"
            
            # 변곡일별 세부 분석
            if target_day == 13:
                signal = self.analyze_13_inflection_signal(df, signal, current_idx)
            elif target_day == 26:
                signal = self.analyze_26_inflection_signal(df, signal, current_idx)
            elif target_day == 42:
                signal = self.analyze_42_inflection_signal(df, signal, current_idx)
            elif target_day == 51:
                signal = self.analyze_51_inflection_signal(df, signal, current_idx)
            elif target_day in [65, 77]:
                signal = self.analyze_major_inflection_signal(df, signal, current_idx, target_day)
            else:
                signal = self.analyze_general_inflection_signal(df, signal, current_idx)
                
        elif days_since_low < target_day - 5:
            signal["status"] = "approaching"
            signal["description"] = f"{target_day}일 변곡 접근 중"
        else:
            signal["status"] = "passed"
            signal["description"] = f"{target_day}일 변곡 지남"
        
        return signal
    
    def analyze_13_inflection_signal(self, df, signal, idx):
        """13일 변곡: 조정 끝 신호"""
        strength = 0
        
        # 골든크로스 확인
        if (idx >= 1 and 
            df['tenkan_sen'].iloc[idx] > df['kijun_sen'].iloc[idx] and
            df['tenkan_sen'].iloc[idx-1] <= df['kijun_sen'].iloc[idx-1]):
            strength += 40
            signal["description"] += "골든크로스 발생, "
        
        # 후행스팬 위치 확인
        if idx >= 26:
            if df['close'].iloc[idx-26] > df['tenkan_sen'].iloc[idx-26]:
                strength += 30
                signal["description"] += "후행스팬 양호, "
        
        # 가격 상승세 확인
        if df['close'].iloc[idx] > df['close'].iloc[idx-5]:
            strength += 20
            signal["description"] += "상승 추세 "
        
        signal["signal_strength"] = min(strength, 100)
        return signal
    
    def analyze_26_inflection_signal(self, df, signal, idx):
        """26일 변곡: 정배열 진입"""
        strength = 0
        current_price = df['close'].iloc[idx]
        
        # 구름대 위 진입 확인
        if (idx >= 26 and 
            current_price > df['senkou_span_a'].iloc[idx] and
            current_price > df['senkou_span_b'].iloc[idx]):
            strength += 50
            signal["description"] += "정배열 진입, "
        
        # 26일 신고가 확인
        if current_price >= df['high'].tail(26).max():
            strength += 30
            signal["description"] += "26일 신고가, "
        
        # 양운 전환 확인
        if df['senkou_span_a'].iloc[idx] > df['senkou_span_b'].iloc[idx]:
            strength += 20
            signal["description"] += "양운 전환 "
        
        signal["signal_strength"] = min(strength, 100)
        return signal
    
    def analyze_42_inflection_signal(self, df, signal, idx):
        """42일 변곡: 3파 시작"""
        strength = 0
        current_price = df['close'].iloc[idx]
        
        # 60일 신고가 확인
        if current_price >= df['high'].tail(60).max():
            strength += 60
            signal["description"] += "60일 신고가(3파), "
        
        # 선행스팬2 상승 확인
        if (idx >= 5 and 
            df['senkou_span_b'].iloc[idx] > df['senkou_span_b'].iloc[idx-5]):
            strength += 25
            signal["description"] += "선행스팬2 상승, "
        
        # 거래량 증가 확인
        if df['volume'].iloc[idx] > df['volume'].tail(10).mean() * 1.2:
            strength += 15
            signal["description"] += "거래량 증가 "
        
        signal["signal_strength"] = min(strength, 100)
        return signal
    
    def analyze_51_inflection_signal(self, df, signal, idx):
        """51일 변곡: 불가항력 변곡"""
        strength = 0
        
        # 강한 상승세 확인
        price_change = (df['close'].iloc[idx] / df['close'].iloc[idx-10] - 1) * 100
        if price_change > 5:
            strength += 50
            signal["description"] += f"10일간 {price_change:.1f}% 상승, "
        elif price_change > 0:
            strength += 25
        
        # 구름 두께 확인
        if idx >= 26:
            cloud_thickness = abs(df['senkou_span_a'].iloc[idx] - df['senkou_span_b'].iloc[idx])
            if cloud_thickness > df['close'].iloc[idx] * 0.02:
                strength += 30
                signal["description"] += "구름 두께 양호, "
        
        # 후행스팬 구름 위 확인
        if (idx >= 26 and 
            df['close'].iloc[idx-26] > max(df['senkou_span_a'].iloc[idx-26], 
                                           df['senkou_span_b'].iloc[idx-26])):
            strength += 20
            signal["description"] += "후행스팬 구름 위 "
        
        signal["signal_strength"] = min(strength, 100)
        return signal
    
    def analyze_major_inflection_signal(self, df, signal, idx, target_day):
        """65, 77일 변곡: 고점 경계 구간"""
        strength = 0
        
        # 고점 경계 구간 특별 분석
        recent_high = df['high'].tail(10).max()
        current_price = df['close'].iloc[idx]
        
        if current_price < recent_high * 0.95:  # 5% 이상 하락
            strength = -60
            signal["description"] = f"{target_day}일 고점권 하락 위험"
        else:
            # 대량거래 경고 확인
            if df['volume'].iloc[idx] > df['volume'].tail(20).mean() * 2:
                strength = -30
                signal["description"] = f"{target_day}일 대량거래 경고"
            else:
                strength = 10
                signal["description"] = f"{target_day}일 구간 지속 관찰"
        
        signal["signal_strength"] = max(min(strength, 100), -100)
        return signal
    
    def analyze_general_inflection_signal(self, df, signal, idx):
        """기타 변곡일 분석"""
        strength = 0
        
        # 기본 추세 확인
        price_change = (df['close'].iloc[idx] / df['close'].iloc[idx-5] - 1) * 100
        if price_change > 2:
            strength += 30
        elif price_change < -2:
            strength -= 30
        
        signal["signal_strength"] = max(min(strength, 100), -100)
        signal["description"] = f"기본 추세 분석: {price_change:.1f}%"
        return signal

# -------------------------------------------
# 3️⃣ 기술적 지표 계산 함수들
# -------------------------------------------
def calculate_technical_indicators(df):
    """기술적 지표 계산"""
    # 이동평균
    df['SMA_5'] = df['close'].rolling(5).mean()
    df['SMA_20'] = df['close'].rolling(20).mean()
    df['SMA_60'] = df['close'].rolling(60).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df['close'].ewm(span=12).mean()
    exp2 = df['close'].ewm(span=26).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
    df['MACD_hist'] = df['MACD'] - df['MACD_signal']
    
    # 모멘텀
    df['Momentum_5'] = df['close'] / df['close'].shift(5) - 1
    df['Momentum_20'] = df['close'] / df['close'].shift(20) - 1
    
    # 볼린저 밴드
    df['BB_middle'] = df['close'].rolling(20).mean()
    bb_std = df['close'].rolling(20).std()
    df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
    df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
    df['BB_position'] = (df['close'] - df['BB_lower']) / (df['BB_upper'] - df['BB_lower'])
    
    # 결측치 처리
    df.fillna(0, inplace=True)
    return df

# -------------------------------------------
# 4️⃣ 데이터 로드 및 전처리
# -------------------------------------------
def load_stock_data(symbol):
    """주식 데이터 로드"""
    # 실시간 데이터 우선 확인
    realtime_path = os.path.join(DATA_DIR, f"{symbol}_realtime.csv")
    historical_path = os.path.join(DATA_DIR, f"{symbol}.csv")
    
    df = None
    
    # 과거 데이터가 있으면 우선 로드
    if os.path.exists(historical_path):
        try:
            df = pd.read_csv(historical_path)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            print(f"✅ {symbol} 과거 데이터 로드: {len(df)}일")
        except Exception as e:
            print(f"⚠️ {symbol} 과거 데이터 로드 실패: {e}")
    
    # 실시간 데이터 추가
    if os.path.exists(realtime_path):
        try:
            rt_df = pd.read_csv(realtime_path, names=['time', 'price', 'volume', 'foreign'])
            if len(rt_df) > 0:
                # 실시간 데이터를 일봉 형태로 변환
                latest_data = {
                    'date': pd.to_datetime(rt_df['time'].iloc[-1]).date(),
                    'open': rt_df['price'].iloc[0],
                    'high': rt_df['price'].max(),
                    'low': rt_df['price'].min(),
                    'close': rt_df['price'].iloc[-1],
                    'volume': rt_df['volume'].iloc[-1]
                }
                
                if df is not None:
                    # 기존 데이터에 추가 (오늘 데이터가 없으면)
                    if latest_data['date'] not in df.index.date:
                        new_row = pd.DataFrame([latest_data])
                        new_row['date'] = pd.to_datetime(new_row['date'])
                        new_row.set_index('date', inplace=True)
                        df = pd.concat([df, new_row])
                else:
                    # 실시간 데이터만 있는 경우 더미 데이터 생성
                    df = create_dummy_data_with_realtime(latest_data)
                
                print(f"✅ {symbol} 실시간 데이터 통합 완료")
        except Exception as e:
            print(f"⚠️ {symbol} 실시간 데이터 처리 실패: {e}")
    
    # 데이터가 없으면 더미 데이터 생성
    if df is None:
        print(f"⚠️ {symbol} 데이터 없음, 더미 데이터 생성")
        df = create_dummy_data(symbol)
    
    return df

def create_dummy_data_with_realtime(latest_data):
    """실시간 데이터 기반 더미 데이터 생성"""
    base_price = latest_data['close']
    dates = pd.date_range(end=latest_data['date'], periods=100)
    
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, 99)  # 일일 수익률
    prices = [base_price * 0.9]  # 시작 가격
    
    for r in returns:
        prices.append(prices[-1] * (1 + r))
    
    df = pd.DataFrame({
        'date': dates,
        'open': [p * 0.995 for p in prices],
        'high': [p * 1.01 for p in prices],
        'low': [p * 0.99 for p in prices],
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, 100)
    })
    
    # 마지막 데이터를 실제 실시간 데이터로 교체
    df.loc[df.index[-1], 'close'] = latest_data['close']
    df.loc[df.index[-1], 'volume'] = latest_data['volume']
    
    df.set_index('date', inplace=True)
    return df

def create_dummy_data(symbol):
    """완전 더미 데이터 생성"""
    base_prices = {
        "005930": 75000,  # 삼성전자
        "000660": 120000,  # SK하이닉스
        "373220": 400000   # LG에너지솔루션
    }
    
    base_price = base_prices.get(symbol, 50000)
    dates = pd.date_range(end=pd.Timestamp.today(), periods=100)
    
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, 100)
    prices = [base_price]
    
    for r in returns[1:]:
        prices.append(prices[-1] * (1 + r))
    
    df = pd.DataFrame({
        'date': dates,
        'open': [p * 0.995 for p in prices],
        'high': [p * 1.01 for p in prices],
        'low': [p * 0.99 for p in prices],
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, 100)
    })
    
    df.set_index('date', inplace=True)
    return df

# -------------------------------------------
# 5️⃣ 머신러닝 모델 학습 및 예측
# -------------------------------------------
def prepare_features(df):
    """ML 피처 준비"""
    df = calculate_technical_indicators(df)
    
    # 타겟 생성 (5일 후 수익률)
    df['future_return'] = df['close'].shift(-5) / df['close'] - 1
    df['target'] = (df['future_return'] > 0.03).astype(int)  # 3% 이상 상승
    
    # 피처 선택
    feature_columns = [
        'SMA_20', 'SMA_60', 'RSI', 'MACD', 'MACD_hist', 
        'Momentum_5', 'Momentum_20', 'BB_position'
    ]
    
    return df, feature_columns

def train_or_load_model(df, feature_columns):
    """모델 학습 또는 로드"""
    if os.path.exists(MODEL_PATH):
        try:
            model = joblib.load(MODEL_PATH)
            print(f"✅ 기존 모델 로드: {MODEL_PATH}")
            return model
        except Exception as e:
            print(f"⚠️ 모델 로드 실패: {e}, 새로 학습")
    
    # 새 모델 학습
    print("🤖 새 모델 학습 시작...")
    
    # 결측치 제거
    train_data = df[feature_columns + ['target']].dropna()
    
    if len(train_data) < 10:
        print("⚠️ 학습 데이터 부족, 기본 모델 생성")
        model = RandomForestClassifier(n_estimators=50, random_state=42)
        # 더미 데이터로 학습
        X_dummy = np.random.random((100, len(feature_columns)))
        y_dummy = np.random.randint(0, 2, 100)
        model.fit(X_dummy, y_dummy)
    else:
        X = train_data[feature_columns]
        y = train_data['target']
        
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )
        model.fit(X, y)
        print(f"✅ 모델 학습 완료: {len(train_data)}개 샘플")
    
    # 모델 저장
    os.makedirs(BACKUP_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    
    return model

def get_ml_prediction(model, df, feature_columns):
    """ML 예측 수행"""
    try:
        # 최근 데이터로 예측
        latest_features = df[feature_columns].iloc[-1:].values
        
        # 결측치 처리
        if np.isnan(latest_features).any():
            latest_features = np.nan_to_num(latest_features)
        
        # 확률 예측
        prob = model.predict_proba(latest_features)[0]
        
        # 상승 확률 추출 (클래스 1)
        if len(prob) > 1:
            ml_score = prob[1] * 100
        else:
            ml_score = 50.0  # 기본값
        
        return {
            "ml_score": round(ml_score, 2),
            "confidence": "HIGH" if ml_score > 70 or ml_score < 30 else "MEDIUM"
        }
    except Exception as e:
        print(f"⚠️ ML 예측 오류: {e}")
        return {"ml_score": 50.0, "confidence": "LOW"}

# -------------------------------------------
# 6️⃣ 통합 분석 및 결과 생성
# -------------------------------------------
def generate_combined_analysis(symbol):
    """통합 분석 수행"""
    print(f"\n🔍 {symbol} 통합 분석 시작...")
    
    # 1. 데이터 로드
    df = load_stock_data(symbol)
    
    # 2. 기술적 지표 계산
    df, feature_columns = prepare_features(df)
    
    # 3. ML 모델 예측
    model = train_or_load_model(df, feature_columns)
    ml_result = get_ml_prediction(model, df, feature_columns)
    
    # 4. 일목균형표 변곡일 분석
    ichimoku = IchimokuInflectionAnalysis(INFLECTION_PATH)
    inflection_result = ichimoku.analyze_inflection_signals(df, symbol)
    
    # 5. 결합 분석
    combined_result = combine_ml_and_inflection(ml_result, inflection_result, df)
    
    return combined_result

def combine_ml_and_inflection(ml_result, inflection_result, df):
    """ML과 변곡일 분석 결합"""
    # 기본 정보
    combined = {
        "symbol": inflection_result["symbol"],
        "current_price": inflection_result["current_price"],
        "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        
        # 개별 분석 결과
        "ml_analysis": ml_result,
        "inflection_analysis": {
            "overall_score": inflection_result["overall_score"],
            "recommendation": inflection_result["recommendation"],
            "active_signals": len([s for s in inflection_result["inflection_signals"].values() 
                                 if isinstance(s, dict) and s.get("status") == "active"])
        },
        
        # 통합 결과
        "combined_score": 0,
        "final_recommendation": "HOLD",
        "confidence_level": "MEDIUM",
        "reasons": []
    }
    
    # 가중치 적용 (ML 60%, 변곡일 40%)
    ml_score = ml_result["ml_score"]
    inflection_score = inflection_result["overall_score"]
    
    # 점수 정규화 (-100 ~ +100 범위로)
    normalized_ml = (ml_score - 50) * 2  # 0-100 -> -100 to +100
    normalized_inflection = inflection_score  # 이미 -100 ~ +100 범위
    
    combined["combined_score"] = round(normalized_ml * 0.6 + normalized_inflection * 0.4, 2)
    
    # 최종 추천 결정
    final_score = combined["combined_score"]
    if final_score >= 60:
        combined["final_recommendation"] = "STRONG_BUY"
        combined["confidence_level"] = "HIGH"
        combined["reasons"].append(f"강력한 상승 신호 (점수: {final_score})")
    elif final_score >= 30:
        combined["final_recommendation"] = "BUY"
        combined["confidence_level"] = "MEDIUM"
        combined["reasons"].append(f"상승 신호 (점수: {final_score})")
    elif final_score <= -30:
        combined["final_recommendation"] = "SELL"
        combined["confidence_level"] = "MEDIUM"
        combined["reasons"].append(f"하락 신호 (점수: {final_score})")
    elif final_score <= -60:
        combined["final_recommendation"] = "STRONG_SELL"
        combined["confidence_level"] = "HIGH"
        combined["reasons"].append(f"강력한 하락 신호 (점수: {final_score})")
    else:
        combined["final_recommendation"] = "HOLD"
        combined["confidence_level"] = "LOW"
        combined["reasons"].append(f"중립 신호 (점수: {final_score})")
    
    # 추가 분석 이유
    if ml_score > 60:
        combined["reasons"].append(f"ML 상승 확률 {ml_score}%")
    if inflection_score > 50:
        combined["reasons"].append("변곡일 상승 신호 활성")
    
    # 기술적 분석 추가
    current_price = df['close'].iloc[-1]
    sma20 = df['SMA_20'].iloc[-1]
    rsi = df['RSI'].iloc[-1]
    
    if current_price > sma20:
        combined["reasons"].append("20일선 위 거래")
    if rsi > 70:
        combined["reasons"].append("RSI 과매수 구간")
    elif rsi < 30:
        combined["reasons"].append("RSI 과매도 구간")
    
    return combined

# -------------------------------------------
# 7️⃣ 메인 실행부
# -------------------------------------------
def main():
    """메인 실행 함수"""
    print("🚀 PIONA ML + 일목균형표 변곡일 통합 분석 시작!")
    print("=" * 60)
    
    # 주요 종목들
    symbols = ["005930", "000660", "373220"]  # 삼성전자, SK하이닉스, LG에너지솔루션
    all_results = {}
    
    for symbol in symbols:
        try:
            result = generate_combined_analysis(symbol)
            all_results[symbol] = result
            
            # 간단한 결과 출력
            print(f"\n📊 {symbol} 분석 완료:")
            print(f"   현재가: {result['current_price']:,}원")
            print(f"   ML 점수: {result['ml_analysis']['ml_score']:.1f}%")
            print(f"   변곡일 점수: {result['inflection_analysis']['overall_score']:.1f}")
            print(f"   최종 점수: {result['combined_score']:.1f}")
            print(f"   추천: {result['final_recommendation']} ({result['confidence_level']})")
            
        except Exception as e:
            print(f"❌ {symbol} 분석 실패: {e}")
            all_results[symbol] = {"error": str(e)}
    
    # 결과 저장
    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 결과 저장: {RESULT_PATH}")
    print("=" * 60)
    print("✅ 통합 분석 완료!")
    
    # 최고 점수 종목 출력
    best_symbol = None
    best_score = -999
    
    for symbol, result in all_results.items():
        if "combined_score" in result and result["combined_score"] > best_score:
            best_score = result["combined_score"]
            best_symbol = symbol
    
    if best_symbol:
        print(f"\n🏆 최고 점수 종목: {best_symbol} (점수: {best_score})")
        best_result = all_results[best_symbol]
        print(f"   추천: {best_result['final_recommendation']}")
        print(f"   이유: {', '.join(best_result['reasons'])}")
    
    return all_results

if __name__ == "__main__":
    try:
        results = main()
    except Exception as e:
        print(f"❌ 실행 오류: {e}")
        import traceback
        traceback.print_exc()
