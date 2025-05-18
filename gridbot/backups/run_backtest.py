# run_backtest.py
import asyncio
import argparse
from backtester import Backtester

async def main():
    parser = argparse.ArgumentParser(description="Run multi-token backtest with grid trading emulation.")
    parser.add_argument('--symbols', type=str, nargs='+', default=['HBAR/USDT', 'BTC/USDT', 'ETH/USDT'],
                        help='List of trading pairs (e.g., HBAR/USDT BTC/USDT)')
    parser.add_argument('--start-date', type=str, default='2024-05-09', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default='2025-05-09', help='End date (YYYY-MM-DD)')
    parser.add_argument('--initial-usdt', type=float, default=1000.0, help='Initial USDT balance per symbol')
    parser.add_argument('--initial-token', type=float, default=0.0, help='Initial token balance per symbol')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()

    # Create initial balances dictionary
    initial_balances = {symbol: (args.initial_usdt, args.initial_token) for symbol in args.symbols}

    backtester = Backtester(
        symbols=args.symbols,
        start_date=args.start_date,
        end_date=args.end_date,
        debug=args.debug
    )
    await backtester.run(initial_balances=initial_balances)

if __name__ == "__main__":
    asyncio.run(main())