# indicator_calculator.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, Tuple, List, Any

class IndicatorCalculator:
    def __init__(self, symbols: list, data_manager, enable_logging: bool = True):
        """
        Initializes the IndicatorCalculator class for computing indicators for multiple symbols.

        Args:
            symbols: List of trading pair symbols (e.g., ['HBAR-USD']).
            data_manager: An instance of DataManager to fetch data.
            enable_logging: If True, enables logging to 'logs/indicator_calculator.log'.
        """
        self.symbols = symbols
        self.data_manager = data_manager
        self.enable_logging = enable_logging
        self.timeframes = ['1m', '5m', '15m', '1h', '6h', '1d']

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

        self.logger.debug("IndicatorCalculator initialized for symbols: %s", symbols)

    def calculate_all_indicators(self) -> Dict[str, Dict]:
        """
        Calculates all indicators for all symbols across all defined timeframes.
        """
        if not self.data_manager:
            self.logger.error("DataManager not provided during IndicatorCalculator initialization.")
            return {}

        all_indicators = {}
        for symbol in self.symbols:
            self.logger.debug(f"Calculating indicators for {symbol}")
            symbol_indicators = {}

            for timeframe in self.timeframes:
                try:
                    klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
                    ticker = self.data_manager.get_buffer(symbol, 'ticker')
                    order_book = self.data_manager.get_buffer(symbol, 'order_book')
                    
                    indicators = self.calculate_timeframe_indicators(klines, ticker, order_book, symbol, timeframe)
                    symbol_indicators[timeframe] = indicators
                    self.logger.debug(f"Indicators for {symbol} ({timeframe}): %s", indicators)
                except Exception as e:
                    self.logger.error(f"Failed to calculate indicators for {symbol} ({timeframe}): {str(e)}")
                    symbol_indicators[timeframe] = {}

            symbol_indicators['timing'] = self.calculate_timing_indicators(ticker, order_book, symbol)
            all_indicators[symbol] = symbol_indicators
            self.logger.debug(f"All indicators for {symbol}: %s", symbol_indicators)

        return all_indicators

    def calculate_timeframe_indicators(self, klines: pd.DataFrame, ticker: pd.DataFrame, order_book: pd.DataFrame, symbol: str, timeframe: str) -> Dict:
        """
        Calculates all indicators for a specific timeframe.

        Args:
            klines: Klines data with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume'].
            ticker: Ticker data buffer.
            order_book: Order book buffer.
            symbol: Trading pair symbol.
            timeframe: Timeframe (e.g., '1h', '1d').

        Returns:
            Dict: Dictionary containing all indicators, including horizontal S/R.
        """
        try:
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            if klines.empty or len(klines) < 52:
                self.logger.warning(f"Empty or insufficient {timeframe} klines for {symbol}: {len(klines)} rows")
                return {}
            if not all(col in klines.columns for col in required_columns):
                self.logger.warning(f"Missing columns in {timeframe} klines for {symbol}")
                return {}

            indicators = {}

            # Momentum Indicators
            indicators['rsi14'] = self._calculate_rsi(klines['close'], 14)
            indicators['stochastic_k'], indicators['stochastic_d'] = self._calculate_stochastic(klines, 14, 3, 3)
            indicators['cci20'] = self._calculate_cci(klines, 20)
            indicators['williams_r14'] = self._calculate_williams_r(klines, 14)

            # Trend Indicators
            indicators['sma20'] = klines['close'].rolling(window=20).mean().iloc[-1]
            indicators['ema10'] = klines['close'].ewm(span=10, adjust=False).mean().iloc[-1]
            indicators['ema20'] = klines['close'].ewm(span=20, adjust=False).mean().iloc[-1]
            indicators['macd'], indicators['macd_signal'], indicators['macd_hist'] = self._calculate_macd(klines['close'])
            indicators['adx14'] = self._calculate_adx(klines, 14)

            # Volatility Indicators
            indicators['bollinger_upper'], indicators['bollinger_middle'], indicators['bollinger_lower'] = self._calculate_bollinger_bands(klines['close'], 20, 2)
            indicators['atr14'] = self._calculate_atr(klines, 14)
            indicators['keltner_upper'], indicators['keltner_middle'], indicators['keltner_lower'] = self._calculate_keltner_channels(klines, 20, 2)

            # Volume Indicators
            indicators['vwap'] = self._calculate_vwap(klines)
            indicators['obv'] = self._calculate_obv(klines)
            indicators['ad_line'] = self._calculate_ad_line(klines)

            # Support/Resistance Indicators
            indicators['fibonacci_levels'] = self._calculate_fibonacci_retracement(klines)
            indicators['pivot_points'] = self._calculate_pivot_points(klines)
            indicators['order_book_imbalance'] = self._calculate_order_book_imbalance(order_book, depth=10) if not order_book.empty else 0.5
            indicators['volume_profile'] = self._calculate_volume_profile(klines)
            indicators['trendlines'] = self._calculate_trendlines(klines)

            # Horizontal S/R (for 1h only)
            if timeframe == '1h':
                indicators['horizontal_sr'] = self._calculate_horizontal_sr(symbol)

            # Other Indicators
            indicators['ichimoku'] = self._calculate_ichimoku_cloud(klines)
            indicators['parabolic_sar'] = self._calculate_parabolic_sar(klines, step=0.02, max_step=0.2)

            self.logger.debug(f"{timeframe} indicators for {symbol}: %s", indicators)
            return indicators

        except Exception as e:
            self.logger.error(f"Error calculating {timeframe} indicators for {symbol}: {str(e)}")
            return {}

    def _calculate_horizontal_sr(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Calculates major horizontal support/resistance levels with 3+ touches using 1h klines.

        Args:
            symbol: Trading pair symbol (e.g., 'HBAR-USD').

        Returns:
            List[Dict[str, Any]]: List of S/R levels, each with {'level': float, 'type': str, 'touches': float}.
                          Empty list if insufficient data.
        """
        try:
            klines = self.data_manager.get_buffer(symbol, 'klines_1h').tail(200)  # 200 klines (~8 days)
            if klines.empty or len(klines) < 100:
                self.logger.warning(f"Insufficient 1h klines for S/R calculation for {symbol}: {len(klines)} rows")
                return []

            current_price = float(klines['close'].iloc[-1])
            if current_price <= 0:
                self.logger.warning(f"Invalid close price for {symbol}: {current_price}")
                return []

            highs = klines['high'].values
            lows = klines['low'].values
            volumes = klines['volume'].values
            tolerance = current_price * 0.005  # 0.5% tolerance

            # Separate S/R: resistance (highs), support (lows)
            high_bins = np.arange(highs.min(), highs.max() + tolerance, tolerance)
            low_bins = np.arange(lows.min(), lows.max() + tolerance, tolerance)
            high_counts = np.zeros(len(high_bins) - 1)
            low_counts = np.zeros(len(low_bins) - 1)

            # Volume-weighted touch counting
            mean_volume = np.mean(volumes[volumes > 0]) or 1
            for i, (high, low, volume) in enumerate(zip(highs, lows, volumes)):
                high_bin_idx = np.digitize(high, high_bins) - 1
                low_bin_idx = np.digitize(low, low_bins) - 1
                if 0 <= high_bin_idx < len(high_counts):
                    high_counts[high_bin_idx] += volume / mean_volume
                if 0 <= low_bin_idx < len(low_counts):
                    low_counts[low_bin_idx] += volume / mean_volume

            # Filter levels with 3+ touches
            resistance_levels = [
                {'level': float(level + tolerance/2), 'type': 'resistance', 'touches': count}
                for level, count in zip(high_bins[:-1], high_counts) if count >= 3
            ]
            support_levels = [
                {'level': float(level + tolerance/2), 'type': 'support', 'touches': count}
                for level, count in zip(low_bins[:-1], low_counts) if count >= 3
            ]

            sr_levels = resistance_levels + support_levels
            self.logger.debug(f"Horizontal S/R for {symbol}: {len(resistance_levels)} resistance, {len(support_levels)} support levels")
            return sr_levels

        except Exception as e:
            self.logger.error(f"Error calculating horizontal S/R for {symbol}: {str(e)}")
            return []

    def calculate_timing_indicators(self, ticker: pd.DataFrame, order_book: pd.DataFrame, symbol: str) -> Dict[str, Dict]:
        """
        Calculates timing indicators for all timeframes using kline and order book data.

        Args:
            ticker (pd.DataFrame): Ticker data buffer (not used, kept for compatibility).
            order_book (pd.DataFrame): Order book data buffer with columns ['timestamp', 'symbol', 'side', 'price_level', 'quantity'].
            symbol (str): Trading pair symbol.

        Returns:
            Dict: Dictionary mapping timeframes ('1m', '5m', '15m', '1h', '6h', '1d') to timing indicators:
                {'bid_ask_spread', 'order_book_imbalance', 'ema5', 'atr14', 'volume_surge_ratio'}.

        Raises:
            ValueError: If order book or kline data is invalid or insufficient.
        """
        try:
            # Validate order book
            if order_book.empty:
                self.logger.error(f"Empty order book data for {symbol}")
                raise ValueError("Empty order book data")
            if not all(col in order_book.columns for col in ['side', 'price_level', 'quantity']):
                self.logger.error(f"Invalid order book columns: {order_book.columns}")
                raise ValueError("Missing required order book columns")

            timing_indicators = {}

            # Calculate indicators for each timeframe
            for timeframe in self.timeframes:
                try:
                    # Fetch klines for the timeframe
                    klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
                    if klines.empty:
                        self.logger.error(f"Empty {timeframe} klines data for {symbol}")
                        raise ValueError(f"Empty {timeframe} klines data")
                    if len(klines) < 14:
                        self.logger.error(f"Insufficient {timeframe} klines data for {symbol}: {len(klines)} rows, need at least 14")
                        raise ValueError(f"Insufficient {timeframe} klines rows")
                    required_kline_cols = ['open', 'high', 'low', 'close', 'volume']
                    if not all(col in klines.columns for col in required_kline_cols):
                        missing_cols = [col for col in required_kline_cols if col not in klines.columns]
                        self.logger.error(f"Missing kline columns for {symbol} ({timeframe}): {missing_cols}")
                        raise ValueError(f"Missing required kline columns for {timeframe}")

                    indicators = {}

                    # Bid-Ask Spread (from order book)
                    bids = order_book[order_book['side'] == 'bid']
                    asks = order_book[order_book['side'] == 'ask']
                    if bids.empty or asks.empty:
                        self.logger.error(f"No bid or ask data in order book for {symbol} ({timeframe})")
                        raise ValueError(f"No valid bid or ask data for {timeframe}")
                    best_bid = bids['price_level'].max()
                    best_ask = asks['price_level'].min()
                    if best_ask == 0 or best_bid is None or best_ask is None:
                        self.logger.error(f"Invalid bid/ask prices for {symbol} ({timeframe}): bid={best_bid}, ask={best_ask}")
                        raise ValueError(f"Invalid bid/ask prices for {timeframe}")
                    indicators['bid_ask_spread'] = (best_ask - best_bid) / best_ask
                    self.logger.debug(f"Bid-Ask Spread (from order book) for {symbol} ({timeframe}): {indicators['bid_ask_spread']}")

                    # Order Book Imbalance
                    indicators['order_book_imbalance'] = self._calculate_order_book_imbalance(order_book, depth=10)
                    self.logger.debug(f"Order Book Imbalance for {symbol} ({timeframe}): {indicators['order_book_imbalance']}")

                    # EMA5 of close price (from klines)
                    indicators['ema5'] = klines['close'].ewm(span=5, adjust=False).mean().iloc[-1]
                    self.logger.debug(f"EMA5 (from {timeframe} klines) for {symbol}: {indicators['ema5']}")

                    # ATR14 from klines
                    indicators['atr14'] = self._calculate_atr(klines, period=14)
                    if indicators['atr14'] == 0.0001:
                        self.logger.error(f"Invalid ATR14 calculation for {symbol} ({timeframe}), defaulted to 0.0001")
                        raise ValueError(f"Invalid ATR14 calculation for {timeframe}")
                    self.logger.debug(f"ATR14 (from {timeframe} klines) for {symbol}: {indicators['atr14']}")

                    # Volume Surge Ratio (from kline volume)
                    recent_volume = klines['volume'].iloc[-1]
                    avg_volume = klines['volume'].rolling(window=14, min_periods=1).mean().iloc[-1]
                    if avg_volume == 0:
                        self.logger.error(f"Zero average volume for {symbol} ({timeframe})")
                        raise ValueError(f"Zero average volume for {timeframe}")
                    indicators['volume_surge_ratio'] = recent_volume / avg_volume
                    if indicators['volume_surge_ratio'] == 1.0:
                        self.logger.debug(f"Volume Surge Ratio == 1.0 for {symbol} ({timeframe}): recent_volume={recent_volume}, avg_volume={avg_volume}, volumes={klines['volume'].tail(14).values}")
                    self.logger.debug(f"Volume Surge Ratio for {symbol} ({timeframe}): {indicators['volume_surge_ratio']}")

                    timing_indicators[timeframe] = indicators
                    self.logger.debug(f"Timing indicators for {symbol} ({timeframe}): {indicators}")

                except Exception as e:
                    self.logger.error(f"Error calculating timing indicators for {symbol} ({timeframe}): {str(e)}")
                    timing_indicators[timeframe] = {}

            return timing_indicators
        except Exception as e:
            self.logger.error(f"Error initializing timing indicators for {symbol}: {str(e)}")
            return {tf: {} for tf in self.timeframes}


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

    def _calculate_stochastic(self, klines: pd.DataFrame, k_period: int = 14, d_period: int = 3, smoothing: int = 3) -> Tuple[float, float]:
        try:
            if klines.empty or len(klines) < k_period:
                self.logger.debug(f"Insufficient klines data for Stochastic: {len(klines)} rows, need {k_period}")
                return 50.0, 50.0
            lowest_low = klines['low'].rolling(window=k_period, min_periods=k_period).min()
            highest_high = klines['high'].rolling(window=k_period, min_periods=k_period).max()
            k = ((klines['close'] - lowest_low) / (highest_high - lowest_low)) * 100
            k_smooth = k.rolling(window=smoothing, min_periods=smoothing).mean()
            d = k_smooth.rolling(window=d_period, min_periods=d_period).mean()
            return (
                k_smooth.iloc[-1] if not np.isnan(k_smooth.iloc[-1]) else 50.0,
                d.iloc[-1] if not np.isnan(d.iloc[-1]) else 50.0
            )
        except Exception as e:
            self.logger.error(f"Error calculating Stochastic Oscillator: {str(e)}")
            return 50.0, 50.0

    def _calculate_cci(self, klines: pd.DataFrame, period: int = 20) -> float:
        try:
            if klines.empty or len(klines) < period:
                self.logger.debug(f"Insufficient klines data for CCI: {len(klines)} rows, need {period}")
                return 0.0
            typical_price = (klines['high'] + klines['low'] + klines['close']) / 3
            sma_tp = typical_price.rolling(window=period, min_periods=period).mean()
            mean_dev = typical_price.rolling(window=period, min_periods=period).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=False)
            cci = (typical_price - sma_tp) / (0.015 * mean_dev)
            return cci.iloc[-1] if not np.isnan(cci.iloc[-1]) else 0.0
        except Exception as e:
            self.logger.error(f"Error calculating CCI: {str(e)}")
            return 0.0

    def _calculate_williams_r(self, klines: pd.DataFrame, period: int = 14) -> float:
        try:
            if klines.empty or len(klines) < period:
                self.logger.debug(f"Insufficient klines data for Williams %R: {len(klines)} rows, need {period}")
                return -50.0
            highest_high = klines['high'].rolling(window=period, min_periods=period).max()
            lowest_low = klines['low'].rolling(window=period, min_periods=period).min()
            williams_r = ((highest_high - klines['close']) / (highest_high - lowest_low)) * -100
            return williams_r.iloc[-1] if not np.isnan(williams_r.iloc[-1]) else -50.0
        except Exception as e:
            self.logger.error(f"Error calculating Williams %R: {str(e)}")
            return -50.0

    def _calculate_macd(self, prices: pd.Series) -> Tuple[float, float, float]:
        try:
            if prices.empty or len(prices) < 26:
                self.logger.debug(f"Insufficient price data for MACD: {len(prices)} rows, need 26")
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

    def _calculate_adx(self, klines: pd.DataFrame, period: int = 14) -> float:
        try:
            if klines.empty or len(klines) < (2 * period + 1):
                self.logger.debug(f"Insufficient klines data for ADX: {len(klines)} rows, need {2 * period + 1}")
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

    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, multiplier: float = 2.0) -> Tuple[float, float, float]:
        try:
            if prices.empty or len(prices) < period:
                self.logger.debug(f"Insufficient price data for Bollinger Bands: {len(prices)} rows, need {period}")
                return 0.0, 0.0, 0.0
            sma = prices.rolling(window=period, min_periods=period).mean()
            std = prices.rolling(window=period, min_periods=period).std()
            upper = sma + (multiplier * std)
            lower = sma - (multiplier * std)
            return (
                upper.iloc[-1] if not np.isnan(upper.iloc[-1]) else 0.0,
                sma.iloc[-1] if not np.isnan(sma.iloc[-1]) else 0.0,
                lower.iloc[-1] if not np.isnan(lower.iloc[-1]) else 0.0
            )
        except Exception as e:
            self.logger.error(f"Error calculating Bollinger Bands: {str(e)}")
            return 0.0, 0.0, 0.0

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

    def _calculate_keltner_channels(self, klines: pd.DataFrame, period: int = 20, multiplier: float = 2.0) -> Tuple[float, float, float]:
        try:
            if klines.empty or len(klines) < period:
                self.logger.debug(f"Insufficient klines data for Keltner Channels: {len(klines)} rows, need {period}")
                return 0.0, 0.0, 0.0
            typical_price = (klines['high'] + klines['low'] + klines['close']) / 3
            middle = typical_price.ewm(span=period, adjust=False, min_periods=period).mean()
            atr = self._calculate_atr(klines, period)
            upper = middle + (multiplier * atr)
            lower = middle - (multiplier * atr)
            return (
                upper.iloc[-1] if not np.isnan(upper.iloc[-1]) else 0.0,
                middle.iloc[-1] if not np.isnan(middle.iloc[-1]) else 0.0,
                lower.iloc[-1] if not np.isnan(lower.iloc[-1]) else 0.0
            )
        except Exception as e:
            self.logger.error(f"Error calculating Keltner Channels: {str(e)}")
            return 0.0, 0.0, 0.0

    def _calculate_vwap(self, klines: pd.DataFrame) -> float:
        try:
            if klines.empty or len(klines) < 1:
                self.logger.debug(f"Insufficient klines data for VWAP: {len(klines)} rows")
                return 0.0
            typical_price = (klines['high'] + klines['low'] + klines['close']) / 3
            volume = klines['volume']
            vwap = (typical_price * volume).cumsum() / volume.cumsum()
            return vwap.iloc[-1] if not np.isnan(vwap.iloc[-1]) else 0.0
        except Exception as e:
            self.logger.error(f"Error calculating VWAP: {str(e)}")
            return 0.0

    def _calculate_obv(self, klines: pd.DataFrame) -> float:
        try:
            if klines.empty or len(klines) < 2:
                self.logger.debug(f"Insufficient klines data for OBV: {len(klines)} rows, need at least 2")
                return 0.0
            close_diff = klines['close'].diff()
            volume = klines['volume']
            obv = volume * np.sign(close_diff)
            obv = obv.cumsum()
            return obv.iloc[-1] if not np.isnan(obv.iloc[-1]) else 0.0
        except Exception as e:
            self.logger.error(f"Error calculating OBV: {str(e)}")
            return 0.0

    def _calculate_ad_line(self, klines: pd.DataFrame) -> float:
        try:
            if klines.empty or len(klines) < 1:
                self.logger.debug(f"Insufficient klines data for A/D Line: {len(klines)} rows")
                return 0.0
            high = klines['high']
            low = klines['low']
            close = klines['close']
            volume = klines['volume']
            mfm = ((close - low) - (high - close)) / (high - low)
            mfm = mfm.replace([np.inf, -np.inf], 0).fillna(0)
            ad = (mfm * volume).cumsum()
            return ad.iloc[-1] if not np.isnan(ad.iloc[-1]) else 0.0
        except Exception as e:
            self.logger.error(f"Error calculating A/D Line: {str(e)}")
            return 0.0

    def _calculate_fibonacci_retracement(self, klines: pd.DataFrame, period: int = 20) -> Dict:
        try:
            if klines.empty or len(klines) < period:
                self.logger.debug(f"Insufficient klines data for Fibonacci Retracement: {len(klines)} rows, need {period}")
                return {'23.6%': 0.0, '38.2%': 0.0, '50%': 0.0, '61.8%': 0.0, '100%': 0.0}
            high = klines['high'].tail(period).max()
            low = klines['low'].tail(period).min()
            diff = high - low
            levels = {
                '23.6%': high - (0.236 * diff),
                '38.2%': high - (0.382 * diff),
                '50%': high - (0.50 * diff),
                '61.8%': high - (0.618 * diff),
                '100%': low
            }
            return levels
        except Exception as e:
            self.logger.error(f"Error calculating Fibonacci Retracement: {str(e)}")
            return {'23.6%': 0.0, '38.2%': 0.0, '50%': 0.0, '61.8%': 0.0, '100%': 0.0}

    def _calculate_pivot_points(self, klines: pd.DataFrame) -> Dict:
        try:
            if klines.empty or len(klines) < 2:
                self.logger.debug(f"Insufficient klines data for Pivot Points: {len(klines)} rows, need at least 2")
                return {'pivot': 0.0, 's1': 0.0, 'r1': 0.0}
            prev_day = klines.iloc[-2]
            pivot = (prev_day['high'] + prev_day['low'] + prev_day['close']) / 3
            s1 = (2 * pivot) - prev_day['high']
            r1 = (2 * pivot) - prev_day['low']
            return {
                'pivot': pivot if not np.isnan(pivot) else 0.0,
                's1': s1 if not np.isnan(s1) else 0.0,
                'r1': r1 if not np.isnan(r1) else 0.0
            }
        except Exception as e:
            self.logger.error(f"Error calculating Pivot Points: {str(e)}")
            return {'pivot': 0.0, 's1': 0.0, 'r1': 0.0}

    def _calculate_order_book_imbalance(self, order_book: pd.DataFrame, depth: int = 10) -> float:
        """
        Calculates order book imbalance based on the top 'depth' levels of bids and asks.

        Args:
            order_book: DataFrame with order book data, expected columns: ['timestamp', 'symbol', 'side', 'price_level', 'quantity'].
            depth: Number of levels to consider (default: 10).

        Returns:
            float: Imbalance ratio (bid_volume - ask_volume) / (bid_volume + ask_volume).

        Raises:
            ValueError: If order book is empty, missing columns, or has no valid bid/ask data.
        """
        try:
            if order_book.empty:
                self.logger.error("Empty order book data for Order Book Imbalance")
                raise ValueError("Empty order book data")
            if not all(col in order_book.columns for col in ['side', 'price_level', 'quantity']):
                self.logger.error(f"Invalid order book columns: {order_book.columns}")
                raise ValueError("Missing required columns in order book")
            bids = order_book[order_book['side'] == 'bid'].sort_values(by='price_level', ascending=False).head(depth)
            asks = order_book[order_book['side'] == 'ask'].sort_values(by='price_level').head(depth)
            if bids.empty or asks.empty:
                self.logger.error(f"No valid bid/ask data: bids={len(bids)}, asks={len(asks)}")
                raise ValueError("No valid bid or ask data")
            bid_volume = bids['quantity'].sum()
            ask_volume = asks['quantity'].sum()
            total_volume = bid_volume + ask_volume
            if total_volume == 0:
                self.logger.error(f"Zero total volume: bid_volume={bid_volume}, ask_volume={ask_volume}")
                raise ValueError("Zero total volume")
            imbalance = (bid_volume - ask_volume) / total_volume
            self.logger.debug(f"Order Book Imbalance calculated: {imbalance:.4f}, bid_volume={bid_volume:.2f}, ask_volume={ask_volume:.2f}")
            return imbalance
        except Exception as e:
            self.logger.error(f"Error calculating Order Book Imbalance: {str(e)}")

    def _calculate_ichimoku_cloud(self, klines: pd.DataFrame) -> Dict:
        try:
            if klines.empty or len(klines) < 52:
                self.logger.debug(f"Insufficient klines data for Ichimoku Cloud: {len(klines)} rows, need 52")
                return {
                    'tenkan_sen': 0.0,
                    'kijun_sen': 0.0,
                    'senkou_span_a': 0.0,
                    'senkou_span_b': 0.0,
                    'chikou_span': 0.0
                }
            high = klines['high']
            low = klines['low']
            close = klines['close']
            tenkan_sen = ((high.rolling(window=9).max() + low.rolling(window=9).min()) / 2).iloc[-1]
            kijun_sen = ((high.rolling(window=26).max() + low.rolling(window=26).min()) / 2).iloc[-1]
            senkou_span_a = ((tenkan_sen + kijun_sen) / 2)
            senkou_span_b = ((high.rolling(window=52).max() + low.rolling(window=52).min()) / 2).iloc[-1]
            chikou_span = close.shift(-26).iloc[-1]
            return {
                'tenkan_sen': tenkan_sen if not np.isnan(tenkan_sen) else 0.0,
                'kijun_sen': kijun_sen if not np.isnan(kijun_sen) else 0.0,
                'senkou_span_a': senkou_span_a if not np.isnan(senkou_span_a) else 0.0,
                'senkou_span_b': senkou_span_b if not np.isnan(senkou_span_b) else 0.0,
                'chikou_span': chikou_span if not np.isnan(chikou_span) else 0.0
            }
        except Exception as e:
            self.logger.error(f"Error calculating Ichimoku Cloud: {str(e)}")
            return {
                'tenkan_sen': 0.0,
                'kijun_sen': 0.0,
                'senkou_span_a': 0.0,
                'senkou_span_b': 0.0,
                'chikou_span': 0.0
            }

    def _calculate_parabolic_sar(self, klines: pd.DataFrame, step: float = 0.02, max_step: float = 0.2) -> float:
        try:
            if klines.empty or len(klines) < 2:
                self.logger.debug(f"Insufficient klines data for Parabolic SAR: {len(klines)} rows, need at least 2")
                return 0.0
            high = klines['high'].values
            low = klines['low'].values
            sar = np.zeros(len(klines))
            ep = high[0]
            af = step
            trend = 1 if klines['close'].iloc[0] > klines['close'].iloc[1] else -1
            sar[0] = low[0] if trend == 1 else high[0]

            for i in range(1, len(klines)):
                sar[i] = sar[i-1] + af * (ep - sar[i-1])
                if trend == 1:
                    sar[i] = min(sar[i], low[i-1], low[i-2] if i >= 2 else low[i-1])
                    if high[i] > ep:
                        ep = high[i]
                        af = min(af + step, max_step)
                    if low[i] < sar[i]:
                        trend = -1
                        sar[i] = ep
                        ep = low[i]
                        af = step
                else:
                    sar[i] = max(sar[i], high[i-1], high[i-2] if i >= 2 else high[i-1])
                    if low[i] < ep:
                        ep = low[i]
                        af = min(af + step, max_step)
                    if high[i] > sar[i]:
                        trend = 1
                        sar[i] = ep
                        ep = high[i]
                        af = step

            return sar[-1] if not np.isnan(sar[-1]) else 0.0
        except Exception as e:
            self.logger.error(f"Error calculating Parabolic SAR: {str(e)}")
            return 0.0

    def _calculate_volume_profile(self, klines: pd.DataFrame, bins: int = 20) -> Dict:
        """
        Calculates volume profile to identify high-volume nodes (HVNs).

        Args:
            klines (pd.DataFrame): Klines data with ['close', 'volume'].
            bins (int): Number of price bins for volume distribution (default: 20).

        Returns:
            Dict: Dictionary with price levels and their normalized volume, sorted by volume.
                  {'hvn_levels': [(price, volume), ...]} where price is the bin center.
        """
        try:
            if klines.empty or len(klines) < 10:
                self.logger.debug(f"Insufficient klines data for Volume Profile: {len(klines)} rows, need at least 10")
                return {'hvn_levels': []}
            if 'close' not in klines.columns or 'volume' not in klines.columns:
                self.logger.warning(f"Missing 'close' or 'volume' columns for Volume Profile")
                return {'hvn_levels': []}

            # Bin prices and aggregate volume
            prices = klines['close']
            volumes = klines['volume']
            price_min, price_max = prices.min(), prices.max()
            if price_max == price_min:
                self.logger.debug(f"Price range too narrow for Volume Profile")
                return {'hvn_levels': []}

            # Create bins
            bins_edges = np.linspace(price_min, price_max, bins + 1)
            bin_centers = (bins_edges[:-1] + bins_edges[1:]) / 2
            bin_indices = np.digitize(prices, bins_edges, right=True)
            bin_indices = np.clip(bin_indices, 1, bins) - 1  # Adjust for edge cases

            # Aggregate volume per bin
            bin_volumes = np.zeros(bins)
            for i in range(len(prices)):
                bin_volumes[bin_indices[i]] += volumes.iloc[i]

            # Normalize volumes
            total_volume = bin_volumes.sum()
            if total_volume == 0:
                self.logger.debug(f"Zero total volume for Volume Profile")
                return {'hvn_levels': []}
            normalized_volumes = bin_volumes / total_volume

            # Sort by volume, return top 3 HVNs
            volume_price_pairs = list(zip(bin_centers, normalized_volumes))
            volume_price_pairs.sort(key=lambda x: x[1], reverse=True)
            top_hvns = volume_price_pairs[:3]  # Top 3 high-volume nodes

            return {'hvn_levels': [(float(price), float(volume)) for price, volume in top_hvns]}
        except Exception as e:
            self.logger.error(f"Error calculating Volume Profile: {str(e)}")
            return {'hvn_levels': []}

    def _calculate_trendlines(self, klines: pd.DataFrame, lookback: int = 20) -> Dict:
        """
        Calculates trendlines as support/resistance based on recent swing highs and lows.

        Args:
            klines (pd.DataFrame): Klines data with ['high', 'low', 'close'].
            lookback (int): Number of periods to analyze for swings (default: 20).

        Returns:
            Dict: Dictionary with support and resistance trendline prices at the latest candle.
                  {'support': price, 'resistance': price}
        """
        try:
            if klines.empty or len(klines) < lookback:
                self.logger.debug(f"Insufficient klines data for Trendlines: {len(klines)} rows, need {lookback}")
                return {'support': 0.0, 'resistance': 0.0}
            if not all(col in klines.columns for col in ['high', 'low', 'close']):
                self.logger.warning(f"Missing 'high', 'low', or 'close' columns for Trendlines: columns={list(klines.columns)}")
                return {'support': 0.0, 'resistance': 0.0}

            # Extract recent data
            recent_klines = klines.tail(lookback)
            highs = recent_klines['high']
            lows = recent_klines['low']
            indices = np.arange(len(recent_klines))

            # Identify swing highs and lows
            swing_highs = []
            swing_lows = []
            for i in range(1, len(recent_klines) - 1):
                if highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i+1]:
                    swing_highs.append((indices[i], highs.iloc[i]))
                if lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i+1]:
                    swing_lows.append((indices[i], lows.iloc[i]))

            # Log swing points for debugging
            self.logger.debug(
                f"Trendlines for {recent_klines.index[-1]}: swing_highs={len(swing_highs)}, swing_lows={len(swing_lows)}, "
                f"klines_shape={recent_klines.shape}, columns={list(recent_klines.columns)}"
            )

            # Initialize default prices
            support_price = 0.0
            resistance_price = 0.0

            # Fit trendlines if sufficient swing points
            if len(swing_highs) >= 2:
                x = np.array([point[0] for point in swing_highs])
                y = np.array([point[1] for point in swing_highs])
                coeffs = np.polyfit(x, y, 1)
                resistance_price = coeffs[0] * indices[-1] + coeffs[1]
            else:
                self.logger.debug(f"Insufficient swing highs ({len(swing_highs)} < 2) for resistance trendline")

            if len(swing_lows) >= 2:
                x = np.array([point[0] for point in swing_lows])
                y = np.array([point[1] for point in swing_lows])
                coeffs = np.polyfit(x, y, 1)
                support_price = coeffs[0] * indices[-1] + coeffs[1]
            else:
                self.logger.debug(f"Insufficient swing lows ({len(swing_lows)} < 2) for support trendline")

            return {
                'support': float(support_price) if support_price > 0 else 0.0,
                'resistance': float(resistance_price) if resistance_price > 0 else 0.0
            }
        except Exception as e:
            self.logger.error(
                f"Error calculating Trendlines: {str(e)}, klines_shape={klines.shape if not klines.empty else 'empty'}, "
                f"columns={list(klines.columns) if not klines.empty else 'none'}"
            )
            return {'support': 0.0, 'resistance': 0.0}