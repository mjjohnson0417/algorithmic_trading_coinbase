
#### README for `indicator_calculator.py`
```markdown
# Indicator Calculator

## Overview
The `indicator_calculator.py` module computes technical indicators for trading pairs using data from `DataManager`, supporting market state analysis.

## Functionality
- **Indicators**: Calculates EMA, RSI, ADX, ATR, and MACD for 1-hour and 1-day timeframes, plus timing indicators (bid-ask spread, order book imbalance, etc.).
- **Data Validation**: Ensures sufficient and valid data before computation.
- **Error Handling**: Returns default values for insufficient or invalid data.

## Dependencies
- Python 3.8+
- Modules: `logging`, `pathlib`, `pandas`, `numpy`
- Custom Modules: None
- External Libraries: `pandas`, `numpy`

## Usage
```python
from indicator_calculator import IndicatorCalculator
from data_manager import DataManager

data_manager = DataManager(symbols=["HBAR-USDT"], exchange_connection=exchange)
calculator = IndicatorCalculator(symbols=["HBAR-USDT"], data_manager=data_manager)
indicators = calculator.calculate_all_indicators()
print(indicators)