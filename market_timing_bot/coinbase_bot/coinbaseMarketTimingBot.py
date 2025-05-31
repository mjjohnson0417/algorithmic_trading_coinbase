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
        symbols = ['BTC-USD', 'XRP-USD']
        data_manager = DataManager(symbols, exchange, enable_logging=True)
        logger.info(f"DataManager initialized for symbols: {symbols}")

        # IndicatorCalculator setup
        indicator_calculator = IndicatorCalculator(symbols, data_manager, enable_logging=True)
        logger.info(f"IndicatorCalculator initialized for symbols: {symbols}")

        # CandlestickPatterns setup
        candlestick_patterns = CandlestickPatterns(symbols, data_manager, enable_logging=True)
        logger.info(f"CandlestickPatterns initialized for symbols: {symbols}")

        # ChartPatterns setup
        chart_patterns = ChartPatterns(symbols, data_manager, enable_logging=True)
        logger.info(f"ChartPatterns initialized for symbols: {symbols}")

        # OrderOperations setup - create instances for each symbol
        order_operations = {}
        for symbol in symbols:
            order_ops = OrderOperations(
                exchange=exchange.rest_exchange,  # Pass the REST ccxt exchange instance
                symbol=symbol,
                portfolio_name="market timing",  # Specify the portfolio name
                dry_run=False,  # Set to True for testing
                enable_logging=True
            )
            await order_ops.initialize()  # Initialize portfolio ID
            order_operations[symbol] = order_ops
        logger.info(f"OrderOperations initialized for symbols: {symbols}")

        # MarketTimingManager setup
        market_timing_manager = MarketTimingManager(
            symbols, 
            candlestick_patterns, 
            chart_patterns, 
            indicator_calculator, 
            data_manager, 
            order_operations,  # Pass the order_operations dict
            enable_logging=True
        )
        logger.info(f"MarketTimingManager initialized for symbols: {symbols}")

        # Wait for DataManager to initialize historical data
        while not data_manager.historical_initialized:
            logger.debug("Waiting for DataManager to initialize historical data...")
            await asyncio.sleep(1)

        # Log initial data
        try:
            all_indicators = indicator_calculator.calculate_all_indicators()
            for symbol in symbols:
                logger.info(f"Indicators for {symbol}:\n{json.dumps(all_indicators[symbol], indent=2, default=str)}")

            all_patterns = candlestick_patterns.calculate_all_patterns()
            for symbol in symbols:
                logger.info(f"Candlestick patterns for {symbol}:\n{json.dumps(all_patterns[symbol], indent=2)}")

            all_chart_patterns = chart_patterns.calculate_all_patterns()
            for symbol in symbols:
                logger.info(f"Chart patterns for {symbol}:\n{json.dumps(all_chart_patterns[symbol], indent=2)}")

            # Log market states for all timeframes
            for symbol in symbols:
                for timeframe in ['1m', '5m', '15m', '1h', '6h', '1d']:
                    state = market_timing_manager.get_market_state(symbol, timeframe)
                    logger.info(f"Market state for {symbol} ({timeframe}): {state}")

        except Exception as e:
            logger.error(f"Error in initial data logging: {e}", exc_info=True)

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