README_keyloader.txt

Binance.US API Key Loader

Overview:
The KeyLoader class in key_loader.py is a Python-based tool for securely loading Binance.US API keys from a .env file. It retrieves REST and WebSocket API credentials (keys and secrets) for use in the HBAR/USDT grid trading bot, specifically for initializing the ExchangeConnection component. The class ensures all required credentials are present and logs the loading process.

Purpose:

    Load Binance.US API keys and secrets from a specified .env file.
    Validate the presence of all required credentials (REST and WebSocket keys/secrets).
    Provide logging for successful or failed key loading.
    Support secure credential management for ExchangeConnection in the trading bot.

Requirements:

    Python 3.8 or higher.
    Packages: python-dotenv.
    A .env file containing Binance.US API credentials at the specified path.
    Linux system (assumed for compatibility with related project files, e.g., /home/jason/api/binance/binance_us.env).
    Logging configured in the calling application to capture KeyLoader logs.

Setup:

    Ensure key_loader.py is in the project directory (e.g., /home/jason/algorithmic_trading_binance/hbar_mainnet_bot/).
    Install dependencies: pip install python-dotenv
    Create or verify the .env file (e.g., /home/jason/api/binance/binance_us.env) with the following format: BUS_KEY=your_rest_api_key BUS_SECRET=your_rest_secret Note: WebSocket credentials use the same BUS_KEY and BUS_SECRET in this implementation.
    Ensure file permissions restrict access to the .env file (e.g., chmod 600 /home/jason/api/binance/binance_us.env).
    Verify integration with hbarGridBotMainNet.py and ExchangeConnection, which use KeyLoader for credentials.

Usage:
The KeyLoader class is instantiated and used programmatically within the main trading bot script (e.g., hbarGridBotMainNet.py) to load API credentials before initializing ExchangeConnection.

Instantiation:
from key_loader import KeyLoader
key_loader = KeyLoader(env_path)

Key Method:

    load_keys(): Loads API keys from the .env file and returns True if successful, False otherwise.

Example:
from key_loader import KeyLoader
env_path = '/home/jason/api/binance/binance_us.env'
key_loader = KeyLoader(env_path)
if key_loader.load_keys():
print("Keys loaded:", key_loader.api_key_rest, key_loader.secret_rest)
else:
print("Failed to load keys")

Workflow:

    Initialize KeyLoader with the path to the .env file.
    Call load_keys() to:
        Load the .env file using python-dotenv.
        Retrieve BUS_KEY and BUS_SECRET for both REST and WebSocket credentials.
        Store credentials in instance variables (api_key_rest, secret_rest, api_key_ws, secret_ws).
    Validate that all credentials are present (non-empty).
    Log success ("API keys loaded successfully") or failure ("Missing BUS_KEY or BUS_SECRET in .env file").
    Return True for success or False for failure (e.g., missing keys or file errors).
    Pass credentials to ExchangeConnection for API connectivity.

File Structure:

    /home/jason/algorithmic_trading_binance/hbar_mainnet_bot/
        key_loader.py: API key loading logic
        hbarGridBotMainNet.py: Main bot script (uses KeyLoader)
        exchange_connection.py: Exchange connection logic (uses loaded keys)
        /home/jason/api/binance/binance_us.env: API key file
        Other project files (e.g., data_manager.py, grid_manager.py)

Output:

    Instance Variables:
        api_key_rest: REST API key (string).
        secret_rest: REST API secret (string).
        api_key_ws: WebSocket API key (same as REST key).
        secret_ws: WebSocket API secret (same as REST secret).
    Logs:
        Info log: "API keys loaded successfully."
        Error logs: "Missing BUS_KEY or BUS_SECRET in .env file." or "Error loading API keys: ...".
        Logs require configuration in the calling application (e.g., RotatingFileHandler in hbarGridBotMainNet.py).
    Return Value:
        load_keys() returns True (success) or False (failure).

Notes:

    WebSocket and REST credentials are identical (BUS_KEY, BUS_SECRET), which may not align with all exchange configurations.
    The .env file path is hardcoded in hbarGridBotMainNet.py (/home/jason/api/binance/binance_us.env).
    Logging depends on external configuration in the main application.
    No credential validation beyond presence (e.g., no API ping to verify key validity).
    Assumes .env file is accessible and correctly formatted.

Limitations:

    Hardcoded .env variable names (BUS_KEY, BUS_SECRET) limit flexibility.
    No support for separate WebSocket credentials, despite class design allowing it.
    No encryption or advanced security for .env file handling.
    Assumes .env file exists and is readable; no fallback for missing files.
    Logging requires external setup, limiting standalone use.

Troubleshooting:

    Missing keys: Verify /home/jason/api/binance/binance_us.env exists and contains BUS_KEY and BUS_SECRET.
    File access errors: Check file permissions (e.g., chmod 600 binance_us.env) and path accuracy.
    No logs: Ensure logging is configured in the main application (e.g., hbarGridBotMainNet.py).
    Invalid credentials: Confirm keys match Binance.US API dashboard settings.
    Missing python-dotenv: Install with pip install python-dotenv.

Future Improvements:

    Support separate REST and WebSocket credentials for flexibility.
    Add credential validation (e.g., test API keys with a ping).
    Use environment variables or config files for .env path flexibility.
    Implement encryption or secure storage for sensitive credentials.
    Add fallback mechanisms for missing or malformed .env files.

License:
For personal use, provided as-is. Comply with Binance.US API terms.

Created: May 11, 2025