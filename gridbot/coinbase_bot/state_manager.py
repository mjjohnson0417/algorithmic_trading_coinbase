# state_manager.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, Optional
from indicator_calculator import IndicatorCalculator
from data_manager import DataManager

class StateManager:
    def __init__(self, data_manager: DataManager, indicator_calculator: IndicatorCalculator, symbols: list, enable_logging: bool = True):
        """
        Initializes the StateManager class for determining market states for multiple symbols.

        Args:
            data_manager (DataManager): Instance of DataManager with populated buffers.
            indicator_calculator (IndicatorCalculator): Instance of IndicatorCalculator.
            symbols (list): List of trading pair symbols (e.g., ['HBAR-USDT', 'BTC-USDT']).
            enable_logging (bool): If True, enables logging to 'logs/state_manager.log'.
        """
        self.data_manager = data_manager
        self.indicator_calculator = indicator_calculator
        self.symbols = symbols
        self.state_dict: Dict[str, Dict[str, Optional[str]]] = {
            symbol: {'long_term': None, 'short_term': None} for symbol in symbols
        }

        # Set up logger
        self.logger = logging.getLogger('StateManager')
        if enable_logging:
            log_dir = Path(__file__).parent / 'logs'
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / 'state_manager.log'
            file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.WARNING)

        self.logger.debug("StateManager initialized with symbols: %s", symbols)

    def calculate_all_market_states(self) -> Dict[str, Dict[str, Optional[str]]]:
        """
        Calculates long-term (1d) and short-term (1h) market states for all symbols.

        Returns:
            Dict[str, Dict[str, Optional[str]]]: Dictionary mapping each symbol to its
                long-term and short-term market states (e.g., 'uptrend', 'downtrend', 'sideways', or None).
        """
        # Calculate all indicators once
        all_indicators = self.indicator_calculator.calculate_all_indicators()

        for symbol in self.symbols:
            self.logger.debug(f"Calculating market states for {symbol}")

            # Calculate long-term (1d) market state
            long_term_state = self.get_market_state(symbol, timeframe='1d', all_indicators=all_indicators)
            self.state_dict[symbol]['long_term'] = long_term_state
            self.logger.debug(f"Long-term state for {symbol}: {long_term_state}")

            # Calculate short-term (1h) market state
            short_term_state = self.get_market_state(symbol, timeframe='1h', all_indicators=all_indicators)
            self.state_dict[symbol]['short_term'] = short_term_state
            self.logger.debug(f"Short-term state for {symbol}: {short_term_state}")

        self.logger.debug(f"All market states: {self.state_dict}")
        return self.state_dict

    def get_market_state(self, symbol: str, timeframe: str = '1d', all_indicators: Optional[Dict] = None) -> Optional[str]:
        """
        Determines the market state based on technical indicators.

        Args:
            symbol (str): Trading pair (e.g., 'HBAR-USDT').
            timeframe (str): '1d' for long-term, '1h' for short-term.
            all_indicators (Optional[Dict]): Pre-calculated indicators from calculate_all_indicators().

        Returns:
            Optional[str]: 'uptrend', 'downtrend', 'sideways', or None if data is insufficient.
        """
        try:
            if timeframe not in ['1h', '1d']:
                raise ValueError("Invalid timeframe. Use '1d' or '1h'.")

            # Use provided indicators or calculate them
            if all_indicators is None:
                all_indicators = self.indicator_calculator.calculate_all_indicators()

            # Get indicators for the symbol and timeframe
            indicators = all_indicators.get(symbol, {}).get(timeframe, {})

            if not indicators:
                self.logger.warning(f"No indicators for {symbol} on {timeframe} timeframe.")
                return None

            ema12 = indicators.get('ema12', 0.0)
            ema26 = indicators.get('ema26', 0.0)
            rsi14 = indicators.get('rsi14', 50.0)
            adx14 = indicators.get('adx14', 0.0)

            if adx14 < 20:
                return "sideways"
            if ema12 > ema26 and rsi14 < 70 and adx14 >= 20:
                return "uptrend"
            if ema12 < ema26 and rsi14 < 30 and adx14 >= 25:  # Stricter for short-term downtrend
                return "downtrend"
            return "sideways"

        except Exception as e:
            self.logger.error(f"Error determining market state for {symbol} on {timeframe}: {e}")
            return None