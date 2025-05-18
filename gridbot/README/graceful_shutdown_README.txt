README_gracefulshutdown.txt

Graceful Shutdown Handler

Overview:
The GracefulShutdown class in graceful_shutdown.py is a Python-based tool for managing the orderly termination of a trading bot application. It handles shutdown signals (SIGTERM, SIGINT) to ensure open orders are canceled, WebSocket connections are closed, and asyncio tasks are terminated gracefully. The class integrates with OrderOperations and DataManager components to perform cleanup before exiting.

Purpose:

    Capture shutdown signals (e.g., Ctrl+C, system termination) to initiate a controlled shutdown.
    Cancel open orders on the exchange (except in dry-run mode).
    Close active WebSocket connections via DataManager.
    Terminate running asyncio tasks and shut down the event loop.
    Ensure a clean exit with minimal risk of dangling resources or unclosed connections.

Requirements:

    Python 3.8 or higher.
    Packages: asyncio, logging (standard library).
    Components: OrderOperations and DataManager instances (from other project modules).
    Asyncio event loop for task management.
    Linux system (assumed for compatibility with related project files).

Setup:

    Ensure graceful_shutdown.py is in the project directory (e.g., /home/jason/algorithmic_trading_binance/hbar_mainnet_bot/).
    Verify dependencies:
        No additional packages required (uses standard library).
        Ensure OrderOperations and DataManager classes are available (e.g., from data_manager.py, order_operations.py).
    Configure logging in the main application to capture shutdown logs (e.g., via logging.basicConfig in calling code).
    Ensure related project files (e.g., data_manager.py, order_operations.py) are available and compatible.

Usage:
The GracefulShutdown class is instantiated and used programmatically within a trading bot application. It is not run standalone but integrated with other components to handle shutdown events.

Instantiation:
from graceful_shutdown import GracefulShutdown
graceful_shutdown = GracefulShutdown(order_operations, data_manager, dry_run, loop)

Parameters:

    order_operations: OrderOperations instance for managing orders.
    data_manager: DataManager instance for managing WebSocket connections.
    dry_run: Boolean to enable/disable actual order cancellations.
    loop: Asyncio event loop for task management.

Example:
import asyncio
from graceful_shutdown import GracefulShutdown
from data_manager import DataManager
Assume OrderOperations is defined

async def main():
loop = asyncio.get_event_loop()
data_manager = DataManager(debug=True)
order_operations = OrderOperations()  # Placeholder
dry_run = True
shutdown_handler = GracefulShutdown(order_operations, data_manager, dry_run, loop)
Run bot logic here

await asyncio.sleep(3600)  # Simulate bot running
asyncio.run(main())

Workflow:

    Initialize GracefulShutdown with OrderOperations, DataManager, dry_run flag, and event loop.
    Register signal handlers for SIGTERM and SIGINT to trigger handle_shutdown.
    On shutdown signal:
        Prevent multiple shutdowns by tracking shutdown_initiated.
        Start async shutdown via shutdown_async.
    Shutdown procedure:
        Fetch and cancel open orders (skipped in dry-run mode) using OrderOperations.
        Close WebSocket connections via DataManager.
        Cancel all running asyncio tasks (except the shutdown task).
        Complete cleanup by shutting down async generators, executors, and the event loop.
    Exit the program with os._exit(0) to ensure a clean termination.

File Structure:

    /home/jason/algorithmic_trading_binance/hbar_mainnet_bot/
        graceful_shutdown.py: Main shutdown handling logic
        data_manager.py: Data management logic (required for WebSocket cleanup)
        order_operations.py: Order management logic (not provided, assumed)
        Other project files (e.g., exchange_connection.py, backtester.py)

Output:

    Logs:
        Info logs for shutdown initiation, order cancellations, WebSocket closure, and task cancellation.
        Error logs for failures during order cancellation, WebSocket closure, or cleanup.
        Example logs: "Received shutdown signal (SIGINT). Initiating graceful shutdown...", "WebSocket connections closed."
        Logs printed to console or configured log file (via logging setup in calling code).
    Program Exit:
        Terminates with exit code 0 after cleanup (via os._exit(0)).
        Ensures no dangling tasks or connections remain.

Notes:

    Requires OrderOperations and DataManager instances; OrderOperations is not provided in the project files.
    Dry-run mode prevents actual order cancellations for testing purposes.
    Shutdown timeout for tasks is 5 seconds to avoid hanging.
    Logging must be configured in the main application (e.g., via logging.basicConfig).
    Uses os._exit(0) for forceful exit, bypassing normal Python cleanup.

Limitations:

    Dependent on OrderOperations, which is not provided, potentially breaking functionality.
    No persistent state preservation (e.g., saving order status before exit).
    Fixed 5-second timeout for task cancellation may be insufficient for complex tasks.
    Assumes Linux signal handling (SIGTERM, SIGINT); may need adjustment for other OS.
    No retry mechanism for failed order cancellations or WebSocket closures.

Troubleshooting:

    Missing OrderOperations: Verify OrderOperations class exists and is properly instantiated.
    WebSocket closure failures: Check DataManager implementation and network connectivity.
    Task cancellation issues: Ensure tasks are cancellable and not stuck in blocking operations.
    No logs: Configure logging in the main application (e.g., logging.basicConfig).
    Signal handling issues: Confirm SIGTERM/SIGINT are supported on the system.

Future Improvements:

    Add persistent storage for order states before shutdown.
    Implement retry logic for order cancellations and WebSocket closures.
    Allow configurable timeout for task cancellation.
    Support additional signals (e.g., SIGHUP) or platform-specific shutdown methods.
    Validate OrderOperations and DataManager instances during initialization.

License:
For personal use, provided as-is. Comply with Binance.US API terms.

Created: May 11, 2025