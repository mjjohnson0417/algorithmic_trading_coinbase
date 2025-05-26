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

    def _validate_klines(self, klines: pd.DataFrame, symbol: str, timeframe: str) -> bool:
        """
        Validates kline data for required columns and sufficient rows.

        Args:
            klines (pd.DataFrame): Kline data with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume'].
            symbol (str): Trading pair symbol.
            timeframe (str): Timeframe (e.g., '1m', '5m').

        Returns:
            bool: True if valid, False otherwise.
        """
        required_columns = ['open', 'high', 'low', 'close']
        if klines.empty:
            self.logger.warning(f"Empty {timeframe} klines buffer for {symbol}")
            return False
        if len(klines) < 1:
            self.logger.warning(f"Insufficient {timeframe} klines data for {symbol}: {len(klines)} rows, need at least 1")
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
                        'doji_four_price': self.doji_four_price(symbol, timeframe)
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
                        'doji_four_price': False
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

    

    