class GracefulShutdown:
    def __init__(self, order_operations_dict: Dict[str, OrderOperations], data_manager: DataManager, exchange: ExchangeConnection, dry_run: bool = False, loop=None):
        self.order_operations_dict = order_operations_dict
        self.data_manager = data_manager
        self.exchange = exchange
        self.dry_run = dry_run
        self.loop = loop or asyncio.get_event_loop()
        self.logger = logging.getLogger('GracefulShutdown')
        self.logger.setLevel(logging.INFO)

    async def shutdown(self, signum, shutdown_event: asyncio.Event):
        self.logger.info(f"Received shutdown signal ({signal.Signals(signum).name}). Initiating graceful shutdown...")
        try:
            if not self.dry_run:
                # Cancel all orders
                cancel_tasks = []
                for symbol, order_ops in self.order_operations_dict.items():
                    self.logger.info(f"Cancelling all orders for {symbol}...")
                    cancel_tasks.append(order_ops.cancel_all_buy_orders())
                    cancel_tasks.append(order_ops.cancel_all_sell_orders())
                if not cancel_tasks:
                    self.logger.warning("No orders to cancel for any symbols.")
                else:
                    await asyncio.gather(*cancel_tasks, return_exceptions=True)
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