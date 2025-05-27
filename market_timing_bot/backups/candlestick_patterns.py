# candlestick_patterns.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import pandas as pd
from typing import List, Dict

class CandlestickPatterns:
    def __init__(self, symbols: List[str], data_manager, enable_logging: bool = True):
        """
        Initializes the CandlestickPatterns class for identifying candlestick patterns using kline data.

        Args:
            symbols (List[str]): List of trading pair symbols (e.g., ['HBAR-USD']).
            data_manager: An instance of DataManager to fetch kline data.
            enable_logging (bool): If True, enables logging to 'logs/candlestick_patterns.log'.
        """
        self.symbols = symbols
        self.data_manager = data_manager
        self.enable_logging = enable_logging

        # Define timeframes for pattern analysis (aligned with DataManager)
        self.timeframes = ['1m', '5m', '15m', '1h', '6h', '1d']

        # Set up logger
        self.logger = logging.getLogger('CandlestickPatterns')
        if enable_logging:
            log_dir = Path(__file__).parent / 'logs'
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / 'candlestick_patterns.log'
            file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.WARNING)

        self.logger.debug("CandlestickPatterns initialized with symbols: %s", symbols)

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
        Calculates all candlestick patterns for all symbols across all timeframes using the latest kline data.

        Returns:
            Dict: Dictionary mapping symbols to timeframes to patterns, e.g.,
                  {'HBAR-USD': {'1m': {'marubozu_bullish': False, 'marubozu_bearish': True, ...}, ...}}.
        """
        if not self.data_manager:
            self.logger.error("DataManager not provided during CandlestickPatterns initialization.")
            return {}

        all_patterns = {}
        for symbol in self.symbols:
            self.logger.debug(f"Calculating candlestick patterns for {symbol}")
            symbol_patterns = {}

            for timeframe in self.timeframes:
                try:
                    patterns = {
                        'marubozu_bullish': self.marubozu_bullish(symbol, timeframe),
                        'marubozu_bearish': self.marubozu_bearish(symbol, timeframe),
                        'hammer': self.hammer(symbol, timeframe),
                        'hanging_man': self.hanging_man(symbol, timeframe),
                        'inverted_hammer': self.inverted_hammer(symbol, timeframe),
                        'shooting_star': self.shooting_star(symbol, timeframe),
                        'doji_standard': self.doji_standard(symbol, timeframe),
                        'doji_long_legged': self.doji_long_legged(symbol, timeframe),
                        'doji_gravestone': self.doji_gravestone(symbol, timeframe),
                        'doji_dragonfly': self.doji_dragonfly(symbol, timeframe),
                        'doji_four_price': self.doji_four_price(symbol, timeframe),
                        'engulfing_bullish': self.engulfing_bullish(symbol, timeframe),
                        'engulfing_bearish': self.engulfing_bearish(symbol, timeframe),
                        'harami_bullish': self.harami_bullish(symbol, timeframe),
                        'harami_bearish': self.harami_bearish(symbol, timeframe),
                        'harami_cross_bullish': self.harami_cross_bullish(symbol, timeframe),
                        'harami_cross_bearish': self.harami_cross_bearish(symbol, timeframe),
                        'tweezer_tops': self.tweezer_tops(symbol, timeframe),
                        'tweezer_bottoms': self.tweezer_bottoms(symbol, timeframe),
                        'dark_cloud_cover': self.dark_cloud_cover(symbol, timeframe),
                        'piercing_line': self.piercing_line(symbol, timeframe),
                        'on_neck': self.on_neck(symbol, timeframe),
                        'morning_star': self.morning_star(symbol, timeframe),
                        'evening_star': self.evening_star(symbol, timeframe),
                        'three_white_soldiers': self.three_white_soldiers(symbol, timeframe),
                        'three_black_crows': self.three_black_crows(symbol, timeframe),
                        'three_inside_up': self.three_inside_up(symbol, timeframe),
                        'three_inside_down': self.three_inside_down(symbol, timeframe),
                        'stick_sandwich_bullish': self.stick_sandwich_bullish(symbol, timeframe),
                        'stick_sandwich_bearish': self.stick_sandwich_bearish(symbol, timeframe),
                        'rising_three_methods': self.rising_three_methods(symbol, timeframe),
                        'falling_three_methods': self.falling_three_methods(symbol, timeframe)
                    }
                    symbol_patterns[timeframe] = patterns
                    self.logger.debug(f"Candlestick patterns for {symbol} ({timeframe}): %s", patterns)
                except Exception as e:
                    self.logger.error(f"Error calculating patterns for {symbol} ({timeframe}): {str(e)}")
                    symbol_patterns[timeframe] = {
                        'marubozu_bullish': False,
                        'marubozu_bearish': False,
                        'hammer': False,
                        'hanging_man': False,
                        'inverted_hammer': False,
                        'shooting_star': False,
                        'doji_standard': False,
                        'doji_long_legged': False,
                        'doji_gravestone': False,
                        'doji_dragonfly': False,
                        'doji_four_price': False,
                        'engulfing_bullish': False,
                        'engulfing_bearish': False,
                        'harami_bullish': False,
                        'harami_bearish': False,
                        'harami_cross_bullish': False,
                        'harami_cross_bearish': False,
                        'tweezer_tops': False,
                        'tweezer_bottoms': False,
                        'dark_cloud_cover': False,
                        'piercing_line': False,
                        'on_neck': False,
                        'morning_star': False,
                        'evening_star': False,
                        'three_white_soldiers': False,
                        'three_black_crows': False,
                        'three_inside_up': False,
                        'three_inside_down': False,
                        'stick_sandwich_bullish': False,
                        'stick_sandwich_bearish': False,
                        'rising_three_methods': False,
                        'falling_three_methods': False
                    }

            all_patterns[symbol] = symbol_patterns
            self.logger.debug(f"All candlestick patterns for {symbol}: %s", symbol_patterns)

        return all_patterns

    def marubozu_bullish(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Bullish Marubozu candlestick pattern in the latest kline for the given symbol and timeframe.
        A Bullish Marubozu has a long bullish body (close > open), with minimal or no shadows (wicks).

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Bullish Marubozu pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe):
                return False

            latest = klines.iloc[-1]
            open_price, close_price = latest['open'], latest['close']
            high, low = latest['high'], latest['low']

            # Check for bullish direction
            if close_price <= open_price:
                self.logger.debug(f"Not a Bullish Marubozu for {symbol} ({timeframe}): close ({close_price}) <= open ({open_price})")
                return False

            # Calculate body and shadows
            body = close_price - open_price
            range_price = high - low
            lower_shadow = open_price - low
            upper_shadow = high - close_price

            # Marubozu criteria: body >= 80% of range, shadows <= 5% of range
            body_ratio = body / range_price if range_price > 0 else 0
            lower_shadow_ratio = lower_shadow / range_price if range_price > 0 else 0
            upper_shadow_ratio = upper_shadow / range_price if range_price > 0 else 0

            is_bullish_marubozu = (
                range_price > 0 and
                body_ratio >= 0.8 and
                lower_shadow_ratio <= 0.05 and
                upper_shadow_ratio <= 0.05
            )

            self.logger.debug(
                f"Bullish Marubozu check for {symbol} ({timeframe}): "
                f"body_ratio={body_ratio:.3f}, lower_shadow_ratio={lower_shadow_ratio:.3f}, "
                f"upper_shadow_ratio={upper_shadow_ratio:.3f}, is_bullish_marubozu={is_bullish_marubozu}"
            )
            return bool(is_bullish_marubozu)  # Convert to Python bool

        except Exception as e:
            self.logger.error(f"Error checking Bullish Marubozu for {symbol} ({timeframe}): {str(e)}")
            return False

    def marubozu_bearish(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Bearish Marubozu candlestick pattern in the latest kline for the given symbol and timeframe.
        A Bearish Marubozu has a long bearish body (close < open), with minimal or no shadows (wicks).

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Bearish Marubozu pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe):
                return False

            latest = klines.iloc[-1]
            open_price, close_price = latest['open'], latest['close']
            high, low = latest['high'], latest['low']

            # Check for bearish direction
            if close_price >= open_price:
                self.logger.debug(f"Not a Bearish Marubozu for {symbol} ({timeframe}): close ({close_price}) >= open ({open_price})")
                return False

            # Calculate body and shadows
            body = open_price - close_price
            range_price = high - low
            upper_shadow = high - open_price
            lower_shadow = close_price - low

            # Marubozu criteria: body >= 80% of range, shadows <= 5% of range
            body_ratio = body / range_price if range_price > 0 else 0
            upper_shadow_ratio = upper_shadow / range_price if range_price > 0 else 0
            lower_shadow_ratio = lower_shadow / range_price if range_price > 0 else 0

            is_bearish_marubozu = (
                range_price > 0 and
                body_ratio >= 0.8 and
                upper_shadow_ratio <= 0.05 and
                lower_shadow_ratio <= 0.05
            )

            self.logger.debug(
                f"Bearish Marubozu check for {symbol} ({timeframe}): "
                f"body_ratio={body_ratio:.3f}, upper_shadow_ratio={upper_shadow_ratio:.3f}, "
                f"lower_shadow_ratio={lower_shadow_ratio:.3f}, is_bearish_marubozu={is_bearish_marubozu}"
            )
            return bool(is_bearish_marubozu)  # Convert to Python bool

        except Exception as e:
            self.logger.error(f"Error checking Bearish Marubozu for {symbol} ({timeframe}): {str(e)}")
            return False

    def hammer(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Hammer candlestick pattern in the latest kline for the given symbol and timeframe.
        A Hammer has a small body, a long lower shadow (at least 2x the body), and a minimal upper shadow.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Hammer pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe):
                return False

            latest = klines.iloc[-1]
            open_price, close_price = latest['open'], latest['close']
            high, low = latest['high'], latest['low']

            # Calculate body and shadows
            body = abs(close_price - open_price)
            lower_shadow = min(open_price, close_price) - low
            upper_shadow = high - max(open_price, close_price)
            range_price = high - low

            # Hammer criteria:
            # - Small body: body <= 30% of range
            # - Long lower shadow: lower_shadow >= 2x body
            # - Minimal upper shadow: upper_shadow <= 0.5x body
            body_ratio = body / range_price if range_price > 0 else 0
            is_hammer = (
                range_price > 0 and
                body_ratio <= 0.3 and
                lower_shadow >= 2 * body and
                upper_shadow <= 0.5 * body
            )

            self.logger.debug(
                f"Hammer check for {symbol} ({timeframe}): "
                f"body_ratio={body_ratio:.3f}, lower_shadow={lower_shadow:.6f}, "
                f"upper_shadow={upper_shadow:.6f}, is_hammer={is_hammer}"
            )
            return bool(is_hammer)  # Convert to Python bool

        except Exception as e:
            self.logger.error(f"Error checking Hammer for {symbol} ({timeframe}): {str(e)}")
            return False

    def hanging_man(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Hanging Man candlestick pattern in the latest kline for the given symbol and timeframe.
        A Hanging Man has a small body, a long lower shadow (at least 2x the body), and a minimal upper shadow.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Hanging Man pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe):
                return False

            latest = klines.iloc[-1]
            open_price, close_price = latest['open'], latest['close']
            high, low = latest['high'], latest['low']

            # Calculate body and shadows
            body = abs(close_price - open_price)
            lower_shadow = min(open_price, close_price) - low
            upper_shadow = high - max(open_price, close_price)
            range_price = high - low

            # Hanging Man criteria:
            # - Small body: body <= 30% of range
            # - Long lower shadow: lower_shadow >= 2x body
            # - Minimal upper shadow: upper_shadow <= 0.5x body
            body_ratio = body / range_price if range_price > 0 else 0
            is_hanging_man = (
                range_price > 0 and
                body_ratio <= 0.3 and
                lower_shadow >= 2 * body and
                upper_shadow <= 0.5 * body
            )

            self.logger.debug(
                f"Hanging Man check for {symbol} ({timeframe}): "
                f"body_ratio={body_ratio:.3f}, lower_shadow={lower_shadow:.6f}, "
                f"upper_shadow={upper_shadow:.6f}, is_hanging_man={is_hanging_man}"
            )
            return bool(is_hanging_man)  # Convert to Python bool

        except Exception as e:
            self.logger.error(f"Error checking Hanging Man for {symbol} ({timeframe}): {str(e)}")
            return False

    def inverted_hammer(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies an Inverted Hammer candlestick pattern in the latest kline for the given symbol and timeframe.
        An Inverted Hammer has a small body, a long upper shadow (at least 2x the body), and a minimal lower shadow.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if an Inverted Hammer pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe):
                return False

            latest = klines.iloc[-1]
            open_price, close_price = latest['open'], latest['close']
            high, low = latest['high'], latest['low']

            # Calculate body and shadows
            body = abs(close_price - open_price)
            upper_shadow = high - max(open_price, close_price)
            lower_shadow = min(open_price, close_price) - low
            range_price = high - low

            # Inverted Hammer criteria:
            # - Small body: body <= 30% of range
            # - Long upper shadow: upper_shadow >= 2x body
            # - Minimal lower shadow: lower_shadow <= 0.5x body
            body_ratio = body / range_price if range_price > 0 else 0
            is_inverted_hammer = (
                range_price > 0 and
                body_ratio <= 0.3 and
                upper_shadow >= 2 * body and
                lower_shadow <= 0.5 * body
            )

            self.logger.debug(
                f"Inverted Hammer check for {symbol} ({timeframe}): "
                f"body_ratio={body_ratio:.3f}, upper_shadow={upper_shadow:.6f}, "
                f"lower_shadow={lower_shadow:.6f}, is_inverted_hammer={is_inverted_hammer}"
            )
            return bool(is_inverted_hammer)  # Convert to Python bool

        except Exception as e:
            self.logger.error(f"Error checking Inverted Hammer for {symbol} ({timeframe}): {str(e)}")
            return False

    def shooting_star(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Shooting Star candlestick pattern in the latest kline for the given symbol and timeframe.
        A Shooting Star has a small body, a long upper shadow (at least 2x the body), and a minimal lower shadow.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Shooting Star pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe):
                return False

            latest = klines.iloc[-1]
            open_price, close_price = latest['open'], latest['close']
            high, low = latest['high'], latest['low']

            # Calculate body and shadows
            body = abs(close_price - open_price)
            upper_shadow = high - max(open_price, close_price)
            lower_shadow = min(open_price, close_price) - low
            range_price = high - low

            # Shooting Star criteria:
            # - Small body: body <= 30% of range
            # - Long upper shadow: upper_shadow >= 2x body
            # - Minimal lower shadow: lower_shadow <= 0.5x body
            body_ratio = body / range_price if range_price > 0 else 0
            is_shooting_star = (
                range_price > 0 and
                body_ratio <= 0.3 and
                upper_shadow >= 2 * body and
                lower_shadow <= 0.5 * body
            )

            self.logger.debug(
                f"Shooting Star check for {symbol} ({timeframe}): "
                f"body_ratio={body_ratio:.3f}, upper_shadow={upper_shadow:.6f}, "
                f"lower_shadow={lower_shadow:.6f}, is_shooting_star={is_shooting_star}"
            )
            return bool(is_shooting_star)  # Convert to Python bool

        except Exception as e:
            self.logger.error(f"Error checking Shooting Star for {symbol} ({timeframe}): {str(e)}")
            return False

    def doji_standard(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Standard Doji candlestick pattern in the latest kline for the given symbol and timeframe.
        A Standard Doji has a very small body (open and close nearly equal).

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Standard Doji pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe):
                return False

            latest = klines.iloc[-1]
            open_price, close_price = latest['open'], latest['close']
            high, low = latest['high'], latest['low']

            # Calculate body and range
            body = abs(close_price - open_price)
            range_price = high - low

            # Standard Doji criterion: body <= 5% of range
            body_ratio = body / range_price if range_price > 0 else 0
            is_doji = range_price > 0 and body_ratio <= 0.05

            self.logger.debug(
                f"Standard Doji check for {symbol} ({timeframe}): "
                f"body_ratio={body_ratio:.3f}, is_doji={is_doji}"
            )
            return bool(is_doji)  # Convert to Python bool

        except Exception as e:
            self.logger.error(f"Error checking Standard Doji for {symbol} ({timeframe}): {str(e)}")
            return False

    def doji_long_legged(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Long-Legged Doji candlestick pattern in the latest kline for the given symbol and timeframe.
        A Long-Legged Doji has a very small body and long upper and lower shadows.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Long-Legged Doji pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe):
                return False

            latest = klines.iloc[-1]
            open_price, close_price = latest['open'], latest['close']
            high, low = latest['high'], latest['low']

            # Calculate body and shadows
            body = abs(close_price - open_price)
            upper_shadow = high - max(open_price, close_price)
            lower_shadow = min(open_price, close_price) - low
            range_price = high - low

            # Long-Legged Doji criteria:
            # - Body <= 5% of range
            # - Upper and lower shadows each >= 30% of range
            body_ratio = body / range_price if range_price > 0 else 0
            upper_shadow_ratio = upper_shadow / range_price if range_price > 0 else 0
            lower_shadow_ratio = lower_shadow / range_price if range_price > 0 else 0
            is_long_legged_doji = (
                range_price > 0 and
                body_ratio <= 0.05 and
                upper_shadow_ratio >= 0.3 and
                lower_shadow_ratio >= 0.3
            )

            self.logger.debug(
                f"Long-Legged Doji check for {symbol} ({timeframe}): "
                f"body_ratio={body_ratio:.3f}, upper_shadow_ratio={upper_shadow_ratio:.3f}, "
                f"lower_shadow_ratio={lower_shadow_ratio:.3f}, is_long_legged_doji={is_long_legged_doji}"
            )
            return bool(is_long_legged_doji)  # Convert to Python bool

        except Exception as e:
            self.logger.error(f"Error checking Long-Legged Doji for {symbol} ({timeframe}): {str(e)}")
            return False

    def doji_gravestone(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Gravestone Doji candlestick pattern in the latest kline for the given symbol and timeframe.
        A Gravestone Doji has a very small body, a long upper shadow, and no lower shadow.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Gravestone Doji pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe):
                return False

            latest = klines.iloc[-1]
            open_price, close_price = latest['open'], latest['close']
            high, low = latest['high'], latest['low']

            # Calculate body and shadows
            body = abs(close_price - open_price)
            upper_shadow = high - max(open_price, close_price)
            lower_shadow = min(open_price, close_price) - low
            range_price = high - low

            # Gravestone Doji criteria:
            # - Body <= 5% of range
            # - Upper shadow >= 70% of range
            # - Lower shadow <= 5% of range
            body_ratio = body / range_price if range_price > 0 else 0
            upper_shadow_ratio = upper_shadow / range_price if range_price > 0 else 0
            lower_shadow_ratio = lower_shadow / range_price if range_price > 0 else 0
            is_gravestone_doji = (
                range_price > 0 and
                body_ratio <= 0.05 and
                upper_shadow_ratio >= 0.7 and
                lower_shadow_ratio <= 0.05
            )

            self.logger.debug(
                f"Gravestone Doji check for {symbol} ({timeframe}): "
                f"body_ratio={body_ratio:.3f}, upper_shadow_ratio={upper_shadow_ratio:.3f}, "
                f"lower_shadow_ratio={lower_shadow_ratio:.3f}, is_gravestone_doji={is_gravestone_doji}"
            )
            return bool(is_gravestone_doji)  # Convert to Python bool

        except Exception as e:
            self.logger.error(f"Error checking Gravestone Doji for {symbol} ({timeframe}): {str(e)}")
            return False

    def doji_dragonfly(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Dragonfly Doji candlestick pattern in the latest kline for the given symbol and timeframe.
        A Dragonfly Doji has a very small body, a long lower shadow, and no upper shadow.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Dragonfly Doji pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe):
                return False

            latest = klines.iloc[-1]
            open_price, close_price = latest['open'], latest['close']
            high, low = latest['high'], latest['low']

            # Calculate body and shadows
            body = abs(close_price - open_price)
            upper_shadow = high - max(open_price, close_price)
            lower_shadow = min(open_price, close_price) - low
            range_price = high - low

            # Dragonfly Doji criteria:
            # - Body <= 5% of range
            # - Lower shadow >= 70% of range
            # - Upper shadow <= 5% of range
            body_ratio = body / range_price if range_price > 0 else 0
            lower_shadow_ratio = lower_shadow / range_price if range_price > 0 else 0
            upper_shadow_ratio = upper_shadow / range_price if range_price > 0 else 0
            is_dragonfly_doji = (
                range_price > 0 and
                body_ratio <= 0.05 and
                lower_shadow_ratio >= 0.7 and
                upper_shadow_ratio <= 0.05
            )

            self.logger.debug(
                f"Dragonfly Doji check for {symbol} ({timeframe}): "
                f"body_ratio={body_ratio:.3f}, lower_shadow_ratio={lower_shadow_ratio:.3f}, "
                f"upper_shadow_ratio={upper_shadow_ratio:.3f}, is_dragonfly_doji={is_dragonfly_doji}"
            )
            return bool(is_dragonfly_doji)  # Convert to Python bool

        except Exception as e:
            self.logger.error(f"Error checking Dragonfly Doji for {symbol} ({timeframe}): {str(e)}")
            return False

    def doji_four_price(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Four Price Doji candlestick pattern in the latest kline for the given symbol and timeframe.
        A Four Price Doji has open, close, high, and low all equal (or nearly equal).

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Four Price Doji pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe):
                return False

            latest = klines.iloc[-1]
            open_price, close_price = latest['open'], latest['close']
            high, low = latest['high'], latest['low']

            # Four Price Doji criterion: open, close, high, low are equal (within tolerance)
            tolerance = 0.0001  # Small tolerance for HBAR-USD price precision
            is_four_price_doji = (
                abs(open_price - close_price) <= tolerance and
                abs(high - low) <= tolerance and
                abs(open_price - high) <= tolerance
            )

            self.logger.debug(
                f"Four Price Doji check for {symbol} ({timeframe}): "
                f"open={open_price:.6f}, close={close_price:.6f}, high={high:.6f}, low={low:.6f}, "
                f"is_four_price_doji={is_four_price_doji}"
            )
            return bool(is_four_price_doji)  # Convert to Python bool

        except Exception as e:
            self.logger.error(f"Error checking Four Price Doji for {symbol} ({timeframe}): {str(e)}")
            return False

    def engulfing_bullish(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Bullish Engulfing candlestick pattern in the latest two klines for the given symbol and timeframe.
        A Bullish Engulfing has a small bearish candle followed by a larger bullish candle that engulfs the previous body.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Bullish Engulfing pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=2):
                return False

            prev = klines.iloc[-2]
            curr = klines.iloc[-1]

            # Bullish Engulfing criteria:
            # - First candle bearish
            # - Second candle bullish, engulfing the first candle's body
            is_bullish_engulfing = (
                prev['close'] < prev['open'] and
                curr['close'] > curr['open'] and
                curr['open'] <= prev['close'] and
                curr['close'] >= prev['open']
            )

            self.logger.debug(
                f"Bullish Engulfing check for {symbol} ({timeframe}): "
                f"prev_open={prev['open']:.6f}, prev_close={prev['close']:.6f}, "
                f"curr_open={curr['open']:.6f}, curr_close={curr['close']:.6f}, "
                f"is_bullish_engulfing={is_bullish_engulfing}"
            )
            return bool(is_bullish_engulfing)  # Convert to Python bool

        except Exception as e:
            self.logger.error(f"Error checking Bullish Engulfing for {symbol} ({timeframe}): {str(e)}")
            return False

    def engulfing_bearish(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Bearish Engulfing candlestick pattern in the latest two klines for the given symbol and timeframe.
        A Bearish Engulfing has a small bullish candle followed by a larger bearish candle that engulfs the previous body.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Bearish Engulfing pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=2):
                return False

            prev = klines.iloc[-2]
            curr = klines.iloc[-1]

            # Bearish Engulfing criteria:
            # - First candle bullish
            # - Second candle bearish, engulfing the first candle's body
            is_bearish_engulfing = (
                prev['close'] > prev['open'] and
                curr['close'] < curr['open'] and
                curr['open'] >= prev['close'] and
                curr['close'] <= prev['open']
            )

            self.logger.debug(
                f"Bearish Engulfing check for {symbol} ({timeframe}): "
                f"prev_open={prev['open']:.6f}, prev_close={prev['close']:.6f}, "
                f"curr_open={curr['open']:.6f}, curr_close={curr['close']:.6f}, "
                f"is_bearish_engulfing={is_bearish_engulfing}"
            )
            return bool(is_bearish_engulfing)  # Convert to Python bool

        except Exception as e:
            self.logger.error(f"Error checking Bearish Engulfing for {symbol} ({timeframe}): {str(e)}")
            return False

    def harami_bullish(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Bullish Harami candlestick pattern in the latest two klines for the given symbol and timeframe.
        A Bullish Harami has a large bearish candle followed by a smaller bullish candle contained within the previous body.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Bullish Harami pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=2):
                return False

            prev = klines.iloc[-2]
            curr = klines.iloc[-1]

            # Bullish Harami criteria:
            # - First candle bearish
            # - Second candle bullish, contained within the first candle's body
            is_bullish_harami = (
                prev['close'] < prev['open'] and
                curr['close'] > curr['open'] and
                curr['open'] >= prev['close'] and
                curr['close'] <= prev['open']
            )

            self.logger.debug(
                f"Bullish Harami check for {symbol} ({timeframe}): "
                f"prev_open={prev['open']:.6f}, prev_close={prev['close']:.6f}, "
                f"curr_open={curr['open']:.6f}, curr_close={curr['close']:.6f}, "
                f"is_bullish_harami={is_bullish_harami}"
            )
            return bool(is_bullish_harami)  # Convert to Python bool

        except Exception as e:
            self.logger.error(f"Error checking Bullish Harami for {symbol} ({timeframe}): {str(e)}")
            return False

    def harami_bearish(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Bearish Harami candlestick pattern in the latest two klines for the given symbol and timeframe.
        A Bearish Harami has a large bullish candle followed by a smaller bearish candle contained within the previous body.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Bearish Harami pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=2):
                return False

            prev = klines.iloc[-2]
            curr = klines.iloc[-1]

            # Bearish Harami criteria:
            # - First candle bullish
            # - Second candle bearish, contained within the first candle's body
            is_bearish_harami = (
                prev['close'] > prev['open'] and
                curr['close'] < curr['open'] and
                curr['open'] <= prev['close'] and
                curr['close'] >= prev['open']
            )

            self.logger.debug(
                f"Bearish Harami check for {symbol} ({timeframe}): "
                f"prev_open={prev['open']:.6f}, prev_close={prev['close']:.6f}, "
                f"curr_open={curr['open']:.6f}, curr_close={curr['close']:.6f}, "
                f"is_bearish_harami={is_bearish_harami}"
            )
            return bool(is_bearish_harami)  # Convert to Python bool

        except Exception as e:
            self.logger.error(f"Error checking Bearish Harami for {symbol} ({timeframe}): {str(e)}")
            return False

    def harami_cross_bullish(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Bullish Harami Cross candlestick pattern in the latest two klines for the given symbol and timeframe.
        A Bullish Harami Cross has a large bearish candle followed by a Doji contained within the previous body.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Bullish Harami Cross pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=2):
                return False

            prev = klines.iloc[-2]
            curr = klines.iloc[-1]

            # Bullish Harami Cross criteria:
            # - First candle bearish
            # - Second candle is a Doji, contained within the first candle's body
            body_curr = abs(curr['close'] - curr['open'])
            range_curr = curr['high'] - curr['low']
            body_ratio_curr = body_curr / range_curr if range_curr > 0 else 0
            is_doji = range_curr > 0 and body_ratio_curr <= 0.05
            is_bullish_harami_cross = (
                prev['close'] < prev['open'] and
                is_doji and
                curr['open'] >= prev['close'] and
                curr['close'] <= prev['open']
            )

            self.logger.debug(
                f"Bullish Harami Cross check for {symbol} ({timeframe}): "
                f"prev_open={prev['open']:.6f}, prev_close={prev['close']:.6f}, "
                f"curr_open={curr['open']:.6f}, curr_close={curr['close']:.6f}, "
                f"body_ratio_curr={body_ratio_curr:.3f}, is_bullish_harami_cross={is_bullish_harami_cross}"
            )
            return bool(is_bullish_harami_cross)  # Convert to Python bool

        except Exception as e:
            self.logger.error(f"Error checking Bullish Harami Cross for {symbol} ({timeframe}): {str(e)}")
            return False

    def harami_cross_bearish(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Bearish Harami Cross candlestick pattern in the latest two klines for the given symbol and timeframe.
        A Bearish Harami Cross has a large bullish candle followed by a Doji contained within the previous body.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Bearish Harami Cross pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=2):
                return False

            prev = klines.iloc[-2]
            curr = klines.iloc[-1]

            # Bearish Harami Cross criteria:
            # - First candle bullish
            # - Second candle is a Doji, contained within the first candle's body
            body_curr = abs(curr['close'] - curr['open'])
            range_curr = curr['high'] - curr['low']
            body_ratio_curr = body_curr / range_curr if range_curr > 0 else 0
            is_doji = range_curr > 0 and body_ratio_curr <= 0.05
            is_bearish_harami_cross = (
                prev['close'] > prev['open'] and
                is_doji and
                curr['open'] <= prev['close'] and
                curr['close'] >= prev['open']
            )

            self.logger.debug(
                f"Bearish Harami Cross check for {symbol} ({timeframe}): "
                f"prev_open={prev['open']:.6f}, prev_close={prev['close']:.6f}, "
                f"curr_open={curr['open']:.6f}, curr_close={curr['close']:.6f}, "
                f"body_ratio_curr={body_ratio_curr:.3f}, is_bearish_harami_cross={is_bearish_harami_cross}"
            )
            return bool(is_bearish_harami_cross)  # Convert to Python bool

        except Exception as e:
            self.logger.error(f"Error checking Bearish Harami Cross for {symbol} ({timeframe}): {str(e)}")
            return False

    def tweezer_tops(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Tweezer Tops candlestick pattern in the latest two klines for the given symbol and timeframe.
        Tweezer Tops has a bullish candle followed by a bearish candle with similar highs.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Tweezer Tops pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=2):
                return False

            prev = klines.iloc[-2]
            curr = klines.iloc[-1]

            # Tweezer Tops criteria:
            # - First candle bullish
            # - Second candle bearish
            # - Highs nearly equal
            tolerance = 0.0001  # Tolerance for HBAR-USD price precision
            is_tweezer_tops = (
                prev['close'] > prev['open'] and
                curr['close'] < curr['open'] and
                abs(curr['high'] - prev['high']) <= tolerance
            )

            self.logger.debug(
                f"Tweezer Tops check for {symbol} ({timeframe}): "
                f"prev_high={prev['high']:.6f}, curr_high={curr['high']:.6f}, "
                f"is_tweezer_tops={is_tweezer_tops}"
            )
            return bool(is_tweezer_tops)  # Convert to Python bool

        except Exception as e:
            self.logger.error(f"Error checking Tweezer Tops for {symbol} ({timeframe}): {str(e)}")
            return False

    def tweezer_bottoms(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Tweezer Bottoms candlestick pattern in the latest two klines for the given symbol and timeframe.
        Tweezer Bottoms has a bearish candle followed by a bullish candle with similar lows.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Tweezer Bottoms pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=2):
                return False

            prev = klines.iloc[-2]
            curr = klines.iloc[-1]

            # Tweezer Bottoms criteria:
            # - First candle bearish
            # - Second candle bullish
            # - Lows nearly equal
            tolerance = 0.0001  # Tolerance for HBAR-USD price precision
            is_tweezer_bottoms = (
                prev['close'] < prev['open'] and
                curr['close'] > curr['open'] and
                abs(curr['low'] - prev['low']) <= tolerance
            )

            self.logger.debug(
                f"Tweezer Bottoms check for {symbol} ({timeframe}): "
                f"prev_low={prev['low']:.6f}, curr_low={curr['low']:.6f}, "
                f"is_tweezer_bottoms={is_tweezer_bottoms}"
            )
            return bool(is_tweezer_bottoms)  # Convert to Python bool

        except Exception as e:
            self.logger.error(f"Error checking Tweezer Bottoms for {symbol} ({timeframe}): {str(e)}")
            return False

    def dark_cloud_cover(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Dark Cloud Cover candlestick pattern in the latest two klines for the given symbol and timeframe.
        Dark Cloud Cover has a bullish candle followed by a bearish candle that opens above the previous high and closes below the previous midpoint.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Dark Cloud Cover pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=2):
                return False

            prev = klines.iloc[-2]
            curr = klines.iloc[-1]

            # Dark Cloud Cover criteria:
            # - First candle bullish
            # - Second candle bearish, opens above prev high, closes below prev midpoint
            prev_midpoint = (prev['open'] + prev['close']) / 2
            is_dark_cloud_cover = (
                prev['close'] > prev['open'] and
                curr['close'] < curr['open'] and
                curr['open'] > prev['high'] and
                curr['close'] < prev_midpoint
            )

            self.logger.debug(
                f"Dark Cloud Cover check for {symbol} ({timeframe}): "
                f"prev_high={prev['high']:.6f}, prev_midpoint={prev_midpoint:.6f}, "
                f"curr_open={curr['open']:.6f}, curr_close={curr['close']:.6f}, "
                f"is_dark_cloud_cover={is_dark_cloud_cover}"
            )
            return bool(is_dark_cloud_cover)  # Convert to Python bool

        except Exception as e:
            self.logger.error(f"Error checking Dark Cloud Cover for {symbol} ({timeframe}): {str(e)}")
            return False
        
    def piercing_line(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Piercing Line candlestick pattern in the latest two klines for the given symbol and timeframe.
        Piercing Line has a bearish candle followed by a bullish candle that opens below the previous low and closes above the previous midpoint.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Piercing Line pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=2):
                return False

            prev = klines.iloc[-2]
            curr = klines.iloc[-1]

            # Piercing Line criteria:
            # - First candle bearish
            # - Second candle bullish, opens below prev low, closes above prev midpoint
            prev_midpoint = (prev['open'] + prev['close']) / 2
            is_piercing_line = (
                prev['close'] < prev['open'] and
                curr['close'] > curr['open'] and
                curr['open'] < prev['low'] and
                curr['close'] > prev_midpoint
            )

            self.logger.debug(
                f"Piercing Line check for {symbol} ({timeframe}): "
                f"prev_low={prev['low']:.6f}, prev_midpoint={prev_midpoint:.6f}, "
                f"curr_open={curr['open']:.6f}, curr_close={curr['close']:.6f}, "
                f"is_piercing_line={is_piercing_line}"
            )
            return bool(is_piercing_line)  # Convert to Python bool

        except Exception as e:
            self.logger.error(f"Error checking Piercing Line for {symbol} ({timeframe}): {str(e)}")
            return False

    def on_neck(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies an On Neck candlestick pattern in the latest two klines for the given symbol and timeframe.
        On Neck has a bearish candle followed by a bullish candle that opens below the previous low and closes at or near the previous close.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if an On Neck pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=2):
                return False

            prev = klines.iloc[-2]
            curr = klines.iloc[-1]

            # On Neck criteria:
            # - First candle bearish
            # - Second candle bullish, opens below prev low, closes at or near prev close
            tolerance = 0.0001  # Tolerance for HBAR-USD price precision
            is_on_neck = (
                prev['close'] < prev['open'] and
                curr['close'] > curr['open'] and
                curr['open'] < prev['low'] and
                abs(curr['close'] - prev['close']) <= tolerance
            )

            self.logger.debug(
                f"On Neck check for {symbol} ({timeframe}): "
                f"prev_low={prev['low']:.6f}, prev_close={prev['close']:.6f}, "
                f"curr_open={curr['open']:.6f}, curr_close={curr['close']:.6f}, "
                f"is_on_neck={is_on_neck}"
            )
            return bool(is_on_neck)  # Convert to Python bool

        except Exception as e:
            self.logger.error(f"Error checking On Neck for {symbol} ({timeframe}): {str(e)}")
            return False

    
    def morning_star(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Morning Star candlestick pattern in the latest three klines for the given symbol and timeframe.
        A Morning Star has a long bearish candle, a short-bodied candle, and a long bullish candle closing above the first candle's midpoint.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Morning Star pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=3):
                return False

            first = klines.iloc[-3]
            second = klines.iloc[-2]
            third = klines.iloc[-1]

            # Morning Star criteria:
            # - First candle bearish
            # - Second candle small body
            # - Third candle bullish, closes above first candle's midpoint
            first_midpoint = (first['open'] + first['close']) / 2
            second_body = abs(second['close'] - second['open'])
            second_range = second['high'] - second['low']
            second_body_ratio = second_body / second_range if second_range > 0 else 0
            is_morning_star = (
                first['close'] < first['open'] and
                (second_range == 0 or second_body_ratio <= 0.3) and
                third['close'] > third['open'] and
                third['close'] > first_midpoint
            )

            self.logger.debug(
                f"Morning Star check for {symbol} ({timeframe}): "
                f"first_open={first['open']:.6f}, first_close={first['close']:.6f}, "
                f"second_body_ratio={second_body_ratio:.3f}, "
                f"third_close={third['close']:.6f}, first_midpoint={first_midpoint:.6f}, "
                f"is_morning_star={is_morning_star}"
            )
            return bool(is_morning_star)

        except Exception as e:
            self.logger.error(f"Error checking Morning Star for {symbol} ({timeframe}): {str(e)}")
            return False

    def evening_star(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies an Evening Star candlestick pattern in the latest three klines for the given symbol and timeframe.
        An Evening Star has a long bullish candle, a short-bodied candle, and a long bearish candle closing below the first candle's midpoint.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if an Evening Star pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=3):
                return False

            first = klines.iloc[-3]
            second = klines.iloc[-2]
            third = klines.iloc[-1]

            # Evening Star criteria:
            # - First candle bullish
            # - Second candle small body
            # - Third candle bearish, closes below first candle's midpoint
            first_midpoint = (first['open'] + first['close']) / 2
            second_body = abs(second['close'] - second['open'])
            second_range = second['high'] - second['low']
            second_body_ratio = second_body / second_range if second_range > 0 else 0
            is_evening_star = (
                first['close'] > first['open'] and
                (second_range == 0 or second_body_ratio <= 0.3) and
                third['close'] < third['open'] and
                third['close'] < first_midpoint
            )

            self.logger.debug(
                f"Evening Star check for {symbol} ({timeframe}): "
                f"first_open={first['open']:.6f}, first_close={first['close']:.6f}, "
                f"second_body_ratio={second_body_ratio:.3f}, "
                f"third_close={third['close']:.6f}, first_midpoint={first_midpoint:.6f}, "
                f"is_evening_star={is_evening_star}"
            )
            return bool(is_evening_star)

        except Exception as e:
            self.logger.error(f"Error checking Evening Star for {symbol} ({timeframe}): {str(e)}")
            return False

    def three_white_soldiers(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Three White Soldiers candlestick pattern in the latest three klines for the given symbol and timeframe.
        Three White Soldiers has three long bullish candles, each closing higher than the previous.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Three White Soldiers pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=3):
                return False

            first = klines.iloc[-3]
            second = klines.iloc[-2]
            third = klines.iloc[-1]

            # Three White Soldiers criteria:
            # - All three candles bullish
            # - Each closes higher than the previous
            # - Each has a significant body (>= 60% of range)
            first_body = first['close'] - first['open']
            first_range = first['high'] - first['low']
            first_body_ratio = first_body / first_range if first_range > 0 else 0
            second_body = second['close'] - second['open']
            second_range = second['high'] - second['low']
            second_body_ratio = second_body / second_range if second_range > 0 else 0
            third_body = third['close'] - third['open']
            third_range = third['high'] - third['low']
            third_body_ratio = third_body / third_range if third_range > 0 else 0
            is_three_white_soldiers = (
                first['close'] > first['open'] and
                second['close'] > second['open'] and
                third['close'] > third['open'] and
                second['close'] > first['close'] and
                third['close'] > second['close'] and
                first_body_ratio >= 0.6 and
                second_body_ratio >= 0.6 and
                third_body_ratio >= 0.6
            )

            self.logger.debug(
                f"Three White Soldiers check for {symbol} ({timeframe}): "
                f"first_body_ratio={first_body_ratio:.3f}, second_body_ratio={second_body_ratio:.3f}, "
                f"third_body_ratio={third_body_ratio:.3f}, is_three_white_soldiers={is_three_white_soldiers}"
            )
            return bool(is_three_white_soldiers)

        except Exception as e:
            self.logger.error(f"Error checking Three White Soldiers for {symbol} ({timeframe}): {str(e)}")
            return False

    def three_black_crows(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Three Black Crows candlestick pattern in the latest three klines for the given symbol and timeframe.
        Three Black Crows has three long bearish candles, each closing lower than the previous.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Three Black Crows pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=3):
                return False

            first = klines.iloc[-3]
            second = klines.iloc[-2]
            third = klines.iloc[-1]

            # Three Black Crows criteria:
            # - All three candles bearish
            # - Each closes lower than the previous
            # - Each has a significant body (>= 60% of range)
            first_body = first['open'] - first['close']
            first_range = first['high'] - first['low']
            first_body_ratio = first_body / first_range if first_range > 0 else 0
            second_body = second['open'] - second['close']
            second_range = second['high'] - second['low']
            second_body_ratio = second_body / second_range if second_range > 0 else 0
            third_body = third['open'] - third['close']
            third_range = third['high'] - third['low']
            third_body_ratio = third_body / third_range if third_range > 0 else 0
            is_three_black_crows = (
                first['close'] < first['open'] and
                second['close'] < second['open'] and
                third['close'] < third['open'] and
                second['close'] < first['close'] and
                third['close'] < second['close'] and
                first_body_ratio >= 0.6 and
                second_body_ratio >= 0.6 and
                third_body_ratio >= 0.6
            )

            self.logger.debug(
                f"Three Black Crows check for {symbol} ({timeframe}): "
                f"first_body_ratio={first_body_ratio:.3f}, second_body_ratio={second_body_ratio:.3f}, "
                f"third_body_ratio={third_body_ratio:.3f}, is_three_black_crows={is_three_black_crows}"
            )
            return bool(is_three_black_crows)

        except Exception as e:
            self.logger.error(f"Error checking Three Black Crows for {symbol} ({timeframe}): {str(e)}")
            return False

    def three_inside_up(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Three Inside Up candlestick pattern in the latest three klines for the given symbol and timeframe.
        Three Inside Up has a bearish candle, a Bullish Harami, and a third bullish candle closing above the second's high.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Three Inside Up pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=3):
                return False

            first = klines.iloc[-3]
            second = klines.iloc[-2]
            third = klines.iloc[-1]

            # Three Inside Up criteria:
            # - First candle bearish
            # - Second candle bullish, within first body (Bullish Harami)
            # - Third candle bullish, closes above second close
            is_three_inside_up = (
                first['close'] < first['open'] and
                second['close'] > second['open'] and
                second['open'] >= first['close'] and
                second['close'] <= first['open'] and
                third['close'] > third['open'] and
                third['close'] > second['close']
            )

            self.logger.debug(
                f"Three Inside Up check for {symbol} ({timeframe}): "
                f"first_open={first['open']:.6f}, first_close={first['close']:.6f}, "
                f"second_open={second['open']:.6f}, second_close={second['close']:.6f}, "
                f"third_close={third['close']:.6f}, is_three_inside_up={is_three_inside_up}"
            )
            return bool(is_three_inside_up)

        except Exception as e:
            self.logger.error(f"Error checking Three Inside Up for {symbol} ({timeframe}): {str(e)}")
            return False

    def three_inside_down(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Three Inside Down candlestick pattern in the latest three klines for the given symbol and timeframe.
        Three Inside Down has a bullish candle, a Bearish Harami, and a third bearish candle closing below the second's low.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Three Inside Down pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=3):
                return False

            first = klines.iloc[-3]
            second = klines.iloc[-2]
            third = klines.iloc[-1]

            # Three Inside Down criteria:
            # - First candle bullish
            # - Second candle bearish, within first body (Bearish Harami)
            # - Third candle bearish, closes below second close
            is_three_inside_down = (
                first['close'] > first['open'] and
                second['close'] < second['open'] and
                second['open'] <= first['close'] and
                second['close'] >= first['open'] and
                third['close'] < third['open'] and
                third['close'] < second['close']
            )

            self.logger.debug(
                f"Three Inside Down check for {symbol} ({timeframe}): "
                f"first_open={first['open']:.6f}, first_close={first['close']:.6f}, "
                f"second_open={second['open']:.6f}, second_close={second['close']:.6f}, "
                f"third_close={third['close']:.6f}, is_three_inside_down={is_three_inside_down}"
            )
            return bool(is_three_inside_down)

        except Exception as e:
            self.logger.error(f"Error checking Three Inside Down for {symbol} ({timeframe}): {str(e)}")
            return False

    def stick_sandwich_bullish(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Bullish Stick Sandwich candlestick pattern in the latest three klines for the given symbol and timeframe.
        A Bullish Stick Sandwich has a bearish candle, a bullish candle, and another bearish candle with a close near the first's close.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Bullish Stick Sandwich pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=3):
                return False

            first = klines.iloc[-3]
            second = klines.iloc[-2]
            third = klines.iloc[-1]

            # Bullish Stick Sandwich criteria:
            # - First candle bearish
            # - Second candle bullish, closes above first close
            # - Third candle bearish, closes near first close
            tolerance = 0.0001  # Tolerance for HBAR-USD price precision
            is_stick_sandwich_bullish = (
                first['close'] < first['open'] and
                second['close'] > second['open'] and
                second['close'] > first['close'] and
                third['close'] < third['open'] and
                abs(third['close'] - first['close']) <= tolerance
            )

            self.logger.debug(
                f"Bullish Stick Sandwich check for {symbol} ({timeframe}): "
                f"first_close={first['close']:.6f}, second_close={second['close']:.6f}, "
                f"third_close={third['close']:.6f}, is_stick_sandwich_bullish={is_stick_sandwich_bullish}"
            )
            return bool(is_stick_sandwich_bullish)

        except Exception as e:
            self.logger.error(f"Error checking Bullish Stick Sandwich for {symbol} ({timeframe}): {str(e)}")
            return False

    def stick_sandwich_bearish(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Bearish Stick Sandwich candlestick pattern in the latest three klines for the given symbol and timeframe.
        A Bearish Stick Sandwich has a bullish candle, a bearish candle, and another bullish candle with a close near the first's close.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Bearish Stick Sandwich pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=3):
                return False

            first = klines.iloc[-3]
            second = klines.iloc[-2]
            third = klines.iloc[-1]

            # Bearish Stick Sandwich criteria:
            # - First candle bullish
            # - Second candle bearish, closes below first close
            # - Third candle bullish, closes near first close
            tolerance = 0.0001  # Tolerance for HBAR-USD price precision
            is_stick_sandwich_bearish = (
                first['close'] > first['open'] and
                second['close'] < second['open'] and
                second['close'] < first['close'] and
                third['close'] > third['open'] and
                abs(third['close'] - first['close']) <= tolerance
            )

            self.logger.debug(
                f"Bearish Stick Sandwich check for {symbol} ({timeframe}): "
                f"first_close={first['close']:.6f}, second_close={second['close']:.6f}, "
                f"third_close={third['close']:.6f}, is_stick_sandwich_bearish={is_stick_sandwich_bearish}"
            )
            return bool(is_stick_sandwich_bearish)

        except Exception as e:
            self.logger.error(f"Error checking Bearish Stick Sandwich for {symbol} ({timeframe}): {str(e)}")
            return False

    def rising_three_methods(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Rising Three Methods candlestick pattern in the latest three klines for the given symbol and timeframe.
        Rising Three Methods has a long bullish candle, a small bearish candle within the first body, and a bullish candle closing above the first close.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Rising Three Methods pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=3):
                return False

            first = klines.iloc[-3]
            second = klines.iloc[-2]
            third = klines.iloc[-1]

            # Rising Three Methods criteria (simplified to three candles):
            # - First candle bullish
            # - Second candle bearish, within first body
            # - Third candle bullish, closes above first close
            is_rising_three_methods = (
                first['close'] > first['open'] and
                second['close'] < second['open'] and
                second['open'] <= first['close'] and
                second['close'] >= first['open'] and
                third['close'] > third['open'] and
                third['close'] > first['close']
            )

            self.logger.debug(
                f"Rising Three Methods check for {symbol} ({timeframe}): "
                f"first_open={first['open']:.6f}, first_close={first['close']:.6f}, "
                f"second_open={second['open']:.6f}, second_close={second['close']:.6f}, "
                f"third_close={third['close']:.6f}, is_rising_three_methods={is_rising_three_methods}"
            )
            return bool(is_rising_three_methods)

        except Exception as e:
            self.logger.error(f"Error checking Rising Three Methods for {symbol} ({timeframe}): {str(e)}")
            return False

    def falling_three_methods(self, symbol: str, timeframe: str) -> bool:
        """
        Identifies a Falling Three Methods candlestick pattern in the latest three klines for the given symbol and timeframe.
        Falling Three Methods has a long bearish candle, a small bullish candle within the first body, and a bearish candle closing below the first close.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe (e.g., '1m', '5m', '15m', '1h', '6h', '1d').

        Returns:
            bool: True if a Falling Three Methods pattern is present, False otherwise.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return False
            if timeframe not in self.timeframes:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return False

            klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
            if not self._validate_klines(klines, symbol, timeframe, min_rows=3):
                return False

            first = klines.iloc[-3]
            second = klines.iloc[-2]
            third = klines.iloc[-1]

            # Falling Three Methods criteria (simplified to three candles):
            # - First candle bearish
            # - Second candle bullish, within first body
            # - Third candle bearish, closes below first close
            is_falling_three_methods = (
                first['close'] < first['open'] and
                second['close'] > second['open'] and
                second['open'] >= first['close'] and
                second['close'] <= first['open'] and
                third['close'] < third['open'] and
                third['close'] < first['close']
            )

            self.logger.debug(
                f"Falling Three Methods check for {symbol} ({timeframe}): "
                f"first_open={first['open']:.6f}, first_close={first['close']:.6f}, "
                f"second_open={second['open']:.6f}, second_close={second['close']:.6f}, "
                f"third_close={third['close']:.6f}, is_falling_three_methods={is_falling_three_methods}"
            )
            return bool(is_falling_three_methods)

        except Exception as e:
            self.logger.error(f"Error checking Falling Three Methods for {symbol} ({timeframe}): {str(e)}")
            return False
    