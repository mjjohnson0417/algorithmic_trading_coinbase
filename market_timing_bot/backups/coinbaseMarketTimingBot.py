import asyncio
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from key_loader import KeyLoader
from exchange_connection import ExchangeConnection
from data_manager import DataManager
from indicator_calculator import IndicatorCalculator
from candlestick_patterns import CandlestickPatterns
from chart_patterns import ChartPatterns
from market_timing_manager import MarketTimingManager
from order_operations import OrderOperations

async def main():
    # Logger setup
    logger = logging.getLogger('MarketTimingBot')
    logger.setLevel(logging.DEBUG)
    log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / 'market_timing_bot.log'
    if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
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
    chart_patterns = None
    market_timing_manager = None

    try:
        # Exchange setup
        exchange = ExchangeConnection(api_key, secret_key)
        if not await exchange.check_rest_connection():
            logger.error("Failed to connect to exchange via REST. Exiting.")
            return
        logger.info("REST connection established successfully.")

        # DataManager setup
        symbols = ['HBAR-USD', 'SUI-USD']
        data_manager = DataManager(symbols, exchange, enable_logging=True)
        logger.info(f"DataManager initialized for symbols: {symbols}")

        # Wait for DataManager to initialize historical data
        while not data_manager.historical_initialized:
            logger.debug("Waiting for DataManager to initialize historical data...")
            await asyncio.sleep(1)

        # Log klines at startup for HBAR-USD across all timeframes
        timeframes = ['1m', '5m', '15m', '1h', '6h', '1d']
        for timeframe in timeframes:
            try:
                kline = data_manager.get_buffer('HBAR-USD', f'klines_{timeframe}')
                logger.debug(
                    f"Klines for HBAR-USD ({timeframe}): columns={list(kline.columns)}, "
                    f"shape={kline.shape}, head=\n{kline.head(5).to_string()}"
                )
            except Exception as e:
                logger.error(f"Error logging klines for HBAR-USD ({timeframe}): {str(e)}")

        # IndicatorCalculator setup
        indicator_calculator = IndicatorCalculator(symbols, data_manager, enable_logging=True)
        logger.info(f"IndicatorCalculator initialized for symbols: {symbols}")

        # CandlestickPatterns setup
        candlestick_patterns = CandlestickPatterns(symbols, data_manager, enable_logging=True)
        logger.info(f"CandlestickPatterns initialized for symbols: {symbols}")

        # ChartPatterns setup
        chart_patterns = ChartPatterns(symbols, data_manager, enable_logging=True)
        logger.info(f"ChartPatterns initialized for symbols: {symbols}")

        # OrderOperations setup
        order_operations = {}
        for symbol in symbols:
            order_ops = OrderOperations(
                exchange=exchange.rest_exchange,
                symbol=symbol,
                portfolio_name="market timing",
                dry_run=False,
                enable_logging=True
            )
            await order_ops.initialize()
            order_operations[symbol] = order_ops
        logger.info(f"OrderOperations initialized for symbols: {symbols}")

        # MarketTimingManager setup
        market_timing_manager = MarketTimingManager(
            symbols, 
            candlestick_patterns, 
            chart_patterns, 
            indicator_calculator, 
            data_manager, 
            order_operations,
            enable_logging=True
        )
        logger.info(f"MarketTimingManager initialized for symbols: {symbols}")

        # Run market timing manager
        await market_timing_manager.run()

    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
    finally:
        try:
            if data_manager:
                logger.info("Closing WebSocket connections...")
                await data_manager.close_websockets()
                if hasattr(data_manager, 'session') and data_manager.session is not None:
                    await data_manager.session.close()
            if exchange:
                logger.info("Closing exchange connection...")
                await exchange.close()
        except Exception as e:
            logger.error(f"Error during final cleanup: {e}", exc_info=True)
        logger.info("Connections closed. Exiting.")

if __name__ == "__main__":
    asyncio.run(main())