import asyncio
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from key_loader import KeyLoader
from exchange_connection import ExchangeConnection
from data_manager import DataManager

async def main():
    # Logger setup
    logger = logging.getLogger('MarketTimingBot')
    logger.setLevel(logging.DEBUG)
    log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / 'market_timing_bot.log'
    if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(console_handler)

    # Key loading
    key_file_path = '/home/jason/api/coinbase/market_timing_key.json'
    key_loader = KeyLoader(key_file_path, enable_logging=True)
    if not key_loader.load_keys():
        logger.error("Failed to load API keys. Exiting.")
        return

    api_key = key_loader.api_key
    secret_key = key_loader.secret

    exchange = None
    data_manager = None

    try:
        # Exchange setup
        exchange = ExchangeConnection(api_key, secret_key)
        if not await exchange.check_rest_connection():
            logger.error("Failed to connect to exchange via REST. Exiting.")
            return
        logger.info("REST connection established successfully.")

        # DataManager setup
        symbols = ['HBAR-USD']  # Spot trading symbol
        data_manager = DataManager(symbols, exchange, enable_logging=True)
        logger.info(f"DataManager initialized for symbols: {symbols}")

        # Keep the bot running
        while True:
            await asyncio.sleep(3600)  # Run indefinitely, check hourly

    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
    finally:
        # Ensure all resources are closed
        try:
            if data_manager:
                logger.info("Closing WebSocket connections...")
                await data_manager.close_websockets()
            if exchange:
                logger.info("Closing exchange connection...")
                await exchange.close()
        except Exception as e:
            logger.error(f"Error during final cleanup: {e}", exc_info=True)
        logger.info("Connections closed. Exiting.")

if __name__ == "__main__":
    asyncio.run(main())