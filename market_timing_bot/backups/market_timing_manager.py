import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List, Dict, Any
import time

class MarketTimingManager:
    """
    Base class for managing market timing decisions by integrating candlestick patterns,
    chart patterns, and market indicators. Stores market states for 1-hour and 1-day timeframes.

    Attributes:
        symbols (List[str]): List of trading pair symbols (e.g., ['HBAR-USD']).
        candlestick_patterns: Instance of CandlestickPatterns for pattern data.
        chart_patterns: Instance of ChartPatterns for pattern data.
        indicator_calculator: Instance of IndicatorCalculator for indicator data.
        enable_logging (bool): If True, enables logging to 'logs/market_timing_manager.log'.
        timeframes (List[str]): Supported timeframes for analysis.
        market_states (Dict[str, Dict[str, str]]): Maps symbols to their 1h and 1d market states.
        logger (logging.Logger): Logger instance for debugging and info messages.
    """
    def __init__(self, symbols: List[str], candlestick_patterns, chart_patterns, 
                 indicator_calculator, enable_logging: bool = True):
        """
        Initializes the MarketTimingManager with required modules, logging, and empty market states.

        Args:
            symbols (List[str]): List of trading pair symbols (e.g., ['HBAR-USD']).
            candlestick_patterns: Instance of CandlestickPatterns for pattern data.
            chart_patterns: Instance of ChartPatterns for pattern data.
            indicator_calculator: Instance of IndicatorCalculator for indicator data.
            enable_logging (bool): If True, enables logging to 'logs/market_timing_manager.log'.
        """
        self.symbols = symbols
        self.candlestick_patterns = candlestick_patterns
        self.chart_patterns = chart_patterns
        self.indicator_calculator = indicator_calculator
        self.enable_logging = enable_logging
        self.timeframes = ['1m', '5m', '15m', '1h', '6h', '1d']
        self.market_states = {}

        # Set up logger
        self.logger = logging.getLogger('MarketTimingManager')
        if enable_logging:
            log_dir = Path(__file__).parent / 'logs'
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / 'market_timing_manager.log'
            file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.WARNING)

        self.logger.debug("MarketTimingManager initialized with symbols: %s", symbols)

    def calculate_market_states(self, symbol: str) -> None:
        """
        Calculates and stores the market states (uptrend, downtrend, sideways) for a given symbol
        for 1-hour and 1-day timeframes.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').

        Raises:
            ValueError: If the symbol is not in self.symbols or indicator/pattern data is missing.
        """
        if symbol not in self.symbols:
            self.logger.error("Symbol %s not found in configured symbols: %s", symbol, self.symbols)
            raise ValueError(f"Symbol {symbol} not found in configured symbols")

        self.logger.debug("Calculating market states for symbol: %s", symbol)

        # Retrieve indicators
        all_indicators = self.indicator_calculator.calculate_all_indicators()
        indicators = all_indicators.get(symbol, {})
        if not indicators or '1h' not in indicators or '1d' not in indicators:
            self.logger.error("Missing indicator data for symbol %s", symbol)
            raise ValueError(f"Missing indicator data for symbol {symbol}")

        # Retrieve patterns
        all_patterns = self.chart_patterns.calculate_all_patterns()
        patterns = all_patterns.get(symbol, {})
        if not patterns or '1h' not in patterns or '1d' not in patterns:
            self.logger.error("Missing pattern data for symbol %s", symbol)
            raise ValueError(f"Missing pattern data for symbol {symbol}")

        # Initialize states for this symbol
        states = {}
        for timeframe in ['1h', '1d']:
            # Extract indicators
            ind = indicators[timeframe]
            ema10 = ind.get('ema10', 0.0)
            ema20 = ind.get('ema20', 0.0)
            rsi14 = ind.get('rsi14', 50.0)
            adx14 = ind.get('adx14', 0.0)
            macd_hist = ind.get('macd_hist', 0.0)

            # Log indicator values
            self.logger.debug("%s indicators for %s: ema10=%f, ema20=%f, rsi14=%f, adx14=%f, macd_hist=%f",
                             timeframe, symbol, ema10, ema20, rsi14, adx14, macd_hist)

            # Check for sideways pattern
            sideways_pattern = patterns[timeframe].get('triangle_symmetrical', False)
            if sideways_pattern:
                self.logger.debug("Sideways pattern detected for %s in %s: triangle_symmetrical", symbol, timeframe)

            # Determine market state
            if adx14 < 20 or sideways_pattern:
                self.logger.info("Market state for %s (%s): sideways (adx14=%f, sideways_pattern=%s)",
                                 symbol, timeframe, adx14, sideways_pattern)
                states[timeframe] = "sideways"
            elif ema10 > ema20 and adx14 >= 20 and rsi14 < 80 and macd_hist > 0:
                self.logger.info("Market state for %s (%s): uptrend", symbol, timeframe)
                states[timeframe] = "uptrend"
            elif ema10 < ema20 and adx14 >= 20 and rsi14 > 20 and macd_hist < 0:
                self.logger.info("Market state for %s (%s): downtrend", symbol, timeframe)
                states[timeframe] = "downtrend"
            else:
                self.logger.info("Market state for %s (%s): sideways (conflicting signals)", symbol, timeframe)
                states[timeframe] = "sideways"

        # Store states
        self.market_states[symbol] = states
        self.logger.debug("Market states for %s: %s", symbol, states)

    def run(self, interval: int = 60) -> None:
        """
        Runs a continuous loop to test market state calculations for all symbols at regular intervals.

        Args:
            interval (int): Time in seconds between iterations (default: 60).

        Notes:
            Runs indefinitely until interrupted (e.g., KeyboardInterrupt).
        """
        self.logger.info("Starting market state monitoring with interval %d seconds", interval)

        while True:
            try:
                self.logger.debug("Beginning new market state calculation iteration")
                for symbol in self.symbols:
                    try:
                        self.calculate_market_states(symbol)
                    except ValueError as e:
                        self.logger.error("Failed to calculate market states for %s: %s", symbol, str(e))
                        continue

                self.logger.info("Current market states: %s", self.market_states)
                time.sleep(interval)

            except KeyboardInterrupt:
                self.logger.info("Market state monitoring interrupted by user")
                break
            except Exception as e:
                self.logger.error("Unexpected error in run loop: %s", str(e))
                time.sleep(interval)  # Continue loop after error