"""
PIONA ML 통합 테스트
"""
import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from utils_indicators import (
    validate_dataframe,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    add_technical_indicators
)
from config import DATA_DIR, MODEL_PATH


class TestUtilsIndicators(unittest.TestCase):
    """기술적 지표 유틸리티 테스트"""

    def setUp(self):
        """테스트 데이터 준비"""
        np.random.seed(42)
        self.df = pd.DataFrame({
            'close': np.random.uniform(100, 200, 100),
            'high': np.random.uniform(100, 200, 100),
            'low': np.random.uniform(100, 200, 100),
            'open': np.random.uniform(100, 200, 100),
            'volume': np.random.randint(1000000, 5000000, 100)
        })

    def test_validate_dataframe_valid(self):
        """유효한 DataFrame 검증 테스트"""
        self.assertTrue(validate_dataframe(self.df, ['close']))

    def test_validate_dataframe_empty(self):
        """빈 DataFrame 검증 테스트"""
        empty_df = pd.DataFrame()
        with self.assertRaises(ValueError):
            validate_dataframe(empty_df)

    def test_validate_dataframe_missing_columns(self):
        """필수 컬럼 누락 테스트"""
        with self.assertRaises(ValueError):
            validate_dataframe(self.df, ['nonexistent_column'])

    def test_calculate_rsi(self):
        """RSI 계산 테스트"""
        rsi = calculate_rsi(self.df['close'])
        self.assertIsInstance(rsi, pd.Series)
        self.assertEqual(len(rsi), len(self.df))
        # RSI는 0~100 사이 값
        valid_rsi = rsi.dropna()
        self.assertTrue(all((valid_rsi >= 0) & (valid_rsi <= 100)))

    def test_calculate_macd(self):
        """MACD 계산 테스트"""
        macd = calculate_macd(self.df['close'])
        self.assertIsInstance(macd, pd.Series)
        self.assertEqual(len(macd), len(self.df))

    def test_calculate_bollinger_bands(self):
        """볼린저 밴드 계산 테스트"""
        upper, middle, lower = calculate_bollinger_bands(self.df['close'])

        self.assertIsInstance(upper, pd.Series)
        self.assertIsInstance(middle, pd.Series)
        self.assertIsInstance(lower, pd.Series)

        # 유효한 데이터에서 upper > middle > lower 확인
        valid_idx = ~(upper.isna() | middle.isna() | lower.isna())
        self.assertTrue(all(upper[valid_idx] >= middle[valid_idx]))
        self.assertTrue(all(middle[valid_idx] >= lower[valid_idx]))

    def test_add_technical_indicators(self):
        """기술적 지표 일괄 추가 테스트"""
        df_with_indicators = add_technical_indicators(self.df.copy())

        # 지표가 추가되었는지 확인
        expected_columns = ['SMA_5', 'SMA_20', 'SMA_60', 'RSI', 'MACD',
                          'Momentum', 'BB_upper', 'BB_middle', 'BB_lower', 'BB_position']

        for col in expected_columns:
            self.assertIn(col, df_with_indicators.columns)


class TestConfig(unittest.TestCase):
    """설정 파일 테스트"""

    def test_directories_exist(self):
        """필수 디렉토리 존재 확인"""
        self.assertTrue(DATA_DIR.exists())

    def test_paths_are_pathlib(self):
        """경로가 pathlib.Path 타입인지 확인"""
        from config import BASE_DIR, DATA_DIR, BACKUP_DIR, MODEL_PATH

        self.assertIsInstance(BASE_DIR, Path)
        self.assertIsInstance(DATA_DIR, Path)
        self.assertIsInstance(BACKUP_DIR, Path)
        self.assertIsInstance(MODEL_PATH, Path)


class TestDataProcessing(unittest.TestCase):
    """데이터 처리 테스트"""

    def setUp(self):
        """테스트 주가 데이터 생성"""
        self.df = pd.DataFrame({
            'close': [100, 102, 101, 103, 105, 104, 106, 108, 107, 109],
            'open': [99, 101, 100, 102, 104, 103, 105, 107, 106, 108],
            'high': [101, 103, 102, 104, 106, 105, 107, 109, 108, 110],
            'low': [98, 100, 99, 101, 103, 102, 104, 106, 105, 107],
            'volume': [1000000] * 10
        })

    def test_future_return_calculation(self):
        """미래 수익률 계산 테스트"""
        df = self.df.copy()
        df['future_return'] = df['close'].shift(-1) / df['close'] - 1

        # 첫 번째 행 확인
        expected = (df['close'].iloc[1] / df['close'].iloc[0]) - 1
        self.assertAlmostEqual(df['future_return'].iloc[0], expected, places=5)

    def test_label_generation(self):
        """레이블 생성 테스트"""
        df = self.df.copy()
        df['future_return'] = df['close'].shift(-5) / df['close'] - 1
        df['label'] = (df['future_return'] > 0.03).astype(int)

        self.assertTrue(all(df['label'].dropna().isin([0, 1])))


class TestIntegration(unittest.TestCase):
    """통합 테스트"""

    def test_full_pipeline(self):
        """전체 파이프라인 테스트"""
        # 더미 데이터 생성
        df = pd.DataFrame({
            'close': np.random.uniform(100, 200, 100),
            'high': np.random.uniform(100, 200, 100),
            'low': np.random.uniform(100, 200, 100),
            'open': np.random.uniform(100, 200, 100),
            'volume': np.random.randint(1000000, 5000000, 100)
        })

        # 지표 추가
        df = add_technical_indicators(df)

        # 타겟 생성
        df['future_return'] = df['close'].shift(-5) / df['close'] - 1
        df['label'] = (df['future_return'] > 0.03).astype(int)

        # 결측치 제거
        df = df.dropna()

        # 데이터가 정상적으로 준비되었는지 확인
        self.assertGreater(len(df), 0)

        # 피처 확인
        expected_features = ['SMA_5', 'SMA_20', 'SMA_60', 'RSI', 'MACD', 'Momentum']
        for feature in expected_features:
            self.assertIn(feature, df.columns)


def run_tests():
    """테스트 실행"""
    # 테스트 스위트 생성
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 모든 테스트 클래스 추가
    suite.addTests(loader.loadTestsFromTestCase(TestUtilsIndicators))
    suite.addTests(loader.loadTestsFromTestCase(TestConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestDataProcessing))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 결과 반환
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
