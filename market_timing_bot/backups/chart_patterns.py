# chart_patterns.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import pandas as pd
import numpy as np
from typing import List, Dict

class ChartPatterns:
    def __init__(self, symbols: List[str], data_manager, enable_logging: bool = True):
        """
        Initializes the ChartPatterns class for identifying chart patterns using kline data.

        Args:
            symbols (List[str]): List of trading pair symbols (e.g., ['HBAR-USD']).
            data_manager: An instance of DataManager to fetch kline data.
            enable_logging (bool): If True, enables logging to 'logs/chart_patterns.log'.
        """
        self.symbols = symbols
        self.data_manager = data_manager
        self.enable_logging = enable_logging

        # Define timeframes for pattern analysis (aligned with DataManager)
        self.timeframes = ['1m', '5m', '15m', '1h', '6h', '1d']

        # Set up logger
        self.logger = logging.getLogger('ChartPatterns')
        if enable_logging:
            log_dir = Path(__file__).parent / 'logs'
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / 'chart_patterns.log'
            file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
            file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.logger.setLevel(logging.INFO)
        else:
            self.logger.setLevel(logging.WARNING)

        self.logger.debug("ChartPatterns initialized with symbols: %s", symbols)

    def _validate_klines(self, klines: pd.DataFrame, symbol: str, timeframe: str, min_rows: int = 1) -> bool:
        """
        Validates kline data for required columns and sufficient rows.

        Args:
            klines (pd.DataFrame): Kline data with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume'].
            symbol (str): Trading pair symbol.
            timeframe (str): Timeframe (e.g., '1m', '5m').
            min_rows (int): Minimum number of rows required (default: 1).

        Returns:
            bool: True if valid, False otherwise.
        """
        required_columns = ['open', 'high', 'low', 'close']
        if klines.empty:
            self.logger.warning(f"Empty {timeframe} klines buffer for {symbol}")
            return False
        if len(klines) < min_rows:
            self.logger.warning(f"Insufficient {timeframe} klines data for {symbol}: {len(klines)} rows, need at least {min_rows}")
            return False
        if not all(col in klines.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in klines.columns]
            self.logger.warning(f"Missing columns in {timeframe} klines for {symbol}: {missing_cols}")
            return False
        if klines[required_columns].isna().any().any():
            self.logger.warning(f"NaN values detected in {timeframe} klines for {symbol}")
            return False
        return True

    def calculate_all_patterns(self) -> Dict[str, Dict[str, Dict[str, bool]]]:
        """
        Calculates all chart patterns for all symbols across all timeframes using kline data.

        Returns:
            Dict: Dictionary mapping symbols to timeframes to patterns, e.g.,
                  {'HBAR-USD': {'1m': {'double_top': False, ..., 'triangle_symmetrical': False}, ...}}.
        """
        if not self.data_manager:
            self.logger.error("DataManager not provided during ChartPatterns initialization.")
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
                    self.logger.debug(f"Chart patterns for {symbol} ({timeframe}): %s", patterns)
                except Exception as e:
                    self.logger.error(f"Error calculating patterns for {symbol} ({timeframe}): {str(e)}")
                    symbol_patterns[timeframe] = {
                        'double_top': False,
                        'double_bottom': False,
                        'head_and_shoulders': False,
                        'inverse_head_and_shoulders': False,
                        'rising_wedge': False,
                        'falling_wedge': False,
                        'rectangle_bullish': False,
                        'rectangle_bearish': False,
                        'flag_bullish': False,
                        'flag_bearish': False,
                        'pennant_bullish': False,
                        'triangle_ascending': False,
                        'triangle_descending': False,
                        'triangle_symmetrical': False
                    }

            all_patterns[symbol] = symbol_patterns
            self.logger.debug(f"All chart patterns for {symbol}: %s", symbol_patterns)

        return all_patterns

    def double_top(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Double Top chart pattern in the latest 15 klines for the given symbol and timeframe.
        A Double Top has two peaks at similar price levels, a trough (neckline), and a breakout below the neckline.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Double Top pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=15):
                return False

            # Analyze the latest 15 klines
            window = klines.tail(15)
            highs = window['high']
            lows = window['low']
            closes = window['close']

            # Find peaks (local highs) within 3% of each other
            tolerance = 0.03  # 3% price tolerance
            max_high = highs.max()
            high_indices = highs[highs >= max_high * (1 - tolerance)].index
            if len(high_indices) < 2:
                self.logger.debug(f"Double Top check for {symbol} ({timeframe}): Insufficient peaks within 3% of max high {max_high:.6f}")
                return False

            # Get the two most recent peaks
            peak_indices = sorted(high_indices, reverse=True)[:2]
            if len(peak_indices) < 2:
                return False
            second_peak_idx = peak_indices[0]
            first_peak_idx = peak_indices[1]
            first_peak = highs[first_peak_idx]
            second_peak = highs[second_peak_idx]

            # Ensure peaks are separated by at least 2 klines
            if second_peak_idx - first_peak_idx < 2:
                self.logger.debug(f"Double Top check for {symbol} ({timeframe}): Peaks too close (indices {first_peak_idx}, {second_peak_idx})")
                return False

            # Find the neckline (lowest low between peaks)
            neckline = lows[first_peak_idx:second_peak_idx + 1].min()
            neckline_idx = lows[first_peak_idx:second_peak_idx + 1].idxmin()

            # Check for breakout below neckline in the latest kline
            latest_close = closes.iloc[-1]
            is_double_top = latest_close < neckline

            self.logger.debug(
                f"Double Top check for {symbol} ({timeframe}): "
                f"first_peak={first_peak:.6f} (idx={first_peak_idx}), "
                f"second_peak={second_peak:.6f} (idx={second_peak_idx}), "
                f"neckline={neckline:.6f} (idx={neckline_idx}), "
                f"latest_close={latest_close:.6f}, is_double_top={is_double_top}"
            )
            return bool(is_double_top)

        except Exception as e:
            self.logger.error(f"Error checking Double Top for {symbol} ({timeframe}): {str(e)}")
            return False

    def double_bottom(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Double Bottom chart pattern in the latest 15 klines for the given symbol and timeframe.
        A Double Bottom has two troughs at similar price levels, a peak (neckline), and a breakout above the neckline.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Double Bottom pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=15):
                return False

            # Analyze the latest 15 klines
            window = klines.tail(15)
            lows = window['low']
            highs = window['high']
            closes = window['close']

            # Find troughs (local lows) within 3% of each other
            tolerance = 0.03  # 3% price tolerance
            min_low = lows.min()
            low_indices = lows[lows <= min_low * (1 + tolerance)].index
            if len(low_indices) < 2:
                self.logger.debug(f"Double Bottom check for {symbol} ({timeframe}): Insufficient troughs within 3% of min low {min_low:.6f}")
                return False

            # Get the two most recent troughs
            trough_indices = sorted(low_indices, reverse=True)[:2]
            if len(trough_indices) < 2:
                self.logger.debug(f"Double Bottom check for {symbol} ({timeframe}): Fewer than two troughs found")
                return False
            second_trough_idx = trough_indices[0]
            first_trough_idx = trough_indices[1]
            first_trough = lows[first_trough_idx]
            second_trough = lows[second_trough_idx]

            # Ensure troughs are separated by at least 2 klines
            if second_trough_idx - first_trough_idx < 2:
                self.logger.debug(f"Double Bottom check for {symbol} ({timeframe}): Troughs too close (indices {first_trough_idx}, {second_trough_idx})")
                return False

            # Find the neckline (highest high between troughs)
            neck_highs = highs[first_trough_idx:second_trough_idx + 1]
            if neck_highs.empty:
                self.logger.debug(f"Double Bottom check for {symbol} ({timeframe}): No highs found between troughs")
                return False
            neckline = neck_highs.max()
            neckline_idx = neck_highs.idxmax()

            # Check for breakout above neckline in the latest kline
            latest_close = closes.iloc[-1]
            is_double_bottom = latest_close > neckline

            self.logger.debug(
                f"Double Bottom check for {symbol} ({timeframe}): "
                f"first_trough={first_trough:.6f} (idx={first_trough_idx}), "
                f"second_trough={second_trough:.6f} (idx={second_trough_idx}), "
                f"neckline={neckline:.6f} (idx={neckline_idx}), "
                f"latest_close={latest_close:.6f}, is_double_bottom={is_double_bottom}"
            )
            return bool(is_double_bottom)

        except Exception as e:
            self.logger.error(f"Error checking Double Bottom for {symbol} ({timeframe}): {str(e)}")
            return False

    def head_and_shoulders(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Head and Shoulders chart pattern in the latest 25 klines for the given symbol and timeframe.
        A Head and Shoulders has three peaks (left shoulder, head, right shoulder) with the head higher, two troughs forming a neckline, and a breakout below the neckline.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Head and Shoulders pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=25):
                return False

            # Analyze the latest 25 klines
            window = klines.tail(25)
            highs = window['high']
            lows = window['low']
            closes = window['close']

            # Find peaks (local highs) and troughs (local lows)
            tolerance = 0.03  # 3% price tolerance for shoulders and troughs
            max_high = highs.max()
            high_indices = highs[highs >= max_high * (1 - tolerance)].index
            if len(high_indices) < 3:
                self.logger.debug(f"Head and Shoulders check for {symbol} ({timeframe}): Insufficient peaks within 3% of max high {max_high:.6f}")
                return False

            # Identify head (highest peak)
            head_idx = highs.idxmax()
            head_high = highs[head_idx]

            # Find left and right shoulders (peaks before and after head)
            left_peaks = highs[highs.index < head_idx]
            right_peaks = highs[highs.index > head_idx]
            if left_peaks.empty or right_peaks.empty:
                self.logger.debug(f"Head and Shoulders check for {symbol} ({timeframe}): No peaks before or after head (idx={head_idx})")
                return False

            left_shoulder_idx = left_peaks.idxmax()
            right_shoulder_idx = right_peaks.idxmax()
            left_shoulder = highs[left_shoulder_idx]
            right_shoulder = highs[right_shoulder_idx]

            # Ensure shoulders are lower than head and similar to each other
            if left_shoulder >= head_high or right_shoulder >= head_high or abs(left_shoulder - right_shoulder) / left_shoulder > tolerance:
                self.logger.debug(f"Head and Shoulders check for {symbol} ({timeframe}): Invalid shoulders (left={left_shoulder:.6f}, right={right_shoulder:.6f}, head={head_high:.6f})")
                return False

            # Ensure shoulders are separated from head by at least 2 klines
            if head_idx - left_shoulder_idx < 2 or right_shoulder_idx - head_idx < 2:
                self.logger.debug(f"Head and Shoulders check for {symbol} ({timeframe}): Peaks too close (indices {left_shoulder_idx}, {head_idx}, {right_shoulder_idx})")
                return False

            # Add minimum price difference requirement (e.g., 1% of head price)
            min_price_diff = head_high * 0.01
            if abs(head_high - left_shoulder) < min_price_diff or abs(head_high - right_shoulder) < min_price_diff:
                self.logger.debug(f"Head and Shoulders check for {symbol} ({timeframe}): Peaks too similar in price (head={head_high:.6f}, left={left_shoulder:.6f}, right={right_shoulder:.6f})")
                return False

            # Find troughs between left shoulder and head, and head and right shoulder
            first_trough = lows[left_shoulder_idx:head_idx + 1].min()
            first_trough_idx = lows[left_shoulder_idx:head_idx + 1].idxmin()
            second_trough = lows[head_idx:right_shoulder_idx + 1].min()
            second_trough_idx = lows[head_idx:right_shoulder_idx + 1].idxmin()

            # Ensure troughs are similar (within 3% tolerance)
            if abs(first_trough - second_trough) / first_trough > tolerance:
                self.logger.debug(f"Head and Shoulders check for {symbol} ({timeframe}): Troughs not similar (first={first_trough:.6f}, second={second_trough:.6f})")
                return False

            # Define neckline as average of troughs
            neckline = (first_trough + second_trough) / 2

            # Check for breakout below neckline in the latest kline
            latest_close = closes.iloc[-1]
            is_head_and_shoulders = latest_close < neckline

            self.logger.debug(
                f"Head and Shoulders check for {symbol} ({timeframe}): "
                f"left_shoulder={left_shoulder:.6f} (idx={left_shoulder_idx}), "
                f"head={head_high:.6f} (idx={head_idx}), "
                f"right_shoulder={right_shoulder:.6f} (idx={right_shoulder_idx}), "
                f"first_trough={first_trough:.6f} (idx={first_trough_idx}), "
                f"second_trough={second_trough:.6f} (idx={second_trough_idx}), "
                f"neckline={neckline:.6f}, latest_close={latest_close:.6f}, "
                f"is_head_and_shoulders={is_head_and_shoulders}"
            )
            return bool(is_head_and_shoulders)

        except Exception as e:
            self.logger.error(f"Error checking Head and Shoulders for {symbol} ({timeframe}): {str(e)}")
            return False

    def inverse_head_and_shoulders(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies an Inverse Head and Shoulders chart pattern in the latest 25 klines for the given symbol and timeframe.
        An Inverse Head and Shoulders has three troughs (left shoulder, head, right shoulder) with the head lower, two peaks forming a neckline, and a breakout above the neckline.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if an Inverse Head and Shoulders pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=25):
                return False

            # Analyze the latest 25 klines
            window = klines.tail(25)
            lows = window['low']
            highs = window['high']
            closes = window['close']

            # Find troughs (local lows) within 3% of each other
            tolerance = 0.03  # 3% price tolerance
            min_low = lows.min()
            low_indices = lows[lows <= min_low * (1 + tolerance)].index
            if len(low_indices) < 3:
                self.logger.debug(f"Inverse Head and Shoulders check for {symbol} ({timeframe}): Insufficient troughs within 3% of min low {min_low:.6f}")
                return False

            # Identify head (lowest trough)
            if lows.empty:
                self.logger.debug(f"Inverse Head and Shoulders check for {symbol} ({timeframe}): No valid lows found")
                return False
            head_idx = lows.idxmin()
            head_low = lows[head_idx]

            # Find left and right shoulders (troughs before and after head)
            left_troughs = lows[lows.index < head_idx]
            right_troughs = lows[lows.index > head_idx]
            if left_troughs.empty or right_troughs.empty:
                self.logger.debug(f"Inverse Head and Shoulders check for {symbol} ({timeframe}): No troughs before or after head (idx={head_idx})")
                return False

            # Ensure valid trough indices
            if len(left_troughs) < 1 or len(right_troughs) < 1:
                self.logger.debug(f"Inverse Head and Shoulders check for {symbol} ({timeframe}): Insufficient troughs for shoulders")
                return False

            left_shoulder_idx = left_troughs.idxmin()
            right_shoulder_idx = right_troughs.idxmin()
            left_shoulder = lows[left_shoulder_idx]
            right_shoulder = lows[right_shoulder_idx]

            # Ensure shoulders are higher than head and similar to each other
            if left_shoulder <= head_low or right_shoulder <= head_low or abs(left_shoulder - right_shoulder) / left_shoulder > tolerance:
                self.logger.debug(f"Inverse Head and Shoulders check for {symbol} ({timeframe}): Invalid shoulders (left={left_shoulder:.6f}, right={right_shoulder:.6f}, head={head_low:.6f})")
                return False

            # Ensure shoulders are separated from head by at least 2 klines
            if head_idx - left_shoulder_idx < 2 or right_shoulder_idx - head_idx < 2:
                self.logger.debug(f"Inverse Head and Shoulders check for {symbol} ({timeframe}): Troughs too close (indices {left_shoulder_idx}, {head_idx}, {right_shoulder_idx})")
                return False

            # Find peaks between left shoulder and head, and head and right shoulder
            first_peak_segment = highs[left_shoulder_idx:head_idx + 1]
            second_peak_segment = highs[head_idx:right_shoulder_idx + 1]
            if first_peak_segment.empty or second_peak_segment.empty:
                self.logger.debug(f"Inverse Head and Shoulders check for {symbol} ({timeframe}): No peaks between shoulders and head")
                return False

            first_peak = first_peak_segment.max()
            first_peak_idx = first_peak_segment.idxmax()
            second_peak = second_peak_segment.max()
            second_peak_idx = second_peak_segment.idxmax()

            # Ensure peaks are similar (within 3% tolerance)
            if abs(first_peak - second_peak) / first_peak > tolerance:
                self.logger.debug(f"Inverse Head and Shoulders check for {symbol} ({timeframe}): Peaks not similar (first={first_peak:.6f}, second={second_peak:.6f})")
                return False

            # Define neckline as average of peaks
            neckline = (first_peak + second_peak) / 2

            # Check for breakout above neckline in the latest kline
            latest_close = closes.iloc[-1]
            is_inverse_head_and_shoulders = latest_close > neckline

            self.logger.debug(
                f"Inverse Head and Shoulders check for {symbol} ({timeframe}): "
                f"left_shoulder={left_shoulder:.6f} (idx={left_shoulder_idx}), "
                f"head={head_low:.6f} (idx={head_idx}), "
                f"right_shoulder={right_shoulder:.6f} (idx={right_shoulder_idx}), "
                f"first_peak={first_peak:.6f} (idx={first_peak_idx}), "
                f"second_peak={second_peak:.6f} (idx={second_peak_idx}), "
                f"neckline={neckline:.6f}, latest_close={latest_close:.6f}, "
                f"is_inverse_head_and_shoulders={is_inverse_head_and_shoulders}"
            )
            return bool(is_inverse_head_and_shoulders)

        except Exception as e:
            self.logger.error(f"Error checking Inverse Head and Shoulders for {symbol} ({timeframe}): {str(e)}")
            return False

    def rising_wedge(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Rising Wedge chart pattern in the latest 20 klines for the given symbol and timeframe.
        A Rising Wedge has converging trendlines with higher highs and higher lows, followed by a breakout below the lower trendline.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Rising Wedge pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=20):
                return False

            # Analyze the latest 20 klines
            window = klines.tail(20)
            highs = window['high']
            lows = window['low']
            closes = window['close']
            indices = np.arange(len(window))

            # Find at least two higher highs and two higher lows
            high_indices = highs[highs > highs.shift(1)].index
            low_indices = lows[lows > lows.shift(1)].index
            if len(high_indices) < 2 or len(low_indices) < 2:
                self.logger.debug(f"Rising Wedge check for {symbol} ({timeframe}): Insufficient higher highs ({len(high_indices)}) or higher lows ({len(low_indices)})")
                return False

            # Select the two most recent highs and lows for trendlines
            high_points = highs[high_indices[-2:]].reset_index()
            low_points = lows[low_indices[-2:]].reset_index()
            if len(high_points) < 2 or len(low_points) < 2:
                return False

            # Calculate trendline slopes using linear regression
            high_x = indices[high_points.index]
            high_y = high_points['high'].values
            low_x = indices[low_points.index]
            low_y = low_points['low'].values

            # Fit linear regression for upper (resistance) and lower (support) trendlines
            high_slope, high_intercept = np.polyfit(high_x, high_y, 1)
            low_slope, low_intercept = np.polyfit(low_x, low_y, 1)

            # Check for convergence: lower trendline slope > upper trendline slope
            if low_slope <= high_slope or high_slope <= 0 or low_slope <= 0:
                self.logger.debug(f"Rising Wedge check for {symbol} ({timeframe}): Non-converging or non-upward trendlines (high_slope={high_slope:.6f}, low_slope={low_slope:.6f})")
                return False

            # Calculate the lower trendline value at the latest kline
            latest_idx = len(window) - 1
            lower_trendline = low_slope * latest_idx + low_intercept

            # Check for breakout below the lower trendline in the latest kline
            latest_close = closes.iloc[-1]
            is_rising_wedge = latest_close < lower_trendline

            self.logger.debug(
                f"Rising Wedge check for {symbol} ({timeframe}): "
                f"high_slope={high_slope:.6f}, low_slope={low_slope:.6f}, "
                f"lower_trendline={lower_trendline:.6f}, latest_close={latest_close:.6f}, "
                f"is_rising_wedge={is_rising_wedge}"
            )
            return bool(is_rising_wedge)

        except Exception as e:
            self.logger.error(f"Error checking Rising Wedge for {symbol} ({timeframe}): {str(e)}")
            return False

    def falling_wedge(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Falling Wedge chart pattern in the latest 20 klines for the given symbol and timeframe.
        A Falling Wedge has converging trendlines with lower highs and lower lows, followed by a breakout above the upper trendline.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Falling Wedge pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=20):
                return False

            # Analyze the latest 20 klines
            window = klines.tail(20)
            highs = window['high']
            lows = window['low']
            closes = window['close']
            indices = np.arange(len(window))

            # Find at least two lower highs and two lower lows
            high_indices = highs[highs < highs.shift(1)].index
            low_indices = lows[lows < lows.shift(1)].index
            if len(high_indices) < 2 or len(low_indices) < 2:
                self.logger.debug(f"Falling Wedge check for {symbol} ({timeframe}): Insufficient lower highs ({len(high_indices)}) or lower lows ({len(low_indices)})")
                return False

            # Select the two most recent highs and lows for trendlines
            high_points = highs[high_indices[-2:]].reset_index()
            low_points = lows[low_indices[-2:]].reset_index()
            if len(high_points) < 2 or len(low_points) < 2:
                return False

            # Calculate trendline slopes using linear regression
            high_x = indices[high_points.index]
            high_y = high_points['high'].values
            low_x = indices[low_points.index]
            low_y = low_points['low'].values

            # Fit linear regression for upper (resistance) and lower (support) trendlines
            high_slope, high_intercept = np.polyfit(high_x, high_y, 1)
            low_slope, low_intercept = np.polyfit(low_x, low_y, 1)

            # Check for convergence: upper trendline slope (more negative) < lower trendline slope
            if high_slope >= low_slope or high_slope >= 0 or low_slope >= 0:
                self.logger.debug(f"Falling Wedge check for {symbol} ({timeframe}): Non-converging or non-downward trendlines (high_slope={high_slope:.6f}, low_slope={low_slope:.6f})")
                return False

            # Calculate the upper trendline value at the latest kline
            latest_idx = len(window) - 1
            upper_trendline = high_slope * latest_idx + high_intercept

            # Check for breakout above the upper trendline in the latest kline
            latest_close = closes.iloc[-1]
            is_falling_wedge = latest_close > upper_trendline

            self.logger.debug(
                f"Falling Wedge check for {symbol} ({timeframe}): "
                f"high_slope={high_slope:.6f}, low_slope={low_slope:.6f}, "
                f"upper_trendline={upper_trendline:.6f}, latest_close={latest_close:.6f}, "
                f"is_falling_wedge={is_falling_wedge}"
            )
            return bool(is_falling_wedge)

        except Exception as e:
            self.logger.error(f"Error checking Falling Wedge for {symbol} ({timeframe}): {str(e)}")
            return False

    def rectangle_bullish(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Bullish Rectangle chart pattern in the latest 20 klines for the given symbol and timeframe.
        A Bullish Rectangle has a horizontal channel with at least two touches of support and resistance, followed by a breakout above the resistance level.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Bullish Rectangle pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=20):
                return False

            # Analyze the latest 20 klines
            window = klines.tail(20)
            highs = window['high']
            lows = window['low']
            closes = window['close']

            # Find support and resistance levels
            tolerance = 0.03  # 3% price tolerance for support/resistance
            max_high = highs.max()
            min_low = lows.min()
            resistance_candidates = highs[highs >= max_high * (1 - tolerance)]
            support_candidates = lows[lows <= min_low * (1 + tolerance)]

            # Ensure at least two touches for both support and resistance
            if len(resistance_candidates) < 2 or len(support_candidates) < 2:
                self.logger.debug(f"Bullish Rectangle check for {symbol} ({timeframe}): Insufficient resistance touches ({len(resistance_candidates)}) or support touches ({len(support_candidates)})")
                return False

            # Calculate average support and resistance levels
            resistance_level = resistance_candidates.mean()
            support_level = support_candidates.mean()

            # Ensure the channel is horizontal (within tolerance) and spans at least 10 klines
            high_range = resistance_candidates.max() - resistance_candidates.min()
            low_range = support_candidates.max() - support_candidates.min()
            if high_range / resistance_level > tolerance or low_range / support_level > tolerance:
                self.logger.debug(f"Bullish Rectangle check for {symbol} ({timeframe}): Non-horizontal channel (high_range={high_range:.6f}, low_range={low_range:.6f})")
                return False

            # Check if the pattern spans at least 10 klines
            first_touch_idx = min(resistance_candidates.index.min(), support_candidates.index.min())
            last_touch_idx = max(resistance_candidates.index.max(), support_candidates.index.max())
            if last_touch_idx - first_touch_idx < 10:
                self.logger.debug(f"Bullish Rectangle check for {symbol} ({timeframe}): Channel too short (duration={last_touch_idx - first_touch_idx} klines)")
                return False

            # Check for breakout above resistance in the latest kline
            latest_close = closes.iloc[-1]
            is_rectangle_bullish = latest_close > resistance_level

            self.logger.debug(
                f"Bullish Rectangle check for {symbol} ({timeframe}): "
                f"resistance_level={resistance_level:.6f}, support_level={support_level:.6f}, "
                f"latest_close={latest_close:.6f}, is_rectangle_bullish={is_rectangle_bullish}"
            )
            return bool(is_rectangle_bullish)

        except Exception as e:
            self.logger.error(f"Error checking Bullish Rectangle for {symbol} ({timeframe}): {str(e)}")
            return False
        
    def rectangle_bearish(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Bearish Rectangle chart pattern in the latest 20 klines for the given symbol and timeframe.
        A Bearish Rectangle has a horizontal channel with at least two touches of support and resistance, followed by a breakout below the support level.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Bearish Rectangle pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=20):
                return False

            # Analyze the latest 20 klines
            window = klines.tail(20)
            highs = window['high']
            lows = window['low']
            closes = window['close']

            # Find support and resistance levels
            tolerance = 0.03  # 3% price tolerance for support/resistance
            max_high = highs.max()
            min_low = lows.min()
            resistance_candidates = highs[highs >= max_high * (1 - tolerance)]
            support_candidates = lows[lows <= min_low * (1 + tolerance)]

            # Ensure at least two touches for both support and resistance
            if len(resistance_candidates) < 2 or len(support_candidates) < 2:
                self.logger.debug(f"Bearish Rectangle check for {symbol} ({timeframe}): Insufficient resistance touches ({len(resistance_candidates)}) or support touches ({len(support_candidates)})")
                return False

            # Calculate average support and resistance levels
            resistance_level = resistance_candidates.mean()
            support_level = support_candidates.mean()

            # Ensure the channel is horizontal (within tolerance) and spans at least 10 klines
            high_range = resistance_candidates.max() - resistance_candidates.min()
            low_range = support_candidates.max() - support_candidates.min()
            if high_range / resistance_level > tolerance or low_range / support_level > tolerance:
                self.logger.debug(f"Bearish Rectangle check for {symbol} ({timeframe}): Non-horizontal channel (high_range={high_range:.6f}, low_range={low_range:.6f})")
                return False

            # Check if the pattern spans at least 10 klines
            first_touch_idx = min(resistance_candidates.index.min(), support_candidates.index.min())
            last_touch_idx = max(resistance_candidates.index.max(), support_candidates.index.max())
            if last_touch_idx - first_touch_idx < 10:
                self.logger.debug(f"Bearish Rectangle check for {symbol} ({timeframe}): Channel too short (duration={last_touch_idx - first_touch_idx} klines)")
                return False

            # Check for breakout below support in the latest kline
            latest_close = closes.iloc[-1]
            is_rectangle_bearish = latest_close < support_level

            self.logger.debug(
                f"Bearish Rectangle check for {symbol} ({timeframe}): "
                f"resistance_level={resistance_level:.6f}, support_level={support_level:.6f}, "
                f"latest_close={latest_close:.6f}, is_rectangle_bearish={is_rectangle_bearish}"
            )
            return bool(is_rectangle_bearish)

        except Exception as e:
            self.logger.error(f"Error checking Bearish Rectangle for {symbol} ({timeframe}): {str(e)}")
            return False
    
    def flag_bullish(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Bullish Flag chart pattern in the latest 15 klines for the given symbol and timeframe.
        A Bullish Flag has a sharp upward move (flagpole), a downward-sloping consolidation channel (flag), and a breakout above the upper trendline.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Bullish Flag pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=15):
                return False

            # Analyze the latest 15 klines
            window = klines.tail(15)
            highs = window['high']
            lows = window['low']
            closes = window['close']
            indices = np.arange(len(window))

            # Identify flagpole: significant upward move in the first 3-5 klines
            flagpole_window = window.iloc[:5]
            flagpole_start = flagpole_window['close'].iloc[0]
            flagpole_end = flagpole_window['close'].max()
            flagpole_gain = (flagpole_end - flagpole_start) / flagpole_start
            if flagpole_gain < 0.05:  # Require at least 5% gain
                self.logger.debug(f"Bullish Flag check for {symbol} ({timeframe}): Insufficient flagpole gain ({flagpole_gain:.3f})")
                return False

            # Identify flag: consolidation with lower highs and lower lows in the remaining klines
            flag_window = window.iloc[5:]
            if len(flag_window) < 5:  # Ensure enough klines for flag
                return False

            high_indices = flag_window['high'][flag_window['high'] < flag_window['high'].shift(1)].index
            low_indices = flag_window['low'][flag_window['low'] < flag_window['low'].shift(1)].index
            if len(high_indices) < 2 or len(low_indices) < 2:
                self.logger.debug(f"Bullish Flag check for {symbol} ({timeframe}): Insufficient lower highs ({len(high_indices)}) or lower lows ({len(low_indices)})")
                return False

            # Select the two most recent highs and lows for trendlines
            high_points = flag_window['high'].loc[high_indices[-2:]].reset_index()
            low_points = flag_window['low'].loc[low_indices[-2:]].reset_index()
            if len(high_points) < 2 or len(low_points) < 2:
                return False

            # Calculate trendline slopes using linear regression
            high_x = indices[high_points.index + 5]  # Adjust for flag window offset
            high_y = high_points['high'].values
            low_x = indices[low_points.index + 5]
            low_y = low_points['low'].values

            # Fit linear regression for upper (resistance) and lower (support) trendlines
            high_slope, high_intercept = np.polyfit(high_x, high_y, 1)
            low_slope, low_intercept = np.polyfit(low_x, low_y, 1)

            # Check for parallel downward channel: similar negative slopes
            slope_tolerance = 0.1  # 10% slope difference tolerance
            if high_slope >= 0 or low_slope >= 0 or abs(high_slope - low_slope) / abs(high_slope) > slope_tolerance:
                self.logger.debug(f"Bullish Flag check for {symbol} ({timeframe}): Non-parallel or non-downward channel (high_slope={high_slope:.6f}, low_slope={low_slope:.6f})")
                return False

            # Calculate the upper trendline value at the latest kline
            latest_idx = len(window) - 1
            upper_trendline = high_slope * latest_idx + high_intercept

            # Check for breakout above the upper trendline in the latest kline
            latest_close = closes.iloc[-1]
            is_flag_bullish = latest_close > upper_trendline

            self.logger.debug(
                f"Bullish Flag check for {symbol} ({timeframe}): "
                f"flagpole_gain={flagpole_gain:.3f}, high_slope={high_slope:.6f}, low_slope={low_slope:.6f}, "
                f"upper_trendline={upper_trendline:.6f}, latest_close={latest_close:.6f}, "
                f"is_flag_bullish={is_flag_bullish}"
            )
            return bool(is_flag_bullish)

        except Exception as e:
            self.logger.error(f"Error checking Bullish Flag for {symbol} ({timeframe}): {str(e)}")
            return False
        
    def flag_bearish(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Bearish Flag chart pattern in the latest 15 klines for the given symbol and timeframe.
        A Bearish Flag has a sharp downward move (flagpole), an upward-sloping consolidation channel (flag), and a breakout below the lower trendline.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Bearish Flag pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=15):
                return False

            # Analyze the latest 15 klines
            window = klines.tail(15)
            highs = window['high']
            lows = window['low']
            closes = window['close']
            indices = np.arange(len(window))

            # Identify flagpole: significant downward move in the first 3-5 klines
            flagpole_window = window.iloc[:5]
            flagpole_start = flagpole_window['close'].iloc[0]
            flagpole_end = flagpole_window['close'].min()
            flagpole_loss = (flagpole_start - flagpole_end) / flagpole_start
            if flagpole_loss < 0.05:  # Require at least 5% loss
                self.logger.debug(f"Bearish Flag check for {symbol} ({timeframe}): Insufficient flagpole loss ({flagpole_loss:.3f})")
                return False

            # Identify flag: consolidation with higher highs and higher lows in the remaining klines
            flag_window = window.iloc[5:]
            if len(flag_window) < 5:  # Ensure enough klines for flag
                return False

            high_indices = flag_window['high'][flag_window['high'] > flag_window['high'].shift(1)].index
            low_indices = flag_window['low'][flag_window['low'] > flag_window['low'].shift(1)].index
            if len(high_indices) < 2 or len(low_indices) < 2:
                self.logger.debug(f"Bearish Flag check for {symbol} ({timeframe}): Insufficient higher highs ({len(high_indices)}) or higher lows ({len(low_indices)})")
                return False

            # Select the two most recent highs and lows for trendlines
            high_points = flag_window['high'].loc[high_indices[-2:]].reset_index()
            low_points = flag_window['low'].loc[low_indices[-2:]].reset_index()
            if len(high_points) < 2 or len(low_points) < 2:
                return False

            # Calculate trendline slopes using linear regression
            high_x = indices[high_points.index + 5]  # Adjust for flag window offset
            high_y = high_points['high'].values
            low_x = indices[low_points.index + 5]
            low_y = low_points['low'].values

            # Fit linear regression for upper (resistance) and lower (support) trendlines
            high_slope, high_intercept = np.polyfit(high_x, high_y, 1)
            low_slope, low_intercept = np.polyfit(low_x, low_y, 1)

            # Check for parallel upward channel: similar positive slopes
            slope_tolerance = 0.1  # 10% slope difference tolerance
            if high_slope <= 0 or low_slope <= 0 or abs(high_slope - low_slope) / abs(high_slope) > slope_tolerance:
                self.logger.debug(f"Bearish Flag check for {symbol} ({timeframe}): Non-parallel or non-upward channel (high_slope={high_slope:.6f}, low_slope={low_slope:.6f})")
                return False

            # Calculate the lower trendline value at the latest kline
            latest_idx = len(window) - 1
            lower_trendline = low_slope * latest_idx + low_intercept

            # Check for breakout below the lower trendline in the latest kline
            latest_close = closes.iloc[-1]
            is_flag_bearish = latest_close < lower_trendline

            self.logger.debug(
                f"Bearish Flag check for {symbol} ({timeframe}): "
                f"flagpole_loss={flagpole_loss:.3f}, high_slope={high_slope:.6f}, low_slope={low_slope:.6f}, "
                f"lower_trendline={lower_trendline:.6f}, latest_close={latest_close:.6f}, "
                f"is_flag_bearish={is_flag_bearish}"
            )
            return bool(is_flag_bearish)

        except Exception as e:
            self.logger.error(f"Error checking Bearish Flag for {symbol} ({timeframe}): {str(e)}")
            return False
    
    def pennant_bullish(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Bullish Pennant chart pattern in the latest 15 klines for the given symbol and timeframe.
        A Bullish Pennant has a sharp upward move (flagpole), a converging triangular consolidation (pennant), and a breakout above the upper trendline.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Bullish Pennant pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=15):
                return False

            # Analyze the latest 15 klines
            window = klines.tail(15)
            highs = window['high']
            lows = window['low']
            closes = window['close']
            indices = np.arange(len(window))

            # Identify flagpole: significant upward move in the first 3-5 klines
            flagpole_window = window.iloc[:5]
            flagpole_start = flagpole_window['close'].iloc[0]
            flagpole_end = flagpole_window['close'].max()
            flagpole_gain = (flagpole_end - flagpole_start) / flagpole_start
            if flagpole_gain < 0.05:  # Require at least 5% gain
                self.logger.debug(f"Bullish Pennant check for {symbol} ({timeframe}): Insufficient flagpole gain ({flagpole_gain:.3f})")
                return False

            # Identify pennant: consolidation with converging trendlines in the remaining klines
            pennant_window = window.iloc[5:]
            if len(pennant_window) < 5:  # Ensure enough klines for pennant
                return False

            high_indices = pennant_window['high'][pennant_window['high'] < pennant_window['high'].shift(1)].index
            low_indices = pennant_window['low'][pennant_window['low'] > pennant_window['low'].shift(1)].index
            if len(high_indices) < 2 or len(low_indices) < 2:
                self.logger.debug(f"Bullish Pennant check for {symbol} ({timeframe}): Insufficient lower highs ({len(high_indices)}) or higher lows ({len(low_indices)})")
                return False

            # Select the two most recent highs and lows for trendlines
            high_points = pennant_window['high'].loc[high_indices[-2:]].reset_index()
            low_points = pennant_window['low'].loc[low_indices[-2:]].reset_index()
            if len(high_points) < 2 or len(low_points) < 2:
                return False

            # Calculate trendline slopes using linear regression
            high_x = indices[high_points.index + 5]  # Adjust for pennant window offset
            high_y = high_points['high'].values
            low_x = indices[low_points.index + 5]
            low_y = low_points['low'].values

            # Fit linear regression for upper (resistance) and lower (support) trendlines
            high_slope, high_intercept = np.polyfit(high_x, high_y, 1)
            low_slope, low_intercept = np.polyfit(low_x, low_y, 1)

            # Check for convergence: upper trendline slope < 0, lower trendline slope > 0
            if high_slope >= 0 or low_slope <= 0:
                self.logger.debug(f"Bullish Pennant check for {symbol} ({timeframe}): Non-converging trendlines (high_slope={high_slope:.6f}, low_slope={low_slope:.6f})")
                return False

            # Calculate the upper trendline value at the latest kline
            latest_idx = len(window) - 1
            upper_trendline = high_slope * latest_idx + high_intercept

            # Check for breakout above the upper trendline in the latest kline
            latest_close = closes.iloc[-1]
            is_pennant_bullish = latest_close > upper_trendline

            self.logger.debug(
                f"Bullish Pennant check for {symbol} ({timeframe}): "
                f"flagpole_gain={flagpole_gain:.3f}, high_slope={high_slope:.6f}, low_slope={low_slope:.6f}, "
                f"upper_trendline={upper_trendline:.6f}, latest_close={latest_close:.6f}, "
                f"is_pennant_bullish={is_pennant_bullish}"
            )
            return bool(is_pennant_bullish)

        except Exception as e:
            self.logger.error(f"Error checking Bullish Pennant for {symbol} ({timeframe}): {str(e)}")
            return False
        
    def pennant_bearish(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Bearish Pennant chart pattern in the latest 15 klines for the given symbol and timeframe.
        A Bearish Pennant has a sharp downward move (flagpole), a converging triangular consolidation (pennant), and a breakout below the lower trendline.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Bearish Pennant pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=15):
                return False

            # Analyze the latest 15 klines
            window = klines.tail(15)
            highs = window['high']
            lows = window['low']
            closes = window['close']
            indices = np.arange(len(window))

            # Identify flagpole: significant downward move in the first 3-5 klines
            flagpole_window = window.iloc[:5]
            flagpole_start = flagpole_window['close'].iloc[0]
            flagpole_end = flagpole_window['close'].min()
            flagpole_loss = (flagpole_start - flagpole_end) / flagpole_start
            if flagpole_loss < 0.05:  # Require at least 5% loss
                self.logger.debug(f"Bearish Pennant check for {symbol} ({timeframe}): Insufficient flagpole loss ({flagpole_loss:.3f})")
                return False

            # Identify pennant: consolidation with converging trendlines in the remaining klines
            pennant_window = window.iloc[5:]
            if len(pennant_window) < 5:  # Ensure enough klines for pennant
                return False

            high_indices = pennant_window['high'][pennant_window['high'] > pennant_window['high'].shift(1)].index
            low_indices = pennant_window['low'][pennant_window['low'] < pennant_window['low'].shift(1)].index
            if len(high_indices) < 2 or len(low_indices) < 2:
                self.logger.debug(f"Bearish Pennant check for {symbol} ({timeframe}): Insufficient higher highs ({len(high_indices)}) or lower lows ({len(low_indices)})")
                return False

            # Select the two most recent highs and lows for trendlines
            high_points = pennant_window['high'].loc[high_indices[-2:]].reset_index()
            low_points = pennant_window['low'].loc[low_indices[-2:]].reset_index()
            if len(high_points) < 2 or len(low_points) < 2:
                return False

            # Calculate trendline slopes using linear regression
            high_x = indices[high_points.index + 5]  # Adjust for pennant window offset
            high_y = high_points['high'].values
            low_x = indices[low_points.index + 5]
            low_y = low_points['low'].values

            # Fit linear regression for upper (resistance) and lower (support) trendlines
            high_slope, high_intercept = np.polyfit(high_x, high_y, 1)
            low_slope, low_intercept = np.polyfit(low_x, low_y, 1)

            # Check for convergence: upper trendline slope > 0, lower trendline slope < 0
            if high_slope <= 0 or low_slope >= 0:
                self.logger.debug(f"Bearish Pennant check for {symbol} ({timeframe}): Non-converging trendlines (high_slope={high_slope:.6f}, low_slope={low_slope:.6f})")
                return False

            # Calculate the lower trendline value at the latest kline
            latest_idx = len(window) - 1
            lower_trendline = low_slope * latest_idx + low_intercept

            # Check for breakout below the lower trendline in the latest kline
            latest_close = closes.iloc[-1]
            is_pennant_bearish = latest_close < lower_trendline

            self.logger.debug(
                f"Bearish Pennant check for {symbol} ({timeframe}): "
                f"flagpole_loss={flagpole_loss:.3f}, high_slope={high_slope:.6f}, low_slope={low_slope:.6f}, "
                f"lower_trendline={lower_trendline:.6f}, latest_close={latest_close:.6f}, "
                f"is_pennant_bearish={is_pennant_bearish}"
            )
            return bool(is_pennant_bearish)

        except Exception as e:
            self.logger.error(f"Error checking Bearish Pennant for {symbol} ({timeframe}): {str(e)}")
            return False
        
    def triangle_ascending(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies an Ascending Triangle chart pattern in the latest 20 klines for the given symbol and timeframe.
        An Ascending Triangle has a flat resistance level, a rising support level, and a breakout above the resistance.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if an Ascending Triangle pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=20):
                return False

            # Analyze the latest 20 klines
            window = klines.tail(20)
            highs = window['high']
            lows = window['low']
            closes = window['close']
            indices = np.arange(len(window))

            # Find resistance level: at least two highs within 3% tolerance
            tolerance = 0.03  # 3% price tolerance
            max_high = highs.max()
            resistance_candidates = highs[highs >= max_high * (1 - tolerance)]
            if len(resistance_candidates) < 2:
                self.logger.debug(f"Ascending Triangle check for {symbol} ({timeframe}): Insufficient resistance touches ({len(resistance_candidates)})")
                return False

            # Calculate resistance level as mean of candidates
            resistance_level = resistance_candidates.mean()
            high_range = resistance_candidates.max() - resistance_candidates.min()
            if high_range / resistance_level > tolerance:
                self.logger.debug(f"Ascending Triangle check for {symbol} ({timeframe}): Non-horizontal resistance (high_range={high_range:.6f})")
                return False

            # Find rising support: at least two higher lows
            low_indices = lows[lows > lows.shift(1)].index
            if len(low_indices) < 2:
                self.logger.debug(f"Ascending Triangle check for {symbol} ({timeframe}): Insufficient higher lows ({len(low_indices)})")
                return False

            # Select the two most recent lows for support trendline
            low_points = lows.loc[low_indices[-2:]].reset_index()
            if len(low_points) < 2:
                return False

            # Calculate support trendline slope using linear regression
            low_x = indices[low_points.index]
            low_y = low_points['low'].values
            low_slope, low_intercept = np.polyfit(low_x, low_y, 1)

            # Ensure support is rising (positive slope)
            if low_slope <= 0:
                self.logger.debug(f"Ascending Triangle check for {symbol} ({timeframe}): Non-rising support (low_slope={low_slope:.6f})")
                return False

            # Check if pattern spans at least 10 klines
            first_touch_idx = min(resistance_candidates.index.min(), low_indices.min())
            last_touch_idx = max(resistance_candidates.index.max(), low_indices.max())
            if last_touch_idx - first_touch_idx < 10:
                self.logger.debug(f"Ascending Triangle check for {symbol} ({timeframe}): Triangle too short (duration={last_touch_idx - first_touch_idx} klines)")
                return False

            # Check for breakout above resistance in the latest kline
            latest_close = closes.iloc[-1]
            is_triangle_ascending = latest_close > resistance_level

            self.logger.debug(
                f"Ascending Triangle check for {symbol} ({timeframe}): "
                f"resistance_level={resistance_level:.6f}, low_slope={low_slope:.6f}, "
                f"latest_close={latest_close:.6f}, is_triangle_ascending={is_triangle_ascending}"
            )
            return bool(is_triangle_ascending)

        except Exception as e:
            self.logger.error(f"Error checking Ascending Triangle for {symbol} ({timeframe}): {str(e)}")


    def triangle_descending(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Descending Triangle chart pattern in the latest 20 klines for the given symbol and timeframe.
        A Descending Triangle has a flat support level, a declining resistance level, and a breakout below the support.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Descending Triangle pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=20):
                return False

            # Analyze the latest 20 klines
            window = klines.tail(20)
            highs = window['high']
            lows = window['low']
            closes = window['close']
            indices = np.arange(len(window))

            # Find support level: at least two lows within 3% tolerance
            tolerance = 0.03  # 3% price tolerance
            min_low = lows.min()
            support_candidates = lows[lows <= min_low * (1 + tolerance)]
            if len(support_candidates) < 2:
                self.logger.debug(f"Descending Triangle check for {symbol} ({timeframe}): Insufficient support touches ({len(support_candidates)})")
                return False

            # Calculate support level as mean of candidates
            support_level = support_candidates.mean()
            low_range = support_candidates.max() - support_candidates.min()
            if low_range / support_level > tolerance:
                self.logger.debug(f"Descending Triangle check for {symbol} ({timeframe}): Non-horizontal support (low_range={low_range:.6f})")
                return False

            # Find declining resistance: at least two lower highs
            high_indices = highs[highs < highs.shift(1)].index
            if len(high_indices) < 2:
                self.logger.debug(f"Descending Triangle check for {symbol} ({timeframe}): Insufficient lower highs ({len(high_indices)})")
                return False

            # Select the two most recent highs for resistance trendline
            high_points = highs.loc[high_indices[-2:]].reset_index()
            if len(high_points) < 2:
                return False

            # Calculate resistance trendline slope using linear regression
            high_x = high_points.index
            high_y = high_points['high'].values
            high_slope, high_intercept = np.polyfit(high_x, high_y, 1)

            # Ensure resistance is declining (negative slope)
            if high_slope >= 0:
                self.logger.debug(f"Descending Triangle check for {symbol} ({timeframe}): Non-declining resistance (high_slope={high_slope:.6f})")
                return False

            # Check if pattern spans at least 10 klines
            first_touch_idx = min(high_indices.min(), support_candidates.index.min())
            last_touch_idx = max(high_indices.max(), support_candidates.index.max())
            if last_touch_idx - first_touch_idx < 10:
                self.logger.debug(f"Descending Triangle check for {symbol} ({timeframe}): Triangle too short (duration={last_touch_idx - first_touch_idx} klines)")
                return False

            # Check for breakout below support in the latest kline
            latest_close = closes.iloc[-1]
            is_triangle_descending = latest_close < support_level

            self.logger.debug(
                f"Descending Triangle check for {symbol} ({timeframe}): "
                f"support_level={support_level:.6f}, high_slope={high_slope:.6f}, "
                f"latest_close={latest_close:.6f}, is_triangle_descending={is_triangle_descending}"
            )
            return bool(is_triangle_descending)

        except Exception as e:
            self.logger.error(f"Error checking Descending Triangle for {symbol} ({timeframe}): {str(e)}")
            return False
        
    def triangle_symmetrical(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Symmetrical Triangle chart pattern in the latest 20 klines for the given symbol and timeframe.
        A Symmetrical Triangle has converging trendlines with lower highs and higher lows, and a breakout above the upper trendline or below the lower trendline.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Symmetrical Triangle pattern is present with a breakout, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=20):
                return False

            # Analyze the latest 20 klines
            window = klines.tail(20)
            highs = window['high']
            lows = window['low']
            closes = window['close']
            indices = np.arange(len(window))

            # Find declining resistance: at least two lower highs
            high_indices = highs[highs < highs.shift(1)].index
            if len(high_indices) < 2:
                self.logger.debug(f"Symmetrical Triangle check for {symbol} ({timeframe}): Insufficient lower highs ({len(high_indices)})")
                return False

            # Find rising support: at least two higher lows
            low_indices = lows[lows > lows.shift(1)].index
            if len(low_indices) < 2:
                self.logger.debug(f"Symmetrical Triangle check for {symbol} ({timeframe}): Insufficient higher lows ({len(low_indices)})")
                return False

            # Select the two most recent highs and lows for trendlines
            high_points = highs.loc[high_indices[-2:]].reset_index()
            low_points = lows.loc[low_indices[-2:]].reset_index()
            if len(high_points) < 2 or len(low_points) < 2:
                return False

            # Calculate trendline slopes using linear regression
            high_x = indices[high_points.index]
            high_y = high_points['high'].values
            low_x = indices[low_points.index]
            low_y = low_points['low'].values

            # Fit linear regression for upper (resistance) and lower (support) trendlines
            high_slope, high_intercept = np.polyfit(high_x, high_y, 1)
            low_slope, low_intercept = np.polyfit(low_x, low_y, 1)

            # Check for convergence: upper trendline slope < 0, lower trendline slope > 0
            if high_slope >= 0 or low_slope <= 0:
                self.logger.debug(f"Symmetrical Triangle check for {symbol} ({timeframe}): Non-converging trendlines (high_slope={high_slope:.6f}, low_slope={low_slope:.6f})")
                return False

            # Check if pattern spans at least 10 klines
            first_touch_idx = min(high_indices.min(), low_indices.min())
            last_touch_idx = max(high_indices.max(), low_indices.max())
            if last_touch_idx - first_touch_idx < 10:
                self.logger.debug(f"Symmetrical Triangle check for {symbol} ({timeframe}): Triangle too short (duration={last_touch_idx - first_touch_idx} klines)")
                return False

            # Calculate trendline values at the latest kline
            latest_idx = len(window) - 1
            upper_trendline = high_slope * latest_idx + high_intercept
            lower_trendline = low_slope * latest_idx + low_intercept

            # Check for breakout above upper trendline or below lower trendline
            latest_close = closes.iloc[-1]
            is_triangle_symmetrical = latest_close > upper_trendline or latest_close < lower_trendline

            self.logger.debug(
                f"Symmetrical Triangle check for {symbol} ({timeframe}): "
                f"high_slope={high_slope:.6f}, low_slope={low_slope:.6f}, "
                f"upper_trendline={upper_trendline:.6f}, lower_trendline={lower_trendline:.6f}, "
                f"latest_close={latest_close:.6f}, is_triangle_symmetrical={is_triangle_symmetrical}"
            )
            return bool(is_triangle_symmetrical)

        except Exception as e:
            self.logger.error(f"Error checking Symmetrical Triangle for {symbol} ({timeframe}): {str(e)}")
            return False