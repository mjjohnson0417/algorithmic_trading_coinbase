# grid_manager.py
import logging
import pandas as pd
import math
import asyncio
from typing import List, Tuple, Optional, Dict
from datetime import datetime, timedelta
from indicator_calculator import IndicatorCalculator
from state_manager import StateManager
from order_operations import OrderOperations

class GridManager:
    MAX_GRID_LEVELS_PER_SYMBOL = 10  # 5 buy, 5 sell levels

    def __init__(self, data_manager, indicator_calculator: IndicatorCalculator, state_manager: StateManager, order_operations_dict: Dict[str, OrderOperations], symbols: List[str], debug: bool = True):
        """
        Initializes the GridManager class for multiple tokens.

        Args:
            data_manager: Instance of DataManager.
            indicator_calculator: Instance of IndicatorCalculator.
            state_manager: Instance of StateManager.
            order_operations_dict: Dictionary of OrderOperations instances, keyed by symbol.
            symbols: List of trading pair symbols (e.g., ['HBAR-USDT', 'BTC-USDT']).
            debug: If True, enables verbose debug logging.
        """
        self.data_manager = data_manager
        self.indicator_calculator = indicator_calculator
        self.state_manager = state_manager
        self.order_operations_dict = order_operations_dict
        self.symbols = symbols
        self.debug = debug
        self.grid_levels = {symbol: [] for symbol in symbols}
        self.orders = {symbol: {} for symbol in symbols}
        self.last_buy_price = {symbol: None for symbol in symbols}
        self.last_sell_price = {symbol: None for symbol in symbols}
        self.allocation_ratio = 0.75  # Allocate 75% of total balance
        self.max_levels_per_symbol = self.MAX_GRID_LEVELS_PER_SYMBOL
        self.order_value = 0.0
        self.grid_initialized = {symbol: False for symbol in symbols}
        self.all_indicators = {}  # Store indicators dictionary
        self.last_market_states = {symbol: {'long_term': None, 'short_term': None} for symbol in symbols}  # Cache market states

        self.logger = logging.getLogger('GridBot')
        if self.debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

        self.logger.info("GridManager initialized with symbols: %s", symbols)

    async def calculate_orders_value(self, symbol: str) -> float:
        """
        Calculates order value by summing USDT and token balances, taking 75%, and dividing by total levels.

        Args:
            symbol: Trading pair symbol (for logging).

        Returns:
            float: Order value in USDT.
        """
        self.logger.debug(f"Calculating order value for {symbol}")
        try:
            usdt_balance = await self.order_operations_dict[self.symbols[0]].get_usdt_balance()
            total_usdt = usdt_balance
            self.logger.debug(f"USDT balance: {usdt_balance:.2f}")

            for sym in self.symbols:
                base_asset = sym.split('-')[0]
                token_balance = await self.order_operations_dict[sym].get_base_asset_balance(base_asset)
                ticker_df = self.data_manager.get_buffer(sym, 'ticker')
                if ticker_df.empty or 'last_price' not in ticker_df.columns or ticker_df['last_price'].isna().iloc[-1]:
                    self.logger.warning(f"No valid ticker price for {sym}, skipping token value")
                    continue
                current_price = ticker_df['last_price'].iloc[-1]
                token_value = token_balance * current_price
                total_usdt += token_value
                self.logger.debug(f"Token balance for {sym}: {token_balance:.6f} {base_asset} = {token_value:.2f} USDT at price {current_price:.4f}")

            if total_usdt <= 0:
                self.logger.error(f"Total USDT balance is {total_usdt:.2f}, cannot place orders")
                return 0.0

            total_levels = len(self.symbols) * self.max_levels_per_symbol
            if total_levels == 0:
                self.logger.error("Total levels is zero, cannot calculate order value")
                return 0.0

            allocated_value = self.allocation_ratio * total_usdt
            order_value = allocated_value / total_levels

            if order_value < 10.0:
                self.logger.warning(f"Order value {order_value:.2f} too low for {symbol}, minimum 10 USDT recommended. Setting to 0.0")
                return 0.0

            self.logger.info(f"Order value for {symbol}: total_usdt={total_usdt:.2f}, allocated_value={allocated_value:.2f}, num_symbols={len(self.symbols)}, total_levels={total_levels}, order_value={order_value:.2f}")
            return order_value
        except Exception as e:
            self.logger.error(f"Error calculating order value for {symbol}: {e}", exc_info=True)
            return 0.0

    async def get_exchange_orders(self, symbol: str) -> List[Dict]:
        """
        Fetches all open orders from the exchange for a given symbol.

        Args:
            symbol: The trading pair symbol.

        Returns:
            List[Dict]: A list of open orders from the exchange.
        """
        try:
            return await self.order_operations_dict[symbol].get_open_orders()
        except Exception as e:
            self.logger.error(f"Error fetching exchange orders for {symbol}: {e}", exc_info=True)
            return []

    async def initialize_grid(self, symbol: str, current_price: float) -> None:
        """
        Initializes the grid levels around the current price using ATR with a half grid spacing offset.

        Args:
            symbol: Trading pair symbol.
            current_price: Current market price.
        """
        if self.grid_initialized[symbol]:
            self.logger.debug(f"Grid already initialized for {symbol}.")
            return

        self.logger.info(f"Initializing grid for {symbol} at current price {current_price:.4f}")
        self.grid_levels[symbol].clear()
        self.orders[symbol].clear()

        # Fetch ATR from all_indicators dictionary (1-hour klines, atr14)
        atr = current_price * 0.02  # Default to 2% if ATR unavailable
        if symbol in self.all_indicators and '1h' in self.all_indicators[symbol] and 'atr14' in self.all_indicators[symbol]['1h']:
            atr = self.all_indicators[symbol]['1h']['atr14']
            self.logger.debug(f"Fetched ATR14 for {symbol} from all_indicators: {atr:.4f}")
        else:
            self.logger.warning(f"No valid ATR data for {symbol} in all_indicators. Using default 2% spacing.")

        # Calculate grid spacing: ATR * multiplier, minimum 2% of current price
        multiplier = 2.0  # Adjusts ATR to ensure ≥2% spacing
        grid_spacing = max(atr * multiplier, current_price * 0.02)
        half_grid_spacing = grid_spacing * 0.5

        # Create 5 buy and 5 sell levels with half grid spacing offset
        levels = set()  # Ensure unique levels
        for i in range(self.max_levels_per_symbol // 2):
            # Buy levels: current_price - (0.5, 1.5, 2.5, ...) * grid_spacing
            buy_level = current_price - ((i + 0.5) * grid_spacing)
            # Sell levels: current_price + (0.5, 1.5, 2.5, ...) * grid_spacing
            sell_level = current_price + ((i + 0.5) * grid_spacing)
            # Round to 4 decimals for precision
            levels.add(round(buy_level, 4))
            levels.add(round(sell_level, 4))

        self.grid_levels[symbol] = sorted(list(levels))
        self.logger.info(f"Grid levels for {symbol}: {self.grid_levels[symbol]}")
        self.grid_initialized[symbol] = True
        self.logger.info(f"Grid initialized for {symbol}.")

    async def check_grid_reset_condition(self, symbol: str) -> bool:
        """
        Checks if the grid needs to be reset based on 30 consecutive ticks above the maximum grid level.

        Args:
            symbol: Trading pair symbol.

        Returns:
            bool: True if reset is needed, False otherwise.
        """
        if not self.grid_initialized[symbol] or not self.grid_levels[symbol]:
            self.logger.debug(f"Grid not initialized or empty for {symbol}. Triggering reset.")
            return True

        ticker_df = self.data_manager.get_buffer(symbol, 'ticker')
        if ticker_df.empty or 'last_price' not in ticker_df.columns or ticker_df['last_price'].isna().any():
            self.logger.warning(f"No valid ticker data for {symbol} for grid reset check.")
            return False

        max_grid_price = max(self.grid_levels[symbol])
        recent_ticks = ticker_df.tail(30)  # Get the last 30 ticks

        if len(recent_ticks) < 30:
            self.logger.debug(f"Insufficient ticker data for {symbol}: {len(recent_ticks)} ticks, need 30.")
            return False

        # Check if all 30 consecutive ticks are above max_grid_price
        above_grid = (recent_ticks['last_price'] > max_grid_price).all()
        if above_grid:
            self.logger.info(f"30 consecutive ticks above grid max [{max_grid_price:.4f}] for {symbol}. Resetting grid.")
            return True

        self.logger.debug(f"No reset for {symbol}: Not 30 consecutive ticks above max_grid_price [{max_grid_price:.4f}].")
        return False

    async def reset_grid(self, symbol: str) -> None:
        """
        Resets the grid by canceling all orders, selling assets, and clearing the grid.

        Args:
            symbol: Trading pair symbol.
        """
        self.logger.info(f"Resetting grid for {symbol}.")
        try:
            await self.order_operations_dict[symbol].cancel_all_buy_orders()
            await self.order_operations_dict[symbol].cancel_all_sell_orders()
            await self.order_operations_dict[symbol].sell_all_assets()
            await self.prune_orders_dictionary(symbol)
            self.grid_initialized[symbol] = False
            self.logger.info(f"Grid for {symbol} reset.")
        except Exception as e:
            self.logger.error(f"Error during grid reset for {symbol}: {e}", exc_info=True)

    async def handle_long_term_downtrend(self, symbol: str) -> None:
        """
        Handles a long-term downtrend by canceling all orders, selling assets, and pausing trading.

        Args:
            symbol: Trading pair symbol.
        """
        self.logger.info(f"Handling long-term downtrend for {symbol}.")
        # Fetch open orders to ensure accurate order state
        exchange_orders = await self.get_exchange_orders(symbol)
        if exchange_orders:  # Only attempt cancellation if orders exist on exchange
            await self.order_operations_dict[symbol].cancel_all_buy_orders()
            await self.order_operations_dict[symbol].cancel_all_sell_orders()
            await self.order_operations_dict[symbol].sell_all_assets()
            await self.prune_orders_dictionary(symbol)
            self.logger.info(f"All orders canceled and assets sold for {symbol}.")
        else:
            self.logger.debug(f"No orders to cancel or assets to sell for {symbol} in long-term downtrend.")
        self.grid_initialized[symbol] = False

    async def handle_short_term_downtrend(self, symbol: str) -> None:
        """
        Handles a short-term downtrend by canceling buy orders and pausing new trading.

        Args:
            symbol: Trading pair symbol.
        """
        self.logger.info(f"Handling short-term downtrend for {symbol}.")
        # Fetch open orders to ensure accurate order state
        exchange_orders = await self.get_exchange_orders(symbol)
        if exchange_orders:  # Only attempt cancellation if orders exist on exchange
            await self.order_operations_dict[symbol].cancel_all_buy_orders()
            await self.prune_orders_dictionary(symbol)
            self.logger.info(f"Buy orders canceled for {symbol}.")
        else:
            self.logger.debug(f"No buy orders to cancel for {symbol} in short-term downtrend.")

    async def prune_orders_dictionary(self, symbol: str) -> None:
        """
        Removes completed or canceled orders from the local orders dictionary.

        Args:
            symbol: Trading pair symbol.
        """
        self.logger.debug(f"Pruning orders for {symbol}.")
        levels_to_remove = []
        try:
            exchange_orders = await self.order_operations_dict[symbol].get_open_orders()
            exchange_order_ids = {order['id'] for order in exchange_orders}
            for price_level, level_data in list(self.orders[symbol].items()):
                # Check buy order
                if level_data.get('buy_order') and level_data['buy_order'].get('order_id') not in exchange_order_ids:
                    self.logger.info(f"Buy order {level_data['buy_order']['order_id']} at level {price_level:.4f} for {symbol} not found on exchange. Removing.")
                    level_data['buy_order'] = None
                # Check sell order
                if level_data.get('sell_order') and level_data['sell_order'].get('order_id') not in exchange_order_ids:
                    self.logger.info(f"Sell order {level_data['sell_order']['order_id']} at level {level_data['sell_price']:.4f} for {symbol} not found on exchange. Removing.")
                    level_data['sell_order'] = None
                # Remove level if both orders are None and locked is False
                if (not level_data.get('buy_order') and
                    not level_data.get('sell_order') and
                    level_data.get('locked') == 'False'):
                    levels_to_remove.append(price_level)
            for price_level in levels_to_remove:
                del self.orders[symbol][price_level]
            self.logger.debug(f"Pruning complete for {symbol}. Current orders: {self.orders[symbol]}")
        except Exception as e:
            self.logger.error(f"Error pruning orders for {symbol}: {e}", exc_info=True)

    async def match_orders_dictionary_to_exchange_orders(self, symbol: str, exchange_orders: List[Dict]) -> None:
        """
        Matches local orders dictionary against exchange orders, updating or removing as needed.

        Args:
            symbol: Trading pair symbol.
            exchange_orders: List of open orders from the exchange.
        """
        self.logger.debug(f"Matching local orders for {symbol} against exchange orders.")
        exchange_order_ids = {order['id'] for order in exchange_orders}
        for price_level, level_data in list(self.orders[symbol].items()):
            # Remove buy order if not in exchange
            if level_data.get('buy_order') and level_data['buy_order'].get('order_id') not in exchange_order_ids:
                self.logger.info(f"Buy order {level_data['buy_order']['order_id']} at {price_level:.4f} for {symbol} not found on exchange. Removing.")
                level_data['buy_order'] = None
            # Remove sell order if not in exchange
            if level_data.get('sell_order') and level_data['sell_order'].get('order_id') not in exchange_order_ids:
                self.logger.info(f"Sell order {level_data['sell_order']['order_id']} at {level_data['sell_price']:.4f} for {symbol} not found on exchange. Removing.")
                level_data['sell_order'] = None
            # Update locked status
            if (not level_data.get('buy_order') and
                not level_data.get('sell_order') and
                level_data.get('locked') == 'True'):
                level_data['locked'] = 'False'
        # Add unrecognized exchange orders to a temporary level
        for ex_order in exchange_orders:
            order_id = ex_order['id']
            found = False
            for level_data in self.orders[symbol].values():
                if (level_data.get('buy_order') and level_data['buy_order'].get('order_id') == order_id) or \
                   (level_data.get('sell_order') and level_data['sell_order'].get('order_id') == order_id):
                    found = True
                    break
            if not found:
                self.logger.info(f"Order {order_id} at {ex_order['price']:.4f} for {symbol} found on exchange but not locally. Adding.")
                temp_level = ex_order['price']
                while temp_level in self.orders[symbol]:
                    temp_level += 0.0001  # Avoid collision
                self.orders[symbol][temp_level] = {
                    'buy_order': {'order_id': order_id, 'side': ex_order['side'], 'status': ex_order['status'], 'price': ex_order['price'], 'amount': ex_order['amount']} if ex_order['side'] == 'buy' else None,
                    'sell_order': {'order_id': order_id, 'side': ex_order['side'], 'status': ex_order['status'], 'price': ex_order['price'], 'amount': ex_order['amount']} if ex_order['side'] == 'sell' else None,
                    'sell_price': ex_order['price'] + (self.grid_levels[symbol][1] - self.grid_levels[symbol][0]) if ex_order['side'] == 'buy' else ex_order['price'],
                    'locked': 'True'
                }
        self.logger.debug(f"Matching complete for {symbol}. Current orders: {self.orders[symbol]}")

    async def check_price_levels(self, symbol: str) -> None:
        """
        Checks if the current price crosses grid levels but does not place orders (used for tracking).

        Args:
            symbol: Trading pair symbol.
        """
        ticker_df = self.data_manager.get_buffer(symbol, 'ticker')
        if ticker_df.empty or 'last_price' not in ticker_df.columns or ticker_df['last_price'].isna().iloc[-1]:
            self.logger.warning(f"No valid ticker price for {symbol} for price level check.")
            return

        current_price = ticker_df['last_price'].iloc[-1]
        self.logger.debug(f"Checking price levels for {symbol} at {current_price:.4f}.")

        if not self.grid_initialized[symbol]:
            await self.initialize_grid(symbol, current_price)
            return

        for level in self.grid_levels[symbol]:
            if current_price <= level and (self.last_buy_price[symbol] is None or current_price < self.last_buy_price[symbol]):
                self.last_buy_price[symbol] = current_price
                self.logger.debug(f"Price {current_price:.4f} at buy level {level:.4f} for {symbol}.")
            elif current_price >= level and (self.last_sell_price[symbol] is None or current_price > self.last_sell_price[symbol]):
                self.last_sell_price[symbol] = current_price
                self.logger.debug(f"Price {current_price:.4f} at sell level {level:.4f} for {symbol}.")

    async def check_market_states(self, symbol: str) -> Tuple[bool, bool, str, str]:
        """
        Checks market states from state_manager, returning booleans for trading suitability and current states.

        Args:
            symbol: Trading pair symbol.

        Returns:
            Tuple[bool, bool, str, str]: (long_term_tradeable, short_term_tradeable, long_term_state, short_term_state).
        """
        state = self.state_manager.state_dict.get(symbol, {'long_term': None, 'short_term': None})
        long_term_state = state['long_term']
        short_term_state = state['short_term']

        long_term_tradeable = long_term_state in ['uptrend', 'sideways']
        short_term_tradeable = short_term_state in ['uptrend', 'sideways']

        # Log state changes for debugging
        if (self.last_market_states[symbol]['long_term'] != long_term_state or
            self.last_market_states[symbol]['short_term'] != short_term_state):
            self.logger.info(f"Market state change for {symbol}: long_term={long_term_state} (tradeable={long_term_tradeable}), short_term={short_term_state} (tradeable={short_term_tradeable})")
            self.last_market_states[symbol] = {'long_term': long_term_state, 'short_term': short_term_state}

        return long_term_tradeable, short_term_tradeable, long_term_state, short_term_state

    async def place_dictionary_orders(self, symbol: str, current_price: float) -> None:
        """
        Places limit buy and sell orders at grid levels if no orders exist at those levels.

        Args:
            symbol: Trading pair symbol.
            current_price: Current market price.
        """
        self.logger.info(f"Placing grid orders for {symbol} at current price {current_price:.4f}")
        if not self.grid_initialized[symbol]:
            await self.initialize_grid(symbol, current_price)

        for level in self.grid_levels[symbol]:
            # Skip if an order already exists at this level
            if level in self.orders[symbol] and self.orders[symbol][level]:
                self.logger.debug(f"Order exists at level {level:.4f} for {symbol}. Skipping.")
                continue

            # Place buy order for levels below current price
            if level < current_price:
                order = await self.order_operations_dict[symbol].create_limit_buy(level, self.order_value)
                if order:
                    if level not in self.orders[symbol]:
                        self.orders[symbol][level] = {}
                    self.orders[symbol][level][order['id']] = {
                        'side': 'buy',
                        'status': 'open',
                        'price': level,
                        'amount': self.order_value
                    }
                    self.logger.info(f"Placed buy order for {symbol} at {level:.4f}. Order ID: {order['id']}")
                else:
                    self.logger.error(f"Failed to place buy order for {symbol} at {level:.4f}")
            # Place sell order for levels above current price
            elif level > current_price:
                base_asset = symbol.split('-')[0]
                available_base_asset = await self.order_operations_dict[symbol].get_base_asset_balance(base_asset)
                quantity_to_sell = self.order_value / level
                if available_base_asset >= quantity_to_sell:
                    order = await self.order_operations_dict[symbol].create_limit_sell(level, quantity_to_sell)
                    if order:
                        if level not in self.orders[symbol]:
                            self.orders[symbol][level] = {}
                        self.orders[symbol][level][order['id']] = {
                            'side': 'sell',
                            'status': 'open',
                            'price': level,
                            'amount': quantity_to_sell
                        }
                        self.logger.info(f"Placed sell order for {symbol} at {level:.4f}. Order ID: {order['id']}")
                    else:
                        self.logger.error(f"Failed to place sell order for {symbol} at {level:.4f}")
                else:
                    self.logger.warning(f"Insufficient {base_asset} balance ({available_base_asset:.6f}) to sell {quantity_to_sell:.6f} at {level:.4f}. Continuing with buy orders.")

    async def place_price_following_orders(self, symbol: str, current_price: float) -> None:
        """
        Places buy orders at all grid levels below the current price and one buy order one grid level
        above if no sell orders exist, and a sell order one level above a filled buy order, locking
        both levels until both are filled.

        Args:
            symbol: Trading pair symbol.
            current_price: Current market price.
        """
        self.logger.info(f"Checking and placing price-following orders for {symbol} at current_price {current_price:.4f}")
        if not self.grid_initialized[symbol]:
            await self.initialize_grid(symbol, current_price)

        # Get open orders from the exchange
        exchange_orders = await self.get_exchange_orders(symbol)

        # Place buy orders at all grid levels below the current price
        below_levels = [level for level in self.grid_levels[symbol] if level < current_price]
        for buy_level in below_levels:
            # Check if level is unlocked or unoccupied
            if (buy_level not in self.orders[symbol] or
                (self.orders[symbol][buy_level].get('locked') == 'False' and
                 not self.orders[symbol][buy_level].get('buy_order') and
                 not self.orders[symbol][buy_level].get('sell_order'))):
                order = await self.order_operations_dict[symbol].create_limit_buy(buy_level, self.order_value)
                if order:
                    self.orders[symbol][buy_level] = {
                        'buy_order': {
                            'order_id': order['id'],
                            'side': 'buy',
                            'status': 'open',
                            'price': buy_level,
                            'amount': self.order_value
                        },
                        'sell_order': None,
                        'sell_price': min([l for l in self.grid_levels[symbol] if l > buy_level], default=None),
                        'locked': 'True'
                    }
                    self.logger.info(f"Placed buy order for {symbol} at {buy_level:.4f} (below {current_price:.4f}). Order ID: {order['id']}")
                else:
                    self.logger.error(f"Failed to place buy order for {symbol} at {buy_level:.4f}")

        # Check for sell orders above the current price
        sell_orders_above = [order for order in exchange_orders if order['side'] == 'sell' and order['price'] > current_price]
        self.logger.debug(f"Found {len(sell_orders_above)} sell orders above current price {current_price:.4f} for {symbol}")

        # If no sell orders, place one buy order one grid level above
        if not sell_orders_above:
            above_levels = [level for level in self.grid_levels[symbol] if level > current_price]
            if above_levels:
                buy_level = min(above_levels)  # Closest level above current price
                # Check if level is unlocked or unoccupied
                if (buy_level not in self.orders[symbol] or
                    (self.orders[symbol][buy_level].get('locked') == 'False' and
                     not self.orders[symbol][buy_level].get('buy_order') and
                     not self.orders[symbol][buy_level].get('sell_order'))):
                    order = await self.order_operations_dict[symbol].create_limit_buy(buy_level, self.order_value)
                    if order:
                        self.orders[symbol][buy_level] = {
                            'buy_order': {
                                'order_id': order['id'],
                                'side': 'buy',
                                'status': 'open',
                                'price': buy_level,
                                'amount': self.order_value
                            },
                            'sell_order': None,
                            'sell_price': min([l for l in self.grid_levels[symbol] if l > buy_level], default=None),
                            'locked': 'True'
                        }
                        self.logger.info(f"Placed buy order for {symbol} at {buy_level:.4f} (one level above {current_price:.4f}). Order ID: {order['id']}")
                    else:
                        self.logger.error(f"Failed to place buy order for {symbol} at {buy_level:.4f}")
            else:
                self.logger.warning(f"No grid levels above current price {current_price:.4f} for {symbol}. Cannot place buy order.")

        # Check for filled buy orders and place sell orders
        for buy_level in list(self.orders[symbol].keys()):
            level_data = self.orders[symbol][buy_level]
            # Process open buy orders
            if level_data.get('buy_order') and level_data['buy_order']['status'] == 'open':
                updated_order = None
                for ex_order in exchange_orders:
                    if ex_order['id'] == level_data['buy_order']['order_id']:
                        updated_order = ex_order
                        break
                if updated_order and updated_order.get('status') == 'closed' and updated_order.get('filled', 0) > 0:
                    self.logger.info(f"Buy order {level_data['buy_order']['order_id']} at {buy_level:.4f} for {symbol} filled. Updating status.")
                    level_data['buy_order']['status'] = 'closed'
                    # Place sell order if not already placed
                    sell_price = level_data['sell_price']
                    if sell_price and not level_data.get('sell_order'):
                        base_asset = symbol.split('-')[0]
                        available_base_asset = await self.order_operations_dict[symbol].get_base_asset_balance(base_asset)
                        quantity_to_sell = self.order_value / sell_price
                        if available_base_asset >= quantity_to_sell:
                            order = await self.order_operations_dict[symbol].create_limit_sell(sell_price, quantity_to_sell)
                            if order:
                                level_data['sell_order'] = {
                                    'order_id': order['id'],
                                    'side': 'sell',
                                    'status': 'open',
                                    'price': sell_price,
                                    'amount': quantity_to_sell
                                }
                                self.logger.info(f"Placed sell order for {symbol} at {sell_price:.4f} (paired with buy at {buy_level:.4f}). Order ID: {order['id']}")
                            else:
                                self.logger.error(f"Failed to place sell order for {symbol} at {sell_price:.4f}")
                        else:
                            self.logger.warning(f"Insufficient {base_asset} balance ({available_base_asset:.6f}) to sell {quantity_to_sell:.6f} at {sell_price:.4f}")

            # Check for filled sell orders and unlock level
            if (level_data.get('buy_order') and level_data['buy_order'].get('status') == 'closed' and
                level_data.get('sell_order') and level_data['sell_order'].get('status') == 'open'):
                updated_order = None
                for ex_order in exchange_orders:
                    if ex_order['id'] == level_data['sell_order']['order_id']:
                        updated_order = ex_order
                        break
                if updated_order and updated_order.get('status') == 'closed' and updated_order.get('filled', 0) > 0:
                    self.logger.info(f"Sell order {level_data['sell_order']['order_id']} at {level_data['sell_price']:.4f} for {symbol} filled. Unlocking level {buy_level:.4f}.")
                    level_data['sell_order']['status'] = 'closed'
                    level_data['locked'] = 'False'

    async def run(self, interval: int = 60):
        """
        Main run loop for the grid bot, managing grid and order operations.

        Args:
            interval: Seconds between iterations.
        """
        self.logger.info("GridManager run loop started.")
        while True:
            # Update indicators and states
            self.all_indicators = self.indicator_calculator.calculate_all_indicators()
            self.state_manager.calculate_all_market_states()
            self.order_value = await self.calculate_orders_value(self.symbols[0])
            tasks = [self.run_for_symbol(symbol) for symbol in self.symbols]
            await asyncio.gather(*tasks)
            await asyncio.sleep(interval)

    async def run_for_symbol(self, symbol: str):
        """
        Run loop iteration for a specific symbol.

        Args:
            symbol: Trading pair symbol.
        """
        self.logger.debug(f"Running iteration for {symbol}")
        try:
            # Check market states
            long_term_tradeable, short_term_tradeable, long_term_state, short_term_state = await self.check_market_states(symbol)
            self.logger.debug(f"Market states for {symbol}: long_term_tradeable={long_term_tradeable}, short_term_tradeable={short_term_tradeable}, long_term_state={long_term_state}, short_term_state={short_term_state}")

            # Get ticker price
            ticker_df = self.data_manager.get_buffer(symbol, 'ticker')
            current_price = None
            if not ticker_df.empty and 'last_price' in ticker_df.columns and not ticker_df['last_price'].isna().iloc[-1]:
                current_price = ticker_df['last_price'].iloc[-1]
                self.logger.debug(f"Valid ticker price for {symbol}: {current_price:.4f}")
            else:
                self.logger.warning(f"No valid ticker price in buffer for {symbol} (empty={ticker_df.empty}, has_last_price={'last_price' in ticker_df.columns}, is_na={ticker_df['last_price'].isna().iloc[-1] if 'last_price' in ticker_df.columns else 'N/A'}). Skipping trading operations.")
                await self.prune_orders_dictionary(symbol)
                await self.match_orders_dictionary_to_exchange_orders(symbol, await self.get_exchange_orders(symbol))
                self.logger.info(f"Completed iteration for {symbol} without trading due to invalid ticker price")
                return

            # Check order value
            if self.order_value <= 0:
                self.logger.warning(f"Order value is {self.order_value:.2f} for {symbol}. Skipping trading due to insufficient funds.")
                await self.prune_orders_dictionary(symbol)
                await self.match_orders_dictionary_to_exchange_orders(symbol, await self.get_exchange_orders(symbol))
                self.logger.info(f"Completed iteration for {symbol} without trading due to invalid ticker price")
                return

            # Synchronize orders before handling market states
            await self.prune_orders_dictionary(symbol)

            # Handle market states with dedicated handlers only on downtrend state transitions
            last_long_term = self.last_market_states[symbol]['long_term']
            last_short_term = self.last_market_states[symbol]['short_term']

            if long_term_state == 'downtrend' and last_long_term != 'downtrend':
                await self.handle_long_term_downtrend(symbol)
            elif short_term_state == 'downtrend' and last_short_term != 'downtrend' and long_term_tradeable:
                await self.handle_short_term_downtrend(symbol)
            else:
                self.logger.info(f"Trading conditions met or no downtrend transition for {symbol}. Proceeding with grid trading.")
                if await self.check_grid_reset_condition(symbol):
                    await self.reset_grid(symbol)
                await self.check_price_levels(symbol)
                # await self.place_price_following_orders(symbol, current_price)  # Commented out per user preference

            # Match orders regardless of trading state
            await self.match_orders_dictionary_to_exchange_orders(symbol, await self.get_exchange_orders(symbol))
            self.logger.info(f"Completed iteration for {symbol}")
        except Exception as e:
            self.logger.error(f"Error in run loop for {symbol}: {e}", exc_info=True)