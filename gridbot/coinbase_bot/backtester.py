# backtester.py
#function to change the multiplier, grid width is calculate_grid_levels
import pandas as pd
import logging
import os
import asyncio
import datetime
import ccxt.async_support as ccxt
from key_loader import KeyLoader
from indicator_calculator import IndicatorCalculator
import numpy as np
from typing import List, Dict, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Backtester:
    MAX_GRID_LEVELS_PER_SYMBOL = 10  # 5 buy, 5 sell levels, matching grid_manager.py

    def __init__(self, symbols: List[str], start_date: str, end_date: str, debug: bool = False):
        """
        Initializes the Backtester to emulate the grid trading strategy of grid_manager.py.

        Args:
            symbols (List[str]): List of trading pairs (e.g., ['BTC-USDT', 'HBAR-USDT']).
            start_date (str): Start date for backtest (e.g., '2024-01-01').
            end_date (str): End date for backtest (e.g., '2024-12-31').
            debug (bool): Enable verbose logging if True.
        """
        self.logger = logging.getLogger('Backtester')
        if debug:
            self.logger.setLevel(logging.DEBUG)
        
        # Validate dates
        self.logger.info(f"Received start_date: {start_date}, end_date: {end_date}")
        try:
            self.start_date = pd.to_datetime(start_date)
            self.end_date = pd.to_datetime(end_date)
            if self.start_date.year < 2000 or self.start_date.year > 2030:
                raise ValueError(f"Start date year {self.start_date.year} is out of range (2000-2030)")
            if self.end_date.year < 2000 or self.end_date.year > 2030:
                raise ValueError(f"End date year {self.end_date.year} is out of range (2000-2030)")
            if self.end_date <= self.start_date:
                raise ValueError("End date must be after start date")
        except ValueError as e:
            self.logger.error(f"Invalid date: {e}")
            raise

        # Normalize symbols to use '-'
        self.symbols = [symbol.replace('/', '-') for symbol in symbols]
        self.debug = debug
        self.data_dir = "/home/jason/algorithmic_trading_coinbase/gridbot/backtest_data"
        os.makedirs(self.data_dir, exist_ok=True)

        # Extended start date for 1d klines
        self.extended_start_date_1d = self.start_date - pd.Timedelta(days=30)
        self.allocation_ratio = 0.75
        self.order_value = 0.0

        # Initialize logging
        log_file = os.path.join(self.data_dir, "backtest.log")
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        if not any(isinstance(h, logging.FileHandler) for h in self.logger.handlers):
            self.logger.addHandler(file_handler)

        # Load API keys
        key_file_path = '/home/jason/api/coinbase/coinbase_keys.json'
        key_loader = KeyLoader(key_file_path)
        if not key_loader.load_keys():
            raise ValueError("Failed to load API keys")

        # Initialize exchange
        self.exchange = ccxt.coinbase({
            'apiKey': key_loader.api_key,
            'secret': key_loader.secret,
            'enableRateLimit': True,
            'asyncio_loop': asyncio.get_event_loop()
        })
        self.logger.info(f"Initialized exchange: {type(self.exchange)}")

        # Initialize IndicatorCalculator
        self.indicator_calculator = IndicatorCalculator(symbols=self.symbols, data_manager=None, enable_logging=debug)

        # Data dictionaries
        self.klines_1d = {symbol: pd.DataFrame() for symbol in self.symbols}
        self.klines_1h = {symbol: pd.DataFrame() for symbol in self.symbols}
        self.klines_1m = {symbol: pd.DataFrame() for symbol in self.symbols}
        self.indicators_1h = {symbol: pd.DataFrame() for symbol in self.symbols}
        self.ticker_1m = {symbol: pd.DataFrame() for symbol in self.symbols}
        self.market_states = {symbol: {'long_term': pd.DataFrame(), 'short_term': pd.DataFrame()} for symbol in self.symbols}

    def get_file_path(self, symbol: str, timeframe: str, data_type: str) -> str:
        """Generate file path for CSV files, handling both '-' and '/' in symbols."""
        symbol_clean = symbol.replace('-', '_').replace('/', '_')
        return os.path.join(self.data_dir, f"{symbol_clean}_{timeframe}_{data_type}.csv")

    def load_existing_klines(self):
        """Load existing klines from CSV files."""
        self.logger.info("Loading existing klines...")
        expected_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for symbol in self.symbols:
            for timeframe in ['1d', '1h', '1m']:
                file_path = self.get_file_path(symbol, timeframe, 'klines')
                try:
                    if os.path.exists(file_path):
                        file_size = os.path.getsize(file_path)
                        self.logger.info(f"{os.path.basename(file_path)} size: {file_size} bytes")
                        df = pd.read_csv(file_path)
                        if not all(col in df.columns for col in expected_columns):
                            self.logger.error(f"Invalid columns in {file_path}: {df.columns}")
                            self.__dict__[f'klines_{timeframe}'][symbol] = pd.DataFrame()
                            continue
                        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                        if df['timestamp'].isna().any():
                            self.logger.error(f"Invalid timestamps in {file_path}")
                            self.__dict__[f'klines_{timeframe}'][symbol] = pd.DataFrame()
                            continue
                        if timeframe == '1d':
                            df = df[(df['timestamp'] >= self.extended_start_date_1d) & (df['timestamp'] <= self.end_date)]
                        else:
                            df = df[(df['timestamp'] >= self.start_date) & (df['timestamp'] <= self.end_date)]
                        self.__dict__[f'klines_{timeframe}'][symbol] = df
                        self.logger.info(f"Loaded {len(df)} {timeframe} klines for {symbol}")
                    else:
                        self.logger.warning(f"No existing {timeframe} klines for {symbol}")
                        self.__dict__[f'klines_{timeframe}'][symbol] = pd.DataFrame()
                except Exception as e:
                    self.logger.error(f"Error loading {timeframe} klines for {symbol}: {e}")
                    self.__dict__[f'klines_{timeframe}'][symbol] = pd.DataFrame()

    def check_missing_dates(self, df: pd.DataFrame, timeframe: str, symbol: str) -> List[pd.Timestamp]:
        """Check for missing dates in the DataFrame."""
        start_date = self.extended_start_date_1d if timeframe == '1d' else self.start_date
        if df.empty:
            self.logger.warning(f"No {timeframe} klines for {symbol}, all dates missing")
            return pd.date_range(start=start_date, end=self.end_date, freq='1d' if timeframe == '1d' else '1h' if timeframe == '1h' else '1min').tolist()

        df = df.sort_values('timestamp')
        expected_freq = '1d' if timeframe == '1d' else '1h' if timeframe == '1h' else '1min'
        expected_dates = pd.date_range(start=start_date, end=self.end_date, freq=expected_freq)
        existing_dates = pd.to_datetime(df['timestamp']).dt.floor('h' if timeframe == '1h' else 'D' if timeframe == '1d' else 'min')
        missing_dates = [d for d in expected_dates if d not in existing_dates.values]
        
        self.logger.info(f"Found {len(missing_dates)} missing {timeframe} klines for {symbol}")
        return missing_dates

    async def fetch_missing_klines(self, symbol: str, timeframe: str, missing_dates: List[pd.Timestamp]) -> pd.DataFrame:
        """Fetch klines for missing dates from Coinbase."""
        if not missing_dates:
            self.logger.info(f"No missing {timeframe} klines for {symbol}")
            return pd.DataFrame()

        start_date = self.extended_start_date_1d if timeframe == '1d' else self.start_date
        self.logger.info(f"Fetching {timeframe} klines for {symbol}...")
        
        klines = []
        total_fetched = 0
        missing_dates = sorted([d for d in missing_dates if start_date <= d <= self.end_date])
        if not missing_dates:
            self.logger.info(f"No missing {timeframe} dates for {symbol}")
            return pd.DataFrame()

        ranges = []
        start = missing_dates[0]
        prev = start
        for date in missing_dates[1:]:
            if timeframe == '1d':
                delta = (date - prev).days
                expected_delta = 1
            elif timeframe == '1h':
                delta = (date - prev).total_seconds() / 3600
                expected_delta = 1
            else:  # 1m
                delta = (date - prev).total_seconds() / 60
                expected_delta = 1
            if delta > expected_delta:
                ranges.append((start, prev))
                start = date
            prev = date
        ranges.append((start, missing_dates[-1]))

        for start_date_range, end_date_range in ranges:
            if start_date_range < start_date or end_date_range > self.end_date:
                continue
            self.logger.info(f"Fetching {timeframe} klines for {symbol} from {start_date_range}")
            since = int(start_date_range.timestamp() * 1000)
            end_ms = int(end_date_range.timestamp() * 1000)
            while since <= end_ms:
                try:
                    batch = await self.exchange.fetch_ohlcv(
                        symbol=symbol,
                        timeframe=timeframe,
                        since=since,
                        limit=1000
                    )
                    if not batch:
                        self.logger.warning(f"No more {timeframe} klines for {symbol}")
                        break
                    batch = [k for k in batch if start_date.timestamp() * 1000 <= k[0] <= self.end_date.timestamp() * 1000]
                    klines.extend(batch)
                    total_fetched += len(batch)
                    if batch:
                        since = int(batch[-1][0]) + 1
                    else:
                        break
                    self.logger.info(f"Fetched {len(batch)} {timeframe} klines for {symbol}")
                    await asyncio.sleep(0.5)
                except Exception as e:
                    self.logger.error(f"Error fetching {timeframe} klines for {symbol}: {e}")
                    break

        if klines:
            df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= self.end_date)]
            self.logger.info(f"Fetched {len(df)} {timeframe} klines for {symbol}")
            return df
        else:
            self.logger.warning(f"No {timeframe} klines fetched for {symbol}")
            return pd.DataFrame()

    async def update_klines(self):
        """Update klines for all symbols."""
        self.logger.info("Updating klines for all symbols...")
        for symbol in self.symbols:
            for timeframe in ['1d', '1h', '1m']:
                file_path = self.get_file_path(symbol, timeframe, 'klines')
                existing_df = self.__dict__[f'klines_{timeframe}'][symbol]
                missing_dates = self.check_missing_dates(existing_df, timeframe, symbol)
                new_df = await self.fetch_missing_klines(symbol, timeframe, missing_dates)

                if not new_df.empty:
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                    combined_df = combined_df.drop_duplicates(subset=['timestamp'], keep='last')
                    combined_df = combined_df.sort_values('timestamp')
                    start_date = self.extended_start_date_1d if timeframe == '1d' else self.start_date
                    combined_df = combined_df[(combined_df['timestamp'] >= start_date) & (combined_df['timestamp'] <= self.end_date)]
                    self.__dict__[f'klines_{timeframe}'][symbol] = combined_df
                    # Ensure parent directory exists
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    combined_df.to_csv(file_path, index=False)
                    self.logger.info(f"Saved {len(combined_df)} {timeframe} klines for {symbol}")
                else:
                    self.logger.info(f"No new {timeframe} klines for {symbol}")

    async def validate_klines(self) -> bool:
        """Validate klines for sufficient data."""
        self.logger.info("Validating klines...")
        for symbol in self.symbols:
            for df, timeframe in [
                (self.klines_1d[symbol], '1d'),
                (self.klines_1h[symbol], '1h'),
                (self.klines_1m[symbol], '1m')
            ]:
                if len(df) < (26 if timeframe in ['1d', '1h'] else 30):  # Need 30 for ticker emulation
                    self.logger.error(f"Insufficient {timeframe} klines for {symbol}: {len(df)} rows")
                    return False
        self.logger.info("Klines validation passed.")
        return True

    def calculate_indicators(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """Calculate indicators for a symbol and timeframe."""
        self.logger.info(f"Calculating {timeframe} indicators for {symbol}...")
        klines = self.__dict__[f'klines_{timeframe}'][symbol]
        if klines.empty:
            self.logger.warning(f"No {timeframe} klines for {symbol}")
            return pd.DataFrame()

        indicator_list = []
        for i in range(26, len(klines)):
            window = klines.iloc[:i + 1]
            indicators = self.indicator_calculator.calculate_1h_indicators(window, symbol) if timeframe == '1h' else self.indicator_calculator.calculate_1d_indicators(window, symbol)
            if indicators:
                indicators['timestamp'] = klines['timestamp'].iloc[i]
                indicator_list.append(indicators)

        if indicator_list:
            indicators_df = pd.DataFrame(indicator_list)
            indicators_df = indicators_df[(indicators_df['timestamp'] >= self.start_date) & (indicators_df['timestamp'] <= self.end_date)]
            self.logger.info(f"Calculated {len(indicators_df)} {timeframe} indicators for {symbol}")
            return indicators_df
        else:
            self.logger.warning(f"No {timeframe} indicators for {symbol}")
            return pd.DataFrame()

    def calculate_emulated_ticker(self, symbol: str) -> pd.DataFrame:
        """Emulate a 1-minute ticker from 1m klines."""
        self.logger.info(f"Calculating 1m ticker for {symbol}...")
        klines = self.klines_1m[symbol]
        if klines.empty:
            self.logger.warning(f"No 1m klines for {symbol}")
            return pd.DataFrame()

        ticker_df = klines[['timestamp', 'close', 'volume']].copy()
        ticker_df = ticker_df.rename(columns={'close': 'last_price'})
        ticker_df = ticker_df[(ticker_df['timestamp'] >= self.start_date) & (ticker_df['timestamp'] <= self.end_date)]
        
        if not ticker_df.empty:
            self.logger.info(f"Calculated ticker with {len(ticker_df)} entries for {symbol}")
        else:
            self.logger.warning(f"No ticker data for {symbol}")
        
        return ticker_df

    def determine_market_state(self, indicators_df: pd.DataFrame, timeframe: str, symbol: str) -> pd.DataFrame:
        """Determine market state based on indicators, mimicking state_manager."""
        self.logger.info(f"Determining {timeframe} market states for {symbol}...")
        if indicators_df.empty:
            self.logger.warning(f"No {timeframe} indicators for {symbol}")
            return pd.DataFrame(columns=['timestamp', 'market_state'])

        states = []
        for _, row in indicators_df.iterrows():
            ema12 = row.get('ema12', 0.0)
            ema26 = row.get('ema26', 0.0)
            rsi14 = row.get('rsi14', 50.0)
            adx14 = row.get('adx14', 0.0)

            if adx14 < 20:
                market_state = 'sideways'
            elif ema12 > ema26 and rsi14 < 70 and adx14 >= 20:
                market_state = 'uptrend'
            elif ema12 < ema26 and rsi14 > 30 and adx14 >= 20:
                market_state = 'downtrend'
            else:
                market_state = 'sideways'

            states.append({'timestamp': row['timestamp'], 'market_state': market_state})

        states_df = pd.DataFrame(states)
        self.logger.info(f"Determined {len(states_df)} {timeframe} market states for {symbol}")
        return states_df

    async def calculate_and_save_data(self):
        """Calculate and save indicators, market states, and ticker."""
        self.logger.info("Calculating and saving data...")
        for symbol in self.symbols:
            # Calculate and save indicators (1h only, as grid_manager uses 1h ATR)
            indicators_df = self.calculate_indicators(symbol, '1h')
            self.indicators_1h[symbol] = indicators_df
            if not indicators_df.empty:
                indicator_file = self.get_file_path(symbol, '1h', 'indicators')
                os.makedirs(os.path.dirname(indicator_file), exist_ok=True)
                indicators_df.to_csv(indicator_file, index=False)
                self.logger.info(f"Saved {len(indicators_df)} 1h indicators for {symbol}")

            # Calculate and save market states (1d for long-term, 1h for short-term)
            for tf, tf_name in [('1d', 'long_term'), ('1h', 'short_term')]:
                indicators_df = self.calculate_indicators(symbol, tf) if tf == '1d' else self.indicators_1h[symbol]
                states_df = self.determine_market_state(indicators_df, tf, symbol)
                self.market_states[symbol][tf_name] = states_df
                if not states_df.empty:
                    state_file = self.get_file_path(symbol, tf, 'market_states')
                    os.makedirs(os.path.dirname(state_file), exist_ok=True)
                    states_df.to_csv(state_file, index=False)
                    self.logger.info(f"Saved {len(states_df)} {tf} market states for {symbol}")

            # Calculate and save ticker
            self.ticker_1m[symbol] = self.calculate_emulated_ticker(symbol)
            if not self.ticker_1m[symbol].empty:
                ticker_file = self.get_file_path(symbol, '1m', 'ticker')
                os.makedirs(os.path.dirname(ticker_file), exist_ok=True)
                self.ticker_1m[symbol].to_csv(ticker_file, index=False)
                self.logger.info(f"Saved {len(self.ticker_1m[symbol])} ticker entries for {symbol}")

    def calculate_order_value(self, balances: Dict[str, Tuple[float, float]], prices: Dict[str, float]) -> float:
        """Calculate a single order value based on total portfolio."""
        total_value = 0.0
        total_levels = len(self.symbols) * self.MAX_GRID_LEVELS_PER_SYMBOL
        
        for sym in self.symbols:
            usdt, token = balances.get(sym, (0.0, 0.0))
            price = prices.get(sym, 0.0)
            total_value += usdt + (token * price)
        
        if total_value <= 0 or total_levels <= 0:
            self.logger.warning("Invalid total value or grid levels, setting order value to 0")
            return 0.0
        
        order_value = (self.allocation_ratio * total_value) / total_levels
        self.logger.debug(f"Calculated order value: ${order_value:.2f} for {total_levels} grid levels")
        return order_value

    def emulate_grid_trading(self, initial_balances: Dict[str, Tuple[float, float]], fee_rate: float = 0.001) -> Dict:
        """
        Emulates the grid trading strategy of grid_manager.py for multiple symbols.

        Args:
            initial_balances (Dict[str, Tuple[float, float]]): Initial USDT and token balances per symbol.
            fee_rate (float): Transaction fee rate (default: 0.001).

        Returns:
            Dict: Performance metrics for each symbol and aggregate.
        """
        self.logger.info(f"Starting grid trading emulation for {len(self.symbols)} symbols")
        output_dir = "/home/jason/algorithmic_trading_coinbase/gridbot/backtest_output"
        os.makedirs(output_dir, exist_ok=True)
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results = {}
        aggregate_metrics = {
            'initial_value': 0.0,
            'final_value': 0.0,
            'profit_loss': 0.0,
            'num_trades': 0,
            'usdt_balance': 0.0,
            'token_balances': {}
        }

        for symbol in self.symbols:
            self.logger.info(f"Emulating grid trading for {symbol}")
            initial_usdt, initial_token = initial_balances.get(symbol, (1000.0, 0.0))
            token = symbol.split('-')[0]

            # Load data
            try:
                klines_1h = pd.read_csv(self.get_file_path(symbol, '1h', 'klines'))
                indicators_1h = pd.read_csv(self.get_file_path(symbol, '1h', 'indicators'))
                market_states_1d = pd.read_csv(self.get_file_path(symbol, '1d', 'market_states'))
                market_states_1h = pd.read_csv(self.get_file_path(symbol, '1h', 'market_states'))
                ticker_1m = pd.read_csv(self.get_file_path(symbol, '1m', 'ticker'))
                for df in [klines_1h, indicators_1h, market_states_1d, market_states_1h, ticker_1m]:
                    if 'timestamp' in df.columns:
                        df['timestamp'] = pd.to_datetime(df['timestamp'])
            except FileNotFoundError as e:
                self.logger.error(f"Missing CSV file for {symbol}: {e}")
                continue

            # Initialize simulation
            usdt_balance = initial_usdt
            token_balance = initial_token
            orders = {}
            trades = []
            portfolio_values = []
            grid_levels = []
            lttrade = True
            sttrade = True

            trades_file = os.path.join(output_dir, f"{symbol.replace('-', '_')}_trades_{timestamp_str}.csv")
            portfolio_file = os.path.join(output_dir, f"{symbol.replace('-', '_')}_portfolio_{timestamp_str}.csv")
            os.makedirs(os.path.dirname(trades_file), exist_ok=True)
            os.makedirs(os.path.dirname(portfolio_file), exist_ok=True)

            def calculate_grid_levels(current_price: float, atr: float) -> List[float]:
                multiplier = 1.0
                #multiplier = 2.0
                grid_spacing = max(atr * multiplier, current_price * 0.02)
                levels = set()
                for i in range(self.MAX_GRID_LEVELS_PER_SYMBOL // 2):
                    buy_level = current_price - ((i + 0.5) * grid_spacing)
                    sell_level = current_price + ((i + 0.5) * grid_spacing)
                    if buy_level > 0:
                        levels.add(round(buy_level, 4))
                    levels.add(round(sell_level, 4))
                return sorted(list(levels))

            def get_latest_state(states_df: pd.DataFrame, timestamp: pd.Timestamp) -> Optional[str]:
                valid_states = states_df[states_df['timestamp'] <= timestamp]
                return valid_states['market_state'].iloc[-1] if not valid_states.empty else 'sideways'

            def get_latest_atr(indicators_df: pd.DataFrame, timestamp: pd.Timestamp) -> float:
                valid_indicators = indicators_df[indicators_df['timestamp'] <= timestamp]
                return valid_indicators['atr14'].iloc[-1] if not valid_indicators.empty else 0.0001

            def check_grid_reset(ticker_df: pd.DataFrame, grid_levels: List[float], timestamp: pd.Timestamp) -> bool:
                if not grid_levels:
                    return True
                recent_ticks = ticker_df[ticker_df['timestamp'] <= timestamp].tail(30)
                if len(recent_ticks) < 30:
                    return False
                max_grid_price = max(grid_levels)
                return (recent_ticks['last_price'] > max_grid_price).all()

            def calculate_order_value(balances: Dict[str, Tuple[float, float]], prices: Dict[str, float]) -> float:
                total_value = 0.0
                total_levels = len(self.symbols) * self.MAX_GRID_LEVELS_PER_SYMBOL
                for sym in self.symbols:
                    usdt, token = balances.get(sym, (0.0, 0.0))
                    price = prices.get(sym, 0.0)
                    total_value += usdt + (token * price)
                return (self.allocation_ratio * total_value) / total_levels if total_levels > 0 else 0.0

            def initialize_orders(current_price: float, order_value: float) -> Dict:
                nonlocal orders, grid_levels
                orders = {}
                below_levels = sorted([level for level in grid_levels if level < current_price])[:5]
                above_levels = sorted([level for level in grid_levels if level >= current_price])[:1]
                if len(below_levels) < 5 or not above_levels:
                    return orders
                buy_levels = below_levels + above_levels
                for buy_level in buy_levels:
                    sell_level = next((level for level in grid_levels if level > buy_level), None)
                    if not sell_level:
                        continue
                    buy_quantity = order_value / buy_level if order_value > 0 else 0.0
                    orders[buy_level] = {
                        'buy_level': buy_level,
                        'buy_order_id': None,
                        'buy_quantity': round(buy_quantity, 8),
                        'buy_state': None,
                        'sell_level': sell_level,
                        'sell_order_id': None,
                        'sell_quantity': 0.0,
                        'sell_state': None
                    }
                return orders

            # Simulate trading
            current_balances = initial_balances.copy()
            current_prices = {symbol: ticker_1m['last_price'].iloc[0] if not ticker_1m.empty else 0.0}

            for index, row in ticker_1m.iterrows():
                timestamp = row['timestamp']
                price = row['last_price']
                current_prices[symbol] = price
                current_balances[symbol] = (usdt_balance, token_balance)

                # Update portfolio value
                portfolio_value = usdt_balance + token_balance * price
                portfolio_values.append({
                    'timestamp': timestamp,
                    'usdt_balance': usdt_balance,
                    f'{token}_balance': token_balance,
                    'portfolio_value': portfolio_value
                })

                # Update order value
                order_value = calculate_order_value(current_balances, current_prices)
                if order_value <= 0:
                    self.logger.warning(f"Zero order value for {symbol} at {timestamp}")
                    continue

                # Get market states
                lt_state = get_latest_state(market_states_1d, timestamp)
                st_state = get_latest_state(market_states_1h, timestamp)

                # Handle long-term downtrend
                if not lttrade:
                    if lt_state in ['uptrend', 'sideways']:
                        lttrade = True
                        self.logger.info(f"Long-term state recovered to {lt_state} for {symbol}, lttrade=True")
                elif lt_state == 'downtrend':
                    usdt_balance += token_balance * price * (1 - fee_rate)
                    trades.append({
                        'timestamp': timestamp,
                        'type': 'sell',
                        'price': price,
                        'quantity': token_balance,
                        'value': token_balance * price
                    })
                    token_balance = 0.0
                    orders.clear()
                    grid_levels = []
                    lttrade = False
                    self.logger.info(f"Long-term downtrend for {symbol} at {timestamp}, sold all assets")
                    continue

                # Handle short-term downtrend
                if not sttrade:
                    if st_state in ['uptrend', 'sideways']:
                        sttrade = True
                        self.logger.info(f"Short-term state recovered to {st_state} for {symbol}, sttrade=True")
                elif st_state == 'downtrend':
                    for level in list(orders.keys()):
                        if orders[level]['buy_state'] == 'open':
                            orders[level]['buy_order_id'] = None
                            orders[level]['buy_state'] = None
                            orders[level]['buy_quantity'] = 0.0
                    sttrade = False
                    self.logger.info(f"Short-term downtrend for {symbol} at {timestamp}, canceled buy orders")
                    continue

                # Check grid reset
                if check_grid_reset(ticker_1m, grid_levels, timestamp):
                    grid_levels = calculate_grid_levels(price, get_latest_atr(indicators_1h, timestamp))
                    orders = initialize_orders(price, order_value)
                    self.logger.info(f"Reset grid for {symbol} at {timestamp}: {len(grid_levels)} levels")

                # Initialize grid if empty
                if not grid_levels:
                    grid_levels = calculate_grid_levels(price, get_latest_atr(indicators_1h, timestamp))
                    orders = initialize_orders(price, order_value)
                    self.logger.info(f"Initialized grid for {symbol} at {timestamp}: {len(grid_levels)} levels")

                # Place and fill orders
                for level in list(orders.keys()):
                    order = orders[level]
                    if not order['buy_state'] and not order['sell_state']:
                        if usdt_balance >= order_value:
                            order['buy_order_id'] = f"buy_{timestamp}_{level}"
                            order['buy_state'] = 'open'
                            self.logger.debug(f"Placed buy order for {symbol} at {level:.4f}")

                    if order['buy_state'] == 'open' and price <= level:
                        usdt_balance -= order_value * (1 + fee_rate)
                        token_balance += order['buy_quantity']
                        order['buy_state'] = 'closed'
                        order['sell_quantity'] = order['buy_quantity']
                        trades.append({
                            'timestamp': timestamp,
                            'type': 'buy',
                            'price': level,
                            'quantity': order['buy_quantity'],
                            'value': order_value
                        })
                        self.logger.info(f"Buy order filled for {symbol} at {level:.4f}")

                    if order['buy_state'] == 'closed' and not order['sell_state']:
                        order['sell_order_id'] = f"sell_{timestamp}_{order['sell_level']}"
                        order['sell_state'] = 'open'
                        self.logger.debug(f"Placed sell order for {symbol} at {order['sell_level']:.4f}")

                    if order['sell_state'] == 'open' and price >= order['sell_level']:
                        usdt_balance += order_value * (1 - fee_rate)
                        token_balance -= order['sell_quantity']
                        trades.append({
                            'timestamp': timestamp,
                            'type': 'sell',
                            'price': order['sell_level'],
                            'quantity': order['sell_quantity'],
                            'value': order_value
                        })
                        self.logger.info(f"Sell order filled for {symbol} at {order['sell_level']:.4f}")
                        order['sell_order_id'] = None
                        order['sell_state'] = None
                        order['sell_quantity'] = 0.0
                        order['buy_order_id'] = None
                        order['buy_state'] = None
                        order['buy_quantity'] = round(order_value / level, 8)

                    # Handle stray orders
                    if order['buy_state'] == 'open' and price > level * 1.05:
                        order['buy_order_id'] = None
                        order['buy_state'] = None
                        self.logger.info(f"Canceled stray buy order for {symbol} at {level:.4f}")

            # Save results
            trades_df = pd.DataFrame(trades)
            portfolio_df = pd.DataFrame(portfolio_values)
            trades_df.to_csv(trades_file, index=False)
            portfolio_df.to_csv(portfolio_file, index=False)
            self.logger.info(f"Saved {len(trades_df)} trades for {symbol}")
            self.logger.info(f"Saved {len(portfolio_df)} portfolio states for {symbol}")

            # Calculate metrics
            final_price = ticker_1m['last_price'].iloc[-1] if not ticker_1m.empty else 0.0
            initial_price = ticker_1m['last_price'].iloc[0] if not ticker_1m.empty else 0.0
            final_value = usdt_balance + token_balance * final_price
            initial_value = initial_usdt + initial_token * initial_price
            profit_loss = final_value - initial_value
            result_type = "Gain" if profit_loss >= 0 else "Loss"
            num_trades = len(trades_df)

            results[symbol] = {
                'initial_value': float(initial_value),
                'final_value': float(final_value),
                'profit_loss': float(profit_loss),
                'result_type': result_type,
                'num_trades': num_trades,
                'usdt_balance': usdt_balance,
                f'{token}_balance': token_balance,
                'trades_file': trades_file,
                'portfolio_file': portfolio_file
            }

            aggregate_metrics['initial_value'] += initial_value
            aggregate_metrics['final_value'] += final_value
            aggregate_metrics['num_trades'] += num_trades
            aggregate_metrics['usdt_balance'] += usdt_balance
            aggregate_metrics['token_balances'][token] = token_balance

        # Finalize aggregate metrics
        aggregate_metrics['profit_loss'] = aggregate_metrics['final_value'] - aggregate_metrics['initial_value']
        aggregate_metrics['result_type'] = "Gain" if aggregate_metrics['profit_loss'] >= 0 else "Loss"
        results['aggregate'] = aggregate_metrics

        # Print results
        print("\n=== Multi-Token Grid Trading Backtest Results ===")
        print(f"Period: {self.start_date} to {self.end_date}")
        for symbol in self.symbols:
            if symbol in results:
                metrics = results[symbol]
                token = symbol.split('-')[0]
                print(f"\nSymbol: {symbol}")
                print(f"Initial Portfolio:")
                print(f"  USDT: {initial_balances[symbol][0]:.2f}")
                print(f"  {token}: {initial_balances[symbol][1]:.6f}")
                print(f"  Total Value: ${metrics['initial_value']:.2f}")
                print(f"Final Portfolio:")
                print(f"  USDT: {metrics['usdt_balance']:.2f}")
                print(f"  {token}: {metrics[f'{token}_balance']:.6f}")
                print(f"  Total Value: ${metrics['final_value']:.2f}")
                print(f"Performance:")
                print(f"  Total Trades: {metrics['num_trades']}")
                print(f"  Profit/Loss: ${abs(metrics['profit_loss']):.2f} ({metrics['result_type']})")
                print(f"Output Files:")
                print(f"  Trades: {metrics['trades_file']}")
                print(f"  Portfolio: {metrics['portfolio_file']}")
        print(f"\nAggregate Performance:")
        print(f"  Initial Value: ${aggregate_metrics['initial_value']:.2f}")
        print(f"  Final Value: ${aggregate_metrics['final_value']:.2f}")
        print(f"  Profit/Loss: ${abs(aggregate_metrics['profit_loss']):.2f} ({aggregate_metrics['result_type']})")
        print(f"  Total Trades: {aggregate_metrics['num_trades']}")
        print("========================================\n")

        return results

    async def run(self, initial_balances: Dict[str, Tuple[float, float]]):
        """Run the backtest for all symbols."""
        self.logger.info("Starting backtest...")
        try:
            self.load_existing_klines()
            await self.update_klines()
            if await self.validate_klines():
                self.logger.info("Klines updated and validated")
                await self.calculate_and_save_data()
                self.logger.info("Data calculated and saved")
                metrics = self.emulate_grid_trading(initial_balances=initial_balances)
                self.logger.info("Grid trading emulation completed")
            else:
                self.logger.error("Klines validation failed")
        finally:
            self.logger.info("Closing exchange connection...")
            try:
                await self.exchange.close()
                self.logger.info("Exchange connection closed successfully")
            except Exception as e:
                self.logger.error(f"Error closing exchange connection: {e}")
