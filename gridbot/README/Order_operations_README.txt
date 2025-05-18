README_orderoperations.txt

Binance.US Order Management

Overview:
The OrderOperations class in order_operations.py is a Python-based tool for managing trading orders on Binance.US, specifically for the HBAR/USDT pair. It provides methods to create, cancel, and fetch limit and market orders, as well as retrieve account balances, using the CCXT library. The class supports dry-run mode for simulated trading and maintains an in-memory record of active orders for tracking.

Purpose:

    Create limit buy/sell and market sell orders on Binance.US.
    Cancel individual or all buy/sell orders.
    Fetch open and historical orders for the trading pair.
    Retrieve USDT and base asset (e.g., HBAR) balances.
    Sell all base assets in market conditions (e.g., downtrends).
    Support dry-run mode for testing without real trades.
    Log order operations for debugging and monitoring.

Requirements:

    Python 3.8 or higher.
    Packages: ccxt.async_support.
    Components: ExchangeConnection (exchange_connection.py) for API access.
    Binance.US API credentials configured via ExchangeConnection.
    Linux system (assumed for compatibility with related project files).
    Logging configured in the calling application to capture logs.

Setup:

    Ensure order_operations.py is in the project directory (e.g., /home/jason/algorithmic_trading_binance/hbar_mainnet_bot/).
    Install dependencies: pip install ccxt.async_support
    Verify integration with other components:
        ExchangeConnection (exchange_connection.py) for REST API access.
        GridManager (grid_manager.py) for order placement and cancellation.
        GracefulShutdown (graceful_shutdown.py) for order cleanup.
        hbarGridBotMainNet.py for main bot orchestration.
    Configure Binance.US API keys via KeyLoader and ExchangeConnection (see key_loader.py, exchange_connection.py).
    Set up logging in the main application (e.g., RotatingFileHandler in hbarGridBotMainNet.py) to capture order logs.

Usage:
The OrderOperations class is instantiated and used programmatically within the trading bot, typically called by GridManager for trading operations or GracefulShutdown for cleanup.

Instantiation:
from order_operations import OrderOperations
order_ops = OrderOperations(exchange, symbol, dry_run, debug)

Parameters:

    exchange: ExchangeConnection instance with REST API access.
    symbol: Trading pair (e.g., 'HBAR/USDT').
    dry_run: Boolean to enable simulated trading (default: False).
    debug: Boolean to enable verbose logging (default: False).

Key Methods:

    create_limit_buy(price, quantity): Create a limit buy order.
    create_limit_sell(price, quantity): Create a limit sell order.
    create_market_sell(quantity): Create a market sell order.
    cancel_order(order_id): Cancel a specific order.
    cancel_all_buy_orders(): Cancel all buy orders.
    cancel_all_sell_orders(): Cancel all sell orders.
    fetch_all_orders(start_time, end_time): Fetch all orders (filtered by time).
    fetch_open_orders(): Fetch currently open orders.
    get_usdt_balance(): Retrieve free USDT balance.
    get_base_asset_balance(base_asset): Retrieve free base asset balance.
    sell_all_assets(): Market sell all base asset balance.

Example:
from order_operations import OrderOperations
from exchange_connection import ExchangeConnection
Assume ExchangeConnection is set up

exchange = ExchangeConnection(api_key_rest, secret_rest, api_key_ws, secret_ws)
order_ops = OrderOperations(exchange, 'HBAR/USDT', dry_run=True, debug=True)
order_id = order_ops.create_limit_buy(price=0.100, quantity=100)
print(f"Created order: {order_id}")

Workflow:

    Initialize OrderOperations with ExchangeConnection, symbol, dry-run mode, and debug mode.
    Maintain active_orders dictionary to track order details (ID, type, price, quantity, symbol, status).
    In dry-run mode:
        Simulate order creation/cancellation with mock IDs (e.g., "dry_run_buy_0.1_100").
        Use simulated USDT balance (1000.0) and zero base asset balance.
        Log actions without interacting with the exchange.
    In live mode:
        Create limit/market orders via CCXT's rest_exchange methods.
        Cancel orders using CCXT's cancel_order method.
        Fetch orders and balances using CCXT's fetch_orders and fetch_balance methods.
        Update active_orders with new or canceled orders.
    Log all actions (success, errors) with debug details if enabled.
    Handle errors (authentication, network, exchange) by logging and returning None or empty lists.

File Structure:

    /home/jason/algorithmic_trading_binance/hbar_mainnet_bot/
        order_operations.py: Order management logic
        exchange_connection.py: Exchange connection logic (required)
        grid_manager.py: Grid trading logic (uses OrderOperations)
        graceful_shutdown.py: Shutdown handling logic (uses OrderOperations)
        hbarGridBotMainNet.py: Main bot script (orchestrates OrderOperations)
        Other project files (e.g., data_manager.py, indicator_calculator.py)

Output:

    Order IDs:
        String IDs for created orders (e.g., "123456" or "dry_run_buy_0.1_100").
        None for failed order creations.
    Order Lists:
        fetch_all_orders: List of dictionaries with keys id, type, price, quantity, symbol, status.
        fetch_open_orders: Subset of orders with status 'open'.
        Empty list for errors or no orders.
    Balances:
        get_usdt_balance: Float (e.g., 1000.0 in dry-run, actual USDT balance in live mode).
        get_base_asset_balance: Float (e.g., 0.0 in dry-run, actual HBAR balance in live mode).
    Logs:
        Info logs for order creation/cancellation (e.g., "Created limit buy order: HBAR/USDT at 0.1 for 100").
        Debug logs (if enabled) for detailed order data and balance fetches.
        Error logs for failures (e.g., "Error creating limit buy order for HBAR/USDT: ...").
        Logs saved via main application’s logging setup (e.g., logs/grid_bot.log).

Notes:

    Dry-run mode simulates trading without API calls, using a fixed USDT balance (1000.0).
    Active_orders dictionary tracks orders in memory but is not persisted across sessions.
    Only limit orders are fetched/formatted; market orders may require additional handling.
    Error handling covers CCXT-specific exceptions (authentication, network, exchange).
    Logging requires external configuration (e.g., via hbarGridBotMainNet.py).
    Assumes ExchangeConnection provides a valid rest_exchange object.

Limitations:

    Specific to HBAR/USDT; modify symbol for other pairs.
    Dry-run balance is fixed (1000.0 USDT, 0.0 base asset) and not configurable.
    No persistent storage for active_orders across bot restarts.
    Limited to limit and market sell orders; no support for stop-loss or other order types.
    No validation of price/quantity precision against exchange requirements.
    Assumes sufficient balance for orders without pre-checks.

Troubleshooting:

    Order creation failures: Verify API credentials in ExchangeConnection and Binance.US API status.
    Empty order lists: Check symbol format ('HBAR/USDT') and time range in fetch_all_orders.
    Balance errors: Ensure ExchangeConnection is properly initialized and API keys are valid.
    No logs: Configure logging in the main application (e.g., RotatingFileHandler).
    Dry-run issues: Confirm dry_run=True and check active_orders dictionary in logs.

Future Improvements:

    Add persistent storage for active_orders (e.g., database or file).
    Support configurable dry-run balances and order validation.
    Implement order precision checks based on exchange rules.
    Add support for additional order types (e.g., stop-loss, take-profit).
    Enhance error recovery with retries for network/exchange errors.
    Provide order status polling for real-time updates.

License:
For personal use, provided as-is. Comply with Binance.US API terms.

Created: May 11, 2025