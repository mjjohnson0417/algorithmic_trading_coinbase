To modify your grid trading bot, currently designed to trade a single crypto pair (HBAR/USDT) on Binance.us, to handle a list of trading pairs, several key areas of the code need adjustments. The goal is to enable the bot to manage multiple symbols concurrently while maintaining its core functionality, such as data fetching, order placement, and grid management. Below, I outline the primary areas requiring changes, based on a thorough analysis of the provided code.
1. DataManager Modifications

The DataManager class is responsible for fetching and storing market data, such as klines, tickers, and order books. Currently, it handles data for a single symbol implicitly through method calls. To support multiple symbols, it needs to manage data for each symbol separately within a single instance, leveraging Binance’s ability to subscribe to multiple streams in one WebSocket connection.

    Constructor (__init__):
        Update to accept a list of symbols:
        python

    def __init__(self, symbols: list, debug: bool = False):
        self.symbols = symbols
        self.debug = debug
        self.klines_buffer_1h = {symbol: pd.DataFrame() for symbol in symbols}
        self.klines_buffer_1m = {symbol: pd.DataFrame() for symbol in symbols}
        self.klines_buffer_1d = {symbol: pd.DataFrame() for symbol in symbols}
        self.order_book_buffer = {symbol: pd.DataFrame() for symbol in symbols}
        self.ticker_buffer = {symbol: pd.DataFrame() for symbol in symbols}
        self.subscription_tasks = []
    Buffers are now dictionaries with symbols as keys, each holding a DataFrame for that symbol’s data.

Preload Methods:

    Modify methods like preload_1h_klines to iterate over all symbols:
    python

    async def preload_1h_klines(self, exchange: ExchangeConnection, hours: int = 72):
        for symbol in self.symbols:
            klines = exchange.rest_exchange.fetch_ohlcv(symbol, '1h', limit=hours)
            df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            self.klines_buffer_1h[symbol] = df
            if self.debug:
                logging.debug(f"Preloaded {len(df)} 1h klines for {symbol}")
    Apply similar changes to preload_1d_klines and preload_1m_klines.

WebSocket Subscriptions:

    Update subscription methods (e.g., subscribe_ticker) to handle multiple symbols in a single connection:
    python

    async def subscribe_tickers(self):
        ws_symbols = [symbol.lower().replace('/', '') for symbol in self.symbols]
        streams = [f"{ws_symbol}@ticker" for ws_symbol in ws_symbols]
        ws_url = f"wss://stream.binance.us:9443/stream?streams={'/'.join(streams)}"
        async with websockets.connect(ws_url) as ws:
            while True:
                message = await ws.recv()
                data = json.loads(message)
                stream_name = data['stream']
                symbol = next(s for s in self.symbols if s.lower().replace('/', '') in stream_name)
                ticker_data = data['data']
                df = pd.DataFrame({
                    'timestamp': [pd.to_datetime(ticker_data['E'], unit='ms')],
                    'event_id': [ticker_data.get('u', int(datetime.now().timestamp() * 1000))],
                    'best_bid': [float(ticker_data['b'])],
                    'bid_qty': [float(ticker_data['B'])],
                    'best_ask': [float(ticker_data['a'])],
                    'ask_qty': [float(ticker_data['A'])],
                    'last_price': [float(ticker_data['c'])],
                    'last_qty': [float(ticker_data['Q'])],
                    'volume_24h': [float(ticker_data['v'])],
                    'quote_volume_24h': [float(ticker_data['q'])]
                })
                self.ticker_buffer[symbol] = pd.concat([self.ticker_buffer[symbol], df], ignore_index=True)
                if len(self.ticker_buffer[symbol]) > 1000:
                    self.ticker_buffer[symbol] = self.ticker_buffer[symbol].iloc[-1000:]
    Store the task: self.subscription_tasks.append(asyncio.create_task(self.subscribe_tickers())).
    Apply similar logic to subscribe_order_book and subscribe_1m_klines, parsing the stream field to route data to the correct symbol’s buffer.

Buffer Access (get_buffer):

    Modify to accept a symbol parameter:
    python

    def get_buffer(self, symbol: str, buffer_type: str = 'klines_1h'):
        buffers = {
            'klines_1h': self.klines_buffer_1h,
            'klines_1m': self.klines_buffer_1m,
            'klines_1d': self.klines_buffer_1d,
            'order_book': self.order_book_buffer,
            'ticker': self.ticker_buffer
        }
        buffer_dict = buffers.get(buffer_type, {})
        return buffer_dict.get(symbol, pd.DataFrame()).copy()

WebSocket Closure (close_websockets):

    Cancel all subscription tasks:
    python

        async def close_websockets(self):
            for task in self.subscription_tasks:
                task.cancel()
            await asyncio.gather(*self.subscription_tasks, return_exceptions=True)

2. Main Function Adjustments

