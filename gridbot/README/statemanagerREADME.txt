
#### README for `state_manager.py`
```markdown
# State Manager

## Overview
The `state_manager.py` module determines market states (uptrend, downtrend, sideways) for trading pairs based on technical indicators.

## Functionality
- **Market State Calculation**: Uses EMA, RSI, and ADX to classify long-term (1-day) and short-term (1-hour) market states.
- **State Storage**: Maintains a dictionary of states for each symbol.
- **Logging**: Logs state calculations and errors.

## Dependencies
- Python 3.8+
- Modules: `logging`, `pathlib`, `typing`
- Custom Modules: `indicator_calculator`, `data_manager`
- External Libraries: None

## Usage
```python
from state_manager import StateManager
from indicator_calculator import IndicatorCalculator
from data_manager import DataManager

data_manager = DataManager(symbols=["HBAR-USDT"], exchange_connection=exchange)
calculator = IndicatorCalculator(symbols=["HBAR-USDT"], data_manager=data_manager)
state_manager = StateManager(data_manager, calculator, symbols=["HBAR-USDT"])
states = state_manager.calculate_all_market_states()
print(states)