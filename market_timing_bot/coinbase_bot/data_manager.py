import asyncio
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import pandas as pd
import websockets
from exchange_connection import ExchangeConnection
from datetime import datetime

class DataManager:
    def __init__(self, symbols: list, exchange_connection: ExchangeConnection, enable_logging: bool = True):
        """
        Initializes the DataManager class for multiple symbols.
        """
        self.symbols = [symbol.upper() for symbol in symbols]
        self.exchange_connection = exchange_connection
        self.enable_logging = enable_logging

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

        self.rest_exchange = exchange_connection.rest_exchange
        if self.rest_exchange is None:
            self.logger.error("No REST exchange instance available from ExchangeConnection")
            raise ValueError("ExchangeConnection has no valid REST exchange")

        asyncio.run_coroutine_threadsafe(self._validate_symbols(), asyncio.get_event_loop())

        self.klines_buffer_1m = {symbol: pd.DataFrame() for symbol in self.symbols}
        self.klines_buffer_5m = {symbol: pd.DataFrame() for symbol in self.symbols}
        self.klines_buffer_15m = {symbol: pd.DataFrame() for symbol in self.symbols}
        self.klines_buffer_1h = {symbol: pd.DataFrame() for symbol in self.symbols}
        self.klines_buffer_6h = {symbol: pd.DataFrame() for symbol in self.symbols}
        self.klines_buffer_1d = {symbol: pd.DataFrame() for symbol in self.symbols}
        self.order_book_buffer = {symbol: pd.DataFrame() for symbol in self.symbols}
        self.ticker_buffer = {symbol: pd.DataFrame(columns=['timestamp', 'symbol', 'last_price', 'volume_24h', 'best_bid', 'best_ask', 'side']) for symbol in self.symbols}
        self.ws_connections = {}
        self.ws_tasks = []
        self.websocket_task = None
        self.last_ticker_price = {symbol: None for symbol in self.symbols}
        self.ticker_logged = {symbol: False for symbol in self.symbols}
        self.buffer_log_counter = {symbol: 0 for symbol in self.symbols}
        self.historical_initialized = False
        self.last_l2_data_time = {symbol: None for symbol in self.symbols}
        self.subscription_confirmed = {symbol: {'ticker': False, 'level2': False} for symbol in self.symbols}
        self.subscription_attempts = {symbol: {'ticker': 0, 'level2': 0} for symbol in self.symbols}
        self.message_queue = asyncio.Queue(maxsize=2000)

        asyncio.create_task(self._initialize_and_start_tasks())

    async def _validate_symbols(self):
        """
        Validates that all symbols are valid product IDs via REST API.
        """
        try:
            markets = await self.rest_exchange.fetch_markets()
            valid_product_ids = [market['id'].upper() for market in markets]
            invalid_symbols = [symbol for symbol in self.symbols if symbol not in valid_product_ids]
            if invalid_symbols:
                self.logger.error(f"Invalid product IDs: {invalid_symbols}")
                raise ValueError(f"Invalid product IDs: {invalid_symbols}")
            for symbol in self.symbols:
                self.logger.info(f"Validated product ID: {symbol}")
        except Exception as e:
            self.logger.error(f"Error validating symbols: {e}", exc_info=True)
            raise

    async def _initialize_and_start_tasks(self):
        """
        Fetches initial historical klines and starts REST update tasks.
        """
        try:
            await self._fetch_initial_historical_data()
            self.historical_initialized = True
            self.logger.info("Completed initial historical kline fetch for all timeframes")
            asyncio.create_task(self._update_buffers_periodically())
            asyncio.create_task(self._process_message_queue())
            asyncio.create_task(self.start_coinbase_websocket(self.exchange_connection))
            self.logger.info("Started REST update tasks for klines and order book, and WebSocket for ticker.")
        except Exception as e:
            self.logger.error(f"Error in initialization tasks: {e}", exc_info=True)

    async def _fetch_initial_historical_data(self):
        """
        Fetches initial historical klines for all Coinbase timeframes.
        """
        max_retries = 5
        for symbol in self.symbols:
            for interval in ['1m', '5m', '15m', '1h', '6h', '1d']:
                attempt = 0
                while attempt < max_retries:
                    try:
                        klines = await self.fetch_historical_data_with_retry(symbol, interval, 300)
                        if klines and len(klines) > 0:
                            df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
                            for col in ['open', 'high', 'low', 'close', 'volume']:
                                df[col] = pd.to_numeric(df[col], errors='coerce')
                            if df[['open', 'high', 'low', 'close']].isna().any().any():
                                self.logger.warning(f"NaN values in {interval} klines for {symbol}")
                                attempt += 1
                                continue
                            getattr(self, f'klines_buffer_{interval}')[symbol] = df
                            self.logger.info(f"Initialized {interval} klines for {symbol}, shape: {df.shape}, latest timestamp: {df['timestamp'].max()}, fetched: {len(klines)}")
                            self.logger.debug(f"Klines buffer for {symbol} ({interval}):\n{df.tail(5).to_string()}")
                            break
                        else:
                            self.logger.warning(f"Empty or no klines fetched for {interval} {symbol}")
                    except Exception as e:
                        self.logger.error(f"Error fetching initial {interval} klines for {symbol} on attempt {attempt + 1}: {e}", exc_info=True)
                    attempt += 1
                    await asyncio.sleep(10)
                if attempt == max_retries:
                    self.logger.error(f"Failed to initialize {interval} klines for {symbol} after {max_retries} retries")



    async def _update_buffers_periodically(self):
        """
        Periodically fetches recent klines and order book data via REST API every 60 seconds.
        """
        failure_counts = {symbol: {'klines': {tf: 0 for tf in ['1m', '5m', '15m', '1h', '6h', '1d']}, 'order_book': 0} for symbol in self.symbols}
        max_failures = 5

        while True:
            for symbol in self.symbols:
                for timeframe in ['1m', '5m', '15m', '1h', '6h', '1d']:
                    try:
                        klines = await self.fetch_historical_data_with_retry(symbol, timeframe, 10)
                        if klines and len(klines) > 0:
                            new_df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                            new_df['timestamp'] = pd.to_datetime(new_df['timestamp'], unit='ms', utc=True)
                            for col in ['open', 'high', 'low', 'close', 'volume']:
                                new_df[col] = pd.to_numeric(new_df[col], errors='coerce')
                            if new_df[['open', 'high', 'low', 'close']].isna().any().any():
                                self.logger.warning(f"NaN values in new {timeframe} klines for {symbol}")
                                failure_counts[symbol]['klines'][timeframe] += 1
                                continue
                            buffer_key = f'klines_buffer_{timeframe}'
                            buffer = getattr(self, buffer_key)[symbol]
                            if not buffer.empty:
                                self.logger.debug(f"Buffer size before concat for {symbol} ({timeframe}): {len(buffer)}")
                                buffer = pd.concat([buffer, new_df], ignore_index=True)
                                self.logger.debug(f"Buffer size before deduplication: {len(buffer)}")
                                buffer = buffer.drop_duplicates(subset=['timestamp'], keep='last')
                                self.logger.debug(f"Buffer size after deduplication: {len(buffer)}")
                                buffer = buffer.tail(300)
                                self.logger.debug(f"Buffer size after tail: {len(buffer)}")
                            else:
                                buffer = new_df
                            getattr(self, buffer_key)[symbol] = buffer
                            self.logger.info(f"Updated {timeframe} klines for {symbol}, shape: {buffer.shape}, latest timestamp: {buffer['timestamp'].max()}")
                            if self.buffer_log_counter[symbol] % 10 == 0:
                                self.logger.debug(f"Klines buffer for {symbol} ({timeframe}):\n{buffer.tail(5).to_string()}")
                            failure_counts[symbol]['klines'][timeframe] = 0
                        else:
                            self.logger.warning(f"No new klines fetched for {timeframe} {symbol}")
                            failure_counts[symbol]['klines'][timeframe] += 1
                        if failure_counts[symbol]['klines'][timeframe] >= max_failures:
                            self.logger.error(f"Reached {max_failures} consecutive failures for {timeframe} klines for {symbol}, reinitializing")
                            await self._fetch_initial_historical_data_for_symbol(symbol, timeframe)
                            failure_counts[symbol]['klines'][timeframe] = 0
                        await asyncio.sleep(1)
                    except Exception as e:
                        self.logger.error(f"Error updating {timeframe} klines for {symbol}: {e}", exc_info=True)
                        failure_counts[symbol]['klines'][timeframe] += 1
                        if failure_counts[symbol]['klines'][timeframe] >= max_failures:
                            self.logger.error(f"Reached {max_failures} consecutive failures for {timeframe} klines for {symbol}, reinitializing")
                            await self._fetch_initial_historical_data_for_symbol(symbol, timeframe)
                            failure_counts[symbol]['klines'][timeframe] = 0

                try:
                    symbol_ccxt = symbol.replace('/', '-')
                    order_book = await self.fetch_order_book_with_retry(symbol_ccxt)
                    if order_book:
                        updates_list = []
                        timestamp = pd.to_datetime(datetime.utcnow().isoformat(), utc=True)
                        for side, entries in [('bid', order_book['bids']), ('ask', order_book['asks'])]:
                            for price, quantity in entries:
                                updates_list.append({
                                    'timestamp': timestamp,
                                    'symbol': symbol,
                                    'side': side,
                                    'price_level': float(price or 0),
                                    'quantity': float(quantity or 0)
                                })
                        new_data = pd.DataFrame(updates_list)
                        if new_data.empty:
                            self.logger.warning(f"Empty order book data for {symbol} after processing")
                            failure_counts[symbol]['order_book'] += 1
                        else:
                            self.order_book_buffer[symbol] = new_data
                            self.order_book_buffer[symbol] = self.order_book_buffer[symbol].drop_duplicates(subset=['symbol', 'side', 'price_level'], keep='last')
                            self.logger.info(f"Order book buffer updated for {symbol}, shape: {self.order_book_buffer[symbol].shape}")
                            if self.buffer_log_counter[symbol] % 10 == 0:
                                self.logger.debug(f"Order book contents for {symbol}:\n{self.order_book_buffer[symbol].tail(5).to_string()}")
                            failure_counts[symbol]['order_book'] = 0
                    else:
                        self.logger.warning(f"No order book data fetched for {symbol}")
                        failure_counts[symbol]['order_book'] += 1
                    if failure_counts[symbol]['order_book'] >= max_failures:
                        self.logger.error(f"Reached {max_failures} consecutive failures for order book for {symbol}, resetting buffer")
                        self.order_book_buffer[symbol] = pd.DataFrame()
                        failure_counts[symbol]['order_book'] = 0
                    await asyncio.sleep(1)
                except Exception as e:
                    self.logger.error(f"Error updating order book for {symbol}: {e}", exc_info=True)
                    failure_counts[symbol]['order_book'] += 1
                    if failure_counts[symbol]['order_book'] >= max_failures:
                        self.logger.error(f"Reached {max_failures} consecutive failures for order book for {symbol}, resetting buffer")
                        self.order_book_buffer[symbol] = pd.DataFrame()
                        failure_counts[symbol]['order_book'] = 0

                self.buffer_log_counter[symbol] = (self.buffer_log_counter[symbol] + 1) % 10
            await asyncio.sleep(60)


    
    def get_buffer(self, symbol: str, buffer_type: str) -> pd.DataFrame:
        """
        Retrieves the specified buffer for a given symbol.
        """
        if symbol not in self.symbols:
            self.logger.error(f"Invalid symbol: {symbol}")
            raise ValueError(f"Symbol {symbol} not found in DataManager symbols")
        buffer_map = {
            'ticker': self.ticker_buffer,
            'klines_1m': self.klines_buffer_1m,
            'klines_5m': self.klines_buffer_5m,
            'klines_15m': self.klines_buffer_15m,
            'klines_1h': self.klines_buffer_1h,
            'klines_6h': self.klines_buffer_6h,
            'klines_1d': self.klines_buffer_1d,
            'order_book': self.order_book_buffer
        }
        if buffer_type not in buffer_map:
            self.logger.error(f"Invalid buffer type: {buffer_type}")
            raise ValueError(f"Buffer type {buffer_type} not supported")
        buffer = buffer_map[buffer_type][symbol]
        if buffer.empty:
            self.logger.warning(f"Empty buffer for {symbol} ({buffer_type})")
        else:
            self.logger.debug(f"Retrieved buffer for {symbol} ({buffer_type}), shape: {buffer.shape}")
        return buffer



    async def fetch_historical_data_with_retry(self, symbol: str, timeframe: str, limit: int = 300, max_attempts: int = 5):
        """
        Fetch historical klines with retry logic, accumulating up to the specified limit.

        Args:
            symbol: Trading pair symbol (e.g., 'HBAR-USD').
            timeframe: Timeframe (e.g., '1h', '1d').
            limit: Number of klines to fetch (default: 300).
            max_attempts: Maximum retry attempts per fetch (default: 5).

        Returns:
            List of klines or None if fetch fails.
        """
        symbol_ccxt = symbol.replace('/', '-')
        timeframe_map = {'1m': '1m', '5m': '5m', '15m': '15m', '1h': '1h', '6h': '6h', '1d': '1d'}
        if timeframe not in timeframe_map:
            self.logger.error(f"Invalid timeframe: {timeframe}")
            return None
        all_klines = []
        remaining = limit
        since = None
        base_delay = 2
        while remaining > 0:
            attempt = 0
            while attempt < max_attempts:
                try:
                    self.rest_exchange.aiohttp_timeout = 60000
                    klines = await self.rest_exchange.fetch_ohlcv(
                        symbol_ccxt,
                        timeframe_map[timeframe],
                        limit=min(remaining, 300),  # Increased to 300 to reduce API calls
                        since=since
                    )
                    if not klines:
                        self.logger.debug(f"No more klines available for {symbol} {timeframe}")
                        break
                    all_klines.extend(klines)
                    fetched_count = len(klines)
                    remaining -= fetched_count
                    self.logger.debug(f"Fetched {fetched_count} {timeframe} klines for {symbol}, {remaining} remaining, total: {len(all_klines)}")
                    if remaining > 0 and klines:
                        # Set 'since' to the timestamp before the earliest fetched kline
                        since = int(klines[0][0] - 1000 * 60 * 60)  # 1 hour earlier
                    await asyncio.sleep(0.5)  # Respect rate limits
                    break  # Successful fetch, proceed to next batch
                except Exception as e:
                    self.logger.error(f"Attempt {attempt + 1} failed to fetch {timeframe} klines for {symbol}: {e}", exc_info=True)
                    if attempt < max_attempts - 1:
                        delay = base_delay * (2 ** attempt)
                        self.logger.debug(f"Retrying after {delay} seconds")
                        await asyncio.sleep(delay)
                    attempt += 1
            if attempt == max_attempts:
                self.logger.error(f"Failed to fetch {timeframe} klines for {symbol} after {max_attempts} attempts")
                return None
            if not klines:  # No more data available
                break
        if not all_klines:
            self.logger.error(f"No klines fetched for {symbol} {timeframe}")
            return None
        all_klines.sort(key=lambda x: x[0])
        all_klines = all_klines[-limit:]  # Take the most recent 'limit' klines
        self.logger.info(f"Total fetched {len(all_klines)} {timeframe} klines for {symbol}")
        return [[int(k[0]), k[1], k[2], k[3], k[4], k[5]] for k in all_klines]


    
    async def fetch_order_book_with_retry(self, symbol_ccxt: str, max_attempts: int = 10):
        """
        Fetch order book data with retry logic.
        """
        base_delay = 2
        attempt = 0
        while attempt < max_attempts:
            try:
                order_book = await self.rest_exchange.fetch_order_book(symbol_ccxt)
                if not order_book or not (order_book.get('bids') and order_book.get('asks')):
                    self.logger.warning(f"Empty or invalid order book for {symbol_ccxt} on attempt {attempt + 1}")
                    raise ValueError("Empty order book returned")
                self.logger.debug(f"Fetched order book for {symbol_ccxt}, bids: {len(order_book['bids'])}, asks: {len(order_book['asks'])}")
                return order_book
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed to fetch order book for {symbol_ccxt}: {e}", exc_info=True)
                if attempt < max_attempts - 1:
                    delay = base_delay * (2 ** attempt)
                    if '502 Bad Gateway' in str(e):
                        self.logger.warning(f"502 Bad Gateway detected, increasing retry delay to {delay * 2}s")
                        delay *= 2
                    await asyncio.sleep(delay)
                attempt += 1
        self.logger.error(f"Failed to fetch order book for {symbol_ccxt} after {max_attempts} attempts")
        return None

    
    async def _process_ticker_message(self, ticker: dict, symbol: str):
        """
        Processes ticker messages and updates the ticker buffer.
        """
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
                self.ticker_buffer[symbol] = self.ticker_buffer[symbol][-1000:]
            log_ticker = False
            if not self.ticker_logged[symbol]:
                log_ticker = True
                self.ticker_logged[symbol] = True
            elif self.last_ticker_price[symbol] is not None and price != 0:
                if abs(price - self.last_ticker_price[symbol]) / self.last_ticker_price[symbol] > 0.01:
                    log_ticker = True
            if log_ticker:
                self.logger.info(f"Ticker buffer updated for {symbol}, shape: {self.ticker_buffer[symbol].shape}, last_price: {price}")
                self.logger.debug(f"Ticker contents for {symbol}:\n{self.ticker_buffer[symbol].tail(5).to_string()}")
            self.last_ticker_price[symbol] = price
        except Exception as e:
            self.logger.error(f"Error processing ticker message for {symbol}: {e} - {ticker}", exc_info=True)

    async def _process_message_queue(self):
        """
        Processes messages from the queue to prevent event loop overload.
        """
        while True:
            try:
                message, websocket = await self.message_queue.get()
                await self.process_message(message, websocket)
                self.message_queue.task_done()
                self.logger.debug(f"Message queue size: {self.message_queue.qsize()}")
                await asyncio.sleep(0.001)
            except Exception as e:
                self.logger.error(f"Error processing queued message: {e}", exc_info=True)

    
    async def process_message(self, message: str, websocket):
        """
        Processes incoming WebSocket messages.
        """
        try:
            self.logger.debug(f"Raw WebSocket message: {message}")
            parsed_message = json.loads(message)
            channel = parsed_message.get('channel')
            self.logger.debug(f"Received WebSocket message: channel={channel}, full_message={parsed_message}")
            if channel == 'ticker':
                for event in parsed_message.get('events', []):
                    for ticker in event.get('tickers', []):
                        product_id = ticker.get('product_id', '').upper()
                        if not product_id:
                            self.logger.warning(f"Ticker message missing product_id: {ticker}")
                            continue
                        if product_id not in self.symbols:
                            continue
                        await self._process_ticker_message(ticker, product_id)
            elif channel == 'l2_data':
                self.logger.warning(f"Received l2_data message, but order book is REST-only. Ignoring for {parsed_message.get('product_id', 'N/A')}")
            elif channel == 'subscriptions':
                self.logger.info(f"Subscription FacadeSubscription confirmation: {parsed_message}")
                subscriptions = parsed_message.get('events', [{}])[0].get('subscriptions', {})
                if 'ticker' in subscriptions:
                    confirmed = [s.upper() for s in subscriptions['ticker']]
                    self.logger.info(f"Ticker subscription confirmed for: {confirmed}")
                    for symbol in confirmed:
                        if symbol in self.symbols:
                            self.subscription_confirmed[symbol]['ticker'] = True
                            self.subscription_attempts[symbol]['ticker'] = 0
                if 'level2' in subscriptions:
                    confirmed = [s.upper() for s in subscriptions['level2']]
                    self.logger.info(f"Level2 subscription confirmed for: {confirmed}")
                    for symbol in confirmed:
                        if symbol in self.symbols:
                            self.subscription_confirmed[symbol]['level2'] = True
                            self.subscription_attempts[symbol]['level2'] = 0
            elif channel == 'error':
                self.logger.error(f"WebSocket error: {parsed_message}")
                if 'message' in parsed_message:
                    self.logger.error(f"Error details: {parsed_message['message']}")
            elif channel is None:
                self.logger.warning(f"Received message with null channel: {parsed_message}")
            else:
                self.logger.warning(f"Received unknown channel: {channel}, message: {parsed_message}")
        except json.JSONDecodeError:
            self.logger.error(f"Error decoding JSON message: {message}")
        except Exception as e:
            self.logger.error(f"Error processing message: {e}, message: {message}", exc_info=True)


    async def start_coinbase_websocket(self, exchange_connection: ExchangeConnection):
        """
        Start WebSocket subscription for ticker data with JWT authentication.
        """
        while not self.historical_initialized:
            await asyncio.sleep(1)
        max_reconnect_attempts = 10
        reconnect_attempt = 0
        reconnect_delay = 1
        max_subscription_attempts = 5
        base_subscription_delay = 3
        while reconnect_attempt < max_reconnect_attempts:
            try:
                ws_url = "wss://advanced-trade-ws.coinbase.com"
                async with websockets.connect(ws_url, ping_interval=20, ping_timeout=10, max_size=2**21, max_queue=2000) as websocket:
                    self.ws_connections['main'] = websocket
                    jwt_token = exchange_connection.generate_jwt()
                    if not jwt_token:
                        self.logger.error("Failed to generate JWT for WebSocket authentication")
                        await asyncio.sleep(10)
                        reconnect_attempt += 1
                        continue
                    product_ids = self.symbols
                    channels_to_subscribe = ['ticker']
                    for channel in channels_to_subscribe:
                        if any(self.subscription_attempts[symbol][channel] < max_subscription_attempts for symbol in self.symbols):
                            subscription = {
                                "type": "subscribe",
                                "product_ids": product_ids,
                                "channel": channel,
                                "jwt": jwt_token
                            }
                            self.logger.debug(f"Sending {channel} subscription for {product_ids}: {json.dumps(subscription)}")
                            await websocket.send(json.dumps(subscription))
                            for symbol in self.symbols:
                                self.subscription_attempts[symbol][channel] += 1
                            await asyncio.sleep(3)
                    self.logger.info(f"Subscribed to ticker WebSocket for {self.symbols}")
                    reconnect_attempt = 0
                    last_jwt_refresh_time = asyncio.get_event_loop().time()
                    last_heartbeat = asyncio.get_event_loop().time()
                    while True:
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=30)
                            await self.message_queue.put((message, websocket))
                            last_heartbeat = asyncio.get_event_loop().time()
                        except asyncio.TimeoutError:
                            current_time = asyncio.get_event_loop().time()
                            for symbol in self.symbols:
                                for channel in ['ticker']:
                                    if self.subscription_attempts[symbol][channel] >= max_subscription_attempts:
                                        continue
                                    confirmed = self.subscription_confirmed[symbol][channel]
                                    data_received = (self.last_ticker_price[symbol] is not None)
                                    if not confirmed or not data_received:
                                        delay = base_subscription_delay * (2 ** self.subscription_attempts[symbol][channel])
                                        self.logger.warning(f"No {channel} data or confirmation for {symbol} after attempt {self.subscription_attempts[symbol][channel]}, retrying in {delay}s")
                                        jwt_token = exchange_connection.generate_jwt()
                                        subscription = {
                                            "type": "subscribe",
                                            "product_ids": [symbol],
                                            "channel": channel,
                                            "jwt": jwt_token
                                        }
                                        self.logger.debug(f"Resending {channel} subscription for {symbol}: {json.dumps(subscription)}")
                                        await websocket.send(json.dumps(subscription))
                                        self.subscription_attempts[symbol][channel] += 1
                                        await asyncio.sleep(3)
                                        if self.subscription_attempts[symbol][channel] >= max_subscription_attempts:
                                            self.logger.error(f"Max subscription attempts ({max_subscription_attempts}) reached for {symbol} {channel}")
                            if current_time - last_heartbeat > 60:
                                self.logger.warning("No WebSocket messages received for 60s, reconnecting...")
                                break
                            if current_time - last_jwt_refresh_time > 90:
                                self.logger.info("Refreshing JWT for WebSocket")
                                jwt_token = exchange_connection.generate_jwt()
                                if jwt_token:
                                    for channel in channels_to_subscribe:
                                        subscription = {
                                            "type": "subscribe",
                                            "product_ids": product_ids,
                                            "channel": channel,
                                            "jwt": jwt_token
                                        }
                                        await websocket.send(json.dumps(subscription))
                                        await asyncio.sleep(3)
                                    self.logger.info(f"Re-subscribed with new JWT for {self.symbols}")
                                    last_jwt_refresh_time = current_time
                        except websockets.ConnectionClosed as e:
                            self.logger.warning(f"WebSocket closed: {e.code}, {e.reason}. Reconnecting...")
                            break
                        except Exception as e:
                            self.logger.error(f"WebSocket error: {e}", exc_info=True)
            except websockets.exceptions.ConnectionClosedOK as e:
                self.logger.warning(f"WebSocket closed normally: {e.code}, {e.reason}. Reconnecting...")
                reconnect_attempt += 1
            except Exception as e:
                self.logger.error(f"Failed to start WebSocket: {e}", exc_info=True)
                reconnect_attempt += 1
            if reconnect_attempt < max_reconnect_attempts:
                self.logger.info(f"Reconnecting WebSocket, attempt {reconnect_attempt + 1}/{max_reconnect_attempts}")
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, 60)
            else:
                self.logger.error(f"Max WebSocket reconnect attempts ({max_reconnect_attempts}) reached. Giving up.")
                break

    async def close_websockets(self):
        """
        Close all managed WebSocket connections.
        """
        if self.ws_connections:
            for ws in self.ws_connections.values():
                try:
                    await ws.close()
                except Exception as e:
                    self.logger.error(f"Error closing WebSocket: {e}")
            self.ws_connections = {}
            self.logger.info("All WebSocket connections closed.")

    async def _fetch_initial_historical_data_for_symbol(self, symbol: str, timeframe: str):
        """
        Fetches initial historical klines for a specific symbol and timeframe.
        """
        max_retries = 5
        attempt = 0
        while attempt < max_retries:
            try:
                klines = await self.fetch_historical_data_with_retry(symbol, timeframe, 300)
                if klines and len(klines) > 0:
                    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    if df[['open', 'high', 'low', 'close']].isna().any().any():
                        self.logger.warning(f"NaN values in {timeframe} klines for {symbol}")
                        attempt += 1
                        continue
                    getattr(self, f'klines_buffer_{timeframe}')[symbol] = df
                    self.logger.info(f"Reinitialized {timeframe} klines for {symbol}, shape: {df.shape}, latest timestamp: {df['timestamp'].max()}, fetched: {len(klines)}")
                    self.logger.debug(f"Klines buffer for {symbol} ({timeframe}):\n{df.tail(5).to_string()}")
                    break
                else:
                    self.logger.warning(f"Empty or no klines fetched for {timeframe} {symbol}")
            except Exception as e:
                self.logger.error(f"Error reinitializing {timeframe} klines for {symbol} on attempt {attempt + 1}: {e}", exc_info=True)
            attempt += 1
            await asyncio.sleep(10)
        if attempt == max_retries:
            self.logger.error(f"Failed to reinitialize {timeframe} klines for {symbol} after {max_retries} retries")
            getattr(self, f'klines_buffer_{timeframe}')[symbol] = pd.DataFrame()