The main function in hbarGridBotMainNet.py orchestrates the bot’s components. It needs to initialize and run instances for each symbol concurrently.

    Symbol List:
        Define a list of symbols:
        python

    symbols = ['HBAR/USDT', 'BTC/USDT', 'ETH/USDT']

Component Initialization:

    Create a single DataManager for all symbols and separate instances of other classes per symbol:
    python

        async def main():
            # ... (logging and key loading remain unchanged)
            exchange = ExchangeConnection(
                api_key_rest=key_loader.api_key_rest,
                secret_rest=key_loader.secret_rest,
                api_key_ws=key_loader.api_key_ws,
                secret_ws=key_loader.secret_ws
            )
            await exchange.connect()

            data_manager = DataManager(symbols=symbols, debug=False)
            await data_manager.preload_1d_klines(exchange)  # Update to preload for all symbols
            await data_manager.preload_1h_klines(exchange)

            grid_managers = []
            order_operations_list = []
            for symbol in symbols:
                order_ops = OrderOperations(exchange=exchange, symbol=symbol, dry_run=False, debug=False)
                order_operations_list.append(order_ops)
                indicator_calc = IndicatorCalculator(debug=False)
                grid_mgr = GridManager(data_manager, indicator_calc, order_ops, symbol, debug=True)
                grid_managers.append(grid_mgr)

                # Cancel open buy orders for this symbol
                all_orders = order_ops.fetch_all_orders()
                for order in all_orders:
                    if order.get('type') == 'limit_buy' and order.get('status') == 'open':
                        order_ops.cancel_order(order['id'])
                        logger.info(f"Cancelled open buy order {order['id']} for {symbol}")

            # Start subscriptions
            ticker_task = asyncio.create_task(data_manager.subscribe_tickers())
            # Add other subscription tasks as needed

            # Initialize graceful shutdown with list of order_operations
            loop = asyncio.get_running_loop()
            graceful_shutdown = GracefulShutdown(order_operations_list, data_manager, dry_run=False, loop=loop)

            # Run all grid managers concurrently
            try:
                tasks = [grid_mgr.run(interval=30) for grid_mgr in grid_managers]
                await asyncio.gather(*tasks)
            except asyncio.CancelledError:
                logger.info("Grid bot cancelled")
            finally:
                ticker_task.cancel()
                await asyncio.gather(ticker_task, return_exceptions=True)
                await exchange.close()
                logger.info("Exchange connection closed.")

3. GracefulShutdown Adjustments

The GracefulShutdown class needs to handle multiple OrderOperations instances to cancel orders for all symbols during shutdown.

    Constructor:
        Accept a list of OrderOperations:
        python

    def __init__(self, order_operations_list: list, data_manager, dry_run: bool, loop: asyncio.AbstractEventLoop):
        self.order_operations_list = order_operations_list
        self.data_manager = data_manager
        self.dry_run = dry_run
        self.loop = loop
        self.shutdown_initiated = False
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        signal.signal(signal.SIGINT, self.handle_shutdown)

Shutdown Logic (shutdown_async):

    Cancel orders for each symbol:
    python

        async def shutdown_async(self):
            logging.info("Starting asynchronous shutdown...")
            for order_ops in self.order_operations_list:
                open_orders = order_ops.fetch_open_orders()
                if not open_orders:
                    logging.info(f"No open orders for {order_ops.symbol}")
                elif not self.dry_run:
                    for order in open_orders:
                        order_ops.cancel_order(order['id'])
                        logging.info(f"Cancelled order {order['id']} for {order_ops.symbol}")

            await self.data_manager.close_websockets()
            logging.info("WebSocket connections closed.")

            tasks = [task for task in asyncio.all_tasks(self.loop) if task is not asyncio.current_task()]
            for task in tasks:
                task.cancel()
            await self.complete_shutdown(tasks)

4. Logging Enhancements

To distinguish logs from different symbols, include the symbol in log messages where applicable:

    In GridManager:
    python

    self.logger.info(f"Calculated {len(self.grid_levels)} grid levels for {self.symbol}")
    Apply similar updates in OrderOperations, StateManager, etc., wherever logs reference symbol-specific actions.

Additional Considerations

    Other Classes:
        OrderOperations, IndicatorCalculator, StateManager, and GridManager are already symbol-specific due to their constructors taking a symbol parameter. They can remain largely unchanged, as each instance will operate on its designated symbol, fetching data via the updated DataManager.
    Resource Management:
        Ensure the bot respects Binance.us API rate limits, especially with multiple symbols increasing REST API calls.
    Concurrency:
        The use of asyncio.gather ensures all GridManager.run tasks run concurrently, but monitor performance to avoid overwhelming system resources.

By implementing these changes, your grid trading bot will efficiently manage a list of trading pairs, utilizing a shared DataManager for data collection and separate instances of other components per symbol for trading logic. This approach balances scalability and maintainability while leveraging the existing codebase structure.