# graceful_shutdown.py
import asyncio
import logging
import signal
from typing import Dict  # Added import
from data_manager import DataManager
from order_operations import OrderOperations
from exchange_connection import ExchangeConnection

class GracefulShutdown:
    def __init__(self, order_operations_dict: Dict[str, OrderOperations], data_manager: DataManager, exchange: ExchangeConnection, dry_run: bool = False, loop=None):
        """
        Initializes the GracefulShutdown class.

        Args:
            order_operations_dict (Dict[str, OrderOperations]): Dictionary of OrderOperations instances by symbol.
            data_manager (DataManager): The DataManager instance.
            exchange (ExchangeConnection): The ExchangeConnection instance.
            dry_run (bool): If True, simulate shutdown without actual operations.
            loop: The asyncio event loop (optional).
        """
        self.order_operations_dict = order_operations_dict
        self.data_manager = data_manager
        self.exchange = exchange
        self.dry_run = dry_run
        self.loop = loop or asyncio.get_event_loop()
        self.logger = logging.getLogger('GracefulShutdown')
        self.logger.setLevel(logging.INFO)

    async def shutdown(self, signum, shutdown_event: asyncio.Event):
        """
        Initiates graceful shutdown by canceling orders, closing WebSocket and exchange connections, and setting the shutdown event.

        Args:
            signum: The signal number received (e.g., SIGINT, SIGTERM).
            shutdown_event (asyncio.Event): Event to signal shutdown completion.
        """
        self.logger.info(f"Received shutdown signal ({signal.Signals(signum).name}). Initiating graceful shutdown...")
        try:
            if not self.dry_run:
                # Cancel all orders
                cancel_tasks = []
                cancel_results = {}
                for symbol, order_ops in self.order_operations_dict.items():
                    self.logger.info(f"Cancelling all orders for {symbol}...")
                    cancel_tasks.append((symbol, 'buy', order_ops.cancel_all_buy_orders()))
                    cancel_tasks.append((symbol, 'sell', order_ops.cancel_all_sell_orders()))
                if not cancel_tasks:
                    self.logger.warning("No orders to cancel for any symbols.")
                else:
                    results = await asyncio.gather(*[task for _, _, task in cancel_tasks], return_exceptions=True)
                    for (symbol, side, _), result in zip(cancel_tasks, results):
                        if isinstance(result, Exception):
                            self.logger.error(f"Error cancelling {side} orders for {symbol}: {result}", exc_info=True)
                        else:
                            cancel_results.setdefault(symbol, {'buy': [], 'sell': []})[side] = result
                            if result:
                                self.logger.info(f"Canceled {side} orders for {symbol}: {result}")
                            else:
                                self.logger.info(f"No open {side} orders to cancel for {symbol}")
                    self.logger.info(f"Completed cancellation of orders for {list(self.order_operations_dict.keys())}")

                # Close WebSocket connections
                self.logger.info("Closing WebSocket connections...")
                await self.data_manager.close_websockets()

                # Close DataManager's REST exchange
                self.logger.info("Closing DataManager REST exchange...")
                await self.data_manager.rest_exchange.close()

                # Close OrderOperations exchange instances
                close_tasks = []
                for symbol, order_ops in self.order_operations_dict.items():
                    self.logger.info(f"Closing exchange for {symbol}...")
                    close_tasks.append(order_ops.exchange.close())
                if close_tasks:
                    await asyncio.gather(*close_tasks, return_exceptions=True)
                    self.logger.info(f"Closed exchange instances for {list(self.order_operations_dict.keys())}")

                # Close ExchangeConnection
                self.logger.info("Closing ExchangeConnection...")
                await self.exchange.close()

            # Signal shutdown completion
            shutdown_event.set()
            self.logger.info("Graceful shutdown completed.")
        except Exception as e:
            self.logger.error(f"Error during graceful shutdown: {e}", exc_info=True)
            shutdown_event.set()  # Ensure event is set even on error