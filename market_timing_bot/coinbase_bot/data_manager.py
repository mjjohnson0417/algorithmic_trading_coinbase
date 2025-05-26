# data_manager.py
import asyncio
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import pandas as pd
import websockets
from exchange_connection import ExchangeConnection
from datetime import datetime
import traceback

class DataManager:
    def __init__(self, symbols: list, exchange_connection: ExchangeConnection, enable_logging: bool = True):
        """
        Initializes the DataManager class for multiple symbols.

        Args:
            symbols (list): List of trading pair symbols (e.g., ['HBAR-USD']).
            exchange_connection (ExchangeConnection): The ExchangeConnection instance for API access.
            enable_logging (bool): If True, enables logging to 'logs/data_manager.log'.
        """
        self.symbols = symbols
        self.exchange_connection = exchange_connection
        self.enable_logging = enable_logging

        # Set up logger
        self.logger = logging.getLogger('DataManager')
        if enable_logging:
            log_dir = Path(__file__).parent / 'logs'
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / 'data_manager.log'
            file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
            # file_handler.setLevel(logging.DEBUG)
            file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            # self.logger.setLevel(logging.DEBUG)
            self.logger.setLevel(logging.INFO)
        else:
            self.logger.setLevel(logging.WARNING)

        # Use the exchange_connection's rest_exchange
        self.rest_exchange = exchange_connection.rest_exchange
        if self.rest_exchange is None:
            self.logger.error("No REST exchange instance available from ExchangeConnection")
            raise ValueError("ExchangeConnection has no valid REST exchange")

        # Initialize buffers for all Coinbase timeframes
        self.klines_buffer_1m = {symbol: pd.DataFrame() for symbol in symbols}
        self.klines_buffer_5m = {symbol: pd.DataFrame() for symbol in symbols}
        self.klines_buffer_15m = {symbol: pd.DataFrame() for symbol in symbols}
        self.klines_buffer_1h = {symbol: pd.DataFrame() for symbol in symbols}
        self.klines_buffer_6h = {symbol: pd.DataFrame() for symbol in symbols}
        self.klines_buffer_1d = {symbol: pd.DataFrame() for symbol in symbols}
        self.order_book_buffer = {symbol: pd.DataFrame() for symbol in symbols}
        self.ticker_buffer = {symbol: pd.DataFrame(columns=['timestamp', 'symbol', 'last_price', 'volume_24h', 'best_bid', 'best_ask', 'side']) for symbol in symbols}
        self.ws_connections = {}
        self.ws_tasks = []
        self.websocket_task = None
        self.last_ticker_price = {symbol: None for symbol in symbols}
        self.ticker_logged = {symbol: False for symbol in symbols}
        self.buffer_log_counter = {symbol: 0 for symbol in symbols}  # Counter for logging buffer contents
        self.historical_initialized = False  # Flag to track historical data loading

        # Schedule historical data fetching and WebSocket setup
        asyncio.create_task(self._initialize_and_start_tasks())

    async def _initialize_and_start_tasks(self):
        """
        Fetches initial historical klines and starts WebSocket and REST update tasks.
        """
        try:
            # Fetch historical klines first
            await self._fetch_initial_historical_data()
            self.historical_initialized = True
            self.logger.info("Completed initial historical kline fetch for all timeframes")

            # Start WebSocket subscriptions for ticker and level2
            self.websocket_task = asyncio.create_task(self.start_coinbase_websocket(self.exchange_connection))
            self.logger.info("Started WebSocket task for ticker and level2")

            # Start REST kline updates
            asyncio.create_task(self._update_klines_periodically())
            self.logger.info("Started REST kline update tasks")
        except Exception as e:
            self.logger.error(f"Error in initialization tasks: {e}", exc_info=True)

    async def _fetch_initial_historical_data(self):
        """
        Fetches initial historical klines for all Coinbase timeframes to populate buffers with the latest 40 klines.
        """
        max_retries = 5
        for symbol in self.symbols:
            for interval in ['1m', '5m', '15m', '1h', '6h', '1d']:
                attempt = 0
                while attempt < max_retries:
                    try:
                        klines = await self.fetch_historical_data_with_retry(symbol, interval, 40)  # Fetch 40 klines
                        if klines and len(klines) > 0:
                            df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
                            getattr(self, f'klines_buffer_{interval}')[symbol] = df
                            self.logger.info(f"Initialized {interval} klines for {symbol}, shape: {df.shape}, latest timestamp: {df['timestamp'].max()}")
                            self.logger.debug(f"{interval} kline contents for {symbol}:\n{df.to_string()}")
                            break
                        else:
                            self.logger.warning(f"Empty or no klines fetched for {interval} {symbol}")
                    except Exception as e:
                        self.logger.error(f"Error fetching initial {interval} klines for {symbol}: {e}", exc_info=True)
                    attempt += 1
                    await asyncio.sleep(5)
                if attempt == max_retries:
                    self.logger.error(f"Failed to initialize {interval} klines for {symbol} after {max_retries} retries")

    async def _update_klines_periodically(self):
        """
        Periodically fetches recent klines via REST API for all timeframes every 60 seconds.
        """
        while True:
            for symbol in self.symbols:
                for timeframe in ['1m', '5m', '15m', '1h', '6h', '1d']:
                    try:
                        klines = await self.fetch_historical_data_with_retry(symbol, timeframe, 10)  # Fetch 10 recent klines
                        if klines and len(klines) > 0:
                            new_df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                            new_df['timestamp'] = pd.to_datetime(new_df['timestamp'], unit='ms', utc=True)
                            buffer_key = f'klines_buffer_{timeframe}'
                            buffer = getattr(self, buffer_key)[symbol]
                            if not buffer.empty:
                                buffer = pd.concat([buffer, new_df], ignore_index=True)
                                buffer = buffer.drop_duplicates(subset=['timestamp'], keep='last')
                                buffer = buffer.tail(40)  # Limit to 40 rows
                            else:
                                buffer = new_df
                            getattr(self, buffer_key)[symbol] = buffer
                            self.buffer_log_counter[symbol] += 1
                            self.logger.info(f"Updated {timeframe} klines for {symbol}, shape: {buffer.shape}, latest timestamp: {buffer['timestamp'].max()}")
                            if self.buffer_log_counter[symbol] % 5 == 0:
                                self.logger.debug(f"Klines contents for {symbol} ({timeframe}):\n{buffer.tail(5).to_string()}")
                        await asyncio.sleep(1)  # Avoid rate limiting
                    except Exception as e:
                        self.logger.error(f"Error updating {timeframe} klines for {symbol}: {e}", exc_info=True)
            await asyncio.sleep(60)  # Update all timeframes every 60 seconds

    def get_buffer(self, symbol: str, buffer_type: str) -> pd.DataFrame:
        """
        Retrieves the specified buffer for a given symbol.

        Args:
            symbol (str): The trading symbol (e.g., 'HBAR-USD').
            buffer_type (str): The type of buffer ('ticker', '1m', '5m', '15m', '1h', '6h', '1d', 'klines_1m', 'klines_5m', 'klines_15m', 'klines_1h', 'klines_6h', 'klines_1d', 'order_book').

        Returns:
            pd.DataFrame: The requested buffer DataFrame.

        Raises:
            ValueError: If the symbol or buffer_type is invalid.
        """
        if symbol not in self.symbols:
            self.logger.error(f"Invalid symbol: {symbol}")
            raise ValueError(f"Symbol {symbol} not found in DataManager symbols")
        
        buffer_map = {
            'ticker': self.ticker_buffer,
            '1m': self.klines_buffer_1m,
            'klines_1m': self.klines_buffer_1m,
            '5m': self.klines_buffer_5m,
            'klines_5m': self.klines_buffer_5m,
            '15m': self.klines_buffer_1m,
            'klines_15m': self.klines_buffer_15m,
            '1h': self.klines_buffer_1h,
            'klines_1h': self.klines_buffer_1h,
            '6h': self.klines_buffer_6h,
            'klines_6h': self.klines_buffer_6h,
            '1d': self.klines_buffer_1d,
            'klines_1d': self.klines_buffer_1d,
            'order_book': self.order_book_buffer
        }
        
        if buffer_type not in buffer_map:
            self.logger.error(f"Invalid buffer type: {buffer_type}")
            raise ValueError(f"Buffer type {buffer_type} not supported")
        
        return buffer_map[buffer_type][symbol]

    async def fetch_historical_data_with_retry(self, symbol: str, timeframe: str, limit: int = 40, max_attempts: int = 5):
        """
        Fetch historical klines with retry logic, ensuring up to 'limit' klines are retrieved.

        Args:
            symbol (str): Trading pair symbol (e.g., 'HBAR-USD').
            timeframe (str): Timeframe ('1m', '5m', '15m', '1h', '6h', '1d').
            limit (int): Number of klines to fetch (default 40).
            max_attempts (int): Maximum retry attempts per request.

        Returns:
            list: List of klines, up to 'limit' entries.
        """
        symbol_ccxt = symbol.replace('/', '-')  # Ensure Coinbase format
        timeframe_map = {'1m': '1m', '5m': '5m', '15m': '15m', '1h': '1h', '6h': '6h', '1d': '1d'}
        if timeframe not in timeframe_map:
            self.logger.error(f"Invalid timeframe: {timeframe}")
            return None

        all_klines = []
        remaining = limit
        since = None  # Start from latest data

        while remaining > 0:
            attempt = 0
            while attempt < max_attempts:
                try:
                    # Fetch up to remaining klines
                    klines = await self.rest_exchange.fetch_ohlcv(
                        symbol_ccxt, 
                        timeframe_map[timeframe], 
                        limit=min(remaining, 100),  # Coinbase API may limit to 100 per request
                        since=since
                    )
                    if not klines:
                        self.logger.debug(f"No more klines available for {symbol} {timeframe}")
                        break

                    all_klines.extend(klines)
                    remaining -= len(klines)
                    self.logger.debug(f"Fetched {len(klines)} {timeframe} klines for {symbol}, {remaining} remaining")

                    if remaining > 0 and klines:
                        # Set 'since' to the earliest timestamp minus a small buffer
                        since = int(klines[0][0] - 1000 * 60 * 60)  # 1 hour earlier
                    break
                except Exception as e:
                    self.logger.error(f"Attempt {attempt + 1} failed to fetch {timeframe} klines for {symbol}: {e}", exc_info=True)
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(5)
                attempt += 1
            if attempt == max_attempts or not klines:
                break

        if not all_klines:
            self.logger.error(f"Failed to fetch {timeframe} klines for {symbol} after {max_attempts} attempts")
            return None

        # Sort klines by timestamp and take the latest 'limit' entries
        all_klines.sort(key=lambda x: x[0])
        all_klines = all_klines[-limit:]
        self.logger.debug(f"Total fetched {len(all_klines)} {timeframe} klines for {symbol}")
        return [[int(k[0]), k[1], k[2], k[3], k[4], k[5]] for k in all_klines]

    async def _process_ticker_message(self, ticker: dict, symbol: str):
        """Processes ticker messages and updates the ticker buffer."""
        try:
            if ticker['type'] != 'ticker':
                self.logger.warning(f"Unexpected ticker type: {ticker['type']}")
                return

            timestamp = pd.to_datetime(ticker.get('time', datetime.utcnow().isoformat()), utc=True)
            price = float(ticker.get('price', 0))
            volume_24h = float(ticker.get('volume_24_h', 0))
            best_bid = float(ticker.get('best_bid', 0))
            best_ask = float(ticker.get('best_ask', 0))
            side = ticker.get('side', 'unknown')

            new_data = pd.DataFrame({
                'timestamp': [timestamp],
                'symbol': [symbol],
                'last_price': [price],
                'volume_24h': [volume_24h],
                'best_bid': [best_bid],
                'best_ask': [best_ask],
                'side': [side],
            })

            if self.ticker_buffer[symbol].empty:
                self.ticker_buffer[symbol] = new_data
            else:
                self.ticker_buffer[symbol] = pd.concat([self.ticker_buffer[symbol], new_data], ignore_index=True)
            self.ticker_buffer[symbol] = self.ticker_buffer[symbol].drop_duplicates(subset=['timestamp'], keep='last')
            self.ticker_buffer[symbol] = self.ticker_buffer[symbol][-1000:]  # Limit buffer size

            log_ticker = False
            if not self.ticker_logged[symbol]:
                log_ticker = True
                self.ticker_logged[symbol] = True
            elif self.last_ticker_price[symbol] is not None and price != 0:
                if abs(price - self.last_ticker_price[symbol]) / self.last_ticker_price[symbol] > 0.01:  # 1% change
                    log_ticker = True

            if log_ticker:
                self.logger.info(f"Ticker buffer updated for {symbol}, shape: {self.ticker_buffer[symbol].shape}, last_price: {price}")
                self.logger.debug(f"Ticker contents for {symbol}:\n{self.ticker_buffer[symbol].tail(5).to_string()}")

            self.last_ticker_price[symbol] = price

        except Exception as e:
            self.logger.error(f"Error processing ticker message for {symbol}: {e} - {ticker}", exc_info=True)
            traceback.print_exc()

    async def _process_order_book_message(self, message: dict, symbol: str):
        """Processes order book messages and updates the order_book_buffer."""
        try:
            if message.get('channel') != 'l2_data':
                self.logger.warning(f"Unexpected message channel for order book: {message.get('channel')}")
                return

            events = message.get('events', [])
            if not events:
                self.logger.warning(f"No events in order book message for {symbol}")
                return

            for event in events:
                updates = event.get('updates', [])
                if not updates:
                    self.logger.warning(f"No updates in order book message for {symbol}")
                    continue

                for update in updates:
                    side = update.get('side')  # 'buy' or 'sell'
                    price_level = float(update.get('price_level', 0))
                    new_quantity = float(update.get('new_quantity', 0))

                    new_data = pd.DataFrame({
                        'timestamp': [pd.to_datetime(update.get('event_time', datetime.utcnow().isoformat()), utc=True)],
                        'symbol': [symbol],
                        'side': [side],
                        'price_level': [price_level],
                        'quantity': [new_quantity],
                    })
                    self.order_book_buffer[symbol] = pd.concat([self.order_book_buffer[symbol], new_data], ignore_index=True)
                    self.order_book_buffer[symbol] = self.order_book_buffer[symbol].drop_duplicates(subset=['symbol', 'side', 'price_level'], keep='last')
                    self.order_book_buffer[symbol] = self.order_book_buffer[symbol][-1000:]  # Limit buffer size

                self.logger.debug(f"Order book buffer updated for {symbol}, shape: {self.order_book_buffer[symbol].shape}")
                self.logger.debug(f"Order book contents for {symbol}:\n{self.order_book_buffer[symbol].tail(5).to_string()}")

        except Exception as e:
            self.logger.error(f"Error processing order book message for {symbol}: {e} - {message}", exc_info=True)
            traceback.print_exc()

    async def process_message(self, message: str, websocket):
        """
        Processes incoming WebSocket messages, directing them to the appropriate handler.

        Args:
            message (str): The message received from the WebSocket.
            websocket (websockets.WebSocketClientProtocol): The WebSocket connection object.
        """
        try:
            parsed_message = json.loads(message)
            channel = parsed_message.get('channel')
            self.logger.debug(f"Received WebSocket message: channel={channel}, data={json.dumps(parsed_message, indent=2)}")

            if channel == 'ticker':
                events = parsed_message.get('events', [])
                for event in events:
                    for ticker in event.get('tickers', []):
                        product_id = ticker.get('product_id')
                        if not product_id:
                            self.logger.warning(f"Ticker message missing product_id: {ticker}")
                            continue
                        symbol = product_id
                        if symbol not in self.symbols:
                            self.logger.debug(f"Ignoring ticker for unsupported symbol: {symbol}")
                            continue
                        await self._process_ticker_message(ticker, symbol)
            elif channel == 'l2_data':
                events = parsed_message.get('events', [])
                for event in events:
                    product_id = event.get('product_id')
                    if not product_id:
                        self.logger.warning(f"Level2 message missing product_id: {event}")
                        continue
                    symbol = product_id
                    if symbol not in self.symbols:
                        self.logger.debug(f"Ignoring level2 for unsupported symbol: {symbol}")
                        continue
                    await self._process_order_book_message(parsed_message, symbol)
            elif channel == 'subscriptions':
                self.logger.info(f"Subscription confirmation: {parsed_message}")
                subscriptions = parsed_message.get('events', [{}])[0].get('subscriptions', {})
                if 'level2' in subscriptions:
                    self.logger.info(f"Level2 subscription confirmed for: {subscriptions['level2']}")
            elif channel == 'error':
                self.logger.error(f"WebSocket error: {parsed_message}")
            else:
                self.logger.debug(f"Received unknown channel: {channel}, data={parsed_message}")

        except json.JSONDecodeError:
            self.logger.error(f"Error decoding JSON message: {message}")
        except Exception as e:
            self.logger.error(f"Error processing message: {e} - {message}", exc_info=True)
            traceback.print_exc()

    async def start_coinbase_websocket(self, exchange_connection: ExchangeConnection):
        """
        Start WebSocket subscription for ticker and level2 data with JWT authentication.

        Args:
            exchange_connection (ExchangeConnection): The ExchangeConnection instance for JWT generation.
        """
        # Wait for historical data to be initialized
        while not self.historical_initialized:
            await asyncio.sleep(1)

        while True:
            try:
                ws_url = "wss://advanced-trade-ws.coinbase.com"
                jwt_token = exchange_connection.generate_jwt()
                if not jwt_token:
                    self.logger.error("Failed to generate JWT for WebSocket authentication")
                    await asyncio.sleep(5)
                    continue

                async with websockets.connect(ws_url) as websocket:
                    self.ws_connections['main'] = websocket
                    product_ids = [symbol.replace('/', '-') for symbol in self.symbols]
                    # Subscribe to ticker and level2
                    subscriptions = [
                        {
                            "type": "subscribe",
                            "product_ids": product_ids,
                            "channel": "ticker",
                            "jwt": jwt_token
                        },
                        {
                            "type": "subscribe",
                            "product_ids": product_ids,
                            "channel": "level2",
                            "jwt": jwt_token
                        }
                    ]
                    for subscription in subscriptions:
                        self.logger.debug(f"Sending subscription: {json.dumps(subscription, indent=2)}")
                        await websocket.send(json.dumps(subscription))
                    self.logger.info(f"Subscribed to ticker and level2 WebSocket for {self.symbols}")

                    last_jwt_refresh_time = asyncio.get_event_loop().time()
                    while True:
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=90)
                            await self.process_message(message, websocket)
                        except asyncio.TimeoutError:
                            if asyncio.get_event_loop().time() - last_jwt_refresh_time > 90:
                                self.logger.info("Refreshing JWT for WebSocket")
                                jwt_token = exchange_connection.generate_jwt()
                                if jwt_token:
                                    for subscription in subscriptions:
                                        subscription['jwt'] = jwt_token
                                        self.logger.debug(f"Re-sending subscription with new JWT: {json.dumps(subscription, indent=2)}")
                                        await websocket.send(json.dumps(subscription))
                                    self.logger.info(f"Re-subscribed with new JWT for {self.symbols}")
                                    last_jwt_refresh_time = asyncio.get_event_loop().time()
                        except websockets.ConnectionClosed as e:
                            self.logger.warning(f"WebSocket connection closed with code {e.code}, reason: {e.reason}. Reconnecting...")
                            break
                        except Exception as e:
                            self.logger.error(f"Error in WebSocket: {e}", exc_info=True)

            except Exception as e:
                self.logger.error(f"Failed to start WebSocket: {e}", exc_info=True)
                await asyncio.sleep(5)

    async def close_websockets(self):
        """
        Close all managed WebSocket connections.
        """
        if self.ws_connections:
            for ws in self.ws_connections.values():
                await ws.close()
            self.ws_connections = {}
            self.logger.info("All WebSocket connections closed.")
        else:
            self.logger.info("No WebSocket connections to close.")
