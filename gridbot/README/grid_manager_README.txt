README_gridmanager.txt

HBAR/USDT Grid Trading Manager

Overview:
The GridManager class in grid_manager.py is a Python-based tool for managing a grid trading strategy for the HBAR/USDT pair on Binance.US. It initializes and maintains a grid of price levels, places and monitors buy/sell orders, and adjusts trading behavior based on market states (long-term and short-term trends). It integrates with DataManager, IndicatorCalculator, OrderOperations, and StateManager to execute the strategy.

Purpose:

    Calculate and maintain grid price levels using ATR for spacing.
    Monitor market states (uptrend, downtrend, sideways) to adjust trading.
    Place and manage limit buy/sell orders at grid levels.
    Handle downtrend conditions by canceling orders or selling assets.
    Prune inactive orders and reset the grid when prices exceed the top level.
    Log trading activity for debugging and analysis.

Requirements:

    Python 3.8 or higher.
    Packages: pandas, asyncio, logging.handlers, pathlib (standard library).
    Components: DataManager, IndicatorCalculator, OrderOperations, StateManager (from respective modules).
    Binance.US API access via OrderOperations for order management.
    Linux system (assumed for compatibility with related project files).

Setup:

    Ensure grid_manager.py is in the project directory (e.g., /home/jason/algorithmic_trading_binance/hbar_mainnet_bot/).
    Install dependencies: pip install pandas Note: Other dependencies (e.g., ccxt) may be required by DataManager or OrderOperations.
    Verify required components:
        DataManager (data_manager.py) for market data.
        IndicatorCalculator (indicator_calculator.py) for ATR and indicators.
        OrderOperations (order_operations.py, not provided) for order execution.
        StateManager (state_manager.py, not provided) for market state analysis.
    Configure logging in the main application (e.g., set up RotatingFileHandler for GridBot logger).
    Ensure Binance.US API keys are configured in OrderOperations or related modules (e.g., via key_loader.py).

Usage:
The GridManager class is instantiated and run programmatically within a trading bot application. It is not run standalone but integrated with other components to manage grid trading.

Instantiation:
from grid_manager import GridManager
grid_manager = GridManager(data_manager, indicator_calculator, order_operations, symbol, debug)

Parameters:

    data_manager: DataManager instance for market data access.
    indicator_calculator: IndicatorCalculator instance for technical indicators.
    order_operations: OrderOperations instance for order management.
    symbol: Trading pair (e.g., 'HBARUSDT').
    debug: Boolean to enable verbose logging (default: False).

Example:
import asyncio
from grid_manager import GridManager
from data_manager import DataManager
Assume other components are defined

async def main():
data_manager = DataManager(debug=True)
indicator_calculator = IndicatorCalculator()  # Placeholder
order_operations = OrderOperations()  # Placeholder
symbol = 'HBARUSDT'
grid_manager = GridManager(data_manager, indicator_calculator, order_operations, symbol, debug=True)
await grid_manager.run(interval=30)
asyncio.run(main())

Workflow:

    Initialize GridManager with required components, symbol, and debug mode.
    Set up logging with GridBot logger (debug level if enabled).
    Wait for ticker buffer population (up to 10 attempts, 5s delay).
    Calculate initial grid levels (20 levels, ATR-based spacing) if not set.
    Run main loop (every 30 seconds by default):
        Fetch exchange orders (last 24 hours).
        Check market states (long-term/short-term) to set trading flags (lttrade, sttrade).
        Handle downtrends: cancel buy orders (short-term) or all orders and sell assets (long-term).
        Check for grid reset (30 ticks above top level) and recalculate levels if needed.
        If trading is active (lttrade and sttrade True):
            Prune inactive orders from the orders dictionary.
            Update orders dictionary with desired levels (5 below, 1 above current price).
            Match orders dictionary to exchange orders, canceling stray orders.
            Calculate order value (75% of open orders value + USDT balance, divided by grid levels).
            Place buy/sell orders at grid levels, respecting buy-first dependency.
    Log all actions (order placements, cancellations, state changes) for debugging.

File Structure:

    /home/jason/algorithmic_trading_binance/hbar_mainnet_bot/
        grid_manager.py: Main grid trading logic
        data_manager.py: Data management logic (required)
        indicator_calculator.py: Indicator calculation logic (required, not provided)
        order_operations.py: Order management logic (required, not provided)
        state_manager.py: Market state logic (required, not provided)
        Other project files (e.g., exchange_connection.py, graceful_shutdown.py)

Output:

    Orders Dictionary:
        In-memory dictionary mapping grid levels to order states (buy_id, sell_id, buy/sell_locked, buy/sell_state).
        Example: {0.10000: {'buy_id': '123', 'buy_locked': True, 'buy_state': 'open', 'sell_id': None, ...}}
    Grid Levels:
        List of 20 price levels (e.g., [0.09500, 0.09750, ..., 0.10500]) based on ATR and current price.
    Logs:
        Debug logs for grid calculations, order placements, market states, and errors.
        Info logs for key actions (e.g., "Placed buy order at 0.10000: ID=123, quantity=100.000000").
        Error logs for failures (e.g., "Error placing buy order: ...").
        Logs printed to console or file (via RotatingFileHandler if configured).
    Trading Actions:
        Buy/sell orders placed or canceled via OrderOperations.
        Assets sold in long-term downtrends.

Notes:

    Requires IndicatorCalculator, OrderOperations, and StateManager (not provided), which may break functionality if missing.
    Grid levels use ATR (period=14, multiplier=2.0) with minimum spacing (0.2% + 1% of price).
    Orders dictionary maintains 5 buy levels below and 1 sell level above the current price.
    Downtrend handling: cancels buy orders (short-term) or all orders and sells assets (long-term).
    Grid reset occurs if 30 ticks exceed the top grid level, recalculating levels.
    Logging requires external configuration (e.g., RotatingFileHandler in main application).

Limitations:

    Specific to HBAR/USDT on Binance.US; modify symbol for other pairs.
    Dependent on missing components (IndicatorCalculator, OrderOperations, StateManager).
    No persistent storage for orders dictionary or grid levels.
    Fixed grid parameters (20 levels, ATR multiplier=2.0) are not configurable.
    Assumes valid ticker data; empty/invalid buffers halt trading.
    No slippage or fee modeling in order value calculations.

Troubleshooting:

    Missing components: Verify IndicatorCalculator, OrderOperations, and StateManager are available.
    Empty ticker buffer: Check DataManager setup and network connectivity.
    Order placement failures: Ensure OrderOperations is correctly configured with API access.
    Invalid grid levels: Confirm 1h klines buffer has valid data and ATR is calculable.
    No logs: Set up logging with RotatingFileHandler in the main application.

Future Improvements:

    Add persistent storage for orders and grid levels (e.g., CSV or database).
    Support configurable grid parameters (levels, ATR multiplier, spacing).
    Implement slippage and dynamic fee calculations.
    Add support for multiple trading pairs.
    Enhance error recovery for failed order placements or data fetches.
    Provide visualization of grid levels and orders.

License:
For personal use, provided as-is. Comply with Binance.US API terms.

Created: May 11, 2025