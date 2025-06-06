# grid_manager.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import asyncio
from typing import List, Dict
import json
import pandas as pd
import platform  # Added for platform-specific ping commands
from order_operations import OrderOperations
from indicator_calculator import IndicatorCalculator
from state_manager import StateManager

class GridManager:
    MAX_GRID_LEVELS_PER_SYMBOL = 10  # 5 buy, 5 sell levels

    def __init__(self, data_manager, indicator_calculator: IndicatorCalculator, state_manager: StateManager, order_operations_dict: Dict[str, OrderOperations], symbols: List[str], debug: bool = True, enable_logging: bool = True):
        """
        Initializes the GridManager class for multiple tokens.

        Args:
            data_manager: Instance of DataManager.
            indicator_calculator: Instance of IndicatorCalculator.
            state_manager: Instance of StateManager.
            order_operations_dict: Dictionary of OrderOperations instances, keyed by symbol.
            symbols: List of trading pair symbols (e.g., ['BTC-USDT', 'HBAR-USDT']).
            debug: If True, enables verbose debug logging.
            enable_logging: If True, enables logging to file.
        """
        self.data_manager = data_manager
        self.indicator_calculator = indicator_calculator
        self.state_manager = state_manager
        self.order_operations_dict = order_operations_dict
        self.symbols = symbols
        self.debug = debug
        self.enable_logging = enable_logging
        self.allocation_ratio = 0.75  # Allocate 75% of total balance
        #self.allocation_ratio = 0.10  # Allocate 75% of total balance
        self.order_value = 0.0
        self.all_indicators = {}  # Store indicators dictionary
        self.grid_levels = {symbol: [] for symbol in symbols}  # Store grid levels
        self.orders = {symbol: {} for symbol in symbols}  # Store orders as dictionary keyed by buy_level
        self.lttrade = True  # Initialize long-term trading flag
        self.sttrade = True  # Initialize short-term trading flag

        # Set up logger
        self.logger = logging.getLogger('GridManager')
        if self.enable_logging and not any(isinstance(h, RotatingFileHandler) for h in self.logger.handlers):
            log_dir = Path(__file__).parent / 'logs'
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / 'grid_manager.log'
            file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
            self.logger.info(f"Initialized GridManager with symbols: {symbols}, log level: {logging.getLevelName(self.logger.level)}, lttrade: {self.lttrade}, sttrade: {self.sttrade}")
            self.logger.debug(f"Logger initialized, testing log file write, indicator_calculator_id: {id(self.indicator_calculator)}, state_manager_id: {id(self.state_manager)}")
            file_handler.flush()  # Ensure initial logs are written
        elif not self.enable_logging:
            self.logger.addHandler(logging.NullHandler())
            self.logger.setLevel(logging.CRITICAL + 1)

    async def check_network(self) -> bool:
        """
        Checks network connectivity by pinging 8.8.8.8 (Google DNS) using subprocess.
        
        Returns:
            bool: True if ping succeeds, False otherwise.
        """
        if self.enable_logging:
            self.logger.debug("Checking network connectivity by pinging 8.8.8.8")
        try:
            ping_cmd = ["ping", "-c", "1", "-W", "2", "8.8.8.8"]  # Linux: 1 ping, 2s timeout
            # if platform.system() == "Windows":
            #     ping_cmd = ["ping", "-n", "1", "-w", "2000", "8.8.8.8"]  # Windows: 1 ping, 2s timeout
            
            process = await asyncio.create_subprocess_exec(
                *ping_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                if self.enable_logging:
                    self.logger.debug("Network check successful: ping to 8.8.8.8 succeeded")
                return True
            else:
                if self.enable_logging:
                    self.logger.warning(f"Network check failed: ping to 8.8.8.8 returned code {process.returncode}, stderr: {stderr.decode().strip()}")
                return False
        except Exception as e:
            if self.enable_logging:
                self.logger.error(f"Error during network check: {e}", exc_info=True)
            return False

    async def initialize_bot(self) -> None:
        """
            Performs one-time initialization tasks for the bot at startup, including canceling stale buy orders,
            initializing grid levels, setting up the orders dictionary, and syncing order statuses for all symbols.
            Checks ticker buffer readiness with retries (6 attempts, 5-second delays, ~30 seconds total) to ensure
            data availability, handling empty or invalid buffers safely.

            Retries up to 6 times with 5-second delays (total ~30 seconds) if the ticker buffer is empty or invalid.
        """
        if self.enable_logging:
            self.logger.info(f"Starting bot initialization for symbols: {self.symbols}")
        try:
            for symbol in self.symbols:
                # Check ticker buffer readiness with retries
                max_retries = 6
                retry_delay = 5  # seconds
                ticker_ready = False
                for attempt in range(max_retries):
                    try:
                        ticker_df = await self.get_ticker_buffer(symbol)
                        if not ticker_df.empty and 'last_price' in ticker_df.columns and not ticker_df['last_price'].isna().iloc[-1]:
                            self.logger.debug(f"Ticker buffer for {symbol} is ready on attempt {attempt + 1}: rows={len(ticker_df)}, last_price={ticker_df['last_price'].iloc[-1]}")
                            ticker_ready = True
                            break
                        else:
                            self.logger.warning(f"Ticker buffer for {symbol} not ready on attempt {attempt + 1}: empty={ticker_df.empty}, has_last_price={'last_price' in ticker_df.columns}, last_price_not_na={'False (no rows)' if ticker_df.empty else not ticker_df['last_price'].isna().iloc[-1] if 'last_price' in ticker_df.columns else False}")
                            if attempt < max_retries - 1:
                                self.logger.debug(f"Retrying ticker buffer check for {symbol} in {retry_delay} seconds")
                                await asyncio.sleep(retry_delay)
                    except Exception as e:
                        self.logger.error(f"Error checking ticker buffer for {symbol} on attempt {attempt + 1}: {e}", exc_info=True)
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                if not ticker_ready:
                    self.logger.warning(f"Failed to get valid ticker buffer for {symbol} after {max_retries} attempts, proceeding with initialization")

                # Sync all open orders into orders dictionary
                try:
                    await self.update_order_status(symbol)
                    self.logger.info(f"Pre-initialization order sync for {symbol}: {json.dumps(self.orders[symbol], default=str)}")
                except Exception as e:
                    self.logger.error(f"Error syncing open orders for {symbol} during initialization: {e}", exc_info=True)

                # Cancel all open buy orders to clean up stale orders
                try:
                    await self.cancel_all_open_buy_orders(symbol)
                except Exception as e:
                    self.logger.error(f"Error canceling open buy orders for {symbol} during initialization: {e}", exc_info=True)

                # Initialize grid levels
                try:
                    grid_levels = await self.initialize_grid(symbol)
                    if grid_levels:
                        self.grid_levels[symbol] = grid_levels
                        self.logger.info(f"Initialized grid levels for {symbol}: {grid_levels}")
                    else:
                        self.logger.warning(f"Failed to initialize grid levels for {symbol}, grid_levels empty")
                except Exception as e:
                    self.logger.error(f"Error initializing grid for {symbol}: {e}", exc_info=True)

                # Initialize orders dictionary with any remaining open orders
                try:
                    await self.initialize_orders(symbol)
                    self.logger.info(f"Initialized orders for {symbol}: {json.dumps(self.orders[symbol], default=str)}")
                except Exception as e:
                    self.logger.error(f"Error initializing orders for {symbol}: {e}", exc_info=True)

                # Final sync to ensure all orders are tracked
                try:
                    await self.update_order_status(symbol)
                    self.logger.info(f"Post-initialization order sync for {symbol}: {json.dumps(self.orders[symbol], default=str)}")
                except Exception as e:
                    self.logger.error(f"Error syncing order statuses for {symbol} during initialization: {e}", exc_info=True)

            self.logger.info(f"Completed bot initialization for all symbols")
            for handler in self.logger.handlers:
                if isinstance(handler, RotatingFileHandler):
                    handler.flush()
        except Exception as e:
            self.logger.error(f"Error during bot initialization: {e}", exc_info=True)

   
    async def calculate_orders_value(self, symbol: str) -> float:
        """
                Calculates order value for a specific symbol by summing USD and token balances, 
                taking 75%, and dividing by the number of grid levels for the symbol.

                Args:
                    symbol: Trading pair symbol (e.g., 'HBAR-USD').

                Returns:
                    float: Order value in USD.
        """
        if self.enable_logging:
            self.logger.debug(f"Calculating order value for {symbol}")
        
        # Fetch free USD balance
        free_usd = await self.order_operations_dict[symbol].get_usd_balance()
        
        # Sum USD locked in open buy orders and base asset locked in open sell orders
        open_orders = await self.order_operations_dict[symbol].get_open_orders()
        locked_usd = 0.0
        locked_base_asset = 0.0
        for order in open_orders:
            try:
                if order['side'].lower() == 'buy' and order['status'].lower() == 'open':
                    if order.get('amount') is not None and order.get('price') is not None:
                        order_value = float(order['amount']) * float(order['price'])
                        locked_usd += order_value
                        self.logger.debug(f"Open buy order: id={order['id']}, amount={order['amount']}, price={order['price']}, value={order_value}")
                    else:
                        self.logger.warning(f"Buy order {order['id']} missing amount or price, fetching details")
                        order_details = await self.order_operations_dict[symbol].fetch_order_status(order['id'])
                        if order_details and order_details.get('amount') is not None and order_details.get('price') is not None:
                            order_value = float(order_details['amount']) * float(order_details['price'])
                            locked_usd += order_value
                            self.logger.debug(f"Fetched buy order: id={order['id']}, amount={order_details['amount']}, price={order_details['price']}, value={order_value}")
                        else:
                            self.logger.warning(f"Could not fetch valid details for buy order {order['id']}")
                elif order['side'].lower() == 'sell' and order['status'].lower() == 'open':
                    if order.get('amount') is not None:
                        locked_base_asset += float(order['amount'])
                        self.logger.debug(f"Open sell order: id={order['id']}, amount={order['amount']}, price={order.get('price', 'N/A')}")
                    else:
                        self.logger.warning(f"Sell order {order['id']} missing amount, fetching details")
                        order_details = await self.order_operations_dict[symbol].fetch_order_status(order['id'])
                        if order_details and order_details.get('amount') is not None:
                            locked_base_asset += float(order_details['amount'])
                            self.logger.debug(f"Fetched sell order: id={order['id']}, amount={order_details['amount']}, price={order_details.get('price', 'N/A')}")
                        else:
                            self.logger.warning(f"Could not fetch valid details for sell order {order['id']}")
            except Exception as e:
                self.logger.error(f"Error processing order {order.get('id', 'unknown')}: {e}", exc_info=True)
        
        # Combine free and locked USD
        total_usd = free_usd + locked_usd
        self.logger.debug(f"USD balance: free={free_usd:.2f}, locked={locked_usd:.2f}, total={total_usd:.2f}")
        
        base_asset = symbol.split('-')[0]
        ticker_df = self.data_manager.get_buffer(symbol, 'ticker')
        if self.enable_logging:
            self.logger.debug(f"Ticker buffer for {symbol}: empty={ticker_df.empty}, rows={len(ticker_df)}, columns={ticker_df.columns}, last_row={ticker_df.tail(1).to_dict()}")
        
        if not ticker_df.empty and 'last_price' in ticker_df.columns and not ticker_df['last_price'].isna().iloc[-1]:
            current_price = ticker_df['last_price'].iloc[-1]
            token_balance = await self.order_operations_dict[symbol].get_base_asset_balance(base_asset)
            # Include locked base asset in total value
            total_base_asset = token_balance + locked_base_asset
            token_value_usd = total_base_asset * current_price
            total_value = total_usd + token_value_usd
            self.logger.debug(f"{base_asset} balance: free={token_balance:.8f}, locked={locked_base_asset:.8f}, total={total_base_asset:.8f}, value_usd={token_value_usd:.2f}")
        else:
            self.logger.warning(f"No valid ticker price for {symbol}, using only USD balance")
            total_value = total_usd
        
        total_levels = self.MAX_GRID_LEVELS_PER_SYMBOL
        order_value = (self.allocation_ratio * total_value) / total_levels if total_levels > 0 else 0.0
        
        if self.enable_logging:
            self.logger.debug(f"Order value for {symbol}: {order_value:.2f}, total_usd={total_usd:.2f}, total_value={total_value:.2f}")
        
        return order_value

    async def get_exchange_orders(self, symbol: str) -> List[Dict]:
        """
        Fetches all orders (open, canceled, closed, etc.) for the symbol from the exchange.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC-USDT').

        Returns:
            List[Dict]: List of order dictionaries.
        """
        try:
            orders = await self.order_operations_dict[symbol].fetch_all_orders()
            if self.enable_logging:
                self.logger.debug(f"Fetched {len(orders)} orders for {symbol}")
            return orders
        except Exception as e:
            if self.enable_logging:
                self.logger.error(f"Error fetching exchange orders for {symbol}: {e}", exc_info=True)
            return []

    async def update_indicators(self) -> None:
        """
        Fetches and stores all indicators from indicator_calculator.

        Stores the indicators dictionary in self.all_indicators for use in other methods.
        """
        if self.enable_logging:
            self.logger.debug(f"Starting update_indicators, indicator_calculator_id: {id(self.indicator_calculator)}")
        try:
            # Check data_manager buffers
            for symbol in self.symbols:
                klines_1h = self.data_manager.get_buffer(symbol, 'klines_1h')
                klines_1d = self.data_manager.get_buffer(symbol, 'klines_1d')
                if self.enable_logging:
                    self.logger.debug(f"Buffer for {symbol}/klines_1h: empty={klines_1h.empty}, rows={len(klines_1h)}, columns={klines_1h.columns}")
                    self.logger.debug(f"Buffer for {symbol}/klines_1d: empty={klines_1h.empty}, rows={len(klines_1d)}, columns={klines_1d.columns}")
            raw_indicators = self.indicator_calculator.calculate_all_indicators()
            if self.enable_logging:
                self.logger.debug(f"Raw indicators output: {json.dumps(raw_indicators, default=str)}")
            self.all_indicators = raw_indicators
            if self.enable_logging:
                if self.all_indicators:
                    self.logger.info(f"Updated indicators: {json.dumps(self.all_indicators, default=str)}")
                    for symbol in self.all_indicators:
                        atr = self.all_indicators[symbol].get('1h', {}).get('atr14', 'N/A')
                        self.logger.debug(f"Indicator for {symbol}: atr14={atr}")
                else:
                    self.logger.warning("No indicators returned from indicator_calculator")
                self.logger.debug("Completed update_indicators")
                for handler in self.logger.handlers:
                    if isinstance(handler, RotatingFileHandler):
                        handler.flush()
        except Exception as e:
            if self.enable_logging:
                self.logger.error(f"Error updating indicators: {e}", exc_info=True)
            self.all_indicators = {}

    async def get_market_states(self) -> Dict:
        """
        Retrieves the market state dictionary from state_manager.

        Returns:
            Dict: Market state dictionary with long_term and short_term states for each symbol.
        """
        if self.enable_logging:
            self.logger.debug(f"Starting get_market_states, state_manager_id: {id(self.state_manager)}")
        try:
            if self.enable_logging:
                self.logger.debug(f"State dict before calculation: {json.dumps(self.state_manager.state_dict, default=str)}")
            self.state_manager.calculate_all_market_states()
            market_states = self.state_manager.state_dict
            if self.enable_logging:
                if market_states:
                    self.logger.info(f"Market states: {json.dumps(market_states, default=str)}")
                    for symbol in market_states:
                        self.logger.debug(f"Market state for {symbol}: long_term={market_states[symbol].get('long_term')}, short_term={market_states[symbol].get('short_term')}")
                else:
                    self.logger.warning("No market states available in state_manager")
                self.logger.debug("Completed get_market_states")
                for handler in self.logger.handlers:
                    if isinstance(handler, RotatingFileHandler):
                        handler.flush()
            return market_states
        except Exception as e:
            if self.enable_logging:
                self.logger.error(f"Error retrieving market states: {e}", exc_info=True)
            return {}

    async def get_ticker_buffer(self, symbol: str) -> pd.DataFrame:
        """
        Retrieves the ticker buffer for a given symbol from data_manager.

        Args:
            symbol: Trading pair symbol.

        Returns:
            pd.DataFrame: Ticker buffer DataFrame.
        """
        if self.enable_logging:
            self.logger.debug(f"Fetching ticker buffer for {symbol}")
        try:
            ticker_df = self.data_manager.get_buffer(symbol, 'ticker')
            if self.enable_logging:
                self.logger.info(f"Ticker buffer for {symbol}: empty={ticker_df.empty}, rows={len(ticker_df)}, columns={ticker_df.columns}, last_row={ticker_df.tail(1).to_dict()}")
                if ticker_df.empty:
                    self.logger.warning(f"Ticker buffer empty for {symbol}, possible WebSocket subscription issue")
                elif 'last_price' not in ticker_df.columns:
                    self.logger.warning(f"Ticker buffer for {symbol} missing 'last_price' column")
                elif ticker_df['last_price'].isna().any():
                    self.logger.warning(f"Ticker buffer for {symbol} contains NaN values in 'last_price'")
                if len(ticker_df) >= 30:
                    self.logger.debug(f"Last 30 tick prices for {symbol}: {ticker_df['last_price'].tail(30).tolist()}")
                for handler in self.logger.handlers:
                    if isinstance(handler, RotatingFileHandler):
                        handler.flush()
            return ticker_df
        except Exception as e:
            if self.enable_logging:
                self.logger.error(f"Error fetching ticker buffer for {symbol}: {e}", exc_info=True)
            return pd.DataFrame()

    async def initialize_grid(self, symbol: str) -> List[float]:
        """
        Calculates grid levels around the current price using ATR from indicators.

        Args:
            symbol: Trading pair symbol.

        Returns:
            List[float]: Sorted list of grid levels.
        """
        if self.enable_logging:
            self.logger.debug(f"Calculating grid levels for {symbol}")
        try:
            # Get current price from ticker buffer
            ticker_df = await self.get_ticker_buffer(symbol)
            if ticker_df.empty or 'last_price' not in ticker_df.columns or ticker_df['last_price'].isna().iloc[-1]:
                if self.enable_logging:
                    self.logger.warning(f"No valid ticker price for {symbol}, cannot calculate grid levels")
                return []

            current_price = ticker_df['last_price'].iloc[-1]

            # Fetch ATR from all_indicators (1-hour klines, atr14)
            atr = self.all_indicators.get(symbol, {}).get('1h', {}).get('atr14', current_price * 0.02)
            if self.enable_logging:
                self.logger.debug(f"ATR14 for {symbol}: {atr:.4f}")

            # Calculate grid spacing
            #multiplier = 2.0
            multiplier = 1.0
            grid_spacing = max(atr * multiplier, current_price * 0.02)
            levels = set()
            for i in range(self.MAX_GRID_LEVELS_PER_SYMBOL // 2):
                buy_level = current_price - ((i + 0.5) * grid_spacing)
                sell_level = current_price + ((i + 0.5) * grid_spacing)
                levels.add(round(buy_level, 4))
                levels.add(round(sell_level, 4))

            grid_levels = sorted(list(levels))
            if self.enable_logging:
                self.logger.info(f"Grid levels for {symbol}: {grid_levels}")
                for handler in self.logger.handlers:
                    if isinstance(handler, RotatingFileHandler):
                        handler.flush()
            return grid_levels
        except Exception as e:
            if self.enable_logging:
                self.logger.error(f"Error calculating grid levels for {symbol}: {e}", exc_info=True)
            return []

    async def check_grid_reset_condition(self, symbol: str) -> bool:
        """
        Checks if the grid needs to be reset based on 30 consecutive ticks above the maximum grid level.

        Args:
            symbol: Trading pair symbol.

        Returns:
            bool: True if and only if the last 30 ticks are above the highest grid level, False otherwise.
        """
        if self.enable_logging:
            self.logger.debug(f"Checking grid reset condition for {symbol}")
        try:
            # Get ticker buffer
            ticker_df = await self.get_ticker_buffer(symbol)
            if ticker_df.empty or 'last_price' not in ticker_df.columns or ticker_df['last_price'].isna().any():
                if self.enable_logging:
                    self.logger.warning(f"No valid ticker data for {symbol} for grid reset check")
                return False

            # Check if grid levels are initialized
            if not self.grid_levels[symbol]:
                if self.enable_logging:
                    self.logger.warning(f"No grid levels for {symbol}, cannot check reset condition")
                return False

            max_grid_price = max(self.grid_levels[symbol])
            recent_ticks = ticker_df.tail(30)  # Get last 30 ticks

            if len(recent_ticks) < 30:
                if self.enable_logging:
                    self.logger.debug(f"Insufficient ticker data for {symbol}: {len(recent_ticks)} ticks, need 30")
                return False

            # Check if all 30 ticks are above max_grid_price
            grid_reset = (recent_ticks['last_price'] > max_grid_price).all()
            if self.enable_logging:
                self.logger.info(f"Grid reset check for {symbol}: {len(recent_ticks)} ticks, max_grid_price={max_grid_price:.4f}, grid_reset={grid_reset}")
                self.logger.debug(f"Recent tick prices for {symbol}: {recent_ticks['last_price'].tail(30).tolist()}")
                if grid_reset:
                    self.logger.info(f"30 consecutive ticks above grid max [{max_grid_price:.4f}] for {symbol}. Grid reset condition met.")
                else:
                    self.logger.debug(f"Grid reset condition not met for {symbol}: Not all 30 ticks above max_grid_price [{max_grid_price:.4f}]")
                for handler in self.logger.handlers:
                    if isinstance(handler, RotatingFileHandler):
                        handler.flush()
            return grid_reset
        except Exception as e:
            if self.enable_logging:
                self.logger.error(f"Error checking grid reset condition for {symbol}: {e}", exc_info=True)
            return False

    async def initialize_orders(self, symbol: str) -> None:
        """
        Initializes the orders dictionary for a given symbol, with six buy orders (five below and one above current price)
        and six corresponding sell orders (each one grid level above the buy order), keyed by buy_level.
        Sell quantities are initialized to 0.0, to be set when buy orders are filled.
        Skips buy order above current price if an open sell order exists between current price and two grid levels above.
        """
        if self.enable_logging:
            self.logger.debug(f"Initializing orders for {symbol}")
        try:
            if not self.grid_levels[symbol]:
                self.logger.warning(f"No grid levels for {symbol}, cannot initialize orders")
                return
            ticker_df = await self.get_ticker_buffer(symbol)
            if ticker_df.empty or 'last_price' not in ticker_df.columns or ticker_df['last_price'].isna().iloc[-1]:
                self.logger.warning(f"No valid ticker price for {symbol}, cannot initialize orders")
                return
            current_price = ticker_df['last_price'].iloc[-1]
            order_value = await self.calculate_orders_value(symbol)
            if order_value <= 0:
                self.logger.warning(f"Invalid order value {order_value} for {symbol}, cannot initialize orders")
                return
            
            # Clear orders and sync with exchange
            self.orders[symbol] = {}
            await self.update_order_status(symbol)
            self.logger.info(f"Post-clear order sync for {symbol}: {json.dumps(self.orders[symbol], default=str)}")
            
            # Count existing stray sell orders
            stray_sell_count = sum(
                1 for order in self.orders[symbol].values()
                if order['sell_state'] == 'stray_sell'
            )
            self.logger.debug(f"Stray sell orders for {symbol}: {stray_sell_count}")
            
            # Check for sell orders between current price and two grid levels above
            has_sell_in_range = False
            grid_levels = sorted(self.grid_levels[symbol])
            # Find the second grid level above current price
            above_levels = [level for level in grid_levels if level > current_price]
            second_above_level = above_levels[1] if len(above_levels) >= 2 else float('inf')
            for order in self.orders[symbol].values():
                sell_price = order['sell_level']
                if (order['sell_state'] in ['open', 'pending', 'stray_sell'] and
                    current_price < sell_price <= second_above_level):
                    has_sell_in_range = True
                    self.logger.debug(f"Found sell order at {sell_price:.4f} within range ({current_price:.4f}, {second_above_level:.4f}] for {symbol}")
                    break
            
            # Limit grid pairs to fit within MAX_GRID_LEVELS_PER_SYMBOL
            max_grid_pairs = max(0, self.MAX_GRID_LEVELS_PER_SYMBOL - stray_sell_count)
            if max_grid_pairs < 6:
                self.logger.info(f"Reducing grid pairs for {symbol} to {max_grid_pairs} due to {stray_sell_count} stray sell orders")
            
            below_levels = sorted([level for level in self.grid_levels[symbol] if level < current_price])[:min(5, max_grid_pairs)]
            above_levels = []
            if not has_sell_in_range:  # Only add above level if no sell order in range
                above_levels = sorted([level for level in self.grid_levels[symbol] if level >= current_price])[:min(1, max_grid_pairs - len(below_levels))]
            buy_levels = below_levels + above_levels
            
            if len(below_levels) < min(5, max_grid_pairs) and below_levels:
                self.logger.warning(f"Insufficient buy levels below current price for {symbol}: found {len(below_levels)}, needed {min(5, max_grid_pairs)}")
                return
            if not above_levels and max_grid_pairs >= 1 and not has_sell_in_range:
                self.logger.warning(f"No buy level above current price for {symbol}")
                return
            
            for buy_level in buy_levels:
                sell_level = next((level for level in grid_levels if level > buy_level), None)
                if not sell_level:
                    self.logger.warning(f"No sell level above buy level {buy_level:.4f} for {symbol}")
                    continue
                buy_quantity = order_value / buy_level
                order_pair = {
                    'buy_level': buy_level,
                    'buy_order_id': None,
                    'buy_quantity': round(buy_quantity, 8),
                    'buy_state': None,
                    'sell_level': sell_level,
                    'sell_order_id': None,
                    'sell_quantity': 0.0,
                    'sell_state': None
                }
                self.orders[symbol][buy_level] = order_pair
                self.logger.debug(f"Added order pair for {symbol}: buy_level={buy_level:.4f}, sell_level={sell_level:.4f}, details={order_pair}")
            
            total_orders = len(buy_levels) + stray_sell_count
            self.logger.info(f"Orders initialized for {symbol}: {total_orders} total (grid pairs: {len(buy_levels)}, stray sell: {stray_sell_count})")
            for handler in self.logger.handlers:
                if isinstance(handler, RotatingFileHandler):
                    handler.flush()
        except Exception as e:
            self.logger.error(f"Error initializing orders for {symbol}: {e}", exc_info=True)

    async def update_order_status(self, symbol: str) -> None:
        """
        Matches orders from the exchange to the orders dictionary by order_id and updates their state.
        Fetches all orders (open, canceled, closed, etc.) to ensure comprehensive synchronization.
        When a buy order is filled, sets sell_quantity to the filled quantity from the exchange.
        Identifies only open stray orders (buy or sell) not in self.orders[symbol] and handles them.
        Logs status changes, emphasizing non-open/closed statuses (e.g., canceled, rejected, expired).

        Args:
            symbol: Trading pair symbol (e.g., 'BTC-USDT').
        """
        if self.enable_logging:
            self.logger.debug(f"Updating order status for {symbol}")
        try:
            if not self.orders[symbol]:
                if self.enable_logging:
                    self.logger.warning(f"No orders initialized for {symbol}, checking for open stray orders")

            # Fetch all orders (open, canceled, closed, etc.) from the exchange
            exchange_orders = await self.get_exchange_orders(symbol)
            if not exchange_orders:
                if self.enable_logging:
                    self.logger.info(f"No orders found on exchange for {symbol}")
                return

            # Create a map of exchange orders by order_id
            order_status_map = {
                ex_order.get('id', ''): {
                    'status': ex_order.get('status', '').lower(),
                    'filled': float(ex_order.get('filled', 0)),
                    'remaining': float(ex_order.get('remaining', ex_order.get('amount', 0))),
                    'side': ex_order.get('side', '').lower(),
                    'price': float(ex_order.get('price', 0))
                }
                for ex_order in exchange_orders
            }

            # Update existing orders in self.orders[symbol]
            for buy_level, order in self.orders[symbol].items():
                buy_order_id = order['buy_order_id']
                sell_order_id = order['sell_order_id']

                # Update buy order state
                if buy_order_id and buy_order_id in order_status_map:
                    new_state = order_status_map[buy_order_id]['status']
                    if new_state != order['buy_state']:
                        log_level = logging.INFO if new_state not in ['open', 'closed'] else logging.DEBUG
                        if self.enable_logging:
                            self.logger.log(log_level, f"Updated buy order status for {symbol}: buy_level={buy_level:.4f}, order_id={buy_order_id}, state={new_state}")
                    order['buy_state'] = new_state
                    if new_state == "closed" and order['sell_quantity'] == 0.0:
                        filled_quantity = order_status_map[buy_order_id]['filled']
                        if filled_quantity > 0:
                            order['sell_quantity'] = round(filled_quantity, 8)
                            if self.enable_logging:
                                self.logger.info(f"Set sell_quantity for {symbol} at level {buy_level:.4f} to {order['sell_quantity']:.8f} based on filled buy order")
                        else:
                            if self.enable_logging:
                                self.logger.warning(f"No filled quantity for buy order {buy_order_id} at {buy_level:.4f} for {symbol}, using buy_quantity as fallback")
                            order['sell_quantity'] = order['buy_quantity']
                elif buy_order_id:
                    if self.enable_logging:
                        self.logger.debug(f"No matching buy order found for {symbol}: buy_level={buy_level:.4f}, order_id={buy_order_id}")
                    order['buy_state'] = "closed"
                    if order['sell_quantity'] == 0.0:
                        order['sell_quantity'] = order['buy_quantity']
                        if self.enable_logging:
                            self.logger.info(f"Set sell_quantity for {symbol} at level {buy_level:.4f} to {order['sell_quantity']:.8f} based on assumed filled buy order")

                # Update sell order state
                if sell_order_id and sell_order_id in order_status_map:
                    new_state = order_status_map[sell_order_id]['status']
                    if new_state != order['sell_state']:
                        log_level = logging.INFO if new_state not in ['open', 'closed'] else logging.DEBUG
                        if self.enable_logging:
                            self.logger.log(log_level, f"Updated sell order status for {symbol}: sell_level={order['sell_level']:.4f}, order_id={sell_order_id}, state={new_state}")
                    order['sell_state'] = new_state
                elif sell_order_id:
                    if self.enable_logging:
                        self.logger.debug(f"No matching sell order found for {symbol}: sell_level={order['sell_level']:.4f}, order_id={sell_order_id}")

            # Identify and handle open stray orders only
            existing_order_ids = {order['buy_order_id'] for order in self.orders[symbol].values() if order['buy_order_id']} | {order['sell_order_id'] for order in self.orders[symbol].values() if order['sell_order_id']}
            for order_id, order_info in order_status_map.items():
                if order_id not in existing_order_ids and order_info['status'] == 'open':
                    stray_key = f"stray_{order_id}"
                    if order_info['side'] == 'sell':
                        stray_order = {
                            'buy_level': order_info['price'],
                            'buy_order_id': None,
                            'buy_quantity': 0.0,
                            'buy_state': None,
                            'sell_level': order_info['price'],
                            'sell_order_id': order_id,
                            'sell_quantity': round(order_info['remaining'], 8),
                            'sell_state': 'stray_sell'
                        }
                        self.orders[symbol][stray_key] = stray_order
                        if self.enable_logging:
                            self.logger.info(f"Added open stray sell order for {symbol}: order_id={order_id}, price={order_info['price']:.4f}, quantity={stray_order['sell_quantity']:.8f}, state=open")
                    else:  # Stray open buy order
                        if self.enable_logging:
                            self.logger.warning(f"Detected open stray buy order for {symbol}: order_id={order_id}, price={order_info['price']:.4f}, quantity={order_info['remaining']:.8f}, state=open")
                        canceled = await self.order_operations_dict[symbol].cancel_order(order_id)
                        if canceled:
                            if self.enable_logging:
                                self.logger.info(f"Canceled open stray buy order for {symbol}: order_id={order_id}")
                        else:
                            if self.enable_logging:
                                self.logger.error(f"Failed to cancel open stray buy order for {symbol}: order_id={order_id}")

            if self.enable_logging:
                self.logger.info(f"Order status updated for {symbol}: {json.dumps(self.orders[symbol], default=str)}")
                for handler in self.logger.handlers:
                    if isinstance(handler, RotatingFileHandler):
                        handler.flush()
        except Exception as e:
            if self.enable_logging:
                self.logger.error(f"Error updating order status for {symbol}: {e}", exc_info=True)

    
    async def verify_orders(self, symbol: str) -> None:
        """
                Maintains the orders dictionary by resetting canceled/rejected/expired orders and completed pairs
                (both buy and sell orders closed) to allow reuse of grid levels. Checks for an open sell order
                above the current price; if none exists (e.g., price has risen past all grid levels in orders or
                highest sell order was filled), adds a new order pair at the next grid level above the current price
                to place a buy order in the current iteration, with the sell order placed in a subsequent iteration
                after the buy order is filled. Calculates order value to set appropriate buy_quantity. Logs actions
                for debugging.

                Args:
                    symbol: Trading pair symbol (e.g., 'BTC-USDT').
        """
        if self.enable_logging:
                self.logger.debug(f"Verifying orders for {symbol}")
        try:
            order_value = await self.calculate_orders_value(symbol)
            ticker_df = await self.get_ticker_buffer(symbol)
            if ticker_df.empty or 'last_price' not in ticker_df.columns or ticker_df['last_price'].isna().iloc[-1]:
                self.logger.warning(f"No valid ticker price for {symbol}, cannot verify orders")
                return
            current_price = ticker_df['last_price'].iloc[-1]

            # Reset canceled/rejected/expired orders
            for buy_level, order in list(self.orders[symbol].items()):
                if order['buy_state'] in ['canceled', 'rejected', 'expired']:
                    self.logger.info(f"Resetting canceled buy order for {symbol}: buy_level={buy_level:.4f}, order_id={order['buy_order_id']}")
                    order['buy_order_id'] = None
                    order['buy_state'] = None
                    order['buy_quantity'] = round(order_value / current_price, 8) if order_value > 0 else 0.0
                if order['sell_state'] in ['canceled', 'rejected', 'expired']:
                    self.logger.info(f"Resetting canceled sell order for {symbol}: sell_level={order['sell_level']:.4f}, order_id={order['sell_order_id']}")
                    order['sell_order_id'] = None
                    order['sell_state'] = None
                    order['sell_quantity'] = 0.0
                if order['buy_state'] == 'closed' and order['sell_state'] == 'closed':
                    self.logger.info(f"Resetting completed order pair for {symbol}: buy_level={buy_level:.4f}")
                    order['buy_order_id'] = None
                    order['buy_state'] = None
                    order['buy_quantity'] = round(order_value / current_price, 8) if order_value > 0 else 0.0
                    order['sell_order_id'] = None
                    order['sell_state'] = None
                    order['sell_quantity'] = 0.0

            # Add new order pair if under limit and no sell order above current price
            outstanding_orders = sum(
                1 for order in self.orders[symbol].values()
                if order['buy_state'] in ['open', 'pending'] or order['sell_state'] in ['open', 'pending', 'stray_sell']
            )
            self.logger.debug(f"Outstanding orders for {symbol} before adding new: {outstanding_orders}")
            if outstanding_orders < self.MAX_GRID_LEVELS_PER_SYMBOL:
                has_sell_above = False
                for key, order in self.orders[symbol].items():
                    if order['sell_level'] > current_price and order['sell_state'] in ['open', 'pending', 'stray_sell']:
                        has_sell_above = True
                        self.logger.debug(f"Found sell order above current price for {symbol}: key={key}, sell_level={order['sell_level']:.4f}, state={order['sell_state']}")
                        break
                if not has_sell_above:
                    grid_levels = sorted(self.grid_levels[symbol])
                    next_buy_level = next((level for level in grid_levels if level > current_price), None)
                    if next_buy_level is None:
                        self.logger.warning(f"No grid level found above current price {current_price:.4f} for {symbol}, cannot set up buy order")
                    elif next_buy_level not in self.orders[symbol] or (
                        self.orders[symbol][next_buy_level]['buy_state'] == 'closed' and 
                        self.orders[symbol][next_buy_level]['sell_state'] == 'closed'
                    ):
                        sell_level = next((level for level in grid_levels if level > next_buy_level), None)
                        if not sell_level:
                            self.logger.warning(f"No sell level above buy level {next_buy_level:.4f} for {symbol}, cannot set up order pair")
                        else:
                            buy_quantity = round(order_value / current_price, 8) if order_value > 0 else 0.0
                            self.orders[symbol][next_buy_level] = {
                                'buy_level': next_buy_level,
                                'buy_order_id': None,
                                'buy_quantity': buy_quantity,
                                'buy_state': None,
                                'sell_level': sell_level,
                                'sell_order_id': None,
                                'sell_quantity': 0.0,
                                'sell_state': None
                            }
                            self.logger.info(f"Added new order pair for {symbol}: buy_level={next_buy_level:.4f}, sell_level={sell_level:.4f}, buy_quantity={buy_quantity:.8f}")

            # Cancel excess buy orders as the final step, starting with lowest prices
            outstanding_orders = sum(
                1 for order in self.orders[symbol].values()
                if order['buy_state'] in ['open', 'pending'] or order['sell_state'] in ['open', 'pending', 'stray_sell']
            )
            self.logger.debug(f"Outstanding orders for {symbol} after modifications: {outstanding_orders}")
            if outstanding_orders > self.MAX_GRID_LEVELS_PER_SYMBOL:
                buy_orders = [(buy_level, order) for buy_level, order in self.orders[symbol].items()
                            if order['buy_state'] in ['open', 'pending']]
                buy_orders.sort(key=lambda x: x[0], reverse=False)  # Cancel lowest buy orders first
                excess_orders = outstanding_orders - self.MAX_GRID_LEVELS_PER_SYMBOL
                for buy_level, order in buy_orders[:excess_orders]:
                    if order['buy_order_id']:
                        canceled = await self.order_operations_dict[symbol].cancel_order(order['buy_order_id'])
                        if canceled:
                            self.logger.info(f"Canceled buy order for {symbol} at level {buy_level:.4f} to enforce order limit: order_id={order['buy_order_id']}")
                            order['buy_order_id'] = None
                            order['buy_state'] = None
                        else:
                            self.logger.error(f"Failed to cancel buy order for {symbol} at level {buy_level:.4f}: order_id={order['buy_order_id']}")

            self.logger.info(f"Verified orders for {symbol}: {json.dumps(self.orders[symbol], default=str)}")
            for handler in self.logger.handlers:
                if isinstance(handler, RotatingFileHandler):
                    handler.flush()
        except Exception as e:
            self.logger.error(f"Error verifying orders for {symbol}: {e}", exc_info=True)           

    async def place_orders(self, symbol: str) -> None:
        """
                Places limit buy and sell orders for unfilled grid levels.

                Args:
                    symbol: Trading pair symbol (e.g., 'BTC-USDT').
        """
        # Places new limit orders for open grid levels
        if self.enable_logging:
            self.logger.setLevel(logging.DEBUG)
        self.logger.debug(f"Started placing orders for {symbol}")
        try:
            for buy_level, order in self.orders[symbol].items():
                # Skip stray sell order keys
                if isinstance(buy_level, str) and "stray" in buy_level.lower():
                    continue
                if order['buy_order_id'] is None and order['buy_state'] is None:
                    buy_quantity = order['buy_quantity']
                    if buy_quantity > 0:
                        buy_order = await self.order_operations_dict[symbol].create_limit_buy(
                            price=buy_level,
                            quantity=buy_quantity
                        )
                        if buy_order and 'id' in buy_order:
                            order['buy_order_id'] = buy_order['id']
                            order['buy_state'] = buy_order.get('status', 'open')
                            self.logger.info(f"Placed buy order for {symbol} at level {buy_level:.4f}, order_id={buy_order['id']}, quantity={buy_quantity:.8f}")
                        else:
                            self.logger.warning(f"Failed to place buy order for {symbol} at level {buy_level:.4f}")
                    else:
                        self.logger.warning(f"Cannot place buy order for {symbol} at level {buy_level:.4f}: buy_quantity={buy_quantity}")
                if order['buy_state'] == 'closed' and order['sell_order_id'] is None and order['sell_state'] is None:
                    sell_quantity = order['sell_quantity']
                    if sell_quantity > 0:
                        sell_order = await self.order_operations_dict[symbol].create_limit_sell(
                            price=order['sell_level'],
                            quantity=sell_quantity
                        )
                        if sell_order and 'id' in sell_order:
                            order['sell_order_id'] = sell_order['id']
                            order['sell_state'] = sell_order.get('status', 'open')
                            self.logger.info(f"Placed sell order for {symbol} at level {order['sell_level']:.4f}, order_id={sell_order['id']}, quantity={sell_quantity:.8f}")
                        else:
                            self.logger.warning(f"Failed to place sell order for {symbol} at level {order['sell_level']:.4f}")
                    else:
                        self.logger.warning(f"Cannot place sell order for {symbol} at level {order['sell_level']:.4f}: sell_quantity={sell_quantity}")
            self.logger.info(f"Completed placing orders for {symbol}")
        except Exception as e:
            self.logger.error(f"Error placing orders for {symbol}: {e}", exc_info=True)

    async def handle_longterm_downtrend(self, symbol: str):
        if self.enable_logging:
            self.logger.info(f"Handling long-term downtrend for {symbol}")
        try:
            # Cancel all open buy orders
            try:
                await self.order_operations_dict[symbol].cancel_all_buy_orders()
                if self.enable_logging:
                    self.logger.info(f"Canceled all open buy orders for {symbol}")
            except Exception as e:
                if self.enable_logging:
                    self.logger.error(f"Error canceling buy orders for {symbol}: {e}", exc_info=True)

            # Cancel all open sell orders
            try:
                await self.order_operations_dict[symbol].cancel_all_sell_orders()
                if self.enable_logging:
                    self.logger.info(f"Canceled all open sell orders for {symbol}")
            except Exception as e:
                if self.enable_logging:
                    self.logger.error(f"Error canceling sell orders for {symbol}: {e}", exc_info=True)

            # Clear the orders dictionary
            try:
                self.orders[symbol].clear()
                if self.enable_logging:
                    self.logger.info(f"Cleared orders dictionary for {symbol}")
            except Exception as e:
                if self.enable_logging:
                    self.logger.error(f"Error clearing orders dictionary for {symbol}: {e}", exc_info=True)

            # Sell the entire base asset balance
            try:
                await self.order_operations_dict[symbol].sell_all_assets()
                if self.enable_logging:
                    self.logger.info(f"Sold base asset balance for {symbol}")
            except Exception as e:
                if self.enable_logging:
                    self.logger.error(f"Error selling base asset balance for {symbol}: {e}", exc_info=True)

            # Set lttrade to False to halt trading
            self.lttrade = False
            if self.enable_logging:
                self.logger.info(f"Completed handling long-term downtrend for {symbol}: all funds should be in USDT, lttrade set to False")
        except Exception as e:
            if self.enable_logging:
                self.logger.error(f"Error handling long-term downtrend for {symbol}: {e}", exc_info=True)

    async def handle_shortterm_downtrend(self, symbol: str) -> None:
        """
        Handles a short-term downtrend for a specific token by canceling all open buy orders
        while leaving open sell orders in place. Sets sttrade to False only if a downtrend
        is detected and actions are executed.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC-USDT').
        """
        if self.enable_logging:
            self.logger.debug(f"Checking for short-term downtrend for {symbol}")
        try:
            # Get the short-term market status for the token
            market_states = self.state_manager.state_dict.get(symbol, {})
            short_term_state = market_states.get('short_term', None)
            if self.enable_logging:
                self.logger.debug(f"Short-term market state for {symbol}: {short_term_state}")

            # Proceed only if the short-term state is downtrend
            if short_term_state != "downtrend":
                if self.enable_logging:
                    self.logger.info(f"No short-term downtrend for {symbol} (state: {short_term_state}), skipping")
                return

            if self.enable_logging:
                self.logger.info(f"Handling short-term downtrend for {symbol}")

            # Cancel all open buy orders
            try:
                await self.order_operations_dict[symbol].cancel_all_buy_orders()
                if self.enable_logging:
                    self.logger.info(f"Canceled all open buy orders for {symbol}")
            except Exception as e:
                if self.enable_logging:
                    self.logger.error(f"Error canceling buy orders for {symbol}: {e}", exc_info=True)

            # Set sttrade to False after executing downtrend actions
            self.sttrade = False
            if self.enable_logging:
                self.logger.info(f"Completed handling short-term downtrend for {symbol}: open buy orders canceled, sell orders unchanged, sttrade set to {self.sttrade}")
                for handler in self.logger.handlers:
                    if isinstance(handler, RotatingFileHandler):
                        handler.flush()
        except Exception as e:
            if self.enable_logging:
                self.logger.error(f"Error in handle_shortterm_downtrend for {symbol}: {e}", exc_info=True)

    async def reset_grid(self, symbol: str) -> None:
        """
        Resets the grid for a specific token if the reset condition is met (30 consecutive ticks above the maximum grid level).
        Cancels all open buy orders, leaves open sell orders in place, and re-initializes the grid levels.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC-USDT').
        """
        if self.enable_logging:
            self.logger.debug(f"Checking grid reset condition for {symbol}")
        try:
            # Check if grid reset condition is met
            grid_reset = await self.check_grid_reset_condition(symbol)
            if not grid_reset:
                if self.enable_logging:
                    self.logger.info(f"Grid reset condition not met for {symbol}, skipping")
                return

            if self.enable_logging:
                self.logger.info(f"Resetting grid for {symbol}")

            # Cancel all open buy orders
            try:
                await self.order_operations_dict[symbol].cancel_all_buy_orders()
                if self.enable_logging:
                    self.logger.info(f"Canceled all open buy orders for {symbol}")
            except Exception as e:
                if self.enable_logging:
                    self.logger.error(f"Error canceling buy orders for {symbol}: {e}", exc_info=True)

            # Re-initialize grid levels
            try:
                new_grid_levels = await self.initialize_grid(symbol)
                if new_grid_levels:
                    self.grid_levels[symbol] = new_grid_levels
                    if self.enable_logging:
                        self.logger.info(f"Re-initialized grid levels for {symbol}: {new_grid_levels}")
                else:
                    if self.enable_logging:
                        self.logger.warning(f"Failed to re-initialize grid levels for {symbol}, keeping existing levels")
            except Exception as e:
                if self.enable_logging:
                    self.logger.error(f"Error re-initializing grid for {symbol}: {e}", exc_info=True)

            if self.enable_logging:
                self.logger.info(f"Completed grid reset for {symbol}: buy orders canceled, sell orders unchanged, grid levels updated")
                for handler in self.logger.handlers:
                    if isinstance(handler, RotatingFileHandler):
                        handler.flush()
        except Exception as e:
            if self.enable_logging:
                self.logger.error(f"Error in reset_grid for {symbol}: {e}", exc_info=True)

    async def cancel_all_open_buy_orders(self, symbol: str) -> None:
        """
        Cancels all open buy orders for a specific token, intended for use at bot startup to clean up
        stale orders after crashes or unexpected shutdowns (e.g., power outages, VM issues).
        Does not affect open sell orders or the orders dictionary.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC-USDT').
        """
        if self.enable_logging:
            self.logger.debug(f"Starting cancellation of all open buy orders for {symbol}")
        try:
            # Cancel all open buy orders via the exchange
            result = await self.order_operations_dict[symbol].cancel_all_buy_orders()
            if result:  # Assuming result is a list of canceled order IDs or similar
                if self.enable_logging:
                    self.logger.info(f"Successfully canceled all open buy orders for {symbol}: {result}")
            else:
                if self.enable_logging:
                    self.logger.info(f"No open buy orders to cancel for {symbol}")
            if self.enable_logging:
                self.logger.info(f"Completed cancellation of open buy orders for {symbol}")
                for handler in self.logger.handlers:
                    if isinstance(handler, RotatingFileHandler):
                        handler.flush()
        except Exception as e:
            if self.enable_logging:
                self.logger.error(f"Error canceling open buy orders for {symbol}: {e}", exc_info=True)

    async def run(self, interval: int = 60):
        """
        Main run loop for the grid bot, updating market states and processing each symbol
        for market state decisions and grid reset conditions. Skips iteration if network
        connectivity check fails.
        """
        if self.enable_logging:
            self.logger.info("GridManager run loop started.")
        while True:
            try:
                if self.enable_logging:
                    self.logger.debug("Starting run loop iteration")
                
                # Check network connectivity
                if not await self.check_network():
                    if self.enable_logging:
                        self.logger.warning("Skipping run loop iteration due to network connectivity failure")
                    await asyncio.sleep(interval)
                    continue
                
                # Update market states (includes indicator updates via state_manager)
                await self.get_market_states()
                # Process each symbol
                for symbol in self.symbols:
                    await self.run_for_symbol(symbol)
                if self.enable_logging:
                    self.logger.info("Run loop iteration completed")
            except Exception as e:
                if self.enable_logging:
                    self.logger.error(f"Error in run loop: {e}", exc_info=True)
            if self.enable_logging:
                self.logger.debug("Heartbeat: run loop active")
                for handler in self.logger.handlers:
                    if isinstance(handler, RotatingFileHandler):
                        handler.flush()
            await asyncio.sleep(interval)

    async def run_for_symbol(self, symbol: str):
        """
        Processes a single symbol, checking market states and reset conditions. Calls downtrend methods
        only once per downtrend when lttrade/sttrade are True, and resets lttrade/sttrade to True when
        market states recover to uptrend or sideways. In sideways/uptrend states with both lttrade and
        sttrade True, maintains grid trading by syncing, verifying, and preparing to place orders. Skips
        actions during persistent downtrends when orders are already canceled.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC-USDT').
        """
        if self.enable_logging:
            self.logger.debug(f"Running iteration for {symbol}")
        try:
            # Fetch ticker buffer for reset condition
            await self.get_ticker_buffer(symbol)
            
            # Check market states
            market_states = self.state_manager.state_dict.get(symbol, {})
            long_term_state = market_states.get('long_term')
            short_term_state = market_states.get('short_term')

            # Handle long-term market state
            if not self.lttrade:
                if long_term_state in ["uptrend", "sideways"]:
                    if self.enable_logging:
                        self.logger.info(f"Long-term state recovered to {long_term_state} for {symbol}, resetting lttrade to True")
                    self.lttrade = True
                # Skip if long_term_state is "downtrend" (no action needed)
            elif long_term_state == "downtrend":
                if self.enable_logging:
                    self.logger.info(f"Long-term downtrend detected for {symbol}, calling handle_longterm_downtrend")
                await self.handle_longterm_downtrend(symbol)

            # Handle short-term market state
            if not self.sttrade:
                if short_term_state in ["uptrend", "sideways"]:
                    if self.enable_logging:
                        self.logger.info(f"Short-term state recovered to {short_term_state} for {symbol}, resetting sttrade to True")
                    self.sttrade = True
                # Skip if short_term_state is "downtrend" (no action needed)
            elif short_term_state == "downtrend":
                if self.enable_logging:
                    self.logger.info(f"Short-term downtrend detected for {symbol}, calling handle_shortterm_downtrend")
                await self.handle_shortterm_downtrend(symbol)

            # Maintain grid trading in sideways/uptrend states when both lttrade and sttrade are True
            if self.lttrade and self.sttrade:
                if self.enable_logging:
                    self.logger.debug(f"Maintaining grid trading for {symbol} in market state: long_term={long_term_state}, short_term={short_term_state}")
                # Sync order statuses with exchange
                try:
                    await self.update_order_status(symbol)
                except Exception as e:
                    if self.enable_logging:
                        self.logger.error(f"Error updating order status for {symbol}: {e}", exc_info=True)
                
                # Verify and clean up orders
                try:
                    await self.verify_orders(symbol)
                except Exception as e:
                    if self.enable_logging:
                        self.logger.error(f"Error verifying orders for {symbol}: {e}", exc_info=True)
                
                # Place new orders for unfilled grid levels (commented out for testing)
                try:
                    await self.place_orders(symbol)
                except Exception as e:
                    if self.enable_logging:
                        self.logger.error(f"Error placing orders for {symbol}: {e}", exc_info=True)

            # Check reset condition
            if await self.check_grid_reset_condition(symbol):
                if self.enable_logging:
                    self.logger.info(f"Grid reset condition met for {symbol}, calling reset_grid")
                await self.reset_grid(symbol)

            if self.enable_logging:
                self.logger.info(f"Completed iteration for {symbol}")
        except Exception as e:
            if self.enable_logging:
                self.logger.error(f"Error in run_for_symbol for {symbol}: {e}", exc_info=True)