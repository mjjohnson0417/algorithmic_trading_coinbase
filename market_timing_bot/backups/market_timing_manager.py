# market_timing_manager.py
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import numpy as np

from market_patterns import UPTREND_PATTERNS, DOWNTREND_PATTERNS, SIDEWAY_PATTERNS

class MarketTimingManager:
    def __init__(self, symbols: List[str], candlestick_patterns, chart_patterns, 
                 indicator_calculator, data_manager, order_operations: Dict, enable_logging: bool = True):
        """
        Initialize MarketTimingManager with trading symbols and data sources.
        """
        self.symbols = symbols
        self.candlestick_patterns = candlestick_patterns
        self.chart_patterns = chart_patterns
        self.indicator_calculator = indicator_calculator
        self.data_manager = data_manager
        self.order_operations = order_operations
        self.timeframes = ['1m', '5m', '15m', '1h', '6h', '1d']

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

        self.logger.info("MarketTimingManager initialized with symbols: %s", symbols)

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
                    self.logger.debug("Portfolio status for %s - Base balance: %s, Open orders: %d", 
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

    def get_market_state(self, symbol: str, timeframe: str) -> str:
        """
        Compute market state from indicators.
        """
        if symbol not in self.symbols or timeframe not in self.timeframes:
            self.logger.error("Invalid symbol %s or timeframe %s", symbol, timeframe)
            return "unknown"

        try:
            indicators = self.indicator_calculator.calculate_all_indicators().get(symbol, {}).get(timeframe, {})
            if not indicators:
                self.logger.warning("No indicators for %s (%s)", symbol, timeframe)
                return "unknown"

            ema10 = float(indicators.get('ema10', 0.0))
            ema20 = float(indicators.get('ema20', 0.0))
            rsi14 = float(indicators.get('rsi14', 50.0))
            adx14 = float(indicators.get('adx14', 0.0))
            macd_hist = float(indicators.get('macd_hist', 0.0))

            patterns = self.chart_patterns.calculate_all_patterns().get(symbol, {}).get(timeframe, {})
            sideways_pattern = patterns.get('triangle_symmetrical', False)

            if adx14 < 20 or sideways_pattern:
                state = "sideways"
            elif ema10 > ema20 and adx14 >= 20 and rsi14 < 80 and macd_hist > 0:
                state = "uptrend"
            elif ema10 < ema20 and adx14 >= 20 and rsi14 > 20 and macd_hist < 0:
                state = "downtrend"
            else:
                state = "sideways"

            self.logger.info("Market state for %s (%s): %s", symbol, timeframe, state)
            return state
        except Exception as e:
            self.logger.error("Error computing market state for %s (%s): %s", symbol, timeframe, str(e))
            return "unknown"

    def _get_nested_indicator_value(self, indicators: Dict, key_path: str) -> Any:
        """
        Retrieve a nested indicator value from the indicators dictionary.
        """
        try:
            if key_path == "volume_surge_ratio":
                value = indicators.get('timing', {}).get('volume_surge_ratio')
                if value is not None:
                    return float(value) if isinstance(value, np.floating) else value

            if '.' in key_path:
                keys = key_path.split('.')
                value = indicators
                for key in keys:
                    value = value.get(key)
                    if value is None:
                        return None
                return float(value) if isinstance(value, np.floating) else value
            else:
                value = indicators.get(key_path)
                return float(value) if isinstance(value, np.floating) else value
        except (TypeError, AttributeError) as e:
            self.logger.debug("Error accessing %s: %s", key_path, str(e))
            return None

    def check_chart_patterns(self, symbol: str, timeframe: str, market_state: str) -> List[Dict[str, Any]]:
        """
        Identify chart patterns that align with the market state.
        """
        if symbol not in self.symbols or timeframe not in self.timeframes:
            self.logger.error("Invalid symbol %s or timeframe %s", symbol, timeframe)
            return []

        pattern_dicts = {
            "uptrend": UPTREND_PATTERNS,
            "downtrend": DOWNTREND_PATTERNS,
            "sideways": SIDEWAY_PATTERNS
        }.get(market_state, SIDEWAY_PATTERNS)

        try:
            chart_patterns = self.chart_patterns.calculate_all_patterns().get(symbol, {}).get(timeframe, {})
            if not isinstance(chart_patterns, dict):
                self.logger.warning("Invalid chart patterns data for %s (%s): %s", symbol, timeframe, chart_patterns)
                return []

            indicators = self.indicator_calculator.calculate_all_indicators().get(symbol, {}).get(timeframe, {})
            if not isinstance(indicators, dict):
                self.logger.warning("Invalid indicators data for %s (%s): %s", symbol, timeframe, indicators)
                return []

            detected_patterns = []

            buffer = self.data_manager.get_buffer(symbol, f"klines_{timeframe}")
            price = None
            if isinstance(buffer, pd.DataFrame) and not buffer.empty and 'close' in buffer.columns and len(buffer['close']) > 0:
                price = float(buffer['close'].iloc[-1])
                self.logger.debug("Close price for %s (%s): %s", symbol, timeframe, price)
            else:
                self.logger.error("Invalid or empty kline buffer for %s (%s): %s", symbol, timeframe, buffer)
                return []

            for pattern_name, pattern_info in pattern_dicts.items():
                if chart_patterns.get(pattern_name, False):
                    self.logger.debug("Checking pattern %s for %s (%s)", pattern_name, symbol, timeframe)
                    indicators_met = []
                    for ind in pattern_info.get("indicators", []):
                        ind_name = ind["name"]
                        condition = ind["condition"].replace("pivot_points.r1", "pivot_points_r1").replace("pivot_points.s1", "pivot_points_s1")
                        ind_value = self._get_nested_indicator_value(indicators, ind_name)

                        if ind_value is None:
                            self.logger.warning("Indicator %s not found for %s (%s)", ind_name, symbol, timeframe)
                            continue

                        try:
                            eval_globals = {"current_price": price}
                            eval_locals = {ind_name.replace('.', '_'): ind_value}
                            for key in indicators:
                                val = self._get_nested_indicator_value(indicators, key)
                                if val is not None:
                                    eval_locals[key.replace('.', '_')] = val
                            if 'pivot_points' in indicators:
                                eval_locals['pivot_points_r1'] = indicators['pivot_points'].get('r1')
                                eval_locals['pivot_points_s1'] = indicators['pivot_points'].get('s1')
                            if eval(condition, eval_globals, eval_locals):
                                indicators_met.append(ind_name)
                            else:
                                self.logger.debug("Condition %s not met for %s in pattern %s for %s (%s): value=%s",
                                                 condition, ind_name, pattern_name, symbol, timeframe, ind_value)
                        except Exception as e:
                            self.logger.warning("Error evaluating condition '%s' for %s in pattern %s for %s (%s): %s",
                                               condition, ind_name, pattern_name, symbol, timeframe, str(e))
                            continue

                    if indicators_met:
                        detected_patterns.append({
                            "pattern": pattern_name,
                            "implication": pattern_info["implication"],
                            "indicators_met": indicators_met
                        })

            self.logger.info("Detected chart patterns for %s (%s): %s", symbol, timeframe, detected_patterns)
            return detected_patterns
        except Exception as e:
            self.logger.error("Error checking chart patterns for %s (%s): %s", symbol, timeframe, str(e))
            raise

    def calculate_trade_prices(self, symbol: str, timeframe: str, market_state: str, chart_pattern: Dict[str, Any], is_bullish_action: bool) -> Dict[str, float]:
        """
        Calculate trade prices based on trading action.
        """
        prices = {"buy": None, "sell": None, "stop_loss": None}
        try:
            buffer = self.data_manager.get_buffer(symbol, f"klines_{timeframe}")
            if not isinstance(buffer, pd.DataFrame) or buffer.empty or 'close' not in buffer.columns or len(buffer['close']) == 0:
                self.logger.error("Invalid kline buffer for %s (%s): %s", symbol, timeframe, buffer)
                return prices

            close_price = float(buffer['close'].iloc[-1])
            self.logger.debug("Close price for %s (%s): %s", symbol, timeframe, close_price)

            if is_bullish_action:
                prices["buy"] = close_price
                prices["sell"] = close_price * 1.02
                prices["stop_loss"] = close_price * 0.98
                self.logger.info("Trade prices calculated for %s (%s) in %s market (buy low, sell high): Buy=%.4f, Sell=%.4f, Stop-Loss=%.4f",
                                 symbol, timeframe, market_state, prices["buy"], prices["sell"], prices["stop_loss"])
            else:
                prices["sell"] = close_price
                prices["buy"] = close_price * 0.98
                prices["stop_loss"] = None
                self.logger.info("Trade prices calculated for %s (%s) in %s market (sell high, buy back low): Sell=%.4f, Buyback=%.4f",
                                 symbol, timeframe, market_state, prices["sell"], prices["buy"])

            self.logger.debug("Calculated prices for %s (%s): %s", symbol, timeframe, prices)
            return prices
        except Exception as e:
            self.logger.error("Error calculating trade prices for %s (%s): %s", symbol, timeframe, str(e))
            return prices

    def check_candlestick_confirmations(self, symbol: str, timeframe: str, chart_patterns: List[Dict[str, Any]], market_state: str) -> List[Dict[str, Any]]:
        """
        Confirm entry points using candlestick patterns and indicators, respecting market_patterns comments.
        """
        if symbol not in self.symbols or timeframe not in self.timeframes:
            self.logger.error("Invalid symbol %s or timeframe %s", symbol, timeframe)
            return []

        pattern_dicts = {
            "uptrend": UPTREND_PATTERNS,
            "downtrend": DOWNTREND_PATTERNS,
            "sideways": SIDEWAY_PATTERNS
        }

        # Patterns that allow bullish actions in downtrend markets per market_patterns.py
        bullish_patterns_in_downtrend = [
            "double_bottom", "inverse_head_and_shoulders", "falling_wedge",
            "rectangle_bullish", "triangle_symmetrical"
        ]

        try:
            candlestick_patterns = self.candlestick_patterns.calculate_all_patterns().get(symbol, {}).get(timeframe, {})
            if not isinstance(candlestick_patterns, dict):
                self.logger.warning("Invalid candlestick patterns data for %s (%s): %s", symbol, timeframe, candlestick_patterns)
                return []

            indicators = self.indicator_calculator.calculate_all_indicators().get(symbol, {}).get(timeframe, {})
            if not isinstance(indicators, dict):
                self.logger.warning("Invalid indicators data for %s (%s): %s", symbol, timeframe, indicators)
                return []

            entry_signals = []

            buffer = self.data_manager.get_buffer(symbol, f"klines_{timeframe}")
            price = None
            if isinstance(buffer, pd.DataFrame) and not buffer.empty and 'close' in buffer.columns and len(buffer['close']) > 0:
                price = float(buffer['close'].iloc[-1])
                self.logger.debug("Close price for %s (%s): %s", symbol, timeframe, price)
            else:
                self.logger.error("Invalid kline buffer for %s (%s): %s", symbol, timeframe, buffer)
                return []

            for chart_pattern in chart_patterns:
                pattern_name = chart_pattern["pattern"]
                pattern_info = None
                for state, patterns in pattern_dicts.items():
                    if pattern_name in patterns:
                        pattern_info = patterns[pattern_name]
                        break

                if not pattern_info:
                    self.logger.debug("Pattern %s not found in pattern dictionaries", pattern_name)
                    continue

                implication = pattern_info["implication"].lower()
                candlestick_dict = pattern_info.get("candlestick_patterns", {})

                for candlestick_name, candlestick_info in candlestick_dict.items():
                    # Determine trading action based on candlestick
                    is_bullish_action = candlestick_name in [
                        "marubozu_bullish", "hammer", "engulfing_bullish", "three_white_soldiers",
                        "piercing_line", "morning_star", "three_inside_up", "harami_cross_bullish",
                        "harami_bullish", "inverted_hammer", "doji_dragonfly", "tweezer_bottoms",
                        "stick_sandwich_bullish", "rising_three_methods"
                    ]
                    is_bearish_action = candlestick_name in [
                        "marubozu_bearish", "hanging_man", "engulfing_bearish", "three_black_crows",
                        "dark_cloud_cover", "shooting_star", "evening_star", "three_inside_down",
                        "harami_cross_bearish", "harami_bearish", "doji_gravestone", "tweezer_tops",
                        "on_neck", "stick_sandwich_bearish", "falling_three_methods"
                    ]
                    is_neutral_action = candlestick_name == "doji_standard"


                    # Validate action against market state and pattern
                    if market_state == "downtrend":
                        if is_bullish_action and pattern_name not in bullish_patterns_in_downtrend:
                            self.logger.debug("Skipping candlestick %s for pattern %s in downtrend: not allowed for non-bullish pattern",
                                             candlestick_name, pattern_name)
                            continue
                        if is_bearish_action and pattern_name in ["double_bottom", "inverse_head_and_shoulders", "falling_wedge", "rectangle_bullish"]:
                            self.logger.debug("Skipping candlestick %s for pattern %s in downtrend: bearish action not allowed for bullish pattern",
                                             candlestick_name, pattern_name)
                            continue
                    elif market_state in ["uptrend", "sideways"]:
                        if is_bearish_action and pattern_name not in ["triangle_symmetrical", "rectangle_bearish", "triangle_descending"]:
                            self.logger.debug("Skipping candlestick %s for pattern %s in %s: bearish action not allowed",
                                             candlestick_name, pattern_name, market_state)
                            continue
                        if is_bullish_action and pattern_name in ["rectangle_bearish", "triangle_descending"]:
                            self.logger.debug("Skipping candlestick %s for pattern %s in %s: bullish action not allowed for bearish pattern",
                                             candlestick_name, pattern_name, market_state)
                            continue

                    if is_neutral_action:
                        self.logger.debug("Skipping candlestick %s for pattern %s: neutral action (doji_standard)",
                                         candlestick_name, pattern_name)
                        continue

                    if not candlestick_patterns.get(candlestick_name, False):
                        self.logger.debug("Candlestick pattern %s not detected for %s (%s)",
                                         candlestick_name, symbol, timeframe)
                        continue

                    indicators_met = []
                    for ind in candlestick_info.get("indicators", []):
                        ind_name = ind["name"]
                        condition = ind["condition"].replace("pivot_points.r1", "pivot_points_r1").replace("pivot_points.s1", "pivot_points_s1")
                        ind_value = self._get_nested_indicator_value(indicators, ind_name)

                        if ind_value is None:
                            self.logger.warning("Indicator %s not found for %s (%s)", ind_name, symbol, timeframe)
                            continue

                        try:
                            eval_globals = {"current_price": price}
                            eval_locals = {ind_name.replace('.', '_'): ind_value}
                            for key in indicators:
                                val = self._get_nested_indicator_value(indicators, key)
                                if val is not None:
                                    eval_locals[key.replace('.', '_')] = val
                            if 'pivot_points' in indicators:
                                eval_locals['pivot_points_r1'] = indicators['pivot_points'].get('r1')
                                eval_locals['pivot_points_s1'] = indicators['pivot_points'].get('s1')
                            if eval(condition, eval_globals, eval_locals):
                                indicators_met.append(ind_name)
                            else:
                                self.logger.debug("Condition %s not met for %s in candlestick %s for %s (%s): value=%s",
                                                 condition, ind_name, candlestick_name, symbol, timeframe, ind_value)
                        except Exception as e:
                            self.logger.warning("Error evaluating condition '%s' for %s in candlestick %s for %s (%s): %s",
                                               condition, ind_name, candlestick_name, symbol, timeframe, str(e))
                            continue

                    if indicators_met:
                        trade_prices = self.calculate_trade_prices(symbol, timeframe, market_state, chart_pattern, is_bullish_action)
                        if trade_prices["buy"] is None and trade_prices["sell"] is None:
                            self.logger.error("Hit detected but no prices calculated for %s (%s): pattern=%s, candlestick=%s, market_state=%s",
                                             symbol, timeframe, pattern_name, candlestick_name, market_state)
                        entry_signal = {
                            "chart_pattern": pattern_name,
                            "candlestick": candlestick_name,
                            "candlestick_type": candlestick_info["type"],
                            "indicators_met": indicators_met,
                            "trade_prices": trade_prices
                        }
                        entry_signals.append(entry_signal)
                        log_message = (
                            "Hit detected for %s (%s): Market State=%s, Chart Pattern=%s, Implication=%s, "
                            "Candlestick=%s, Indicators Met=%s, Trade Prices=%s"
                        )
                        if market_state == "sideways":
                            log_message += " (Sideways market)"
                        elif market_state == "downtrend":
                            log_message += " (Downtrend market)"
                        self.logger.info(
                            log_message,
                            symbol, timeframe, market_state, pattern_name, implication,
                            candlestick_name, indicators_met, trade_prices
                        )
                    else:
                        self.logger.debug("No indicators met for candlestick %s in pattern %s for %s (%s)",
                                         candlestick_name, pattern_name, symbol, timeframe)

            self.logger.info("Entry signals for %s (%s): %s", symbol, timeframe, entry_signals)
            return entry_signals
        except Exception as e:
            self.logger.error("Error checking candlestick confirmations for %s (%s): %s", symbol, timeframe, str(e))
            raise

    async def run(self, interval: int = 60) -> None:
        """
        Periodically monitor market states, chart patterns, and candlestick confirmations.
        """
        self.logger.info("Starting market monitoring with interval %d seconds", interval)
        while True:
            try:
                try:
                    portfolio_status = await self.get_portfolio_status()
                    self.logger.info("Portfolio Status: %s", portfolio_status)
                except Exception as e:
                    self.logger.error("Failed to fetch portfolio status: %s", str(e))

                for symbol in self.symbols:
                    daily_state = self.get_market_state(symbol, '1d')
                    self.logger.info("1-day market state for %s: %s", symbol, daily_state)

                    for timeframe in ['6h', '1h']:
                        chart_patterns = self.check_chart_patterns(symbol, timeframe, daily_state)
                        if chart_patterns:
                            self.logger.info("Chart patterns for %s (%s): %s", symbol, timeframe, chart_patterns)
                            entry_timeframe = '1h' if timeframe == '6h' else '15m'
                            if entry_timeframe in self.timeframes:
                                entry_signals = self.check_candlestick_confirmations(symbol, entry_timeframe, chart_patterns, daily_state)
                                if entry_signals:
                                    self.logger.info("Entry signals for %s (%s): %s", symbol, entry_timeframe, entry_signals)

                await asyncio.sleep(interval)
            except KeyboardInterrupt:
                self.logger.info("Market monitoring interrupted by user")
                break