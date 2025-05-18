README_exchangeconnection.txt

Binance.US Exchange Connection

Overview:
The ExchangeConnection class in exchange_connection.py is a Python-based tool for establishing connections to the Binance.US exchange using both REST and WebSocket APIs. It initializes connections with provided API keys and secrets, enabling other components (e.g., DataManager) to fetch market data or execute trades. The class uses the CCXT library for interaction with the exchange.

Purpose:

    Initialize REST and WebSocket connections to Binance.US with secure credentials.
    Verify connection status for REST and WebSocket APIs.
    Provide a reusable interface for market data retrieval and trading operations.
    Support integration with trading systems (e.g., data_manager.py, backtester.py).

Requirements:

    Python 3.8 or higher.
    Packages: ccxt, ccxt.async_support.
    Binance.US API keys and secrets (REST and WebSocket) provided by the user.
    Internet connection for API access.
    Linux system (assumed for compatibility with related project files).

Setup:

    Ensure exchange_connection.py is in the project directory (e.g., /home/jason/algorithmic_trading_binance/hbar_mainnet_bot/).
    Install dependencies: pip install ccxt ccxt.async_support
    Obtain Binance.US API keys and secrets:
        Create REST and WebSocket API credentials via the Binance.US dashboard.
        Store credentials securely (e.g., in a .env file or configuration managed by key_loader.py).
    Verify related project files (e.g., data_manager.py, key_loader.py) are available and compatible.

Usage:
The ExchangeConnection class is instantiated and used programmatically within a larger trading system, typically in conjunction with other components like DataManager or Backtester.

Instantiation:
from exchange_connection import ExchangeConnection
exchange = ExchangeConnection(api_key_rest, secret_rest, api_key_ws, secret_ws)

Key Methods:

    connect(): Establishes both REST and WebSocket connections.
    check_rest_connection(): Returns True if REST connection is active.
    check_websocket_connection(): Returns True if WebSocket connection is active (for CCXT manual use).

Example:
import asyncio
from exchange_connection import ExchangeConnection
async def main():
exchange = ExchangeConnection(
api_key_rest='your_rest_api_key',
secret_rest='your_rest_secret',
api_key_ws='your_ws_api_key',
secret_ws='your_ws_secret'
)
await exchange.connect()
if exchange.check_rest_connection():
print("REST API connected")
if exchange.check_websocket_connection():
print("WebSocket API connected")
asyncio.run(main())

Workflow:

    Initialize ExchangeConnection with REST and WebSocket API keys and secrets.
    Call connect() to establish connections:
        REST: Connects via CCXT binanceus, loads markets.
        WebSocket: Initializes CCXT binanceus for manual use, loads markets.
    Verify connections using check_rest_connection() and check_websocket_connection().
    Use the rest_exchange object for REST API calls (e.g., fetch_ohlcv in DataManager).
    Use the ws_exchange object for manual WebSocket operations (if implemented).
    Handle errors via logging for connection failures.

File Structure:

    /home/jason/algorithmic_trading_binance/hbar_mainnet_bot/
        exchange_connection.py: Main exchange connection logic
        data_manager.py: Data management logic (uses ExchangeConnection)
        backtester.py: Backtesting logic (may use ExchangeConnection)
        key_loader.py: API key loader (not provided, assumed for credential management)
        Other project files (e.g., run_backtest.py)

Output:

    Connection Objects:
        rest_exchange: CCXT binanceus instance for REST API operations.
        ws_exchange: CCXT binanceus instance for WebSocket operations (manual use).
    Logs:
        Info logs for successful connections (e.g., "Successfully connected to Binance.us REST API").
        Error logs for connection failures (e.g., "Error connecting to Binance.us REST API: ...").
        Logs printed to console or configured log file (via logging setup in calling code).

Notes:

    Requires valid Binance.US API keys and secrets; invalid credentials raise ValueError.
    WebSocket connection is initialized but marked for "manual use" (not directly used in provided code).
    CCXT handles rate limits internally; no additional delays implemented.
    Assumes integration with key_loader.py for credential loading (not provided).
    Logging requires configuration in the calling code (e.g., via data_manager.py or backtester.py).

Limitations:

    Specific to Binance.US; modify CCXT exchange (binanceus) for other exchanges.
    WebSocket functionality is initialized but not actively used in provided code.
    No automatic reconnection logic for dropped connections.
    Dependent on external credential management (e.g., key_loader.py).
    No data validation for API keys/secrets beyond presence check.

Troubleshooting:

    Connection errors: Verify API keys/secrets and Binance.US API status.
    Missing CCXT: Install ccxt and ccxt.async_support packages.
    Invalid credentials: Ensure keys/secrets match Binance.US dashboard settings.
    Logging issues: Check logging configuration in calling code (e.g., data_manager.py).

Future Improvements:

    Add automatic reconnection for REST and WebSocket APIs.
    Implement active WebSocket data streaming (e.g., integrate with data_manager.py).
    Support multiple exchanges via configurable CCXT instances.
    Add credential validation (e.g., test API key with a ping).
    Include timeout handling for connection attempts.

License:
For personal use, provided as-is. Comply with Binance.US API terms.

Created: May 11, 2025