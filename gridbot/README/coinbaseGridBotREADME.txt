# Coinbase Grid Bot

## Overview
The `coinbaseGridBot.py` module serves as the entry point for a grid trading bot designed for the Coinbase Advanced Trade API. It orchestrates the initialization and execution of various components to manage grid trading for specified trading pairs (e.g., HBAR-USDT).

## Functionality
- **Initialization**: Loads API keys, sets up logging, and initializes core components including `ExchangeConnection`, `DataManager`, `IndicatorCalculator`, `StateManager`, `OrderOperations`, and `GridManager`.
- **Execution**: Runs the main event loop, starts the `GridManager` to manage trading, and handles graceful shutdown on signals (SIGINT, SIGTERM).
- **Error Handling**: Ensures proper cleanup of resources (WebSocket and exchange connections) during shutdown or critical errors.

## Dependencies
- Python 3.8+
- Modules: `asyncio`, `logging`, `pathlib`, `signal`
- Custom Modules: `key_loader`, `exchange_connection`, `data_manager`, `indicator_calculator`, `state_manager`, `grid_manager`, `order_operations`, `graceful_shutdown`
- External Libraries: Listed in the installation document

## Usage
1. Ensure API keys are stored in a JSON file (e.g., `/home/jason/api/coinbase/coinbase_keys.json`).
2. Run the script:
   ```bash
   python coinbaseGridBot.py
3. The bot will initialize components, start the grid trading loop, and log activities to logs/grid_manager.log

- service is called coinbase-gridbot.service
- script to check the bot status and send an email if it fails is /usr/local/bin/check-coinbase-gridbot.sh
- crontab has an entry to run the script every five minutes
- script log location: /var/log/coinbase-gridbot-check.log