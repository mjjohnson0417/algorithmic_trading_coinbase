# data_manager.py
import asyncio
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import pandas as pd
import websockets
import ccxt.async_support as ccxt
from exchange_connection import ExchangeConnection
from datetime import datetime
import traceback
from key_loader import KeyLoader

class DataManager:
    def __init__(self, symbols: list, exchange_connection: ExchangeConnection, enable_logging: bool = True):
        """
        Initializes the DataManager class for multiple symbols.

        Args:
            symbols (list): List of trading pair symbols (e.g., ['HBAR-USDT', 'BTC-USDT']).
            exchange_connection (ExchangeConnection): The ExchangeConnection instance for JWT generation.
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
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.WARNING)

        # Initialize ccxt.coinbase for historical data
        self.rest_exchange = ccxt.coinbase({
            'apiKey': exchange_connection.api_key,
            'secret': exchange_connection.secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })

        # Initialize buffers
        self.klines_buffer_1h = {symbol: pd.DataFrame() for symbol in symbols}
        self.klines_buffer_1m = {symbol: pd.DataFrame() for symbol in symbols}
        self.klines_buffer_1d = {symbol: pd.DataFrame() for symbol in symbols}
        self.order_book_buffer = {symbol: pd.DataFrame() for symbol in symbols}
        self.ticker_buffer = {symbol: pd.DataFrame(columns=['timestamp', 'symbol', 'last_price', 'volume_24h', 'best_bid', 'best_ask', 'side']) for symbol in symbols}
        self.ws_connections = {}
        self.ws_tasks = []
        self.kline_tasks = {symbol: {} for symbol in symbols}
        self.ticker_ws_task = None
        self.last_ticker_price = {symbol: None for symbol in symbols}
        self.ticker_logged = {symbol: False for symbol in symbols}

        # Start ticker WebSocket task
        self.ticker_ws_task = asyncio.create_task(self.start_coinbase_ticker_websocket(exchange_connection))
        self.logger.info("Started ticker WebSocket task")

        # Fetch initial historical klines and start update tasks afterward
        asyncio.create_task(self._initialize_and_start_tasks())

    async def _initialize_and_start_tasks(self):
        """
        Fetches initial historical klines and then starts kline update tasks.
        """
        await self._fetch_initial_historical_data()
        # Start kline update tasks after initialization
        for symbol in self.symbols:
            self.kline_tasks[symbol]['1h'] = asyncio.create_task(self.check_new_1h_kline(symbol))
            self.kline_tasks[symbol]['1d'] = asyncio.create_task(self.check_new_1d_kline(symbol))
            self.logger.info(f"Started kline update tasks for {symbol} (1h, 1d)")

    async def _fetch_initial_historical_data(self):
        """
        Fetches initial historical klines for 1h and 1d to populate buffers with the latest 40 klines.
        """
        max_retries = 5
        for symbol in self.symbols:
            for interval in ['1h', '1d']:
                attempt = 0
                while attempt < max_retries:
                    try:
                        klines = await self.fetch_historical_data_with_retry(symbol, interval, 40)  # Fetch 40 klines
                        if klines and len(klines) > 0:
                            df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
                            if interval == '1h':
                                self.klines_buffer_1h[symbol] = df
                                self.logger.info(f"Initialized 1h klines for {symbol}, shape: {df.shape}, latest timestamp: {df['timestamp'].max()}")
                                self.logger.info(f"1h kline contents for {symbol}:\n{df.to_string()}")
                            elif interval == '1d':
                                self.klines_buffer_1d[symbol] = df
                                self.logger.info(f"Initialized 1d klines for {symbol}, shape: {df.shape}, latest timestamp: {df['timestamp'].max()}")
                                self.logger.info(f"1d kline contents for {symbol}:\n{df.to_string()}")
                            break
                        else:
                            self.logger.warning(f"Empty or no klines fetched for {interval} {symbol}")
                    except Exception as e:
                        self.logger.error(f"Error fetching initial {interval} klines for {symbol}: {e}")
                    attempt += 1
                    await asyncio.sleep(5)
                if attempt == max_retries:
                    self.logger.error(f"Failed to initialize {interval} klines for {symbol} after {max_retries} retries")

    def get_buffer(self, symbol: str, buffer_type: str) -> pd.DataFrame:
        """
        Retrieves the specified buffer for a given symbol.

        Args:
            symbol (str): The trading symbol (e.g., 'HBAR-USDT').
            buffer_type (str): The type of buffer ('ticker', '1h', '1d', '1m', 'order_book', 'klines_1h', 'klines_1d').

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
            '1h': self.klines_buffer_1h,
            'klines_1h': self.klines_buffer_1h,
            '1d': self.klines_buffer_1d,
            'klines_1d': self.klines_buffer_1d,
            '1m': self.klines_buffer_1m,
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
            symbol (str): Trading pair symbol (e.g., 'HBAR-USDT').
            timeframe (str): Timeframe ('1m', '1h', '1d').
            limit (int): Number of klines to fetch (default 40).
            max_attempts (int): Maximum retry attempts per request.

        Returns:
            list: List of klines, up to 'limit' entries.
        """
        symbol_ccxt = symbol.replace('/', '-')  # Ensure Coinbase format
        timeframe_map = {'1m': '1m', '1h': '1h', '1d': '1d'}
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
                    self.logger.warning(f"Attempt {attempt + 1} failed to fetch {timeframe} klines for {symbol}: {e}")
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
            self.ticker_buffer[symbol] = self.ticker_buffer[symbol].tail(1000)  # Limit buffer size

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
            if message['type'] != 'level2':
                self.logger.warning(f"Unexpected message type for order book: {message['type']}")
                return

            updates = message.get('updates', [])
            if not updates:
                self.logger.warning(f"No updates in order book message for {symbol}")
                return

            for update in updates:
                side = update['side']
                price_level = float(update['price_level'])
                new_quantity = float(update['new_quantity'])

                new_data = pd.DataFrame({
                    'timestamp': [pd.to_datetime(message.get('time', datetime.utcnow().isoformat()), utc=True)],
                    'symbol': [symbol],
                    'side': [side],
                    'price_level': [price_level],
                    'quantity': [new_quantity],
                })
                self.order_book_buffer[symbol] = pd.concat([self.order_book_buffer[symbol], new_data], ignore_index=True)
                self.order_book_buffer[symbol] = self.order_book_buffer[symbol].drop_duplicates(subset=['symbol', 'side', 'price_level'], keep='last')
                self.order_book_buffer[symbol] = self.order_book_buffer[symbol].tail(1000)  # Limit buffer size

            self.logger.debug(f"Order book buffer updated for {symbol}, shape: {self.order_book_buffer[symbol].shape}")
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

            if channel == 'ticker':
                events = parsed_message.get('events', [])
                for event in events:
                    for ticker in event.get('tickers', []):
                        product_id = ticker.get('product_id')
                        if not product_id:
                            self.logger.warning(f"Ticker message missing product_id: {ticker}")
                            continue
                        symbol = product_id  # Use product_id directly (e.g., BTC-USDT)
                        if symbol not in self.symbols:
                            self.logger.debug(f"Ignoring ticker for unsupported symbol: {symbol}")
                            continue
                        await self._process_ticker_message(ticker, symbol)
            elif channel == 'subscriptions':
                self.logger.info(f"Subscription confirmation: {parsed_message}")
            elif channel == 'error':
                self.logger.error(f"WebSocket error: {parsed_message}")
            else:
                self.logger.debug(f"Received unknown channel: {channel}, data: {parsed_message}")

        except json.JSONDecodeError:
            self.logger.error(f"Error decoding JSON message: {message}")
        except Exception as e:
            self.logger.error(f"Error processing message: {e} - {message}", exc_info=True)
            traceback.print_exc()

    async def check_new_1h_kline(self, symbol: str):
        """
        Periodically fetch the newest 1-hour kline via REST API to update buffer.
        """
        while True:
            self.logger.debug(f"Checking for new 1h kline for {symbol}")
            try:
                klines_1h = await self.fetch_historical_data_with_retry(symbol, '1h', 1)  # Fetch newest 1 kline
                if klines_1h and len(klines_1h) > 0:
                    df_1h = pd.DataFrame(klines_1h, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df_1h['timestamp'] = pd.to_datetime(df_1h['timestamp'], unit='ms', utc=True)
                    if not self.klines_buffer_1h[symbol].empty:
                        latest_timestamp = self.klines_buffer_1h[symbol]['timestamp'].max()
                        new_data = df_1h[df_1h['timestamp'] > latest_timestamp]
                        if not new_data.empty:
                            self.klines_buffer_1h[symbol] = pd.concat([self.klines_buffer_1h[symbol], new_data], ignore_index=True)
                            self.klines_buffer_1h[symbol] = self.klines_buffer_1h[symbol].tail(40)  # Limit to 40 rows
                            self.logger.info(f"Updated 1h klines for {symbol} with {len(new_data)} new rows, shape: {self.klines_buffer_1h[symbol].shape}, latest timestamp: {self.klines_buffer_1h[symbol]['timestamp'].max()}")
                            self.logger.debug(f"New 1h kline data for {symbol}:\n{new_data.to_string()}")
                        else:
                            self.logger.debug(f"No new 1h klines for {symbol}")
                    else:
                        self.klines_buffer_1h[symbol] = df_1h.tail(40)
                        self.logger.info(f"Initialized 1h klines for {symbol}, shape: {df_1h.shape}, latest timestamp: {df_1h['timestamp'].max()}")
                        self.logger.info(f"Initialized 1h kline contents for {symbol}:\n{df_1h.to_string()}")
                else:
                    self.logger.warning(f"Failed to fetch 1h klines for {symbol}")
            except Exception as e:
                self.logger.error(f"Error checking 1h kline for {symbol}: {e}")
            await asyncio.sleep(60)  # Check every minute for testing

    async def check_new_1d_kline(self, symbol: str):
        """
        Periodically fetch the newest 1-day kline via REST API to update buffer.
        """
        while True:
            self.logger.debug(f"Checking for new 1d kline for {symbol}")
            try:
                klines_1d = await self.fetch_historical_data_with_retry(symbol, '1d', 1)  # Fetch newest 1 kline
                if klines_1d and len(klines_1d) > 0:
                    df_1d = pd.DataFrame(klines_1d, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df_1d['timestamp'] = pd.to_datetime(df_1d['timestamp'], unit='ms', utc=True)
                    if not self.klines_buffer_1d[symbol].empty:
                        latest_timestamp = self.klines_buffer_1d[symbol]['timestamp'].max()
                        new_data = df_1d[df_1d['timestamp'] > latest_timestamp]
                        if not new_data.empty:
                            self.klines_buffer_1d[symbol] = pd.concat([self.klines_buffer_1d[symbol], new_data], ignore_index=True)
                            self.klines_buffer_1d[symbol] = self.klines_buffer_1d[symbol].tail(40)  # Limit to 40 rows
                            self.logger.info(f"Updated 1d klines for {symbol} with {len(new_data)} new rows, shape: {self.klines_buffer_1d[symbol].shape}, latest timestamp: {self.klines_buffer_1d[symbol]['timestamp'].max()}")
                            self.logger.debug(f"New 1d kline data for {symbol}:\n{new_data.to_string()}")
                        else:
                            self.logger.debug(f"No new 1d klines for {symbol}")
                    else:
                        self.klines_buffer_1d[symbol] = df_1d.tail(40)
                        self.logger.info(f"Initialized 1d klines for {symbol}, shape: {df_1d.shape}, latest timestamp: {df_1d['timestamp'].max()}")
                        self.logger.info(f"Initialized 1d kline contents for {symbol}:\n{df_1d.to_string()}")
                else:
                    self.logger.warning(f"Failed to fetch 1d klines for {symbol}")
            except Exception as e:
                self.logger.error(f"Error checking 1d kline for {symbol}: {e}")
            await asyncio.sleep(600)  # Check every 10 minutes for testing

    async def check_new_1m_kline(self, symbol: str):
        """
        Check for new 1-minute klines and update buffer (disabled).
        """
        self.logger.debug(f"1m kline check for {symbol} is disabled as per configuration")

    async def start_coinbase_ticker_websocket(self, exchange_connection: ExchangeConnection):
        """
        Start WebSocket subscription for ticker data with JWT authentication.

        Args:
            exchange_connection (ExchangeConnection): The ExchangeConnection instance for JWT generation.
        """
        while True:
            try:
                ws_url = "wss://advanced-trade-ws.coinbase.com"
                jwt_token = exchange_connection.generate_jwt()
                if not jwt_token:
                    self.logger.error("Failed to generate JWT for WebSocket authentication")
                    await asyncio.sleep(5)
                    continue

                async with websockets.connect(ws_url) as websocket:
                    self.ws_connections['ticker'] = websocket
                    subscription = {
                        "type": "subscribe",
                        "product_ids": [symbol.replace('/', '-') for symbol in self.symbols],
                        "channel": "ticker",
                        "jwt": jwt_token
                    }
                    await websocket.send(json.dumps(subscription))
                    self.logger.info(f"Subscribed to ticker WebSocket for {self.symbols}")

                    last_jwt_refresh = asyncio.get_event_loop().time()
                    while True:
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=90)
                            await self.process_message(message, websocket)
                        except asyncio.TimeoutError:
                            if asyncio.get_event_loop().time() - last_jwt_refresh > 90:
                                self.logger.info("Refreshing JWT for ticker WebSocket")
                                jwt_token = exchange_connection.generate_jwt()
                                if jwt_token:
                                    subscription['jwt'] = jwt_token
                                    await websocket.send(json.dumps(subscription))
                                    self.logger.info(f"Re-subscribed with new JWT for {self.symbols}")
                                    last_jwt_refresh = asyncio.get_event_loop().time()
                        except websockets.ConnectionClosed as e:
                            self.logger.warning(f"Ticker WebSocket connection closed with code {e.code}, reason: {e.reason}. Reconnecting...")
                            break
                        except Exception as e:
                            self.logger.error(f"Error in ticker WebSocket: {e}", exc_info=True)

            except Exception as e:
                self.logger.error(f"Failed to start ticker WebSocket: {e}", exc_info=True)
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
