# multicoinGridBot.py
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from key_loader import KeyLoader
from exchange_connection import ExchangeConnection
from data_manager import DataManager
from indicator_calculator import IndicatorCalculator
from order_operations import OrderOperations
from grid_manager import GridManager
from graceful_shutdown import GracefulShutdown

async def main():
    # Set up logger
    logger = logging.getLogger('GridBot')
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        log_dir = Path(__file__).parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / 'grid_bot.log'
        file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Load API keys
    env_path = '/home/jason/api/binance/binance_us.env'
    key_loader = KeyLoader(env_path)
    if not key_loader.load_keys():
        logger.error("Failed to load API keys")
        print("Failed to load API keys. Check logs for details.")
        return

    # Initialize exchange connection
    exchange = ExchangeConnection(
        api_key_rest=key_loader.api_key_rest,
        secret_rest=key_loader.secret_rest,
        api_key_ws=key_loader.api_key_ws,
        secret_ws=key_loader.secret_ws
    )
    await exchange.connect()
    logger.info("Exchange connection established")
    print("Connected to Binance.us exchange")

    # Define list of symbols
    symbols = ['XRP/USDT', 'ETH/USDT', 'BTC/USDT']
    #symbols = ['XRP/USDT']
    logger.info(f"Initializing bot for symbols: {symbols}")
    print(f"Initializing bot for {len(symbols)} symbols: {', '.join(symbols)}")

    # Initialize DataManager with logging disabled to suppress ticker logs
    data_manager = DataManager(symbols=symbols, enable_logging=False)

    # Preload klines
    if await data_manager.preload_1d_klines(exchange):
        logger.info("Successfully preloaded 1-day klines for all symbols")
    else:
        logger.error("Failed to preload 1-day klines for some symbols")
        return

    if await data_manager.preload_1h_klines(exchange):
        logger.info("Successfully preloaded 1-hour klines for all symbols")
    else:
        logger.error("Failed to preload 1-hour klines for some symbols")
        return

    # Start ticker subscription
    await data_manager.subscribe_ticker()  # Non-blocking; task runs in background
    logger.info("Ticker subscriptions started")

    # Initialize IndicatorCalculator with logging enabled
    indicator_calculator = IndicatorCalculator(symbols=symbols, enable_logging=False)

    # Initialize OrderOperations for each symbol
    order_operations_dict = {
        symbol: OrderOperations(exchange, symbol, dry_run=False, enable_logging=False)
        for symbol in symbols
    }

    # Cancel any existing open buy orders for all symbols
    logger.info("Checking and canceling any existing open buy orders")
    print("Checking and canceling existing open buy orders...")
    for symbol in symbols:
        try:
            order_ops = order_operations_dict[symbol]
            open_orders = order_ops.fetch_open_orders()
            buy_orders = [order for order in open_orders if order['side'] == 'buy']
            if buy_orders:
                order_ops.cancel_all_buy_orders()
                logger.info(f"Canceled {len(buy_orders)} open buy orders for {symbol}")
                print(f"Canceled {len(buy_orders)} open buy orders for {symbol}")
            else:
                logger.info(f"No open buy orders found for {symbol}")
                print(f"No open buy orders for {symbol}")
        except Exception as e:
            logger.error(f"Error canceling buy orders for {symbol}: {e}", exc_info=True)
            print(f"Error canceling buy orders for {symbol}: {e}")

    # Initialize GridManager
    grid_manager = GridManager(
        data_manager=data_manager,
        indicator_calculator=indicator_calculator,
        order_operations_dict=order_operations_dict,
        symbols=symbols,
        debug=False
    )

    # Initialize graceful shutdown
    loop = asyncio.get_running_loop()
    graceful_shutdown = GracefulShutdown(order_operations_dict=order_operations_dict, data_manager=data_manager, dry_run=False, loop=loop)

    # Run the bot
    try:
        print("Bot is running. Press Ctrl+C to stop...")
        await grid_manager.run(interval=30)
    except asyncio.CancelledError:
        logger.info("Bot cancelled by user interrupt")
        print("Bot interrupted. Shutting down...")
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
        print(f"Critical error occurred: {e}. Check logs for details.")
    finally:
        await data_manager.close_websockets()
        await exchange.close()
        logger.info("Shutdown complete")
        print("Bot has shut down gracefully")

if __name__ == "__main__":
    asyncio.run(main())