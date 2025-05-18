HBAR/USDT Grid Trading Backtester

Overview:
This Python tool backtests a grid trading strategy for the HBAR/USDT pair on Binance.US. It fetches historical kline data, calculates technical indicators, determines market states, emulates a ticker, and simulates grid trading. Trades, portfolio states, and performance metrics are logged to CSV files.

Purpose:

    Fetch and update 1-minute, 1-hour, and 1-day kline data for HBAR/USDT.
    Calculate indicators (EMA, RSI, ATR, ADX) for market analysis.
    Classify market states (uptrend, downtrend, sideways).
    Emulate a 1-minute ticker from kline data.
    Simulate grid trading with configurable parameters.
    Output performance metrics and detailed logs.

Requirements:

    Python 3.8 or higher.
    Packages: pandas, numpy, ccxt.async_support, python-dotenv (plus dependencies for indicator_calculator.py and key_loader.py).
    Binance.US API keys in /home/jason/api/binance/binance_us.env.
    Linux system with storage for CSV files.

Setup:

    Place project files in /home/jason/algorithmic_trading_binance/hbar_mainnet_bot/.
    Install dependencies: pip install pandas numpy ccxt.async_support python-dotenv Note: Additional packages may be needed for indicator_calculator.py.
    Create /home/jason/api/binance/binance_us.env with: BINANCE_US_API_KEY=your_api_key BINANCE_US_SECRET=your_secret_key
    Create directories: mkdir -p /home/jason/algorithmic_trading_binance/hbar_mainnet_bot/backtest_data mkdir -p /home/jason/algorithmic_trading_binance/hbar_mainnet_bot/backtest_output

Usage:
Run the backtest with run_backtest.py:
python run_backtest.py --start-date YYYY-MM-DD --end-date YYYY-MM-DD --initial-usdt USDT_AMOUNT --initial-hbar HBAR_AMOUNT --debug

Arguments:

    --start-date: Start date (default: 2024-05-09).
    --end-date: End date (default: 2025-05-09).
    --initial-usdt: Initial USDT (default: 1000.0).
    --initial-hbar: Initial HBAR (default: 0.0).
    --debug: Enable verbose logging (optional).

Example:
python run_backtest.py --start-date 2024-01-01 --end-date 2024-12-31 --initial-usdt 1000.0 --initial-hbar 0.0 --debug

Workflow:

    Load existing klines from backtest_data/ CSV files (1d, 1h, 1m).
    Check for missing klines and fetch updates from Binance.US via CCXT.
    Validate klines (require at least 26 rows for 1d/1h).
    Calculate indicators (EMA12, EMA26, RSI14, ATR14, ADX14) for 1d/1h.
    Determine market states (uptrend, downtrend, sideways).
    Emulate a 1-minute ticker from 1m klines.
    Simulate grid trading:
        Calculate grid levels using ATR (multiplier: 2.0).
        Place buy/sell orders based on market states and price.
        Log trades and portfolio states to backtest_output/.
        Output metrics (profit/loss, trades, final value) to console.

File Structure:

    /home/jason/algorithmic_trading_binance/hbar_mainnet_bot/
        backtest_data/
            hbar_usdt_1d_klines.csv: 1-day klines
            hbar_usdt_1h_klines.csv: 1-hour klines
            hbar_usdt_1m_klines.csv: 1-minute klines
            hbar_usdt_1d_indicators.csv: 1-day indicators
            hbar_usdt_1h_indicators.csv: 1-hour indicators
            hbar_usdt_1d_market_states.csv: 1-day market states
            hbar_usdt_1h_market_states.csv: 1-hour market states
            hbar_usdt_1m_ticker.csv: 1-minute ticker
            klines_update.log: Log file
        backtest_output/
            hbar_usdt_trades_YYYYMMDD_HHMMSS.csv: Trade logs
            hbar_usdt_portfolio_YYYYMMDD_HHMMSS.csv: Portfolio logs
        backtester.py: Main backtesting logic
        run_backtest.py: Script to run backtest
        indicator_calculator.py: Indicator logic (not provided)
        key_loader.py: API key loader (not provided)
        /home/jason/api/binance/binance_us.env: API keys

Output:

    Console: Shows initial/final portfolio, profit/loss, trade count, and CSV paths.
    CSV Files:
        Trades: timestamp, type (buy/sell), price, quantity, value.
        Portfolio: timestamp, usdt_balance, hbar_balance, portfolio_value.
        Data: Updated klines, indicators, market states, ticker in backtest_data/.

Notes:

    Hardcoded paths (/home/jason/) require modification for other systems.
    Requires indicator_calculator.py and key_loader.py.
    Respects Binance.US rate limits with 0.5s delays.
    Grid strategy:
        Minimum grid spacing: 0.2% + 1% of price.
        Maintains 5 levels below, 1 above price.
        Cancels orders or sells in downtrends.
    Logs saved to klines_update.log; debug mode adds detail.

Limitations:

    Specific to HBAR/USDT on Binance.US.
    Assumes 0.1% fees, ignores slippage.
    Missing indicator_calculator.py or key_loader.py may break execution.
    Limited by available kline data and API access.

Troubleshooting:

    API errors: Check .env file path and contents.
    Missing data: Verify backtest_data/ CSVs and internet connection.
    Insufficient data: Ensure date range has enough klines (26+ for 1d/1h).
    Dependencies: Install all packages and check indicator_calculator.py.

Future Improvements:

    Support multiple pairs/exchanges.
    Configurable grid parameters.
    Add slippage and dynamic fees.
    Include performance visualizations.
    Use relative paths for portability.

License:
For personal use, provided as-is. Comply with Binance.US API terms.

Created: May 10, 2025