import asyncio
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from key_loader import KeyLoader
from exchange_connection import ExchangeConnection
from data_manager import DataManager
from indicator_calculator import IndicatorCalculator
from candlestick_patterns import CandlestickPatterns
import json

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
    indicator_calculator = None
    candlestick_patterns = None

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

        # IndicatorCalculator setup
        indicator_calculator = IndicatorCalculator(symbols, data_manager, enable_logging=True)
        logger.info(f"IndicatorCalculator initialized for symbols: {symbols}")

        # CandlestickPatterns setup
        candlestick_patterns = CandlestickPatterns(symbols, data_manager, enable_logging=True)
        logger.info(f"CandlestickPatterns initialized for symbols: {symbols}")

        # Wait for DataManager to initialize historical data
        while not data_manager.historical_initialized:
            logger.debug("Waiting for DataManager to initialize historical data...")
            await asyncio.sleep(1)

        # Keep the bot running, checking every minute
        while True:
            try:
                # Calculate and log indicators
                all_indicators = indicator_calculator.calculate_all_indicators()
                for symbol in symbols:
                    logger.info(f"Indicators for {symbol}:\n{json.dumps(all_indicators[symbol], indent=2, default=str)}")

                # Calculate and log candlestick patterns
                all_patterns = candlestick_patterns.calculate_all_patterns()
                for symbol in symbols:
                    logger.info(f"Candlestick patterns for {symbol}:\n{json.dumps(all_patterns[symbol], indent=2)}")
            except Exception as e:
                logger.error(f"Error calculating indicators or patterns: {e}", exc_info=True)
            
            await asyncio.sleep(60)  # Run every minute

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