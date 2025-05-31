import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import ccxt.async_support as ccxt
from typing import Dict, Optional, List
from datetime import datetime, timezone
import jwt
import time

class OrderOperations:
    _portfolio_cache = {}  # Class-level cache for portfolio IDs

    def __init__(self, exchange, symbol: str, portfolio_name: str = "market timing", dry_run: bool = False, enable_logging: bool = True):
        self.exchange = exchange
        self.symbol = symbol
        self.portfolio_name = portfolio_name
        self.dry_run = dry_run
        self._dry_run_balance = 1000.0
        self.portfolio_id = None

        # Set up logger
        self.logger = logging.getLogger(f"OrderOperations.{symbol.replace('-', '_')}")
        if enable_logging:
            log_dir = Path(__file__).parent / "logs"
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / f"order_operations_{symbol.replace('-', '_')}.log"
            file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(file_handler)
            self.logger.setLevel(logging.INFO)
        else:
            self.logger.propagate = False
            self.logger.handlers = []

    async def get_portfolios(self) -> Optional[str]:
        if self.portfolio_name in self._portfolio_cache:
            self.logger.debug(f"Using cached portfolio ID for '{self.portfolio_name}': {self._portfolio_cache[self.portfolio_name]}")
            return self._portfolio_cache[self.portfolio_name]
        try:
            self.logger.debug("Generating JWT for /api/v3/brokerage/portfolios request...")
            timestamp = int(time.time())
            payload = {
                "sub": self.exchange.apiKey,
                "iss": "coinbase-cloud",
                "nbf": timestamp,
                "exp": timestamp + 120,
                "iat": timestamp,
                "aud": ["retail_rest_api_proxy"],
                "uri": "GET api.coinbase.com/api/v3/brokerage/portfolios"
            }
            encoded_jwt = jwt.encode(
                payload,
                self.exchange.secret,
                algorithm="ES256",
                headers={"kid": self.exchange.apiKey}
            )
            self.logger.debug(f"JWT Payload: {payload}")
            self.logger.debug(f"Encoded JWT: {encoded_jwt}")

            self.logger.debug("Fetching portfolios using CCXT fetch to /api/v3/brokerage/portfolios...")
            response = await self.exchange.fetch(
                'https://api.coinbase.com/api/v3/brokerage/portfolios',
                method='GET',
                headers={'Authorization': f'Bearer {encoded_jwt}'}
            )
            self.logger.debug(f"Raw portfolios API response: {response}")
            portfolios = response.get('portfolios', [])
            for portfolio in portfolios:
                portfolio_name = portfolio.get('name', '')
                portfolio_id = portfolio.get('uuid')
                self.logger.info(f"Found portfolio: Name: {portfolio_name}, ID: {portfolio_id}")
                if portfolio_name.lower() == self.portfolio_name.lower():
                    self._portfolio_cache[self.portfolio_name] = portfolio_id
                    self.logger.info(f"Selected portfolio '{self.portfolio_name}' with ID: {portfolio_id}")
                    return portfolio_id

            self.logger.warning(f"No '{self.portfolio_name}' portfolio found. Using default portfolio.")
            self._portfolio_cache[self.portfolio_name] = None
            return None
        except ccxt.AuthenticationError as e:
            self.logger.error(f"Authentication error fetching portfolios: {e}", exc_info=True)
            return None
        except ccxt.NetworkError as e:
            self.logger.error(f"Network error fetching portfolios: {e}", exc_info=True)
            return None
        except Exception as e:
            self.logger.error(f"Error fetching portfolios: {e}", exc_info=True)
            return None

    async def initialize(self):
        self.portfolio_id = await self.get_portfolios()
        if not self.portfolio_id:
            self.logger.warning(f"Using default portfolio for {self.symbol} as '{self.portfolio_name}' not found.")

    async def fetch_all_account_balances(self) -> List[Dict]:
        """
        Fetches all account balances across all portfolios.

        Returns:
            List[Dict]: A list of account balance entries, each containing portfolio ID, currency, and balance details.
        """
        if self.dry_run:
            self.logger.debug("[DRY RUN] Returning simulated account balances: [{'portfolio': %s, 'currency': 'USD', 'balance': %s}]", 
                             self.portfolio_id, self._dry_run_balance)
            return [{'portfolio': self.portfolio_id, 'currency': 'USD', 'available_balance': {'value': self._dry_run_balance}}]
        try:
            self.logger.debug("Generating JWT for /api/v3/brokerage/accounts request...")
            timestamp = int(time.time())
            payload = {
                "sub": self.exchange.apiKey,
                "iss": "coinbase-cloud",
                "nbf": timestamp,
                "exp": timestamp + 120,
                "iat": timestamp,
                "aud": ["retail_rest_api_proxy"],
                "uri": "GET api.coinbase.com/api/v3/brokerage/accounts"
            }
            encoded_jwt = jwt.encode(
                payload,
                self.exchange.secret,
                algorithm="ES256",
                headers={"kid": self.exchange.apiKey}
            )
            self.logger.debug(f"JWT Payload: {payload}")
            self.logger.debug(f"Encoded JWT: {encoded_jwt}")

            self.logger.debug("Fetching all account balances using CCXT fetch to /api/v3/brokerage/accounts...")
            response = await self.exchange.fetch(
                'https://api.coinbase.com/api/v3/brokerage/accounts',
                method='GET',
                headers={'Authorization': f'Bearer {encoded_jwt}'}
            )
            self.logger.debug("Raw accounts API response: %s", response)
            accounts = response.get('accounts', [])
            return accounts
        except ccxt.AuthenticationError as e:
            self.logger.error(f"Authentication error fetching account balances: {e}", exc_info=True)
            return []
        except ccxt.NetworkError as e:
            self.logger.error(f"Network error fetching account balances: {e}", exc_info=True)
            return []
        except Exception as e:
            self.logger.error(f"Error fetching account balances: {e}", exc_info=True)
            return []

    async def get_usd_balance(self) -> float:
        """
        Fetches the USD balance for the specified portfolio by filtering all account balances.

        Returns:
            float: USD balance for the specified portfolio.
        """
        if self.dry_run:
            self.logger.debug("[DRY RUN] Returning simulated USD balance: %s", self._dry_run_balance)
            return self._dry_run_balance
        try:
            # Fetch all account balances
            accounts = await self.fetch_all_account_balances()
            usd_balance = 0.0
            for account in accounts:
                # Check retail_portfolio_id for the portfolio match
                portfolio_id = account.get('retail_portfolio_id')
                currency = account.get('currency')
                self.logger.debug("Checking account: portfolio_id=%s, currency=%s", portfolio_id, currency)
                if portfolio_id == self.portfolio_id and currency == 'USD':
                    balance_value = account.get('available_balance', {}).get('value', '0.0')
                    try:
                        usd_balance = float(balance_value)
                        self.logger.debug("Found USD balance for portfolio %s: %s", self.portfolio_id, usd_balance)
                        break
                    except (ValueError, TypeError) as e:
                        self.logger.warning("Error parsing USD balance for portfolio %s: %s, value: %s", 
                                           self.portfolio_id, e, balance_value)
                        continue
            self.logger.debug("Fetched USD balance for portfolio %s: %s", self.portfolio_id, usd_balance)
            if usd_balance == 0.0:
                self.logger.warning("No USD balance found for portfolio %s, returning 0.0", self.portfolio_id)
            return usd_balance
        except Exception as e:
            self.logger.error("Error fetching USD balance for portfolio %s: %s", self.portfolio_id, e, exc_info=True)
            return 0.0

    async def get_base_asset_balance(self, base_asset: str) -> float:
        """
        Fetches the available balance of the base asset (e.g., BTC for BTC-USD) for the specified portfolio.

        Args:
            base_asset (str): The base asset symbol (e.g., 'BTC').

        Returns:
            float: Available balance of the base asset.
        """
        if self.dry_run:
            self.logger.debug("[DRY RUN] Returning simulated %s balance: 0.0", base_asset)
            return 0.0
        try:
            # Fetch all account balances
            accounts = await self.fetch_all_account_balances()
            asset_balance = 0.0
            for account in accounts:
                # Check retail_portfolio_id for the portfolio match
                portfolio_id = account.get('retail_portfolio_id')
                currency = account.get('currency')
                self.logger.debug("Checking account: portfolio_id=%s, currency=%s", portfolio_id, currency)
                if portfolio_id == self.portfolio_id and currency == base_asset:
                    balance_value = account.get('available_balance', {}).get('value', '0.0')
                    try:
                        asset_balance = float(balance_value)
                        self.logger.debug("Found %s balance for portfolio %s: %s", base_asset, self.portfolio_id, asset_balance)
                        break
                    except (ValueError, TypeError) as e:
                        self.logger.warning("Error parsing %s balance for portfolio %s: %s, value: %s", 
                                           base_asset, self.portfolio_id, e, balance_value)
                        continue
            self.logger.debug("Fetched %s balance for portfolio %s: %s", base_asset, self.portfolio_id, asset_balance)
            if asset_balance == 0.0:
                self.logger.warning("No %s balance found for portfolio %s, returning 0.0", base_asset, self.portfolio_id)
            return asset_balance
        except Exception as e:
            self.logger.error("Error fetching %s balance for portfolio %s: %s", base_asset, self.portfolio_id, e, exc_info=True)
            return 0.0

    async def get_open_orders(self) -> List[Dict]:
        """
        Fetches open orders for the symbol.

        Returns:
            List[Dict]: List of open orders.
        """
        if self.dry_run:
            self.logger.debug("[DRY RUN] Returning empty open orders for %s", self.symbol)
            return []
        try:
            orders = await self.exchange.fetch_open_orders(self.symbol, params={'portfolio': self.portfolio_id})
            self.logger.debug("Fetched %d open orders for %s", len(orders), self.symbol)
            return orders
        except Exception as e:
            self.logger.error("Error fetching open orders for %s: %s", self.symbol, e, exc_info=True)
            return []

    # ... rest of the methods (create_limit_buy, create_limit_sell, etc.) remain unchanged ...

    async def create_limit_buy(self, price: float, quantity: float) -> Optional[Dict]:
        """
        Creates a limit buy order.

        Args:
            price (float): The price at which to place the order.
            quantity (float): The amount of base currency to buy (e.g., HBAR).

        Returns:
            Optional[Dict]: The created order object or None if an error occurred.
        """
        if self.dry_run:
            self.logger.info("[DRY RUN] Created limit buy order for %s at %s for %s", quantity, price, self.symbol)
            return {
                "id": f"dry_run_buy_{price}_{int(datetime.now(timezone.utc).timestamp() * 1000)}",
                "status": "open",
                "amount": quantity,
                "price": price,
                "side": "buy",
                "type": "limit"
            }
        try:
            order = await self.exchange.create_limit_buy_order(
                symbol=self.symbol,
                amount=quantity,
                price=price
            )
            self.logger.debug("Created limit buy order for %s: %s", self.symbol, order)
            return order
        except Exception as e:
            self.logger.error("Error creating limit buy order for %s at %s: %s", self.symbol, price, e, exc_info=True)
            return None

    async def create_limit_sell(self, price: float, quantity: float) -> Optional[Dict]:
        """
        Creates a limit sell order.

        Args:
            price (float): The price at which to place the order.
            quantity (float): The amount of base currency to sell.

        Returns:
            Optional[Dict]: The created order object or None if an error occurred.
        """
        if self.dry_run:
            self.logger.info("[DRY RUN] Created limit sell order for %s at %s for %s", quantity, price, self.symbol)
            return {
                "id": f"dry_run_sell_{price}_{int(datetime.now(timezone.utc).timestamp() * 1000)}",
                "status": "open",
                "amount": quantity,
                "price": price,
                "side": "sell",
                "type": "limit"
            }
        try:
            order = await self.exchange.create_limit_sell_order(
                symbol=self.symbol,
                amount=quantity,
                price=price
            )
            self.logger.debug("Created limit sell order for %s: %s", self.symbol, order)
            return order
        except Exception as e:
            self.logger.error("Error creating limit sell order for %s at %s: %s", self.symbol, price, e, exc_info=True)
            return None

    async def create_market_sell(self, quantity: float) -> Optional[Dict]:
        """
        Creates a market sell order.

        Args:
            quantity (float): The amount of base currency to sell.

        Returns:
            Optional[Dict]: The created order object or None if an error occurred.
        """
        if self.dry_run:
            self.logger.info("[DRY RUN] Created market sell order for %s %s", quantity, self.symbol)
            return {
                "id": f"dry_run_market_sell_{quantity}_{int(datetime.now(timezone.utc).timestamp() * 1000)}",
                "status": "closed",
                "amount": quantity,
                "filled": quantity,
                "side": "sell",
                "type": "market"
            }
        try:
            order = await self.exchange.create_market_sell_order(self.symbol, quantity)
            self.logger.debug("Created market sell order for %s: %s", self.symbol, order)
            return order
        except Exception as e:
            self.logger.error("Error creating market sell order for %s: %s", self.symbol, e, exc_info=True)
            return None

    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancels an open order by its ID.

        Args:
            order_id (str): The ID of the order to cancel.

        Returns:
            bool: True if the order was successfully canceled, False otherwise.
        """
        if self.dry_run:
            self.logger.info("[DRY RUN] Canceled order %s for %s", order_id, self.symbol)
            return True
        try:
            await self.exchange.cancel_order(order_id, self.symbol)
            self.logger.info("Canceled order %s for %s", order_id, self.symbol)
            return True
        except Exception as e:
            self.logger.error("Error canceling order %s for %s: %s", order_id, self.symbol, e, exc_info=True)
            return False

    async def fetch_order_status(self, order_id: str) -> Optional[Dict]:
        """
        Fetches the status of a specific order by its ID.

        Args:
            order_id (str): The ID of the order to fetch.

        Returns:
            Optional[Dict]: The order details or None if an error occurred.
        """
        if self.dry_run:
            self.logger.debug("[DRY RUN] Fetching status for order %s for %s", order_id, self.symbol)
            return {
                "id": order_id,
                "status": "open" if order_id.startswith("dry_run") else "closed",
                "filled": 0.0,
                "remaining": 0.0,
                "side": "buy" if "buy" in order_id else "sell",
                "price": 0.0
            }
        try:
            order = await self.exchange.fetch_order(order_id, self.symbol)
            self.logger.debug("Fetched order status for %s for %s: %s", order_id, self.symbol, order)
            return order
        except Exception as e:
            self.logger.error("Error fetching order status for %s for %s: %s", order_id, self.symbol, e, exc_info=True)
            return None

    async def get_open_orders(self) -> List[Dict]:
        """
        Retrieves all currently open orders for the trading pair.

        Returns:
            List[Dict]: A list of open order dictionaries.
        """
        if self.dry_run:
            self.logger.debug("[DRY RUN] Returning empty list for open orders for %s", self.symbol)
            return []
        try:
            open_orders = await self.exchange.fetch_open_orders(self.symbol)
            self.logger.debug("Fetched %s open orders for %s", len(open_orders), self.symbol)
            return open_orders
        except Exception as e:
            self.logger.error("Error fetching open orders for %s: %s", self.symbol, e, exc_info=True)
            return []

    async def fetch_all_orders(self) -> List[Dict]:
        """
        Retrieves all orders (open, canceled, closed, etc.) for the trading pair.

        Returns:
            List[Dict]: A list of order dictionaries.
        """
        if self.dry_run:
            self.logger.debug("[DRY RUN] Returning empty list for all orders for %s", self.symbol)
            return []
        try:
            orders = await self.exchange.fetch_orders(self.symbol)
            self.logger.debug("Fetched %s orders for %s", len(orders), self.symbol)
            return orders
        except Exception as e:
            self.logger.error("Error fetching all orders for %s: %s", self.symbol, e, exc_info=True)
            return []
        except AttributeError:
            # Fallback if fetch_orders is not supported (e.g., Coinbase)
            self.logger.warning("fetch_orders not supported, using fetch_open_orders and fetch_closed_orders")
            try:
                open_orders = await self.exchange.fetch_open_orders(self.symbol)
                closed_orders = await self.exchange.fetch_closed_orders(self.symbol)
                orders = open_orders + closed_orders
                self.logger.debug("Fetched %s orders (open and closed) for %s", len(orders), self.symbol)
                return orders
            except Exception as e:
                self.logger.error("Error fetching open and closed orders for %s: %s", self.symbol, e, exc_info=True)
                return []

    async def cancel_all_buy_orders(self) -> List[str]:
        """
        Cancels all open buy orders for the symbol.

        Returns:
            List[str]: List of canceled order IDs.
        """
        self.logger.debug("Attempting to cancel all buy orders for %s", self.symbol)
        canceled_order_ids = []
        if self.dry_run:
            self.logger.info("[DRY RUN] All buy orders for %s would have been cancelled.", self.symbol)
            return canceled_order_ids
        try:
            open_orders = await self.exchange.fetch_open_orders(self.symbol)
            buy_orders = [order for order in open_orders if order['side'] == 'buy']
            if not buy_orders:
                self.logger.info("No open buy orders found for %s to cancel.", self.symbol)
                return canceled_order_ids
            for order in buy_orders:
                try:
                    await self.exchange.cancel_order(order['id'], self.symbol)
                    self.logger.info("Cancelled buy order %s for %s.", order['id'], self.symbol)
                    canceled_order_ids.append(order['id'])
                except Exception as e:
                    self.logger.error("Error cancelling buy order %s for %s: %s", order['id'], self.symbol, e, exc_info=True)
            return canceled_order_ids
        except Exception as e:
            self.logger.error("Error fetching open orders for %s to cancel buys: %s", self.symbol, e, exc_info=True)
            return canceled_order_ids

    async def cancel_all_sell_orders(self) -> List[str]:
        """
        Cancels all open sell orders for the symbol.

        Returns:
            List[str]: List of canceled order IDs.
        """
        self.logger.debug("Attempting to cancel all sell orders for %s", self.symbol)
        canceled_order_ids = []
        if self.dry_run:
            self.logger.info("[DRY RUN] All sell orders for %s would have been cancelled.", self.symbol)
            return canceled_order_ids
        try:
            open_orders = await self.exchange.fetch_open_orders(self.symbol)
            sell_orders = [order for order in open_orders if order['side'] == 'sell']
            if not sell_orders:
                self.logger.info("No open sell orders found for %s to cancel.", self.symbol)
                return canceled_order_ids
            for order in sell_orders:
                try:
                    await self.exchange.cancel_order(order['id'], self.symbol)
                    self.logger.info("Cancelled sell order %s for %s.", order['id'], self.symbol)
                    canceled_order_ids.append(order['id'])
                except Exception as e:
                    self.logger.error("Error cancelling sell order %s for %s: %s", order['id'], self.symbol, e, exc_info=True)
            return canceled_order_ids
        except Exception as e:
            self.logger.error("Error fetching open orders for %s to cancel sells: %s", self.symbol, e, exc_info=True)
            return canceled_order_ids

    async def sell_all_assets(self) -> None:
        """
        Sells all assets for the base currency of the symbol.
        """
        base_asset = self.symbol.split('-')[0]  # e.g., 'HBAR' from 'HBAR-USDT'
        balance = await self.get_base_asset_balance(base_asset)
        if balance > 0:
            order = await self.create_market_sell(balance)
            if order:
                self.logger.info("Placed market sell order for %s %s: %s", balance, base_asset, order)
            else:
                self.logger.error("Failed to place market sell order for %s %s.", balance, base_asset)
        else:
            self.logger.info("No %s balance to sell for %s.", base_asset, self.symbol)