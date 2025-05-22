# run_backtest.py
import asyncio
import argparse
import pandas as pd
from backtester import Backtester

async def main():
    parser = argparse.ArgumentParser(description="Run multi-token backtest with grid trading emulation.")
    parser.add_argument('--symbols', type=str, nargs='+', default=['XRP-USDT', 'HBAR-USDT'],
                        help='List of trading pairs (e.g., BTC-USDT HBAR-USDT)')
    parser.add_argument('--start-date', type=str, default='2025-05-09', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default='2025-05-18', help='End date (YYYY-MM-DD)')
    parser.add_argument('--initial-usdt', type=float, default=1000.0, help='Initial USDT balance per symbol')
    parser.add_argument('--initial-token', type=float, default=0.0, help='Initial token balance per symbol')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    # Normalize symbols to use '-' instead of '/'
    symbols = [symbol.replace('/', '-') for symbol in args.symbols]

    # Validate dates
    try:
        start_date = pd.to_datetime(args.start_date)
        end_date = pd.to_datetime(args.end_date)
        if start_date.year < 2000 or start_date.year > 2030:
            raise ValueError(f"Start date year {start_date.year} is out of range (2000-2030)")
        if end_date.year < 2000 or end_date.year > 2030:
            raise ValueError(f"End date year {end_date.year} is out of range (2000-2030)")
        if end_date <= start_date:
            raise ValueError("End date must be after start date")
    except ValueError as e:
        print(f"Error: Invalid date format or range: {e}")
        return

    # Create initial balances dictionary
    initial_balances = {symbol: (args.initial_usdt, args.initial_token) for symbol in symbols}

    backtester = Backtester(
        symbols=symbols,
        start_date=args.start_date,
        end_date=args.end_date,
        debug=args.debug
    )
    await backtester.run(initial_balances=initial_balances)

if __name__ == "__main__":
    asyncio.run(main())