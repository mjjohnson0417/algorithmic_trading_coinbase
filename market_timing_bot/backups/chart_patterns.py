import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import pandas as pd
import numpy as np
from typing import List, Dict

class ChartPatterns:
    def __init__(self, symbols: List[str], data_manager, enable_logging: bool = True):
        self.symbols = symbols
        self.data_manager = data_manager
        self.enable_logging = enable_logging
        self.timeframes = ['1m', '5m', '15m', '1h', '6h', '1d']

        self.logger = logging.getLogger('ChartPatterns')
        if enable_logging:
            log_dir = Path(__file__).parent / 'logs'
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / 'chart_patterns.log'
            file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s\t%(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.WARNING)

        self.logger.debug("ChartPatterns initialized with symbols: %s", symbols)

    def _validate_klines(self, klines: pd.DataFrame, symbol: str, timeframe: str, min_rows: int = 1) -> bool:
        required_columns = ['open', 'high', 'low', 'close']
        if klines.empty:
            self.logger.warning(f"Empty {timeframe} klines for {symbol}: shape={klines.shape}")
            return False
        if len(klines) < min_rows:
            self.logger.warning(f"Insufficient {timeframe} klines for {symbol}: {len(klines)} rows, need {min_rows}")
            return False
        missing_columns = [col for col in required_columns if col not in klines.columns]
        if missing_columns:
            self.logger.warning(
                f"Invalid {timeframe} klines for {symbol}: Missing columns {missing_columns}, "
                f"available columns={list(klines.columns)}, shape={klines.shape}, head=\n{klines.head(5).to_string()}"
            )
            return False
        if klines[required_columns].isna().any().any():
            self.logger.warning(f"Invalid {timeframe} klines for {symbol}: NaN values in {required_columns}")
            return False
        return True

    def _find_pivot_points(self, series: pd.Series, is_high: bool, window: int = 3) -> pd.Series:
        pivots = pd.Series(index=series.index, dtype=float)
        for i in range(window, len(series) - window):
            current = series.iloc[i]
            left = series.iloc[i - window:i]
            right = series.iloc[i + 1:i + window + 1]
            if is_high and current > left.max() and current > right.max():
                pivots.iloc[i] = current
            elif not is_high and current < left.min() and current < right.min():
                pivots.iloc[i] = current
        return pivots.dropna()

    def calculate_all_patterns(self) -> Dict[str, Dict[str, Dict[str, any]]]:
        if not self.data_manager:
            self.logger.error("DataManager not provided.")
            return {}

        all_patterns = {}
        for symbol in self.symbols:
            self.logger.debug(f"Calculating chart patterns for {symbol}")
            symbol_patterns = {}
            for timeframe in self.timeframes:
                try:
                    patterns = {
                        'double_top': self.double_top(symbol, timeframe),
                        'double_bottom': self.double_bottom(symbol, timeframe),
                        'head_and_shoulders': self.head_and_shoulders(symbol, timeframe),
                        'inverse_head_and_shoulders': self.inverse_head_and_shoulders(symbol, timeframe),
                        'rising_wedge': self.rising_wedge(symbol, timeframe),
                        'falling_wedge': self.falling_wedge(symbol, timeframe),
                        'rectangle_bullish': self.rectangle_bullish(symbol, timeframe),
                        'rectangle_bearish': self.rectangle_bearish(symbol, timeframe),
                        'flag_bullish': self.flag_bullish(symbol, timeframe),
                        'flag_bearish': self.flag_bearish(symbol, timeframe),
                        'pennant_bullish': self.pennant_bullish(symbol, timeframe),
                        'triangle_ascending': self.triangle_ascending(symbol, timeframe),
                        'triangle_descending': self.triangle_descending(symbol, timeframe),
                        'triangle_symmetrical': self.triangle_symmetrical(symbol, timeframe)
                    }
                    symbol_patterns[timeframe] = patterns
                except Exception as e:
                    self.logger.error(f"Error calculating patterns for {symbol} ({timeframe}): {str(e)}")
                    symbol_patterns[timeframe] = {
                        pattern: {'detected': False, 'upper_trendline': None, 'lower_trendline': None,
                                  'neckline': None, 'support_level': None, 'resistance_level': None,
                                  'flagpole_height': None, 'peak_level': None, 'trough_level': None}
                        for pattern in ['double_top', 'double_bottom', 'head_and_shoulders', 'inverse_head_and_shoulders',
                                        'rising_wedge', 'falling_wedge', 'rectangle_bullish', 'rectangle_bearish',
                                        'flag_bullish', 'flag_bearish', 'pennant_bullish', 'triangle_ascending',
                                        'triangle_descending', 'triangle_symmetrical']
                    }
            all_patterns[symbol] = symbol_patterns
            self.logger.debug(f"All chart patterns for {symbol}: %s", symbol_patterns)
        return all_patterns

    def double_top(self, symbol: str, timeframe: str) -> Dict[str, any]:
        result = {'detected': False, 'neckline': None, 'peak_level': None}
        try:
            if symbol not in self.symbols or timeframe not in self.timeframes:
                return result

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=15):
                return result

            window = klines.tail(15).copy()
            try:
                highs = window['high']
                lows = window['low']
                closes = window['close']
            except KeyError as e:
                self.logger.error(
                    f"KeyError accessing columns in {timeframe} klines for {symbol}: {str(e)}, "
                    f"columns={list(window.columns)}, shape={window.shape}, head=\n{window.head(5).to_string()}"
                )
                return result

            tolerance = 0.03
            max_high = highs.max()
            high_indices = highs[highs >= max_high * (1 - tolerance)].index
            if len(high_indices) < 2:
                return result

            peak_indices = sorted(high_indices, reverse=True)[:2]
            if len(peak_indices) < 2 or peak_indices[0] <= peak_indices[1] or peak_indices[0] - peak_indices[1] < 2:
                return result

            second_peak_idx, first_peak_idx = peak_indices[0], peak_indices[1]
            first_peak = highs[first_peak_idx]
            second_peak = highs[second_peak_idx]
            peak_level = (first_peak + second_peak) / 2

            neckline_slice = lows[first_peak_idx:second_peak_idx + 1]
            if neckline_slice.empty:
                return result
            neckline = neckline_slice.min()

            latest_close = closes.iloc[-1]
            is_double_top = latest_close < neckline

            if is_double_top:
                result = {
                    'detected': True,
                    'neckline': float(neckline),
                    'peak_level': float(peak_level)
                }

            self.logger.debug(f"Double Top check for {symbol} ({timeframe}): {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error checking Double Top for {symbol} ({timeframe}): {str(e)}")
            return result

    def double_bottom(self, symbol: str, timeframe: str) -> Dict[str, any]:
        result = {'detected': False, 'neckline': None, 'trough_level': None}
        try:
            if symbol not in self.symbols or timeframe not in self.timeframes:
                return result

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=15):
                return result

            window = klines.tail(15).copy()
            try:
                lows = window['low']
                highs = window['high']
                closes = window['close']
            except KeyError as e:
                self.logger.error(
                    f"KeyError accessing columns in {timeframe} klines for {symbol}: {str(e)}, "
                    f"columns={list(window.columns)}, shape={window.shape}, head=\n{window.head(5).to_string()}"
                )
                return result

            tolerance = 0.03
            min_low = lows.min()
            low_indices = lows[lows <= min_low * (1 + tolerance)].index
            if len(low_indices) < 2:
                return result

            trough_indices = sorted(low_indices, reverse=True)[:2]
            if len(trough_indices) < 2 or trough_indices[0] <= trough_indices[1] or trough_indices[0] - trough_indices[1] < 2:
                return result

            second_trough_idx, first_trough_idx = trough_indices[0], trough_indices[1]
            first_trough = lows[first_trough_idx]
            second_trough = lows[second_trough_idx]
            trough_level = (first_trough + second_trough) / 2

            neck_highs = highs[first_trough_idx:second_trough_idx + 1]
            if neck_highs.empty:
                return result
            neckline = neck_highs.max()

            latest_close = closes.iloc[-1]
            is_double_bottom = latest_close > neckline

            if is_double_bottom:
                result = {
                    'detected': True,
                    'neckline': float(neckline),
                    'trough_level': float(trough_level)
                }

            self.logger.debug(f"Double Bottom check for {symbol} ({timeframe}): {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error checking Double Bottom for {symbol} ({timeframe}): {str(e)}")
            return result

    def head_and_shoulders(self, symbol: str, timeframe: str) -> Dict[str, any]:
        result = {'detected': False, 'neckline': None, 'peak_level': None}
        try:
            if symbol not in self.symbols or timeframe not in self.timeframes:
                return result

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=25):
                return result

            window = klines.tail(25).copy()
            try:
                highs = window['high']
                lows = window['low']
                closes = window['close']
            except KeyError as e:
                self.logger.error(
                    f"KeyError accessing columns in {timeframe} klines for {symbol}: {str(e)}, "
                    f"columns={list(window.columns)}, shape={window.shape}, head=\n{window.head(5).to_string()}"
                )
                return result

            tolerance = 0.03
            head_idx = highs.idxmax()
            head_high = highs[head_idx]

            left_peaks = highs[highs.index < head_idx]
            right_peaks = highs[highs.index > head_idx]
            if left_peaks.empty or right_peaks.empty:
                return result

            left_shoulder_idx = left_peaks.idxmax()
            right_shoulder_idx = right_peaks.idxmax()
            left_shoulder = highs[left_shoulder_idx]
            right_shoulder = highs[right_shoulder_idx]

            if left_shoulder >= head_high or right_shoulder >= head_high or abs(left_shoulder - right_shoulder) / left_shoulder > tolerance:
                return result
            if head_idx - left_shoulder_idx < 2 or right_shoulder_idx - head_idx < 2:
                return result
            if abs(head_high - left_shoulder) < head_high * 0.01 or abs(head_high - right_shoulder) < head_high * 0.01:
                return result

            peak_level = (left_shoulder + right_shoulder) / 2

            first_trough_slice = lows[left_shoulder_idx:head_idx + 1]
            second_trough_slice = lows[head_idx:right_shoulder_idx + 1]
            if first_trough_slice.empty or second_trough_slice.empty:
                return result
            first_trough = first_trough_slice.min()
            second_trough = second_trough_slice.min()

            if abs(first_trough - second_trough) / first_trough > tolerance:
                return result

            neckline = (first_trough + second_trough) / 2
            latest_close = closes.iloc[-1]
            is_head_and_shoulders = latest_close < neckline

            if is_head_and_shoulders:
                result = {
                    'detected': True,
                    'neckline': float(neckline),
                    'peak_level': float(peak_level)
                }

            self.logger.debug(f"Head and Shoulders check for {symbol} ({timeframe}): {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error checking Head and Shoulders for {symbol} ({timeframe}): {str(e)}")
            return result

    def inverse_head_and_shoulders(self, symbol: str, timeframe: str) -> Dict[str, any]:
        result = {'detected': False, 'neckline': None, 'trough_level': None}
        try:
            if symbol not in self.symbols or timeframe not in self.timeframes:
                return result

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=25):
                return result

            window = klines.tail(25).copy()
            try:
                lows = window['low']
                highs = window['high']
                closes = window['close']
            except KeyError as e:
                self.logger.error(
                    f"KeyError accessing columns in {timeframe} klines for {symbol}: {str(e)}, "
                    f"columns={list(window.columns)}, shape={window.shape}, head=\n{window.head(5).to_string()}"
                )
                return result

            tolerance = 0.03
            head_idx = lows.idxmin()
            head_low = lows[head_idx]

            left_troughs = lows[lows.index < head_idx]
            right_troughs = lows[lows.index > head_idx]
            if left_troughs.empty or right_troughs.empty:
                return result

            left_shoulder_idx = left_troughs.idxmin()
            right_shoulder_idx = right_troughs.idxmin()
            left_shoulder = lows[left_shoulder_idx]
            right_shoulder = lows[right_shoulder_idx]

            if left_shoulder <= head_low or right_shoulder <= head_low or abs(left_shoulder - right_shoulder) / left_shoulder > tolerance:
                return result
            if head_idx - left_shoulder_idx < 2 or right_shoulder_idx - head_idx < 2:
                return result

            trough_level = (left_shoulder + right_shoulder) / 2

            first_peak_segment = highs[left_shoulder_idx:head_idx + 1]
            second_peak_segment = highs[head_idx:right_shoulder_idx + 1]
            if first_peak_segment.empty or second_peak_segment.empty:
                return result
            first_peak = first_peak_segment.max()
            second_peak = second_peak_segment.max()

            if abs(first_peak - second_peak) / first_peak > tolerance:
                return result

            neckline = (first_peak + second_peak) / 2
            latest_close = closes.iloc[-1]
            is_inverse_head_and_shoulders = latest_close > neckline

            if is_inverse_head_and_shoulders:
                result = {
                    'detected': True,
                    'neckline': float(neckline),
                    'trough_level': float(trough_level)
                }

            self.logger.debug(f"Inverse Head and Shoulders check for {symbol} ({timeframe}): {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error checking Inverse Head and Shoulders for {symbol} ({timeframe}): {str(e)}")
            return result

    def rising_wedge(self, symbol: str, timeframe: str) -> Dict[str, any]:
        result = {'detected': False, 'upper_trendline': None, 'lower_trendline': None}
        try:
            if symbol not in self.symbols or timeframe not in self.timeframes:
                return result

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=20):
                return result

            window = klines.tail(20).copy()
            try:
                highs = window['high']
                lows = window['low']
                closes = window['close']
            except KeyError as e:
                self.logger.error(
                    f"KeyError accessing columns in {timeframe} klines for {symbol}: {str(e)}, "
                    f"columns={list(window.columns)}, shape={window.shape}, head=\n{window.head(5).to_string()}"
                )
                return result

            indices = np.arange(len(window))

            window['range'] = window['high'] - window['low']
            atr = window['range'].rolling(window=14).mean().iloc[-1] or 0.001
            self.logger.debug(f"ATR for {symbol} ({timeframe}): {atr:.6f}")

            pivot_highs = self._find_pivot_points(highs, is_high=True)
            pivot_lows = self._find_pivot_points(lows, is_high=False)
            if len(pivot_highs) < 3 or len(pivot_lows) < 3:
                self.logger.debug(f"Rising Wedge rejected for {symbol} ({timeframe}): Insufficient pivot points (highs={len(pivot_highs)}, lows={len(pivot_lows)})")
                return result

            high_points = pivot_highs.iloc[-3:].reset_index()
            low_points = pivot_lows.iloc[-3:].reset_index()
            if len(high_points) < 3 or len(low_points) < 3:
                return result

            if not (high_points['high'] > low_points['low'].max()).all():
                self.logger.debug(f"Rising Wedge rejected for {symbol} ({timeframe}): High points not above low points")
                return result

            high_x = high_points.index.values
            high_y = high_points['high'].values
            low_x = low_points.index.values
            low_y = low_points['low'].values

            high_slope, high_intercept = np.polyfit(high_x, high_y, 1)
            low_slope, low_intercept = np.polyfit(low_x, low_y, 1)

            if not (0 < high_slope < low_slope):
                self.logger.debug(f"Rising Wedge rejected for {symbol} ({timeframe}): Invalid slopes (high_slope={high_slope:.6f}, low_slope={low_slope:.6f})")
                return result

            trendline_points = np.arange(len(window) - 10, len(window))
            upper_trendlines = high_slope * trendline_points + high_intercept
            lower_trendlines = low_slope * trendline_points + low_intercept

            if not (upper_trendlines > lower_trendlines).all():
                self.logger.debug(f"Rising Wedge rejected for {symbol} ({timeframe}): Upper trendline not consistently above lower")
                return result

            latest_idx = len(window) - 1
            upper_trendline = upper_trendlines[-1]
            lower_trendline = lower_trendlines[-1]

            min_separation = 0.01 if timeframe in ['1m', '5m'] else 0.005
            max_separation = 0.05
            separation = abs(upper_trendline - lower_trendline) / upper_trendline
            if separation < min_separation or separation > max_separation:
                self.logger.debug(f"Rising Wedge rejected for {symbol} ({timeframe}): Invalid trendline separation ({separation:.4f})")
                return result

            latest_close = closes.iloc[-1]
            is_rising_wedge = latest_close < lower_trendline and abs(latest_close - lower_trendline) > 0.5 * atr

            if is_rising_wedge:
                result = {
                    'detected': True,
                    'upper_trendline': float(upper_trendline),
                    'lower_trendline': float(lower_trendline)
                }
                self.logger.debug(f"Rising Wedge detected for {symbol} ({timeframe}): upper={upper_trendline:.6f}, lower={lower_trendline:.6f}, close={latest_close:.6f}")

            self.logger.debug(f"Rising Wedge check for {symbol} ({timeframe}): {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error checking Rising Wedge for {symbol} ({timeframe}): {str(e)}")
            return result

    def falling_wedge(self, symbol: str, timeframe: str) -> Dict[str, any]:
        result = {'detected': False, 'upper_trendline': None, 'lower_trendline': None}
        try:
            if symbol not in self.symbols or timeframe not in self.timeframes:
                return result

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=20):
                return result

            window = klines.tail(20).copy()
            try:
                highs = window['high']
                lows = window['low']
                closes = window['close']
            except KeyError as e:
                self.logger.error(
                    f"KeyError accessing columns in {timeframe} klines for {symbol}: {str(e)}, "
                    f"columns={list(window.columns)}, shape={window.shape}, head=\n{window.head(5).to_string()}"
                )
                return result

            indices = np.arange(len(window))

            window['range'] = window['high'] - window['low']
            atr = window['range'].rolling(window=20).mean().iloc[-1] or 0.0001
            self.logger.debug(f"ATR for {symbol} ({timeframe}): {atr:.6f}")

            pivot_highs = self._find_pivot_points(highs, is_high=True)
            pivot_lows = self._find_pivot_points(lows, is_high=False)
            if len(pivot_highs) < 3 or len(pivot_lows) < 3:
                self.logger.debug(f"Falling Wedge rejected for {symbol} ({timeframe}): Insufficient pivot points (highs={len(pivot_highs)}, lows={len(pivot_lows)})")
                return result

            high_points = pivot_highs.iloc[-3:].reset_index()
            low_points = pivot_lows.iloc[-3:].reset_index()
            if len(high_points) < 3 or len(low_points) < 3:
                return result

            if not (high_points['high'] > low_points['low'].max()).all():
                self.logger.debug(f"Falling Wedge rejected for {symbol} ({timeframe}): High points not above low points")
                return result

            if not (high_points['high'].diff().dropna() < 0).all():
                self.logger.debug(f"Falling Wedge rejected for {symbol} ({timeframe}): High points not consistently lower")
                return result
            if not (low_points['low'].diff().dropna() > 0).all():
                self.logger.debug(f"Falling Wedge rejected for {symbol} ({timeframe}): Low points not consistently higher")
                return result

            high_x = high_points.index.values
            high_y = high_points['high'].values
            low_x = low_points.index.values
            low_y = low_points['low'].values

            high_slope, high_intercept = np.polyfit(high_x, high_y, 1)
            low_slope, low_intercept = np.polyfit(low_x, low_y, 1)

            if not (high_slope < low_slope < 0):
                self.logger.debug(f"Falling Wedge rejected for {symbol} ({timeframe}): Invalid slopes (high_slope={high_slope:.6f}, low_slope={low_slope:.6f})")
                return result

            trendline_points = np.arange(len(window) - 10, len(window))
            upper_trendlines = high_slope * trendline_points + high_intercept
            lower_trendlines = low_slope * trendline_points + low_intercept

            if not (upper_trendlines > lower_trendlines).all():
                self.logger.debug(f"Falling Wedge rejected for {symbol} ({timeframe}): Upper trendline not consistently above lower")
                return result

            latest_idx = len(window) - 1
            upper_trendline = upper_trendlines[-1]
            lower_trendline = lower_trendlines[-1]

            min_separation = 0.01 if timeframe in ['1m', '5m'] else 0.005
            max_separation = 0.05
            separation = abs(upper_trendline - lower_trendline) / upper_trendline
            if separation < min_separation or separation > max_separation:
                self.logger.debug(f"Falling Wedge rejected for {symbol} ({timeframe}): Invalid trendline separation ({separation:.4f})")
                return result

            latest_close = closes.iloc[-1]
            is_falling_wedge = latest_close > upper_trendline and abs(latest_close - upper_trendline) > 0.5 * atr

            if is_falling_wedge:
                result = {
                    'detected': True,
                    'upper_trendline': float(upper_trendline),
                    'lower_trendline': float(lower_trendline)
                }
                self.logger.debug(f"Falling Wedge detected for {symbol} ({timeframe}): upper={upper_trendline:.6f}, lower={lower_trendline:.6f}, close={latest_close:.6f}")

            self.logger.debug(f"Falling Wedge check for {symbol} ({timeframe}): {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error checking Falling Wedge for {symbol} ({timeframe}): {str(e)}")
            return result

    def rectangle_bullish(self, symbol: str, timeframe: str) -> Dict[str, any]:
        result = {'detected': False, 'support_level': None, 'resistance_level': None}
        try:
            if symbol not in self.symbols or timeframe not in self.timeframes:
                return result

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=20):
                return result

            window = klines.tail(20).copy()
            try:
                highs = window['high']
                lows = window['low']
                closes = window['close']
            except KeyError as e:
                self.logger.error(
                    f"KeyError accessing columns in {timeframe} klines for {symbol}: {str(e)}, "
                    f"columns={list(window.columns)}, shape={window.shape}, head=\n{window.head(5).to_string()}"
                )
                return result

            tolerance = 0.03
            max_high = highs.max()
            min_low = lows.min()
            resistance_candidates = highs[highs >= max_high * (1 - tolerance)]
            support_candidates = lows[lows <= min_low * (1 + tolerance)]
            if len(resistance_candidates) < 2 or len(support_candidates) < 2:
                return result

            resistance_level = resistance_candidates.mean()
            support_level = support_candidates.mean()
            high_range = resistance_candidates.max() - resistance_candidates.min()
            low_range = support_candidates.max() - support_candidates.min()
            if high_range / resistance_level > tolerance or low_range / support_level > tolerance:
                return result

            first_touch_idx = min(resistance_candidates.index.min(), support_candidates.index.min())
            last_touch_idx = max(resistance_candidates.index.max(), support_candidates.index.max())
            if last_touch_idx - first_touch_idx < 10:
                return result

            latest_close = closes.iloc[-1]
            is_rectangle_bullish = latest_close > resistance_level

            if is_rectangle_bullish:
                result = {
                    'detected': True,
                    'support_level': float(support_level),
                    'resistance_level': float(resistance_level)
                }

            self.logger.debug(f"Bullish Rectangle check for {symbol} ({timeframe}): {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error checking Bullish Rectangle for {symbol} ({timeframe}): {str(e)}")
            return result

    def rectangle_bearish(self, symbol: str, timeframe: str) -> Dict[str, any]:
        result = {'detected': False, 'support_level': None, 'resistance_level': None}
        try:
            if symbol not in self.symbols or timeframe not in self.timeframes:
                return result

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=20):
                return result

            window = klines.tail(20).copy()
            try:
                highs = window['high']
                lows = window['low']
                closes = window['close']
            except KeyError as e:
                self.logger.error(
                    f"KeyError accessing columns in {timeframe} klines for {symbol}: {str(e)}, "
                    f"columns={list(window.columns)}, shape={window.shape}, head=\n{window.head(5).to_string()}"
                )
                return result

            tolerance = 0.03
            max_high = highs.max()
            min_low = lows.min()
            resistance_candidates = highs[highs >= max_high * (1 - tolerance)]
            support_candidates = lows[lows <= min_low * (1 + tolerance)]
            if len(resistance_candidates) < 2 or len(support_candidates) < 2:
                return result

            resistance_level = resistance_candidates.mean()
            support_level = support_candidates.mean()
            high_range = resistance_candidates.max() - resistance_candidates.min()
            low_range = support_candidates.max() - support_candidates.min()
            if high_range / resistance_level > tolerance or low_range / support_level > tolerance:
                return result

            first_touch_idx = min(resistance_candidates.index.min(), support_candidates.index.min())
            last_touch_idx = max(resistance_candidates.index.max(), support_candidates.index.max())
            if last_touch_idx - first_touch_idx < 10:
                return result

            latest_close = closes.iloc[-1]
            is_rectangle_bearish = latest_close < support_level

            if is_rectangle_bearish:
                result = {
                    'detected': True,
                    'support_level': float(support_level),
                    'resistance_level': float(resistance_level)
                }

            self.logger.debug(f"Bearish Rectangle check for {symbol} ({timeframe}): {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error checking Bearish Rectangle for {symbol} ({timeframe}): {str(e)}")
            return result

    def flag_bullish(self, symbol: str, timeframe: str) -> Dict[str, any]:
        result = {'detected': False, 'upper_trendline': None, 'lower_trendline': None, 'flagpole_height': None}
        try:
            if symbol not in self.symbols or timeframe not in self.timeframes:
                self.logger.error(f"Invalid symbol: {symbol} or timeframe: {timeframe}")
                return result

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=15):
                return result

            window = klines.tail(15).copy()
            try:
                highs = window['high']
                lows = window['low']
                closes = window['close']
            except KeyError as e:
                self.logger.error(
                    f"KeyError accessing columns in {timeframe} klines for {symbol}: {str(e)}, "
                    f"columns={list(window.columns)}, shape={window.shape}, head=\n{window.head(5).to_string()}"
                )
                return result

            indices = np.arange(len(window))

            window['range'] = window['high'] - window['low']
            atr = window['range'].rolling(window=14).mean().iloc[-1] or 0.0001
            self.logger.debug(f"ATR for {symbol} ({timeframe}): {atr:.6f}")

            flagpole_window = window.iloc[:5]
            flagpole_start = flagpole_window['close'].iloc[0]
            flagpole_end = flagpole_window['close'].max()
            flagpole_gain = (flagpole_end - flagpole_start) / flagpole_start
            if flagpole_gain < 0.05:
                self.logger.debug(f"Bullish Flag rejected for {symbol} ({timeframe}): Insufficient flagpole gain ({flagpole_gain:.3f})")
                return result
            flagpole_height = flagpole_end - flagpole_start

            flag_window = window.iloc[5:]
            if len(flag_window) < 5:
                return result

            pivot_highs = self._find_pivot_points(flag_window['high'], is_high=True)
            pivot_lows = self._find_pivot_points(flag_window['low'], is_high=False)
            if len(pivot_highs) < 3 or len(pivot_lows) < 3:
                self.logger.debug(f"Bullish Flag rejected for {symbol} ({timeframe}): Insufficient pivot points (highs={len(pivot_highs)}, lows={len(pivot_lows)})")
                return result

            high_points = pivot_highs.iloc[-3:].reset_index()
            low_points = pivot_lows.iloc[-3:].reset_index()
            if len(high_points) < 3 or len(low_points) < 3:
                return result

            if not (high_points['high'] > low_points['low'].max()).all():
                self.logger.debug(f"Bullish Flag rejected for {symbol} ({timeframe}): High points not above low points")
                return result

            if not (high_points['high'].diff().dropna() < 0).all():
                self.logger.debug(f"Bullish Flag rejected for {symbol} ({timeframe}): High points not consistently lower")
                return result
            if not (low_points['low'].diff().dropna() > 0).all():
                self.logger.debug(f"Bullish Flag rejected for {symbol} ({timeframe}): Low points not consistently higher")
                return result

            high_x = high_points.index.values + 5
            high_y = high_points['high'].values
            low_x = low_points.index.values + 5
            low_y = low_points['low'].values

            high_slope, high_intercept = np.polyfit(high_x, high_y, 1)
            low_slope, low_intercept = np.polyfit(low_x, low_y, 1)

            slope_tolerance = 0.1
            if high_slope >= 0 or low_slope >= 0 or abs(high_slope - low_slope) / abs(high_slope) > slope_tolerance:
                self.logger.debug(f"Bullish Flag rejected for {symbol} ({timeframe}): Non-parallel or non-downward channel (high_slope={high_slope:.6f}, low_slope={low_slope:.6f})")
                return result

            trendline_points = np.arange(len(window) - 10, len(window))
            upper_trendlines = high_slope * trendline_points + high_intercept
            lower_trendlines = low_slope * trendline_points + low_intercept

            if not (upper_trendlines > lower_trendlines).all():
                self.logger.debug(f"Bullish Flag rejected for {symbol} ({timeframe}): Upper trendline not consistently above lower")
                return result

            latest_idx = len(window) - 1
            upper_trendline = upper_trendlines[-1]
            lower_trendline = lower_trendlines[-1]

            min_separation = 0.01 if timeframe in ['1m', '5m'] else 0.005
            max_separation = 0.05
            separation = abs(upper_trendline - lower_trendline) / upper_trendline
            if separation < min_separation or separation > max_separation:
                self.logger.debug(f"Bullish Flag rejected for {symbol} ({timeframe}): Invalid trendline separation ({separation:.4f})")
                return result

            latest_close = closes.iloc[-1]
            is_flag_bullish = latest_close > upper_trendline and abs(latest_close - upper_trendline) > 0.5 * atr

            if is_flag_bullish:
                result = {
                    'detected': True,
                    'upper_trendline': float(upper_trendline),
                    'lower_trendline': float(lower_trendline),
                    'flagpole_height': float(flagpole_height)
                }
                self.logger.debug(f"Bullish Flag detected for {symbol} ({timeframe}): upper={upper_trendline:.6f}, lower={lower_trendline:.6f}, close={latest_close:.6f}")

            self.logger.debug(f"Bullish Flag check for {symbol} ({timeframe}): {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error checking Bullish Flag for {symbol} ({timeframe}): {str(e)}")
            return result

    def flag_bearish(self, symbol: str, timeframe: str) -> Dict[str, any]:
        result = {'detected': False, 'upper_trendline': None, 'lower_trendline': None, 'flagpole_height': None}
        try:
            if symbol not in self.symbols or timeframe not in self.timeframes:
                return result

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=15):
                return result

            window = klines.tail(15).copy()
            try:
                highs = window['high']
                lows = window['low']
                closes = window['close']
            except KeyError as e:
                self.logger.error(
                    f"KeyError accessing columns in {timeframe} klines for {symbol}: {str(e)}, "
                    f"columns={list(window.columns)}, shape={window.shape}, head=\n{window.head(5).to_string()}"
                )
                return result

            indices = np.arange(len(window))

            window['range'] = window['high'] - window['low']
            atr = window['range'].rolling(window=14).mean().iloc[-1] or 0.0001
            self.logger.debug(f"ATR for {symbol} ({timeframe}): {atr:.6f}")

            flagpole_window = window.iloc[:5]
            flagpole_start = flagpole_window['close'].iloc[0]
            flagpole_end = flagpole_window['close'].min()
            flagpole_loss = (flagpole_start - flagpole_end) / flagpole_start
            if flagpole_loss < 0.05:
                self.logger.debug(f"Bearish Flag rejected for {symbol} ({timeframe}): Insufficient flagpole loss ({flagpole_loss:.3f})")
                return result
            flagpole_height = flagpole_start - flagpole_end

            flag_window = window.iloc[5:]
            if len(flag_window) < 5:
                return result

            pivot_highs = self._find_pivot_points(flag_window['high'], is_high=True)
            pivot_lows = self._find_pivot_points(flag_window['low'], is_high=False)
            if len(pivot_highs) < 3 or len(pivot_lows) < 3:
                self.logger.debug(f"Bearish Flag rejected for {symbol} ({timeframe}): Insufficient pivot points (highs={len(pivot_highs)}, lows={len(pivot_lows)})")
                return result

            high_points = pivot_highs.iloc[-3:].reset_index()
            low_points = pivot_lows.iloc[-3:].reset_index()
            if len(high_points) < 3 or len(low_points) < 3:
                return result

            if not (high_points['high'] > low_points['low'].max()).all():
                self.logger.debug(f"Bearish Flag rejected for {symbol} ({timeframe}): High points not above low points")
                return result

            if not (high_points['high'].diff().dropna() > 0).all():
                self.logger.debug(f"Bearish Flag rejected for {symbol} ({timeframe}): High points not consistently higher")
                return result
            if not (low_points['low'].diff().dropna() < 0).all():
                self.logger.debug(f"Bearish Flag rejected for {symbol} ({timeframe}): Low points not consistently lower")
                return result

            high_x = high_points.index.values + 5
            high_y = high_points['high'].values
            low_x = low_points.index.values + 5
            low_y = low_points['low'].values

            high_slope, high_intercept = np.polyfit(high_x, high_y, 1)
            low_slope, low_intercept = np.polyfit(low_x, low_y, 1)

            slope_tolerance = 0.1
            if high_slope <= 0 or low_slope <= 0 or abs(high_slope - low_slope) / abs(high_slope) > slope_tolerance:
                self.logger.debug(f"Bearish Flag rejected for {symbol} ({timeframe}): Non-parallel or non-upward channel (high_slope={high_slope:.6f}, low_slope={low_slope:.6f})")
                return result

            trendline_points = np.arange(len(window) - 10, len(window))
            upper_trendlines = high_slope * trendline_points + high_intercept
            lower_trendlines = low_slope * trendline_points + low_intercept

            if not (upper_trendlines > lower_trendlines).all():
                self.logger.debug(f"Bearish Flag rejected for {symbol} ({timeframe}): Upper trendline not consistently above lower")
                return result

            latest_idx = len(window) - 1
            upper_trendline = upper_trendlines[-1]
            lower_trendline = lower_trendlines[-1]

            min_separation = 0.01 if timeframe in ['1m', '5m'] else 0.005
            max_separation = 0.05
            separation = abs(upper_trendline - lower_trendline) / upper_trendline
            if separation < min_separation or separation > max_separation:
                self.logger.debug(f"Bearish Flag rejected for {symbol} ({timeframe}): Invalid trendline separation ({separation:.4f})")
                return result

            latest_close = closes.iloc[-1]
            is_flag_bearish = latest_close < lower_trendline and abs(latest_close - lower_trendline) > 0.5 * atr

            if is_flag_bearish:
                result = {
                    'detected': True,
                    'upper_trendline': float(upper_trendline),
                    'lower_trendline': float(lower_trendline),
                    'flagpole_height': float(flagpole_height)
                }
                self.logger.debug(f"Bearish Flag detected for {symbol} ({timeframe}): upper={upper_trendline:.6f}, lower={lower_trendline:.6f}, close={latest_close:.6f}")

            self.logger.debug(f"Bearish Flag check for {symbol} ({timeframe}): {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error checking Bearish Flag for {symbol} ({timeframe}): {str(e)}")
            return result

    def pennant_bullish(self, symbol: str, timeframe: str) -> Dict[str, any]:
        result = {'detected': False, 'upper_trendline': None, 'lower_trendline': None, 'flagpole_height': None}
        try:
            if symbol not in self.symbols or timeframe not in self.timeframes:
                return result

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=15):
                return result

            window = klines.tail(15).copy()
            try:
                highs = window['high']
                lows = window['low']
                closes = window['close']
            except KeyError as e:
                self.logger.error(
                    f"KeyError accessing columns in {timeframe} klines for {symbol}: {str(e)}, "
                    f"columns={list(window.columns)}, shape={window.shape}, head=\n{window.head(5).to_string()}"
                )
                return result

            indices = np.arange(len(window))

            window['range'] = window['high'] - window['low']
            atr = window['range'].rolling(window=14).mean().iloc[-1] or 0.0001
            self.logger.debug(f"ATR for {symbol} ({timeframe}): {atr:.6f}")

            flagpole_window = window.iloc[:5]
            flagpole_start = flagpole_window['close'].iloc[0]
            flagpole_end = flagpole_window['close'].max()
            flagpole_gain = (flagpole_end - flagpole_start) / flagpole_start
            if flagpole_gain < 0.05:
                self.logger.debug(f"Bullish Pennant rejected for {symbol} ({timeframe}): Insufficient flagpole gain ({flagpole_gain:.3f})")
                return result
            flagpole_height = flagpole_end - flagpole_start

            pennant_window = window.iloc[5:]
            if len(pennant_window) < 5:
                return result

            pivot_highs = self._find_pivot_points(pennant_window['high'], is_high=True)
            pivot_lows = self._find_pivot_points(pennant_window['low'], is_high=False)
            if len(pivot_highs) < 3 or len(pivot_lows) < 3:
                self.logger.debug(f"Bullish Pennant rejected for {symbol} ({timeframe}): Insufficient pivot points (highs={len(pivot_highs)}, lows={len(pivot_lows)})")
                return result

            high_points = pivot_highs.iloc[-3:].reset_index()
            low_points = pivot_lows.iloc[-3:].reset_index()
            if len(high_points) < 3 or len(low_points) < 3:
                return result

            if not (high_points['high'] > low_points['low'].max()).all():
                self.logger.debug(f"Bullish Pennant rejected for {symbol} ({timeframe}): High points not above low points")
                return result

            if not (high_points['high'].diff().dropna() < 0).all():
                self.logger.debug(f"Bullish Pennant rejected for {symbol} ({timeframe}): High points not consistently lower")
                return result
            if not (low_points['low'].diff().dropna() > 0).all():
                self.logger.debug(f"Bullish Pennant rejected for {symbol} ({timeframe}): Low points not consistently higher")
                return result

            high_x = high_points.index.values + 5
            high_y = high_points['high'].values
            low_x = low_points.index.values + 5
            low_y = low_points['low'].values

            high_slope, high_intercept = np.polyfit(high_x, high_y, 1)
            low_slope, low_intercept = np.polyfit(low_x, low_y, 1)

            if high_slope >= 0 or low_slope <= 0:
                self.logger.debug(f"Bullish Pennant rejected for {symbol} ({timeframe}): Invalid slopes (high_slope={high_slope:.6f}, low_slope={low_slope:.6f})")
                return result

            trendline_points = np.arange(len(window) - 10, len(window))
            upper_trendlines = high_slope * trendline_points + high_intercept
            lower_trendlines = low_slope * trendline_points + low_intercept

            if not (upper_trendlines > lower_trendlines).all():
                self.logger.debug(f"Bullish Pennant rejected for {symbol} ({timeframe}): Upper trendline not consistently above lower")
                return result

            latest_idx = len(window) - 1
            upper_trendline = upper_trendlines[-1]
            lower_trendline = lower_trendlines[-1]

            min_separation = 0.01 if timeframe in ['1m', '5m'] else 0.005
            max_separation = 0.05
            separation = abs(upper_trendline - lower_trendline) / upper_trendline
            if separation < min_separation or separation > max_separation:
                self.logger.debug(f"Bullish Pennant rejected for {symbol} ({timeframe}): Invalid trendline separation ({separation:.4f})")
                return result

            latest_close = closes.iloc[-1]
            is_pennant_bullish = latest_close > upper_trendline and abs(latest_close - upper_trendline) > 0.5 * atr

            if is_pennant_bullish:
                result = {
                    'detected': True,
                    'upper_trendline': float(upper_trendline),
                    'lower_trendline': float(lower_trendline),
                    'flagpole_height': float(flagpole_height)
                }
                self.logger.debug(f"Bullish Pennant detected for {symbol} ({timeframe}): upper={upper_trendline:.6f}, lower={lower_trendline:.6f}, close={latest_close:.6f}")

            self.logger.debug(f"Bullish Pennant check for {symbol} ({timeframe}): {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error checking Bullish Pennant for {symbol} ({timeframe}): {str(e)}")
            return result

    def triangle_ascending(self, symbol: str, timeframe: str) -> Dict[str, any]:
        result = {'detected': False, 'resistance_level': None, 'support_trendline': None}
        try:
            if symbol not in self.symbols or timeframe not in self.timeframes:
                return result

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=20):
                return result

            window = klines.tail(20).copy()
            try:
                highs = window['high']
                lows = window['low']
                closes = window['close']
            except KeyError as e:
                self.logger.error(
                    f"KeyError accessing columns in {timeframe} klines for {symbol}: {str(e)}, "
                    f"columns={list(window.columns)}, shape={window.shape}, head=\n{window.head(5).to_string()}"
                )
                return result

            indices = np.arange(len(window))

            tolerance = 0.03
            max_high = highs.max()
            resistance_candidates = highs[highs >= max_high * (1 - tolerance)]
            if len(resistance_candidates) < 2:
                self.logger.debug(f"Ascending Triangle rejected for {symbol} ({timeframe}): Insufficient resistance candidates")
                return result

            resistance_level = resistance_candidates.mean()
            high_range = resistance_candidates.max() - resistance_candidates.min()
            if high_range / resistance_level > tolerance:
                self.logger.debug(f"Ascending Triangle rejected for {symbol} ({timeframe}): Resistance range too wide")
                return result

            pivot_lows = self._find_pivot_points(lows, is_high=False)
            if len(pivot_lows) < 2:
                self.logger.debug(f"Ascending Triangle rejected for {symbol} ({timeframe}): Insufficient pivot lows")
                return result

            low_points = pivot_lows.iloc[-2:].reset_index()
            if len(low_points) < 2:
                return result

            low_y = low_points.iloc[:, 1].values
            low_x = low_points.index.values
            low_slope, low_intercept = np.polyfit(low_x, low_y, 1)

            if low_slope <= 0:
                self.logger.debug(f"Ascending Triangle rejected for {symbol} ({timeframe}): Support trendline not ascending (slope={low_slope:.6f})")
                return result

            latest_idx = len(window) - 1
            support_trendline = low_slope * latest_idx + low_intercept

            first_touch_idx = min(resistance_candidates.index.min(), pivot_lows.index.min())
            last_touch_idx = max(resistance_candidates.index.max(), pivot_lows.index.max())
            if last_touch_idx - first_touch_idx < 10:
                self.logger.debug(f"Ascending Triangle rejected for {symbol} ({timeframe}): Insufficient touch span")
                return result

            latest_close = closes.iloc[-1]
            is_triangle_ascending = latest_close > resistance_level

            if is_triangle_ascending:
                result = {
                    'detected': True,
                    'resistance_level': float(resistance_level),
                    'support_trendline': float(support_trendline)
                }

            self.logger.debug(f"Ascending Triangle check for {symbol} ({timeframe}): {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error checking Ascending Triangle for {symbol} ({timeframe}): {str(e)}")
            return result

    def triangle_descending(self, symbol: str, timeframe: str) -> Dict[str, any]:
        result = {'detected': False, 'support_level': None, 'resistance_trendline': None}
        try:
            if symbol not in self.symbols or timeframe not in self.timeframes:
                return result

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=20):
                return result

            window = klines.tail(20).copy()
            try:
                highs = window['high']
                lows = window['low']
                closes = window['close']
            except KeyError as e:
                self.logger.error(
                    f"KeyError accessing columns in {timeframe} klines for {symbol}: {str(e)}, "
                    f"columns={list(window.columns)}, shape={window.shape}, head=\n{window.head(5).to_string()}"
                )
                return result

            indices = np.arange(len(window))

            tolerance = 0.03
            min_low = lows.min()
            support_candidates = lows[lows <= min_low * (1 + tolerance)]
            if len(support_candidates) < 2:
                self.logger.debug(f"Descending Triangle rejected for {symbol} ({timeframe}): Insufficient support candidates")
                return result

            support_level = support_candidates.mean()
            low_range = support_candidates.max() - support_candidates.min()
            if low_range / support_level > tolerance:
                self.logger.debug(f"Descending Triangle rejected for {symbol} ({timeframe}): Support range too wide")
                return result

            pivot_highs = self._find_pivot_points(highs, is_high=True)
            if len(pivot_highs) < 2:
                self.logger.debug(f"Descending Triangle rejected for {symbol} ({timeframe}): Insufficient pivot highs")
                return result

            high_points = pivot_highs.iloc[-2:].reset_index()
            if len(high_points) < 2:
                return result

            high_y = high_points.iloc[:, 1].values
            high_x = high_points.index.values
            high_slope, high_intercept = np.polyfit(high_x, high_y, 1)

            if high_slope >= 0:
                self.logger.debug(f"Descending Triangle rejected for {symbol} ({timeframe}): Resistance trendline not descending (slope={high_slope:.6f})")
                return result

            latest_idx = len(window) - 1
            resistance_trendline = high_slope * latest_idx + high_intercept

            first_touch_idx = min(pivot_highs.index.min(), support_candidates.index.min())
            last_touch_idx = max(pivot_highs.index.max(), support_candidates.index.max())
            if last_touch_idx - first_touch_idx < 10:
                self.logger.debug(f"Descending Triangle rejected for {symbol} ({timeframe}): Insufficient touch span")
                return result

            latest_close = closes.iloc[-1]
            is_triangle_descending = latest_close < support_level

            if is_triangle_descending:
                result = {
                    'detected': True,
                    'support_level': float(support_level),
                    'resistance_trendline': float(resistance_trendline)
                }

            self.logger.debug(f"Descending Triangle check for {symbol} ({timeframe}): {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error checking Descending Triangle for {symbol} ({timeframe}): {str(e)}")
            return result

    def triangle_symmetrical(self, symbol: str, timeframe: str) -> Dict[str, any]:
        result = {'detected': False, 'upper_trendline': None, 'lower_trendline': None}
        try:
            if symbol not in self.symbols or timeframe not in self.timeframes:
                return result

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=20):
                return result

            window = klines.tail(20).copy()
            try:
                highs = window['high']
                lows = window['low']
                closes = window['close']
            except KeyError as e:
                self.logger.error(
                    f"KeyError accessing columns in {timeframe} klines for {symbol}: {str(e)}, "
                    f"columns={list(window.columns)}, shape={window.shape}, head=\n{window.head(5).to_string()}"
                )
                return result

            indices = np.arange(len(window))

            window['range'] = window['high'] - window['low']
            atr = window['range'].rolling(window=14).mean().iloc[-1] or 0.0001
            self.logger.debug(f"ATR for {symbol} ({timeframe}): {atr:.6f}")

            pivot_highs = self._find_pivot_points(highs, is_high=True)
            pivot_lows = self._find_pivot_points(lows, is_high=False)
            if len(pivot_highs) < 3 or len(pivot_lows) < 3:
                self.logger.debug(f"Symmetrical Triangle rejected for {symbol} ({timeframe}): Insufficient pivot points (highs={len(pivot_highs)}, lows={len(pivot_lows)})")
                return result

            high_points = pivot_highs.iloc[-3:].reset_index()
            low_points = pivot_lows.iloc[-3:].reset_index()
            if len(high_points) < 3 or len(low_points) < 3:
                return result

            if not (high_points['high'] > low_points['low'].max()).all():
                self.logger.debug(f"Symmetrical Triangle rejected for {symbol} ({timeframe}): High points not above low points")
                return result

            if not (high_points['high'].diff().dropna() < 0).all():
                self.logger.debug(f"Symmetrical Triangle rejected for {symbol} ({timeframe}): High points not consistently lower")
                return result
            if not (low_points['low'].diff().dropna() > 0).all():
                self.logger.debug(f"Symmetrical Triangle rejected for {symbol} ({timeframe}): Low points not consistently higher")
                return result

            high_x = high_points.index.values
            high_y = high_points['high'].values
            low_x = low_points.index.values
            low_y = low_points['low'].values

            high_slope, high_intercept = np.polyfit(high_x, high_y, 1)
            low_slope, low_intercept = np.polyfit(low_x, low_y, 1)

            if not (high_slope < 0 < low_slope):
                self.logger.debug(f"Symmetrical Triangle rejected for {symbol} ({timeframe}): Invalid slopes (high_slope={high_slope:.6f}, low_slope={low_slope:.6f})")
                return result

            trendline_points = np.arange(len(window) - 10, len(window))
            upper_trendlines = high_slope * trendline_points + high_intercept
            lower_trendlines = low_slope * trendline_points + low_intercept

            if not (upper_trendlines > lower_trendlines).all():
                self.logger.debug(f"Symmetrical Triangle rejected for {symbol} ({timeframe}): Upper trendline not consistently above lower")
                return result

            latest_idx = len(window) - 1
            upper_trendline = upper_trendlines[-1]
            lower_trendline = lower_trendlines[-1]

            min_separation = 0.01 if timeframe in ['1m', '5m'] else 0.005
            max_separation = 0.05
            separation = abs(upper_trendline - lower_trendline) / upper_trendline
            if separation < min_separation or separation > max_separation:
                self.logger.debug(f"Symmetrical Triangle rejected for {symbol} ({timeframe}): Invalid trendline separation ({separation:.4f})")
                return result

            latest_close = closes.iloc[-1]
            is_triangle_symmetrical = (
                (latest_close > upper_trendline and abs(latest_close - upper_trendline) > 0.5 * atr) or
                (latest_close < lower_trendline and abs(latest_close - lower_trendline) > 0.5 * atr)
            )

            if is_triangle_symmetrical:
                result = {
                    'detected': True,
                    'upper_trendline': float(upper_trendline),
                    'lower_trendline': float(lower_trendline)
                }
                self.logger.debug(f"Symmetrical Triangle detected for {symbol} ({timeframe}): upper={upper_trendline:.6f}, lower={lower_trendline:.6f}, close={latest_close:.6f}")

            self.logger.debug(f"Symmetrical Triangle check for {symbol} ({timeframe}): {result}")
            return result
        except Exception as e:
            self.logger.error(f"Error checking Symmetrical Triangle for {symbol} ({timeframe}): {str(e)}")
            return result