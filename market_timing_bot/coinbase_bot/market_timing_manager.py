# market_timing_manager.py
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List, Dict, Union, Any
import pandas as pd
import numpy as np
import uuid
from datetime import datetime
import json
import threading
from collections import Counter

from market_patterns import UPTREND_PATTERNS, DOWNTREND_PATTERNS, SIDEWAY_PATTERNS
from candlestick_dictionary import CANDLESTICK_PATTERNS

class MarketTimingManager:
    def __init__(self, symbols: List[str], candlestick_patterns, chart_patterns, 
                 indicator_calculator, data_manager, order_operations: Dict, 
                 enable_logging: bool = True, testing_mode: bool = True):
        """
        Initialize MarketTimingManager with trading symbols and data sources.
        """
        self.symbols = symbols
        self.candlestick_patterns = candlestick_patterns
        self.chart_patterns = chart_patterns
        self.indicator_calculator = indicator_calculator
        self.data_manager = data_manager
        self.order_operations = order_operations
        self.timeframes = ['15m', '1h', '6h', '1d']
        self.orders = {}
        self.max_orders_per_symbol = 10
        self.testing_mode = testing_mode
        self.cache_lock = threading.Lock()
        self.indicators_cache = {symbol: {} for symbol in symbols}
        self.candlestick_cache = {symbol: {} for symbol in symbols}
        self.chart_cache = {symbol: {} for symbol in symbols}

        self.logger = logging.getLogger('MarketTimingManager')
        if enable_logging:
            log_dir = Path(__file__).parent / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / 'market_timing_manager.log'
            file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.WARNING)
        self.logger.info("MarketTimingManager initialized with symbols: %s, testing_mode: %s", symbols, testing_mode)

    async def get_portfolio_status(self) -> Dict[str, Any]:
        """
        Fetch USD balance, token balances, and open orders for all symbols.
        """
        self.logger.debug("Fetching portfolio status for all symbols")
        portfolio_status = {}

        try:
            first_symbol = self.symbols[0]
            usd_balance = await self.order_operations[first_symbol].get_usd_balance()
            portfolio_status['USD'] = {'balance': usd_balance}
            self.logger.debug("USD balance: %s", usd_balance)

            for symbol in self.symbols:
                try:
                    base_asset = symbol.split('-')[0]
                    base_balance = await self.order_operations[symbol].get_base_asset_balance(base_asset)
                    open_orders = await self.order_operations[symbol].get_open_orders()
                    portfolio_status[symbol] = {
                        'base_balance': base_balance,
                        'open_orders': open_orders
                    }
                    self.logger.debug("Portfolio status for %s - Base balance: %s, Open orders=%d", 
                                    symbol, base_balance, len(open_orders))
                except Exception as e:
                    self.logger.error("Failed to fetch portfolio data for symbol %s: %s", symbol, str(e))
                    raise Exception(f"Portfolio fetch failed for symbol {symbol}: {str(e)}")

            self.logger.info("Portfolio status fetched successfully: USD=%.2f, Symbols=%d", 
                           usd_balance, len(self.symbols))
            return portfolio_status
        except Exception as e:
            self.logger.error("Error fetching portfolio status: %s", str(e))
            raise
    
    def calculate_order_size(self, symbol: str, is_bullish: bool, portfolio_status: Dict[str, Any]) -> float:
        """
        Calculate order size (tokens to buy or sell) based on total account value.
        """
        try:
            buffer = self.data_manager.get_buffer(symbol, 'klines_1h')
            if not isinstance(buffer, pd.DataFrame) or buffer.empty or 'close' not in buffer.columns:
                self.logger.warning("No price data for %s", symbol)
                return 0.0
            price = float(buffer['close'].iloc[-1])
            if price <= 0:
                self.logger.warning("Invalid price for %s: %.4f", symbol, price)
                return 0.0

            usd_balance = portfolio_status.get('USD', {}).get('balance', 0.0)
            total_value = usd_balance
            for sym in self.symbols:
                symbol_data = portfolio_status.get(sym, {})
                base_balance = symbol_data.get('base_balance', 0.0)
                sym_buffer = self.data_manager.get_buffer(sym, 'klines_1h')
                if isinstance(sym_buffer, pd.DataFrame) and not sym_buffer.empty and 'close' in sym_buffer.columns:
                    current_price = float(sym_buffer['close'].iloc[-1])
                    total_value += base_balance * current_price
                else:
                    self.logger.warning("No price data for %s; excluding from account value", sym)

            usable_value = total_value * 0.5
            symbol_data = portfolio_status.get(symbol, {})
            open_orders_count = len(symbol_data.get('open_orders', []))
            if open_orders_count >= self.max_orders_per_symbol:
                self.logger.debug("Max open orders reached for %s: %d", symbol, open_orders_count)
                return 0.0

            total_order_slots = self.max_orders_per_symbol * len(self.symbols)
            order_value = usable_value / total_order_slots
            quantity = order_value / price

            if not self.testing_mode:
                if is_bullish:
                    if quantity * price > usd_balance:
                        self.logger.warning("Insufficient USD for %s: Needed %.2f, Available %.2f", 
                                           symbol, quantity * price, usd_balance)
                        return 0.0
                else:
                    base_balance = symbol_data.get('base_balance', 0.0)
                    if quantity > base_balance:
                        self.logger.warning("Insufficient tokens for %s: Needed %.2f, Available %.2f", 
                                           symbol, quantity, base_balance)
                        return 0.0

            self.logger.debug("Order size for %s: %.2f tokens (IsBullish=%s, Price=%.4f, TotalValue=%.2f, Usable=%.2f, OrderSlots=%d)", 
                             symbol, quantity, is_bullish, price, total_value, usable_value, total_order_slots)
            return quantity

        except Exception as e:
            self.logger.error("Error calculating order size for %s: %s", symbol, str(e))
            return 0.0

    def get_market_state(self, symbol: str, timeframe: str = None, market_data: Dict = None) -> Union[str, Dict[str, str]]:
        """
        Compute market state(s) for a given symbol using cached indicators.
        If timeframe is specified, returns a single state for that timeframe.
        If timeframe is None, returns a dictionary of states for all timeframes.
        
        Args:
            symbol: Trading pair symbol (e.g., 'HBAR-USD').
            timeframe: Specific timeframe (e.g., '15m', '1h', '6h') or None for all timeframes.
            market_data: Dictionary containing market data (unused, kept for compatibility).
        
        Returns:
            str: Market state ('uptrend', 'downtrend', 'sideways', or 'unknown') if timeframe is specified.
            Dict[str, str]: Dictionary of market states for all timeframes if timeframe is None.
        """
        if symbol not in self.symbols:
            self.logger.error("Invalid symbol %s", symbol)
            return "unknown" if timeframe else {tf: "unknown" for tf in self.timeframes}

        try:
            with self.cache_lock:
                indicators = self.indicators_cache.get(symbol, {})
            
            market_states = {}
            timeframes_to_process = [timeframe] if timeframe else self.timeframes

            for tf in timeframes_to_process:
                timeframe_indicators = indicators.get(tf, {})
                if not timeframe_indicators:
                    self.logger.warning("No cached indicators for %s (%s)", symbol, tf)
                    market_states[tf] = "unknown"
                    continue

                ema10 = float(timeframe_indicators.get('ema10', 0.0))
                ema20 = float(timeframe_indicators.get('ema20', 0.0))
                adx14 = float(timeframe_indicators.get('adx14', 0.0))
                macd_hist = float(timeframe_indicators.get('macd_hist', 0.0))

                if adx14 < 20:
                    state = "sideways"
                elif ema10 > ema20 and adx14 >= 20 and macd_hist > 0:
                    state = "uptrend"
                elif ema10 < ema20 and adx14 >= 20 and macd_hist < 0:
                    state = "downtrend"
                else:
                    state = "sideways"

                market_states[tf] = state
                self.logger.info("Market state for %s (%s): %s", symbol, tf, state)

            return market_states[timeframe] if timeframe else market_states
        except Exception as e:
            self.logger.error("Error computing market state for %s (%s): %s", symbol, timeframe or "all timeframes", str(e))
            return "unknown" if timeframe else {tf: "unknown" for tf in self.timeframes}

    def collect_market_data(self, symbol: str) -> Dict[str, Any]:
        """
        Collect current candlestick patterns, chart patterns, and indicators for a symbol from cache.
        """
        market_data = {
            'candlestick_patterns': {},
            'chart_patterns': {},
            'indicators': {}
        }
        try:
            if symbol not in self.symbols:
                self.logger.error("Invalid symbol: %s", symbol)
                return market_data

            candlestick_timeframes = ['1h', '15m']
            chart_timeframes = ['6h', '1h']
            indicator_timeframes = ['15m', '1h', '6h', '1d']

            with self.cache_lock:
                candlestick_patterns = self.candlestick_cache.get(symbol, {})
                for timeframe in candlestick_timeframes:
                    patterns = candlestick_patterns.get(timeframe, {})
                    if patterns:
                        market_data['candlestick_patterns'][timeframe] = patterns
                        self.logger.debug("Retrieved %d cached candlestick patterns for %s (%s)", len(patterns), symbol, timeframe)
                    else:
                        self.logger.warning("No cached candlestick patterns for %s (%s)", symbol, timeframe)

                chart_patterns = self.chart_cache.get(symbol, {})
                for timeframe in chart_timeframes:
                    patterns = chart_patterns.get(timeframe, {})
                    if patterns:
                        market_data['chart_patterns'][timeframe] = patterns
                        self.logger.debug("Retrieved %d cached chart patterns for %s (%s)", len(patterns), symbol, timeframe)
                    else:
                        self.logger.warning("No cached chart patterns for %s (%s)", symbol, timeframe)

                indicators = self.indicators_cache.get(symbol, {})
                for timeframe in indicator_timeframes + ['timing']:
                    if timeframe in indicators:
                        market_data['indicators'][timeframe] = indicators[timeframe]
                        self.logger.debug("Retrieved cached indicators for %s (%s)", symbol, timeframe)
                    else:
                        self.logger.warning("No cached indicators for %s (%s)", symbol, timeframe)

            self.logger.info("Collected cached market data for %s", symbol)
            return market_data
        except Exception as e:
            self.logger.error("Error collecting cached market data for %s: %s", symbol, str(e))
            return market_data

    def get_ticker_buffer(self, symbol: str) -> pd.DataFrame:
        """
        Retrieves the ticker buffer for a given symbol from DataManager.
        """
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                raise ValueError(f"Symbol {symbol} not found in symbols")
            ticker_buffer = self.data_manager.get_buffer(symbol, 'ticker')
            if ticker_buffer.empty:
                self.logger.warning(f"Empty ticker buffer for {symbol}")
            self.logger.debug(f"Retrieved ticker buffer for {symbol}, shape: {ticker_buffer.shape}")
            return ticker_buffer
        except Exception as e:
            self.logger.error(f"Error retrieving ticker buffer for {symbol}: {str(e)}")
            return pd.DataFrame()

    def assess_market_context(self, symbol, market_data):
        """
        Assesses market context across 15m, 1h, and 6h timeframes.
        Returns states for each timeframe and the dominant trend if two or more timeframes align.
        Excludes 1d timeframe.
        """
        states = {}
        valid_states = ['uptrend', 'downtrend', 'sideways']
        
        # Collect market states for 15m, 1h, and 6h
        for timeframe in ['15m', '1h', '6h']:
            state = self.get_market_state(symbol, timeframe, market_data)
            states[timeframe] = state if state in valid_states else 'unknown'
        
        # Log states for debugging
        self.logger.debug(f"Market states for {symbol}: {states}")
        
        # Count occurrences of each state
        state_counts = {}
        for timeframe in ['15m', '1h', '6h']:
            state = states[timeframe]
            state_counts[state] = state_counts.get(state, 0) + 1
        
        # Determine trend
        max_count = max(state_counts.values(), default=0)
        trend = 'sideways'  # Default if no alignment
        if max_count >= 2:
            for state in valid_states:
                if state_counts.get(state, 0) == max_count:
                    trend = state
                    break
        
        return {
            'States': states,
            'Trend': trend
        }

    def identify_key_levels(self, symbol: str) -> Dict[str, Any]:
        """
        Identifies key support/resistance levels from 6h klines and checks proximity to current price.
        Returns levels within 0.25% of current price without scoring.
        Logs all levels retrieved from indicators_cache for all time periods.
        """
        self.logger.debug(f"Starting identify_key_levels for {symbol}")
        
        if symbol not in self.symbols:
            self.logger.warning(f"Invalid symbol: {symbol}, skipping proximity check")
            return {'nearby_levels': []}

        # Get current price
        try:
            ticker = self.get_ticker_buffer(symbol)
            if ticker.empty or 'last_price' not in ticker.columns:
                self.logger.warning(f"No valid ticker data for {symbol}, skipping proximity check")
                return {'nearby_levels': []}
            
            current_price = float(ticker['last_price'].iloc[-1])
            self.logger.debug(f"Current price for {symbol}: {current_price:.6f}")
            if current_price <= 0:
                self.logger.warning(f"Non-positive ticker price for {symbol}: {current_price}, skipping proximity check")
                return {'nearby_levels': []}
        except (ValueError, TypeError, IndexError) as e:
            self.logger.warning(f"Error retrieving or parsing ticker price for {symbol}: {str(e)}")
            return {'nearby_levels': []}

        # Collect indicator data
        try:
            with self.cache_lock:
                indicators = self.indicators_cache.get(symbol, {})
            levels = []
            
            # NEW: Process all timeframes (6h, 1h, 15m, 5m)
            for timeframe in ['6h', '1h', '15m', '5m']:
                if timeframe in indicators:
                    self.logger.debug(f"Processing levels for {symbol} ({timeframe})")
                    # Pivot Points
                    pivot_points = indicators[timeframe].get('pivot_points', {})
                    for name in ['s1', 'r1']:
                        if name in pivot_points and pivot_points[name] > 0:
                            try:
                                price = float(pivot_points[name])
                                is_support = name == 's1'
                                levels.append((price, f'pivot_{name}_{timeframe}', is_support))
                            except (ValueError, TypeError):
                                self.logger.warning(f"Invalid pivot point {name} for {symbol} ({timeframe}), skipping")
                    # Fibonacci 50%, 38.2%, 61.8%
                    fib_levels = indicators[timeframe].get('fibonacci_levels', {})
                    for fib in ['38.2%', '50%', '61.8%']:
                        if fib in fib_levels and fib_levels[fib] > 0:
                            try:
                                price = float(fib_levels[fib])
                                levels.append((price, f'fib_{fib}_{timeframe}', None))
                            except (ValueError, TypeError):
                                self.logger.warning(f"Invalid Fibonacci {fib} level for {symbol} ({timeframe}), skipping")
                    # VWAP
                    vwap = indicators[timeframe].get('vwap', 0.0)
                    if vwap > 0:
                        try:
                            price = float(vwap)
                            levels.append((price, f'vwap_{timeframe}', None))
                        except (ValueError, TypeError):
                            self.logger.warning(f"Invalid VWAP for {symbol} ({timeframe}), skipping")
                    # EMA20
                    ema20 = indicators[timeframe].get('ema20', 0.0)
                    if ema20 > 0:
                        try:
                            price = float(ema20)
                            levels.append((price, f'ema20_{timeframe}', None))
                        except (ValueError, TypeError):
                            self.logger.warning(f"Invalid EMA20 for {symbol} ({timeframe}), skipping")
                    # Trend Lines
                    trendlines = indicators[timeframe].get('trendlines', {})
                    for trend_type in ['support', 'resistance']:
                        if trend_type in trendlines and trendlines[trend_type] > 0:
                            try:
                                price = float(trendlines[trend_type])
                                is_support = trend_type == 'support'
                                levels.append((price, f'trendline_{trend_type}_{timeframe}', is_support))
                            except (ValueError, TypeError):
                                self.logger.warning(f"Invalid trendline {trend_type} for {symbol} ({timeframe}), skipping")
                    # Volume Profile HVN
                    volume_profile = indicators[timeframe].get('volume_profile', {}).get('hvn_levels', [])
                    for price, _ in volume_profile:
                        if price > 0:
                            try:
                                price = float(price)
                                levels.append((price, f'volume_hvn_{timeframe}', None))
                            except (ValueError, TypeError):
                                self.logger.warning(f"Invalid volume HVN level for {symbol} ({timeframe}), skipping")
                    
                    # NEW: Log all levels for this timeframe
                    timeframe_levels = [(p, n, s) for p, n, s in levels if timeframe in n]
                    self.logger.debug(f"All retrieved levels for {symbol} ({timeframe}): {timeframe_levels}")
            
            # NEW: Log all combined levels across timeframes
            self.logger.debug(f"All retrieved levels for {symbol} (all timeframes): {[(price, name, is_support) for price, name, is_support in levels]}")
            
            # Proximity check (0.25%) for 6h levels only, as per original logic
            max_threshold = current_price * 0.0025
            nearby_levels = []
            for level, name, is_support in levels:
                if '6h' in name:  # Maintain original 6h-only proximity check
                    distance = abs(current_price - level)
                    if 0 <= distance <= max_threshold:
                        nearby_levels.append({
                            'name': name,
                            'level': level,
                            'distance_pct': distance / current_price,
                            'is_support': is_support
                        })
            
            result = {'nearby_levels': sorted(nearby_levels, key=lambda x: x['distance_pct'])}
            self.logger.info(f"Key levels for {symbol}: nearby_levels_count={len(result['nearby_levels'])}")
            return result
        except Exception as e:
            self.logger.error(f"Error processing key levels for {symbol}: {str(e)}")
            return {'nearby_levels': []}

    def identify_chart_patterns(self, symbol: str) -> Dict[str, Any]:
        self.logger.debug(f"Starting identify_chart_patterns for {symbol}")
        try:
            if symbol not in self.symbols:
                raise ValueError(f"Invalid symbol: {symbol}")

            pattern_timeframes = ['1h', '6h']
            detected_patterns = []
            bullish_patterns = {
                'double_bottom', 'inverse_head_and_shoulders', 'falling_wedge',
                'rectangle_bullish', 'flag_bullish', 'pennant_bullish', 'triangle_ascending'
            }

            ticker = self.get_ticker_buffer(symbol)
            if ticker.empty or 'last_price' not in ticker.columns:
                self.logger.warning(f"Empty ticker buffer for {symbol}, skipping pattern identification")
                return {'detected_patterns': []}
            current_price = float(ticker['last_price'].iloc[-1])

            with self.cache_lock:
                chart_patterns = self.chart_cache.get(symbol, {})
            # ... (rest of the method remains the same)

            for timeframe in pattern_timeframes:
                if timeframe not in chart_patterns:
                    self.logger.warning(f"No chart patterns in cache for {symbol} ({timeframe}), skipping")
                    continue
                patterns = chart_patterns[timeframe]

                for pattern_name, pattern_data in patterns.items():
                    if not isinstance(pattern_data, dict) or not pattern_data['detected']:
                        continue

                    has_breakout = False
                    breakout_price = None
                    if pattern_name in ['double_top', 'double_bottom', 'head_and_shoulders', 'inverse_head_and_shoulders']:
                        if 'neckline' in pattern_data and pattern_data['neckline'] is not None:
                            breakout_price = pattern_data['neckline']
                            has_breakout = (
                                (pattern_name in bullish_patterns and current_price > pattern_data['neckline']) or
                                (pattern_name not in bullish_patterns and current_price < pattern_data['neckline'])
                            )
                    elif pattern_name in ['rising_wedge', 'falling_wedge', 'flag_bullish', 'flag_bearish', 'pennant_bullish', 'triangle_symmetrical']:
                        if 'upper_trendline' in pattern_data and 'lower_trendline' in pattern_data:
                            breakout_price = pattern_data['upper_trendline'] if pattern_name in bullish_patterns else pattern_data['lower_trendline']
                            has_breakout = (
                                (pattern_name in bullish_patterns and current_price > pattern_data['upper_trendline']) or
                                (pattern_name not in bullish_patterns and current_price < pattern_data['lower_trendline'])
                            )
                    elif pattern_name in ['rectangle_bullish', 'rectangle_bearish']:
                        if 'resistance_level' in pattern_data and 'support_level' in pattern_data:
                            breakout_price = pattern_data['resistance_level'] if pattern_name in bullish_patterns else pattern_data['support_level']
                            has_breakout = (
                                (pattern_name in bullish_patterns and current_price > pattern_data['resistance_level']) or
                                (pattern_name not in bullish_patterns and current_price < pattern_data['support_level'])
                            )
                    elif pattern_name == 'triangle_ascending':
                        if 'resistance_level' in pattern_data:
                            breakout_price = pattern_data['resistance_level']
                            has_breakout = current_price > pattern_data['resistance_level']
                    elif pattern_name == 'triangle_descending':
                        if 'support_level' in pattern_data:
                            breakout_price = pattern_data['support_level']
                            has_breakout = current_price < pattern_data['support_level']

                    if breakout_price is not None:
                        pattern_dict = {
                            'name': pattern_name,
                            'timeframe': timeframe,
                            'is_bullish': pattern_name in bullish_patterns,
                            'breakout_price': float(breakout_price),
                            'has_breakout': has_breakout
                        }
                        detected_patterns.append(pattern_dict)
                        self.logger.debug(f"Detected pattern for {symbol} ({timeframe}): {pattern_dict}")

            return {'detected_patterns': detected_patterns}
        except Exception as e:
            self.logger.error(f"Unexpected error identifying chart patterns for {symbol}: {str(e)}")
            raise

    def identify_candlestick_patterns(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identifies candlestick patterns for 1h, 15m, and 5m timeframes without scoring.
        Excludes neutral patterns like doji_standard.
        """
        self.logger.debug(f"Starting identify_candlestick_patterns for {symbol}")
        try:
            if symbol not in self.symbols:
                self.logger.error(f"Invalid symbol: {symbol}")
                return {'detected_patterns': []}

            candlestick_patterns = market_data.get('candlestick_patterns', {})
            detected_patterns = []
            bullish_patterns = {
                'marubozu_bullish', 'hammer', 'inverted_hammer', 'doji_dragonfly',
                'engulfing_bullish', 'piercing_line', 'morning_star', 'three_white_soldiers',
                'rising_three_methods', 'harami_bullish', 'harami_cross_bullish',
                'tweezer_bottoms', 'three_inside_up', 'stick_sandwich_bullish'
            }
            bearish_patterns = {
                'marubozu_bearish', 'hanging_man', 'shooting_star', 'doji_gravestone',
                'engulfing_bearish', 'dark_cloud_cover', 'evening_star', 'three_black_crows',
                'falling_three_methods', 'harami_bearish', 'harami_cross_bearish',
                'tweezer_tops', 'three_inside_down', 'stick_sandwich_bearish', 'on_neck'
            }

            for timeframe in ['1h', '15m', '5m']:
                if timeframe not in candlestick_patterns:
                    continue
                tf_patterns = candlestick_patterns[timeframe]
                for pattern_name, pattern_data in tf_patterns.items():
                    is_detected = isinstance(pattern_data, bool) and pattern_data or \
                                isinstance(pattern_data, dict) and pattern_data.get('detected', False)
                    if not is_detected:
                        continue
                    if pattern_name not in bullish_patterns and pattern_name not in bearish_patterns:
                        self.logger.debug(f"Skipping neutral pattern {pattern_name} for {symbol} ({timeframe})")
                        continue
                    is_bullish = pattern_name in bullish_patterns
                    pattern_info = {
                        'name': pattern_name,
                        'timeframe': timeframe,
                        'is_bullish': is_bullish
                    }
                    detected_patterns.append(pattern_info)
                    self.logger.debug(f"Added pattern: {pattern_info}")

            result = {'detected_patterns': detected_patterns}
            self.logger.info(f"Candlestick patterns for {symbol}: detected_count={len(detected_patterns)}")
            return result
        except Exception as e:
            self.logger.error(f"Error identifying candlestick patterns for {symbol}: {str(e)}")
            return {'detected_patterns': []}
        
    def evaluate_confirmation_indicators(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates confirmation indicators for 5m, 15m, and 1h timeframes without scoring.
        Returns bullish/bearish signals for each timeframe based on at least three of four conditions.
        """
        self.logger.debug(f"Starting evaluate_confirmation_indicators for {symbol}")
        try:
            if symbol not in self.symbols:
                raise ValueError(f"Invalid symbol: {symbol}")

            if 'indicators' not in market_data:
                raise KeyError(f"Missing indicators in market_data for {symbol}")

            evaluated_directions = []
            timeframes = ['5m', '15m', '1h']
            for timeframe in timeframes:
                if timeframe not in market_data['indicators']:
                    self.logger.debug(f"No indicators for {symbol} ({timeframe}), skipping")
                    continue
                indicators = market_data['indicators'][timeframe]
                required_keys = ['ema10', 'ema20', 'adx14', 'macd_hist']
                for key in required_keys:
                    if key not in indicators or not isinstance(indicators[key], (int, float)):
                        self.logger.warning(f"Invalid/missing {key} for {symbol} ({timeframe})")
                        continue

                if 'timing' not in market_data['indicators'] or timeframe not in market_data['indicators']['timing'] or \
                'volume_surge_ratio' not in market_data['indicators']['timing'][timeframe]:
                    continue

                ema10 = indicators['ema10']
                ema20 = indicators['ema20']
                adx14 = indicators['adx14']
                macd_hist = indicators['macd_hist']
                volume_surge_ratio = market_data['indicators']['timing'][timeframe]['volume_surge_ratio']

                # Count bullish conditions
                bullish_conditions = [
                    ema10 > ema20,
                    macd_hist > 0,
                    adx14 > 25,
                    volume_surge_ratio > 1
                ]
                bullish_count = sum(bullish_conditions)
                is_bullish = bullish_count >= 3  # At least three conditions

                # Count bearish conditions
                bearish_conditions = [
                    ema10 < ema20,
                    macd_hist < 0,
                    adx14 > 25,
                    volume_surge_ratio > 1
                ]
                bearish_count = sum(bearish_conditions)
                is_bearish = bearish_count >= 3  # At least three conditions

                direction_dict = {
                    'timeframe': timeframe,
                    'is_bullish': is_bullish,
                    'is_bearish': is_bearish
                }
                evaluated_directions.append(direction_dict)
                self.logger.debug(f"Confirmation indicators for {symbol} ({timeframe}): {direction_dict}")

            return {'evaluated_directions': evaluated_directions}
        except Exception as e:
            self.logger.error(f"Unexpected error evaluating confirmation indicators for {symbol}: {str(e)}")
            return {'evaluated_directions': []}

    def determine_trade_levels(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Calculate entry, stop-loss, and take-profit levels for long and short trades.
        Uses 6h S/R levels (0.25% proximity), 1h/15m/5m confirmations, 1d trend filter (ADX > 25).
        Ensures 1.5% S/R spacing, 1:3 risk-reward, and prints input dictionaries.
        """
        trades = []
        try:
            # Get current price
            ticker = self.get_ticker_buffer(symbol)
            self.logger.debug(f"Ticker data for {symbol}: shape={ticker.shape}, columns={list(ticker.columns)}")
            if ticker.empty or 'last_price' not in ticker.columns:
                self.logger.warning(f"No valid ticker data for {symbol}")
                return trades
            current_price = float(ticker['last_price'].iloc[-1])
            self.logger.debug(f"Current price for {symbol}: {current_price:.6f}")
            if current_price <= 0:
                self.logger.warning(f"Invalid price for {symbol}: {current_price}")
                return trades

            # Collect market data from caches
            with self.cache_lock:
                market_data = {
                    'candlestick_patterns': self.candlestick_cache.get(symbol, {}),
                    'chart_patterns': self.chart_cache.get(symbol, {}),
                    'indicators': self.indicators_cache.get(symbol, {})
                }
            self.logger.debug(f"Market data keys for {symbol}: {list(market_data.keys())}")

            # Get inputs
            context = self.assess_market_context(symbol, market_data)
            levels = self.identify_key_levels(symbol)
            chart_patterns = self.identify_chart_patterns(symbol)
            candlestick_patterns = self.identify_candlestick_patterns(symbol, market_data)
            direction_evaluation = self.evaluate_confirmation_indicators(symbol, market_data)

            # Log inputs
            self.logger.debug(f"Inputs for {symbol}:")
            self.logger.debug(f"context: {context}")
            self.logger.debug(f"levels: {levels}")
            self.logger.debug(f"chart_patterns: {chart_patterns}")
            self.logger.debug(f"candlestick_patterns: {candlestick_patterns}")
            self.logger.debug(f"direction_evaluation: {direction_evaluation}")

            # Check 1d trend filter
            apply_trend_filter = False
            trend = context.get('Trend', 'sideways')
            if '1d' in self.indicators_cache.get(symbol, {}):
                adx14 = self.indicators_cache[symbol]['1d'].get('adx14', 0.0)
                apply_trend_filter = adx14 > 25
                self.logger.debug(f"1d trend filter for {symbol}: ADX14={adx14:.2f}, apply={apply_trend_filter}, trend={trend}")

            # Collect all support/resistance levels
            indicators_cache = self.indicators_cache.get(symbol, {})
            sr_levels = []
            for tf in ['6h', '1h', '15m']:
                if tf in indicators_cache:
                    ind = indicators_cache[tf]
                    for key in ['pivot_points', 'fibonacci_levels', 'vwap', 'ema20', 'trendlines']:
                        if key in ind:
                            if isinstance(ind[key], dict):
                                for k, v in ind[key].items():
                                    if isinstance(v, (int, float)) and v > 0:
                                        is_support = 's' in k.lower() or 'support' in k.lower()
                                        sr_levels.append((v, f"{k}_{tf}", is_support))
                            elif key == 'vwap' and isinstance(ind[key], (int, float)) and ind[key] > 0:
                                sr_levels.append((ind[key], f"vwap_{tf}", None))
                    if 'volume_profile' in ind and 'hvn_levels' in ind['volume_profile']:
                        for price, _ in ind['volume_profile']['hvn_levels']:
                            if price > 0:
                                sr_levels.append((price, f"volume_hvn_{tf}", None))
            sr_levels.sort(key=lambda x: x[0])
            
            # Log all support/resistance levels used for spacing
            self.logger.debug(f"All support/resistance levels for {symbol}: {[(price, name, is_support) for price, name, is_support in sr_levels]}")

            # Process nearby levels
            for level in levels.get('nearby_levels', []):
                price, name, is_support = level['level'], level['name'], level['is_support']
                self.logger.debug(f"Evaluating level for {symbol}: price={price:.6f}, name={name}, is_support={is_support}, current_price={current_price:.6f}")

                # Long trade (buy near support)
                if (is_support or is_support is None) and (not apply_trend_filter or trend != 'downtrend'):
                    self.logger.debug(f"Checking long trade for {symbol}: level_price={price:.6f}, current_price={current_price:.6f}")
                    if current_price <= price:
                        next_resistance = next((p for p, _, _ in sr_levels if p > price), None)
                        if next_resistance:
                            spacing_pct = (next_resistance - current_price) / current_price
                            self.logger.debug(f"Long trade spacing for {symbol}: next_resistance={next_resistance:.6f}, spacing={spacing_pct:.4%}")
                        else:
                            self.logger.debug(f"No next resistance found for {symbol} long trade")
                        if next_resistance and spacing_pct >= 0.015:
                            if self._has_bullish_confirmations(symbol, ['1h', '15m', '5m'], market_data, chart_patterns, candlestick_patterns, direction_evaluation):
                                stop_loss = current_price * 0.995
                                take_profit = next_resistance
                                rr_ratio = (take_profit - current_price) / (current_price - stop_loss)
                                self.logger.debug(f"Long trade RR for {symbol}: entry={current_price:.6f}, stop_loss={stop_loss:.6f}, take_profit={take_profit:.6f}, rr_ratio={rr_ratio:.2f}")
                                if rr_ratio >= 3.0:
                                    trades.append({
                                        'direction': 'long',
                                        'entry_price': current_price,
                                        'stop_loss_price': stop_loss,
                                        'take_profit_price': take_profit,
                                        'level_name': name,
                                        'is_bullish': True,
                                        'rr_ratio': rr_ratio
                                    })
                                    self.logger.debug(f"Long trade added for {symbol}")
                                else:
                                    self.logger.debug(f"Long trade rejected for {symbol}: rr_ratio={rr_ratio:.2f} < 3.0")
                            else:
                                self.logger.debug(f"Long trade rejected for {symbol}: no bullish confirmations")
                        else:
                            self.logger.debug(f"Long trade rejected for {symbol}: insufficient spacing ({spacing_pct:.4%} < 1.5%) or no next resistance")
                    else:
                        self.logger.debug(f"Long trade skipped for {symbol}: current_price={current_price:.6f} > level_price={price:.6f}")

                # Short trade (sell near resistance)
                if (is_support is False or is_support is None) and (not apply_trend_filter or trend != 'uptrend'):
                    self.logger.debug(f"Checking short trade for {symbol}: level_price={price:.6f}, current_price={current_price:.6f}")
                    if current_price >= price:
                        next_support = next((p for p, _, _ in sr_levels if p < price), None)
                        if next_support:
                            spacing_pct = (current_price - next_support) / current_price
                            self.logger.debug(f"Short trade spacing for {symbol}: next_support={next_support:.6f}, spacing={spacing_pct:.4%}")
                        else:
                            self.logger.debug(f"No next support found for {symbol} short trade")
                        if next_support and spacing_pct >= 0.015:
                            if self._has_bearish_confirmations(symbol, ['1h', '15m', '5m'], market_data, chart_patterns, candlestick_patterns, direction_evaluation):
                                stop_loss = current_price * 1.005
                                take_profit = next_support
                                rr_ratio = (current_price - take_profit) / (stop_loss - current_price)
                                self.logger.debug(f"Short trade RR for {symbol}: entry={current_price:.6f}, stop_loss={stop_loss:.6f}, take_profit={take_profit:.6f}, rr_ratio={rr_ratio:.2f}")
                                if rr_ratio >= 3.0:
                                    trades.append({
                                        'direction': 'short',
                                        'entry_price': current_price,
                                        'stop_loss_price': stop_loss,
                                        'take_profit_price': take_profit,
                                        'level_name': name,
                                        'is_bullish': False,
                                        'rr_ratio': rr_ratio
                                    })
                                    self.logger.debug(f"Short trade added for {symbol}")
                                else:
                                    self.logger.debug(f"Short trade rejected for {symbol}: rr_ratio={rr_ratio:.2f} < 3.0")
                            else:
                                self.logger.debug(f"Short trade rejected for {symbol}: no bearish confirmations")
                        else:
                            self.logger.debug(f"Short trade rejected for {symbol}: insufficient spacing ({spacing_pct:.4%} < 1.5%) or no next support")
                    else:
                        self.logger.debug(f"Short trade skipped for {symbol}: current_price={current_price:.6f} < level_price={price:.6f}")

            self.logger.debug(f"Final trades for {symbol}: {trades}")
            self.logger.info(f"Computed {len(trades)} trade levels for {symbol}")
            return trades
        except Exception as e:
            self.logger.error(f"Error in determine_trade_levels for {symbol}: {str(e)}")
            return trades

    #rewrite the order size method
    #need a method to actually place orders
    #need a method to track orders

    async def run(self) -> None:
        self.logger.info("Starting trading run loop for symbols: %s", self.symbols)
        while True:
            try:
                # Update caches
                all_indicators = self.indicator_calculator.calculate_all_indicators()
                self.logger.info("Updated indicators for %d symbols", len(all_indicators))
                all_candlestick = self.candlestick_patterns.calculate_all_patterns()
                self.logger.info("Updated candlestick patterns for %d symbols", len(all_candlestick))
                all_chart = self.chart_patterns.calculate_all_patterns()
                self.logger.info("Updated chart patterns for %d symbols", len(all_chart))

                with self.cache_lock:
                    self.indicators_cache = all_indicators
                    self.candlestick_cache = all_candlestick
                    self.chart_cache = all_chart

                for symbol in self.symbols:
                    try:
                        ticker = self.get_ticker_buffer(symbol)
                        self.logger.info(f"Ticker for %s: %d rows", symbol, ticker.shape[0] if not ticker.empty else 0)

                        if ticker.empty or 'last_price' not in ticker.columns:
                            self.logger.warning(f"No valid ticker data for %s, skipping", symbol)
                            continue
                        try:
                            current_price = float(ticker['last_price'].iloc[-1])
                        except (ValueError, IndexError) as e:
                            self.logger.warning(f"Error parsing price for %s: %s, skipping", symbol, str(e))
                            continue
                        if current_price <= 0:
                            self.logger.warning(f"Invalid price for %s: %s, skipping", symbol, current_price)
                            continue

                        # Collect market data once
                        market_data = self.collect_market_data(symbol)
                        self.logger.debug(f"Market data for %s: chart_patterns=%s, candlestick_patterns=%s", 
                                        symbol, market_data.get('chart_patterns', {}), market_data.get('candlestick_patterns', {}))

                        # Pass market_data to methods
                        context = self.assess_market_context(symbol, market_data)
                        self.logger.info(f"Market context for %s: Trend={context.get('Trend', 'sideways')}")
                        self.logger.debug(f"Full assess_market_context dictionary for %s: %s", symbol, context)

                        levels = self.identify_key_levels(symbol)  # Update to use cache or market_data
                        self.logger.info(f"Key levels for %s: nearby_levels_count=%d", symbol, len(levels.get('nearby_levels', [])))

                        chart_patterns = self.identify_chart_patterns(symbol)  # Update to use cache or market_data
                        self.logger.info(f"Chart patterns for %s: detected_count=%d", symbol, len(chart_patterns.get('detected_patterns', [])))

                        candlestick_patterns = self.identify_candlestick_patterns(symbol, market_data)
                        self.logger.info(f"Candlestick patterns for %s: detected_count=%d", symbol, len(candlestick_patterns.get('detected_patterns', [])))

                        direction_evaluation = self.evaluate_confirmation_indicators(symbol, market_data)
                        self.logger.info(f"Confirmation indicators evaluation for %s: supported_count=%d", 
                                        symbol, sum(1 for d in direction_evaluation.get('evaluated_directions', []) if d['is_bullish'] or d['is_bearish']))

                        trade_levels_list = self.determine_trade_levels(symbol)  # Update to use market_data
                        self.logger.info(f"Computed %d trade levels for %s", len(trade_levels_list), symbol)
                        self.logger.debug(f"Trade levels for %s: %s", symbol, trade_levels_list)

                    except Exception as e:
                        self.logger.error(f"Error processing symbol %s: %s", symbol, str(e), exc_info=True)

                await asyncio.sleep(60)
            except Exception as e:
                self.logger.error(f"Error in run loop: %s", str(e), exc_info=True)
                await asyncio.sleep(60)
