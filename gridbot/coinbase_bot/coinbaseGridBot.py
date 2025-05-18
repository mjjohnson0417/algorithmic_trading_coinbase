# coinbaseGridBot.py
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import signal
from key_loader import KeyLoader
from exchange_connection import ExchangeConnection
from data_manager import DataManager
from indicator_calculator import IndicatorCalculator
from state_manager import StateManager
from grid_manager import GridManager
from order_operations import OrderOperations
from graceful_shutdown import GracefulShutdown

async def main():
    # Logger setup
    logger = logging.getLogger('GridManager')
    logger.setLevel(logging.DEBUG)
    log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / 'grid_manager.log'
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
    key_file_path = '/home/jason/api/coinbase/coinbase_keys.json'
    key_loader = KeyLoader(key_file_path, enable_logging=True)
    if not key_loader.load_keys():
        logger.error("Failed to load API keys. Exiting.")
        return

    api_key = key_loader.api_key
    secret_key = key_loader.secret

    exchange = None
    data_manager = None
    indicator_calculator = None
    state_manager = None
    grid_manager = None
    shutdown_event = asyncio.Event()

    try:
        # Exchange setup
        exchange = ExchangeConnection(api_key, secret_key)
        if not await exchange.check_rest_connection():
            logger.error("Failed to connect to exchange via REST. Exiting.")
            return

        # DataManager setup
        symbols = ['HBAR-USDT']
        data_manager = DataManager(symbols, exchange, enable_logging=True)

        # IndicatorCalculator setup
        indicator_calculator = IndicatorCalculator(symbols, data_manager, enable_logging=True)
        # Pre-calculate indicators to ensure data is ready
        indicators = indicator_calculator.calculate_all_indicators()
        logger.info(f"Pre-calculated indicators: {indicators}")

        # StateManager setup
        state_manager = StateManager(data_manager, indicator_calculator, symbols, enable_logging=True)

        # OrderOperations setup
        order_operations_dict = {
            symbol: OrderOperations(
                exchange=exchange.rest_exchange,
                symbol=symbol,
                dry_run=False,
                enable_logging=True
            )
            for symbol in symbols
        }

        # GridManager setup
        grid_manager = GridManager(data_manager, indicator_calculator, state_manager, order_operations_dict, symbols, debug=True, enable_logging=True)

        # Run one-time initialization
        logger.info("Running GridManager initialization.")
        try:
            await grid_manager.initialize_bot()
            logger.info("GridManager initialization completed successfully.")
        except Exception as e:
            logger.error(f"GridManager initialization failed: {e}", exc_info=True)
            return  # Exit if initialization fails

        # Graceful Shutdown Setup
        current_loop = asyncio.get_running_loop()
        graceful_shutdown_instance = GracefulShutdown(
            order_operations_dict=order_operations_dict,
            data_manager=data_manager,
            exchange=exchange,
            dry_run=False,
            loop=current_loop
        )

        def handle_signal(signum, shutdown_event):
            asyncio.create_task(graceful_shutdown_instance.shutdown(signum, shutdown_event))

        current_loop.add_signal_handler(signal.SIGINT, handle_signal, signal.SIGINT, shutdown_event)
        current_loop.add_signal_handler(signal.SIGTERM, handle_signal, signal.SIGTERM, shutdown_event)

        # Run GridManager
        logger.info("Starting GridManager run loop.")
        asyncio.create_task(grid_manager.run(interval=60))

        # Wait for shutdown
        logger.info("Monitoring GridManager. Press Ctrl+C to exit.")
        await shutdown_event.wait()

    except Exception as e:
        logger.error("Critical error: %s", e, exc_info=True)
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