
#### README for `grid_manager.py`
```markdown
# Grid Manager

## Overview
The `grid_manager.py` module implements the core logic for a grid trading bot, managing grid levels, orders, and market state responses for multiple trading pairs.

## Functionality
- **Grid Initialization**: Sets up grid levels around the current price using ATR.
- **Order Management**: Places, verifies, and syncs limit buy/sell orders.
- **Market State Handling**: Responds to long-term and short-term market states (e.g., cancels orders in downtrends).
- **Grid Reset**: Reinitializes grid if price moves significantly above the highest level.
- **Run Loop**: Periodically updates states and manages trading.

## Dependencies
- Python 3.8+
- Modules: `logging`, `pathlib`, `asyncio`, `typing`, `json`, `pandas`
- Custom Modules: `order_operations`, `indicator_calculator`, `state_manager`, `data_manager`
- External Libraries: `pandas`

## Usage
```python
from grid_manager import GridManager
# Initialize dependencies (data_manager, indicator_calculator, state_manager, order_operations_dict)
grid_manager = GridManager(data_manager, indicator_calculator, state_manager, order_operations_dict, symbols=["HBAR-USDT"])
await grid_manager.initialize_bot()
asyncio.create_task(grid_manager.run(interval=60))