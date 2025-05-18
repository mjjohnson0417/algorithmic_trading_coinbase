README_hbargridbotmainnet.txt

HBAR/USDT Grid Trading Bot Main Script

Overview:
The hbarGridBotMainNet.py script is the main entry point for a Python-based grid trading bot for the HBAR/USDT pair on Binance.US. It initializes all necessary components (ExchangeConnection, DataManager, IndicatorCalculator, OrderOperations, GridManager, GracefulShutdown), sets up logging, loads API keys, and runs the grid trading strategy. The bot cancels existing open buy orders on startup, preloads historical data, and manages real-time trading with graceful shutdown handling.

Purpose:

    Orchestrate the grid trading bot by initializing and connecting all components.
    Load Binance.US API keys securely using KeyLoader.
    Configure logging to file and console for monitoring and debugging.
    Cancel open limit buy orders before starting to ensure a clean state.
    Preload historical kline data and subscribe to real-time ticker updates.
    Run the GridManager to execute the grid trading strategy.
    Handle shutdown signals gracefully to clean up resources.

Requirements:

    Python 3.8 or higher.
    Packages: asyncio, logging.handlers, pathlib (standard library), ccxt.async_support, python-dotenv.
    Components: KeyLoader, ExchangeConnection, DataManager, IndicatorCalculator, OrderOperations, StateManager, GridManager, GracefulShutdown (from respective modules).
    Binance.US API keys stored in /home/jason/api/binance/binance_us.env.
    Linux system with write access to /home/jason/algorithmic_trading_binance/hbar_mainnet_bot/logs/.
    Internet connection for API access.

Setup:

    Place hbarGridBotMainNet.py in the project directory (e.g., /home/jason/algorithmic_trading_binance/hbar_mainnet_bot/).
    Install dependencies: pip install ccxt.async_support python-dotenv pandas Note: Additional packages may be required by IndicatorCalculator or OrderOperations.
    Configure API keys: Create /home/jason/api/binance/binance_us.env with: BINANCE_US_API_KEY=your_rest_api_key BINANCE_US_SECRET=your_rest_secret BINANCE_US_WS_API_KEY=your_ws_api_key BINANCE_US_WS_SECRET=your_ws_secret
    Ensure required components are available:
        key_loader.py
        exchange_connection.py
        data_manager.py
        indicator_calculator.py (not provided)
        order_operations.py (not provided)
        state_manager.py (not provided)
        grid_manager.py
        graceful_shutdown.py
    Create logs directory: mkdir -p /home/jason/algorithmic_trading_binance/hbar_mainnet_bot/logs

Usage:
Run the script directly to start the grid trading bot:
python hbarGridBotMainNet.py

The script runs indefinitely until interrupted (e.g., Ctrl+C, SIGTERM), executing the grid trading strategy every 30 seconds.

Example:
cd /home/jason/algorithmic_trading_binance/hbar_mainnet_bot
python hbarGridBotMainNet.py

Workflow:

    Set up logging with RotatingFileHandler (5MB per file, 5 backups) and console output.
    Load API keys using KeyLoader from /home/jason/api/binance/binance_us.env.
    Initialize ExchangeConnection with REST and WebSocket credentials and connect to Binance.US.
    Instantiate bot components:
        DataManager (debug=False) for market data.
        IndicatorCalculator (debug=False) for technical indicators.
        OrderOperations (dry_run=False) for order management.
        GridManager (debug=True) for grid trading logic.
        GracefulShutdown for handling termination signals.
    Cancel all open limit buy orders to start with a clean slate.
    Preload 1-day and 1-hour kline data for HBAR/USDT.
    Subscribe to real-time ticker updates via WebSocket.
    Run GridManager with a 30-second interval to execute the trading strategy.
    On shutdown (Ctrl+C, SIGTERM):
        Cancel ticker subscription.
        Close exchange connections.
        Log shutdown completion.

File Structure:

    /home/jason/algorithmic_trading_binance/hbar_mainnet_bot/
        hbarGridBotMainNet.py: Main bot script
        key_loader.py: API key loader
        exchange_connection.py: Exchange connection logic
        data_manager.py: Data management logic
        indicator_calculator.py: Indicator calculation logic (not provided)
        order_operations.py: Order management logic (not provided)
        state_manager.py: Market state logic (not provided)
        grid_manager.py: Grid trading logic
        graceful_shutdown.py: Shutdown handling logic
        logs/
            grid_bot.log: Main log file
            grid_bot.log.1, grid_bot.log.2, ...: Rolled-over log files
        /home/jason/api/binance/binance_us.env: API key file

Output:

    Logs:
        Info logs for startup, order cancellations, component initialization, and shutdown.
        Error logs for failures (e.g., "Failed to load API keys", "Critical error in grid bot: ...").
        Debug logs from GridManager (enabled) for detailed trading actions.
        Logs saved to logs/grid_bot.log (rotated at 5MB) and printed to console.
        Example: "2025-05-11 10:00:00 - INFO - Cancelled 2 open limit buy orders before starting the grid bot."
    Trading Actions:
        Open limit buy orders canceled on startup.
        Buy/sell orders placed by GridManager based on market conditions.
        Assets sold in downtrends (via GridManager).
    Data:
        Preloaded 1d/1h klines and real-time ticker data stored in DataManager buffers.

Notes:

    Hardcoded paths (/home/jason/) require modification for other systems.
    Requires missing components (IndicatorCalculator, OrderOperations, StateManager), which may break functionality if unavailable.
    Logging is configured with RotatingFileHandler for persistent, size-limited logs.
    Dry-run mode is disabled (dry_run=False), so orders are executed on the exchange.
    Graceful shutdown ensures cleanup of orders, WebSocket connections, and tasks.
    Ticker subscription runs concurrently with the main trading loop.

Limitations:

    Specific to HBAR/USDT on Binance.US; modify symbol for other pairs.
    Dependent on missing components (IndicatorCalculator, OrderOperations, StateManager).
    Hardcoded .env file path (/home/jason/api/binance/binance_us.env).
    No configuration options (e.g., symbol, interval, debug mode) via command-line arguments.
    Assumes sufficient USDT balance for trading; no balance checks on startup.
    No persistent storage for trading state beyond logs.

Troubleshooting:

    API key errors: Verify /home/jason/api/binance/binance_us.env contents and permissions.
    Missing components: Ensure IndicatorCalculator, OrderOperations, and StateManager are available.
    Log file issues: Check write permissions for logs/ directory.
    Connection failures: Confirm internet access and Binance.US API status.
    No trading activity: Verify DataManager ticker buffer is populated and GridManager debug logs.

Future Improvements:

    Add command-line arguments for symbol, interval, and debug mode.
    Support multiple trading pairs.
    Implement balance checks before starting the bot.
    Use relative paths or configuration files for flexibility.
    Add persistent storage for trading state (e.g., database).
    Enhance error recovery for component initialization failures.

License:
For personal use, provided as-is. Comply with Binance.US API terms.

Created: May 11, 2025