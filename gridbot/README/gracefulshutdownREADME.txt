
#### README for `graceful_shutdown.py`
```markdown
# Graceful Shutdown

## Overview
The `graceful_shutdown.py` module ensures the grid trading bot shuts down cleanly by canceling orders and closing connections when a termination signal is received.

## Functionality
- **Shutdown Process**: Cancels all open orders, closes WebSocket and REST connections, and signals completion.
- **Dry Run Mode**: Simulates shutdown without executing actions.
- **Error Handling**: Logs errors and ensures shutdown completion.

## Dependencies
- Python 3.8+
- Modules: `asyncio`, `logging`, `signal`, `typing`
- Custom Modules: `data_manager`, `order_operations`, `exchange_connection`
- External Libraries: None

## Usage
```python
from graceful_shutdown import GracefulShutdown

shutdown = GracefulShutdown(order_operations_dict, data_manager, exchange)
shutdown_event = asyncio.Event()
await shutdown.shutdown(signal.SIGINT, shutdown_event)