README_datamanager.txt

HBAR/USDT Data Manager

Overview:
The DataManager class in data_manager.py is a Python-based tool for fetching and managing real-time and historical market data for the HBAR/USDT trading pair on Binance.US. It uses REST API and WebSocket connections to preload and update kline data (1-minute, 1-hour, 1-day), order book (Level 2 depth), and ticker data, storing them in pandas DataFrames for use in trading strategies.

Purpose:

    Preload historical klines (1m, 1h, 1d) using Binance.US REST API.
    Periodically check for new 1h and 1d klines via REST API.
    Subscribe to real-time 1m klines, order book, and ticker updates via WebSocket.
    Maintain in-memory DataFrame buffers for efficient data access.
    Provide debug logging for troubleshooting and data inspection.

Requirements:

    Python 3.8 or higher.
    Packages: pandas, websockets, ccxt.async_support (plus dependencies for exchange_connection.py).
    Binance.US API keys (for REST API access) configured in exchange_connection.py.
    Internet connection for REST API and WebSocket access.
    Linux system (assumed for compatibility with related project files).

Setup:

    Ensure data_manager.py is in the project directory (e.g., /home/jason/algorithmic_trading_binance/hbar_mainnet_bot/).
    Install dependencies: pip install pandas websockets ccxt.async_support Note: Additional packages may be needed for exchange_connection.py.
    Configure Binance.US API keys in the environment used by ExchangeConnection (refer to exchange_connection.py documentation).
    Verify exchange_connection.py is available and correctly set up for REST and WebSocket connections.

Usage:
The DataManager class is instantiated and used programmatically within a larger trading system. It is not run standalone but integrated with other components (e.g., a trading bot).

Instantiation:
from data_manager import DataManager
data_manager = DataManager(debug=True)

Key Methods:

    preload_1m_klines(symbol, exchange, minutes=60): Preload 60 minutes of 1m klines.
    preload_1h_klines(symbol, exchange, hours=72): Preload 72 hours of 1h klines.
    preload_1d_klines(symbol, exchange, days=60): Preload 60 days of 1d klines.
    check_new_1h_kline(symbol, exchange, interval=60): Periodically fetch new 1h klines.
    check_new_1d_kline(symbol, exchange, interval=3600): Periodically fetch new 1d klines.
    subscribe_1m_klines(symbol, exchange): Subscribe to real-time 1m klines via WebSocket.
    subscribe_order_book(symbol): Subscribe to real-time Level 2 order book via WebSocket.
    subscribe_ticker(symbol): Subscribe to real-time ticker updates via WebSocket.
    get_buffer(buffer_type): Retrieve a copy of a data buffer (klines_1m, klines_1h, klines_1d, order_book, ticker).
    close_websockets(): Cancel all WebSocket tasks.

Example:
import asyncio
from data_manager import DataManager
from exchange_connection import ExchangeConnection
async def main():
data_manager = DataManager(debug=True)
exchange = ExchangeConnection()  # Assumes proper setup
await data_manager.preload_1h_klines('HBARUSDT', exchange)
await data_manager.subscribe_ticker('HBARUSDT')
ticker_data = data_manager.get_buffer('ticker')
print(ticker_data)
await data_manager.close_websockets()
asyncio.run(main())

Workflow:

    Initialize DataManager with optional debug mode.
    Preload historical data:
        1m klines (60 unique entries) via REST API.
        1h klines (72 hours) via REST API.
        1d klines (60 days) via REST API.
    Periodically update klines:
        Check for new 1h klines every 60 seconds.
        Check for new 1d klines every 3600 seconds.
    Subscribe to real-time data via WebSocket:
        1m klines (only final klines added to buffer).
        Level 2 order book (20 bids/asks, updated every 100ms).
        Ticker (price, volume, bid/ask data).
    Store data in DataFrame buffers:
        Limit buffers to 60 (1m/1d klines), 72 (1h klines), or 1000 (order book/ticker) entries.
        Remove duplicates based on timestamps or event IDs.
    Access data using get_buffer() for trading logic.
    Close WebSocket connections when done.

File Structure:

    /home/jason/algorithmic_trading_binance/hbar_mainnet_bot/
        data_manager.py: Main data management logic
        exchange_connection.py: Exchange connection logic (not provided)
        Other project files (e.g., backtester.py, run_backtest.py)

Output:

    In-Memory DataFrames:
        klines_1m: timestamp, open, high, low, close, volume (max 60 rows).
        klines_1h: timestamp, open, high, low, close, volume (max 72 rows).
        klines_1d: timestamp, open, high, low, close, volume (max 60 rows).
        order_book: timestamp, update_id, side (bid/ask), level, price, quantity (max 1000 rows).
        ticker: timestamp, event_id, best_bid, bid_qty, best_ask, ask_qty, last_price, last_qty, volume_24h, quote_volume_24h (max 1000 rows).
    Logs:
        Debug logs (if enabled) printed to console or configured log file.
        Logs include data fetch status, buffer updates, and WebSocket events.

Notes:

    Requires exchange_connection.py for REST and WebSocket access.
    WebSocket URLs are specific to Binance.US (e.g., wss://stream.binance.us:9443).
    Buffers are trimmed to prevent memory overuse (60-1000 rows).
    Debug mode provides detailed logs of data fetches and buffer states.
    WebSocket tasks reconnect automatically after errors (5s delay).
    Data is stored in-memory, not saved to disk.

Limitations:

    Specific to HBAR/USDT on Binance.US; modify ws_symbol for other pairs.
    No persistent storage; data is lost on program termination.
    Dependent on exchange_connection.py functionality.
    WebSocket reliability depends on network stability.
    No error handling for invalid symbol formats.

Troubleshooting:

    Connection errors: Verify API keys and ExchangeConnection setup.
    Empty buffers: Check internet connectivity and symbol (HBARUSDT).
    WebSocket failures: Ensure wss://stream.binance.us:9443 is accessible.
    Missing dependencies: Install all required packages and verify exchange_connection.py.

Future Improvements:

    Add persistent storage (e.g., CSV or database) for buffers.
    Support multiple trading pairs and exchanges.
    Implement buffer size configuration.
    Add data validation (e.g., check for gaps in klines).
    Enhance error handling for WebSocket disconnections.

License:
For personal use, provided as-is. Comply with Binance.US API terms.

Created: May 11, 2025