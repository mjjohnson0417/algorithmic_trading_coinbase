README_indicatorcalculator.txt

Technical Indicator Calculator

Overview:
The IndicatorCalculator class in indicator_calculator.py is a Python-based tool for computing technical indicators used in trading strategies, specifically for the HBAR/USDT pair on Binance.US. It calculates indicators such as EMA, RSI, ADX, ATR, and MACD from 1-hour and 1-day kline data, as well as timing indicators from ticker and order book data. These indicators support market state analysis and grid trading decisions in the GridManager.

Purpose:

    Calculate 1-hour and 1-day technical indicators (EMA12/26, RSI14, ADX14, ATR14, MACD) from kline data.
    Compute timing indicators (bid-ask spread, order book imbalance, EMA5, ATR14, volume surge ratio) from ticker and order book data.
    Validate input data and handle errors gracefully with default values.
    Provide debug logging for troubleshooting and indicator verification.
    Support GridManager and StateManager for market trend analysis and order placement.

Requirements:

    Python 3.8 or higher.
    Packages: pandas, numpy.
    Input Data: pandas DataFrames with specific columns (klines: timestamp, open, high, low, close, volume; ticker: last_price, best_bid, best_ask, last_qty; order book: price, quantity, side).
    Linux system (assumed for compatibility with related project files).

Setup:

    Ensure indicator_calculator.py is in the project directory (e.g., /home/jason/algorithmic_trading_binance/hbar_mainnet_bot/).
    Install dependencies: pip install pandas numpy
    Verify integration with other components:
        DataManager (data_manager.py) for kline, ticker, and order book data.
        GridManager (grid_manager.py) for ATR in grid level calculations.
        StateManager (state_manager.py, not provided) for market state analysis.
    Configure logging in the main application (e.g., via RotatingFileHandler in hbarGridBotMainNet.py) to capture debug logs if enabled.

Usage:
The IndicatorCalculator class is instantiated and used programmatically within a trading bot, typically called by GridManager or StateManager to compute indicators for trading decisions.

Instantiation:
from indicator_calculator import IndicatorCalculator
indicator_calculator = IndicatorCalculator(debug=False)

Key Methods:

    calculate_1h_indicators(klines_1h, symbol): Compute 1-hour indicators from kline data.
    calculate_1d_indicators(klines_1d, symbol): Compute 1-day indicators from kline data.
    calculate_timing_indicators(ticker, order_book, symbol): Compute timing indicators from ticker and order book data.

Example:
from indicator_calculator import IndicatorCalculator
from data_manager import DataManager
Assume DataManager is set up

data_manager = DataManager(debug=True)
indicator_calculator = IndicatorCalculator(debug=True)
symbol = 'HBARUSDT'
klines_1h = data_manager.get_buffer('klines_1h')
indicators = indicator_calculator.calculate_1h_indicators(klines_1h, symbol)
print(indicators)

Workflow:

    Initialize IndicatorCalculator with optional debug mode.
    Validate input DataFrames:
        Klines: Require 26+ rows, columns [timestamp, open, high, low, close, volume], no NaN values.
        Ticker: Require 14+ rows for ATR14, columns [last_price, best_bid, best_ask, last_qty].
        Order book: Require price, quantity, side columns for bid/ask analysis.
    Compute indicators:
        1h/1d: EMA12/26, RSI14, ADX14, ATR14, MACD (macd, macd_signal, macd_hist).
        Timing: bid-ask spread, order book imbalance, EMA5, ATR14, volume surge ratio.
    Handle errors:
        Return empty dict for klines or default values for timing indicators if data is invalid.
        Log warnings/errors and print to console for visibility.
    Return indicator dictionaries for use in trading logic (e.g., GridManager, StateManager).

File Structure:

    /home/jason/algorithmic_trading_binance/hbar_mainnet_bot/
        indicator_calculator.py: Indicator calculation logic
        data_manager.py: Data management logic (required for input data)
        grid_manager.py: Grid trading logic (uses ATR)
        state_manager.py: Market state logic (not provided, assumed)
        Other project files (e.g., hbarGridBotMainNet.py, exchange_connection.py)

Output:

    Indicator Dictionaries:
        1h/1d indicators: {'ema12': float, 'ema26': float, 'rsi14': float, 'adx14': float, 'atr14': float, 'macd': float, 'macd_signal': float, 'macd_hist': float}
        Timing indicators: {'bid_ask_spread': float, 'order_book_imbalance': float, 'ema5': float, 'atr14': float, 'volume_surge_ratio': float, 'best_ask': float}
        Empty dict or defaults (e.g., {'bid_ask_spread': 0.0, ...}) for invalid inputs.
    Logs:
        Debug logs (if enabled) for input validation, indicator values, and errors.
        Example: "1-hour indicators for HBARUSDT: {'ema12': 0.105, 'ema26': 0.104, ...}"
        Warnings/errors printed to console and logged (e.g., "WARNING: Empty 1-hour klines buffer for HBARUSDT").
    Console Output:
        Warnings for invalid data (e.g., insufficient rows, missing columns, NaN values).
        Errors for calculation failures.

Notes:

    Used by GridManager for ATR in grid level calculations and StateManager for trend analysis.
    Requires valid DataManager buffers (klines_1h, klines_1d, ticker, order_book).
    Debug mode provides detailed logging but requires logging configuration in the main application.
    Default values ensure trading continuity if data is invalid (e.g., RSI=50.0, ATR=0.0001).
    Timing indicators prioritize ticker data for bid-ask spread, falling back to order book if invalid.

Limitations:

    Specific to HBAR/USDT; assumes DataManager provides compatible data formats.
    Requires 26+ kline rows for reliable indicators, limiting use with sparse data.
    No support for custom indicator periods or additional indicators.
    Timing indicators assume specific ticker/order book columns, which may not always be available.
    Logging depends on external configuration (e.g., via hbarGridBotMainNet.py).

Troubleshooting:

    Empty/invalid indicators: Check DataManager buffers for sufficient rows and required columns.
    NaN values: Verify kline data integrity; ensure DataManager handles missing data.
    No logs: Configure logging in the main application (e.g., RotatingFileHandler).
    Calculation errors: Enable debug mode to inspect input data and error details.
    Missing dependencies: Install pandas and numpy.

Future Improvements:

    Add support for customizable indicator periods and additional indicators (e.g., Bollinger Bands).
    Implement persistent caching of indicator results to reduce recomputation.
    Enhance input validation with data interpolation for missing values.
    Support multiple trading pairs with symbol-specific configurations.
    Add unit tests for indicator calculations.

License:
For personal use, provided as-is. Comply with Binance.US API terms.

Created: May 11, 2025