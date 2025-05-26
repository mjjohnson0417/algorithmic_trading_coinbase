# indicator_calculator.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict

class IndicatorCalculator:
    def __init__(self, symbols: list, data_manager, enable_logging: bool = True):
        """
        Initializes the IndicatorCalculator class for computing indicators for multiple symbols.

        Args:
            symbols (list): List of trading pair symbols (e.g., ['HBAR-USDT', 'BTC-USDT']).
            data_manager: An instance of DataManager to fetch data.
            enable_logging (bool): If True, enables logging to 'logs/indicator_calculator.log'.
        """
        self.symbols = symbols
        self.data_manager = data_manager
        self.enable_logging = enable_logging

        # Set up logger
        self.logger = logging.getLogger('IndicatorCalculator')
        if enable_logging:
            log_dir = Path(__file__).parent / 'logs'
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / 'indicator_calculator.log'
            file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.WARNING)

        self.logger.debug("IndicatorCalculator initialized with symbols: %s", symbols)

    def calculate_all_indicators(self) -> Dict[str, Dict]:
        """
        Calculates 1-hour, 1-day, and timing indicators for all symbols.

        Returns:
            Dict[str, Dict]: Dictionary mapping each symbol to its indicators (1-hour, 1-day, timing).
        """
        if not self.data_manager:
            self.logger.error("DataManager not provided during IndicatorCalculator initialization.")
            return {}

        all_indicators = {}
        for symbol in self.symbols:
            self.logger.debug(f"Calculating indicators for {symbol}")

            # Get buffers from DataManager
            klines_1h = self.data_manager.get_buffer(symbol, 'klines_1h')
            klines_1d = self.data_manager.get_buffer(symbol, 'klines_1d')
            ticker = self.data_manager.get_buffer(symbol, 'ticker')
            order_book = self.data_manager.get_buffer(symbol, 'order_book')

            # Calculate indicators
            indicators = {
                '1h': self.calculate_1h_indicators(klines_1h, symbol),
                '1d': self.calculate_1d_indicators(klines_1d, symbol),
                'timing': self.calculate_timing_indicators(ticker, order_book, symbol)
            }

            all_indicators[symbol] = indicators
            self.logger.debug(f"Indicators for {symbol}: %s", indicators)

        return all_indicators

    def calculate_1h_indicators(self, klines_1h: pd.DataFrame, symbol: str) -> Dict:
        """
        Calculates 1-hour indicators from klines data.

        Args:
            klines_1h (pd.DataFrame): 1-hour klines data with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume'].
            symbol (str): Trading pair symbol.

        Returns:
            Dict: Dictionary of 1-hour indicators.
        """
        try:
            # Validate input data
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            if klines_1h.empty:
                self.logger.warning(f"Empty 1-hour klines buffer for {symbol}")
                return {}
            if len(klines_1h) < 26:
                self.logger.warning(f"Insufficient 1-hour klines data for {symbol}: {len(klines_1h)} rows, need at least 26")
                return {}
            if not all(col in klines_1h.columns for col in required_columns):
                missing_cols = [col for col in required_columns if col not in klines_1h.columns]
                self.logger.warning(f"Missing columns in 1-hour klines for {symbol}: {missing_cols}")
                return {}

            # Check for NaN values
            if klines_1h[required_columns].isna().any().any():
                self.logger.warning(f"NaN values detected in 1-hour klines for {symbol}: {klines_1h[required_columns].isna().sum().to_dict()}")
                klines_1h = klines_1h.dropna(subset=required_columns)
                if len(klines_1h) < 26:
                    self.logger.warning(f"After dropping NaN, insufficient rows for {symbol}: {len(klines_1h)}")
                    return {}

            # Log buffer details
            self.logger.debug(f"1-hour klines for {symbol}: rows={len(klines_1h)}, columns={list(klines_1h.columns)}")
            self.logger.debug(f"Sample klines data (last row): {klines_1h.tail(1).to_dict()}")
            self.logger.debug(f"Klines time range: {klines_1h['timestamp'].min()} to {klines_1h['timestamp'].max()}")

            # Calculate indicators
            indicators = {}

            # EMA12 and EMA26
            indicators['ema12'] = klines_1h['close'].ewm(span=12, adjust=False).mean().iloc[-1]
            indicators['ema26'] = klines_1h['close'].ewm(span=26, adjust=False).mean().iloc[-1]
            self.logger.debug(f"EMA for {symbol}: ema12={indicators['ema12']}, ema26={indicators['ema26']}")

            # RSI14
            indicators['rsi14'] = self._calculate_rsi(klines_1h['close'], 14)
            self.logger.debug(f"RSI14 for {symbol}: rsi14={indicators['rsi14']}")

            # ADX14
            indicators['adx14'] = self._calculate_adx(klines_1h, 14)
            self.logger.debug(f"ADX14 for {symbol}: adx14={indicators['adx14']}")

            # ATR14
            indicators['atr14'] = self._calculate_atr(klines_1h, 14)
            self.logger.debug(f"ATR14 for {symbol}: atr14={indicators['atr14']}")

            # MACD
            macd, macd_signal, macd_hist = self._calculate_macd(klines_1h['close'])
            indicators['macd'] = macd
            indicators['macd_signal'] = macd_signal
            indicators['macd_hist'] = macd_hist
            self.logger.debug(f"MACD for {symbol}: macd={macd}, macd_signal={macd_signal}, macd_hist={macd_hist}")

            self.logger.debug(f"1-hour indicators for {symbol}: {indicators}")
            return indicators

        except Exception as e:
            self.logger.error(f"Error calculating 1-hour indicators for {symbol}: {str(e)}")
            return {}

    def calculate_1d_indicators(self, klines_1d: pd.DataFrame, symbol: str) -> Dict:
        """
        Calculates 1-day indicators from klines data.

        Args:
            klines_1d (pd.DataFrame): 1-day klines data with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume'].
            symbol (str): Trading pair symbol.

        Returns:
            Dict: Dictionary of 1-day indicators.
        """
        try:
            # Validate input data
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            if klines_1d.empty:
                self.logger.warning(f"Empty 1-day klines buffer for {symbol}")
                return {}
            if len(klines_1d) < 26:
                self.logger.warning(f"Insufficient 1-day klines data for {symbol}: {len(klines_1d)} rows, need at least 26")
                return {}
            if not all(col in klines_1d.columns for col in required_columns):
                missing_cols = [col for col in required_columns if col not in klines_1d.columns]
                self.logger.warning(f"Missing columns in 1-day klines for {symbol}: {missing_cols}")
                return {}

            # Check for NaN values
            if klines_1d[required_columns].isna().any().any():
                self.logger.warning(f"NaN values detected in 1-day klines for {symbol}: {klines_1d[required_columns].isna().sum().to_dict()}")
                klines_1d = klines_1d.dropna(subset=required_columns)
                if len(klines_1d) < 26:
                    self.logger.warning(f"After dropping NaN, insufficient rows for {symbol}: {len(klines_1d)}")
                    return {}

            # Log buffer details
            self.logger.debug(f"1-day klines for {symbol}: rows={len(klines_1d)}, columns={list(klines_1d.columns)}")
            self.logger.debug(f"Sample klines data (last row): {klines_1d.tail(1).to_dict()}")
            self.logger.debug(f"Klines time range: {klines_1d['timestamp'].min()} to {klines_1d['timestamp'].max()}")

            # Calculate indicators
            indicators = {}

            # EMA12 and EMA26
            indicators['ema12'] = klines_1d['close'].ewm(span=12, adjust=False).mean().iloc[-1]
            indicators['ema26'] = klines_1d['close'].ewm(span=26, adjust=False).mean().iloc[-1]
            self.logger.debug(f"EMA for {symbol}: ema12={indicators['ema12']}, ema26={indicators['ema26']}")

            # RSI14
            indicators['rsi14'] = self._calculate_rsi(klines_1d['close'], 14)
            self.logger.debug(f"RSI14 for {symbol}: rsi14={indicators['rsi14']}")

            # ADX14
            indicators['adx14'] = self._calculate_adx(klines_1d, 14)
            self.logger.debug(f"ADX14 for {symbol}: adx14={indicators['adx14']}")

            # ATR14
            indicators['atr14'] = self._calculate_atr(klines_1d, 14)
            self.logger.debug(f"ATR14 for {symbol}: atr14={indicators['atr14']}")

            # MACD
            macd, macd_signal, macd_hist = self._calculate_macd(klines_1d['close'])
            indicators['macd'] = macd
            indicators['macd_signal'] = macd_signal
            indicators['macd_hist'] = macd_hist
            self.logger.debug(f"MACD for {symbol}: macd={macd}, macd_signal={macd_signal}, macd_hist={macd_hist}")

            self.logger.debug(f"1-day indicators for {symbol}: {indicators}")
            return indicators

        except Exception as e:
            self.logger.error(f"Error calculating 1-day indicators for {symbol}: {str(e)}")
            return {}

    def calculate_timing_indicators(self, ticker: pd.DataFrame, order_book: pd.DataFrame, symbol: str) -> Dict:
        """
        Calculates timing indicators from ticker and order book data.

        Args:
            ticker (pd.DataFrame): Ticker data buffer.
            order_book (pd.DataFrame): Order book data buffer.
            symbol (str): Trading pair symbol.

        Returns:
            Dict: Dictionary of timing indicators.
        """
        try:
            # Validate inputs
            if ticker.empty or len(ticker) < 14:
                self.logger.warning(f"Insufficient ticker data for {symbol}: {len(ticker)} rows")
                return {
                    'bid_ask_spread': 0.0,
                    'order_book_imbalance': 0.5,
                    'ema5': 0.0,
                    'atr14': 0.0001,
                    'volume_surge_ratio': 1.0
                }
            if order_book.empty:
                self.logger.warning(f"Empty order book data for {symbol}")
                return {
                    'bid_ask_spread': 0.0,
                    'order_book_imbalance': 0.5,
                    'ema5': 0.0,
                    'atr14': 0.0001,
                    'volume_surge_ratio': 1.0
                }

            indicators = {}

            # Bid-Ask Spread
            best_bid = ticker['best_bid'].iloc[-1] if not ticker.empty else 0.0
            best_ask = ticker['best_ask'].iloc[-1] if not ticker.empty else 0.0
            indicators['bid_ask_spread'] = (best_ask - best_bid) / best_ask if best_ask else 0.0
            self.logger.debug(f"Bid-Ask Spread for {symbol}: {indicators['bid_ask_spread']}")

            # Order Book Imbalance (using ticker data as proxy if order_book is empty)
            bid_volume = ticker['volume_24h'].iloc[-1] if not ticker.empty else 0.0
            ask_volume = ticker['volume_24h'].iloc[-1] if not ticker.empty else 0.0
            total_volume = bid_volume + ask_volume
            indicators['order_book_imbalance'] = (bid_volume - ask_volume) / total_volume if total_volume else 0.5
            self.logger.debug(f"Order Book Imbalance for {symbol}: {indicators['order_book_imbalance']}")

            # EMA5 of last price
            indicators['ema5'] = ticker['last_price'].ewm(span=5, adjust=False).mean().iloc[-1]
            self.logger.debug(f"EMA5 for {symbol}: {indicators['ema5']}")

            # ATR14 from ticker's last price
            price_diffs = abs(ticker['last_price'].diff()).dropna()
            indicators['atr14'] = price_diffs.rolling(window=14, min_periods=1).mean().iloc[-1] if not price_diffs.empty else 0.0001
            self.logger.debug(f"ATR14 (from ticker) for {symbol}: {indicators['atr14']}")

            # Volume Surge Ratio
            if 'volume_24h' in ticker.columns and len(ticker) >= 14:
                recent_volume = ticker['volume_24h'].iloc[-1]
                avg_volume = ticker['volume_24h'].rolling(window=14, min_periods=1).mean().iloc[-1]
                indicators['volume_surge_ratio'] = recent_volume / avg_volume if avg_volume else 1.0
            else:
                indicators['volume_surge_ratio'] = 1.0
            self.logger.debug(f"Volume Surge Ratio for {symbol}: {indicators['volume_surge_ratio']}")

            self.logger.debug(f"Timing indicators for {symbol}: {indicators}")
            return indicators

        except Exception as e:
            self.logger.error(f"Error calculating timing indicators for {symbol}: {str(e)}")
            return {
                'bid_ask_spread': 0.0,
                'order_book_imbalance': 0.5,
                'ema5': 0.0,
                'atr14': 0.0001,
                'volume_surge_ratio': 1.0
            }

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        try:
            if prices.empty or len(prices) < period:
                self.logger.debug(f"Insufficient price data for RSI: {len(prices)} rows, need {period}")
                return 50.0
            delta = prices.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.ewm(span=period, adjust=False, min_periods=period).mean()
            avg_loss = loss.ewm(span=period, adjust=False, min_periods=period).mean()
            rs = avg_gain / avg_loss if avg_loss.iloc[-1] != 0 else np.inf
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1] if not np.isnan(rsi.iloc[-1]) else 50.0
        except Exception as e:
            self.logger.error(f"Error calculating RSI: {str(e)}")
            return 50.0

    def _calculate_adx(self, klines: pd.DataFrame, period: int = 14) -> float:
        try:
            if klines.empty or len(klines) < (2 * period + 1):
                self.logger.debug(f"Insufficient klines data for ADX: {len(klines)} rows, need at least {2 * period + 1}")
                return 0.0
            high = klines['high']
            low = klines['low']
            close = klines['close']
            high_low = high - low
            high_prev_close = abs(high - close.shift(1))
            low_prev_close = abs(low - close.shift(1))
            tr = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(axis=1)
            plus_dm = high.diff().where(high.diff() > 0, 0)
            plus_dm = plus_dm.where(plus_dm > low.diff().abs(), 0)
            minus_dm = -low.diff().where(low.diff() < 0, 0)
            minus_dm = minus_dm.where(minus_dm > high.diff().abs(), 0)
            atr = tr.ewm(span=period, adjust=False, min_periods=period).mean()
            plus_di = (plus_dm.ewm(span=period, adjust=False, min_periods=period).mean() / atr) * 100
            minus_di = (minus_dm.ewm(span=period, adjust=False, min_periods=period).mean() / atr) * 100
            dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
            dx = dx.replace([np.inf, -np.inf], np.nan).fillna(0)
            adx = dx.ewm(span=period, adjust=False, min_periods=period).mean().iloc[-1]
            return adx if not np.isnan(adx) else 0.0
        except Exception as e:
            self.logger.error(f"Error calculating ADX: {str(e)}")
            return 0.0

    def _calculate_atr(self, klines: pd.DataFrame, period: int = 14) -> float:
        try:
            if klines.empty or len(klines) < period:
                self.logger.debug(f"Insufficient klines data for ATR: {len(klines)} rows, need {period}")
                return 0.0001
            high_low = klines['high'] - klines['low']
            high_close = abs(klines['high'] - klines['close'].shift(1))
            low_close = abs(klines['low'] - klines['close'].shift(1))
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=period, min_periods=1).mean().iloc[-1]
            return atr if not np.isnan(atr) else 0.0001
        except Exception as e:
            self.logger.error(f"Error calculating ATR: {str(e)}")
            return 0.0001

    def _calculate_macd(self, prices: pd.Series) -> tuple:
        try:
            if prices.empty:
                self.logger.debug("Empty price data for MACD")
                return 0.0, 0.0, 0.0
            ema12 = prices.ewm(span=12, adjust=False, min_periods=12).mean()
            ema26 = prices.ewm(span=26, adjust=False, min_periods=26).mean()
            macd = ema12 - ema26
            macd_signal = macd.ewm(span=9, adjust=False, min_periods=9).mean()
            macd_hist = macd - macd_signal
            return (
                macd.iloc[-1] if not np.isnan(macd.iloc[-1]) else 0.0,
                macd_signal.iloc[-1] if not np.isnan(macd_signal.iloc[-1]) else 0.0,
                macd_hist.iloc[-1] if not np.isnan(macd_hist.iloc[-1]) else 0.0
            )
        except Exception as e:
            self.logger.error(f"Error calculating MACD: {str(e)}")
            return 0.0, 0.0, 0.0