# backtester.py
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
    def __init__(self, symbols: List[str], start_date: str, end_date: str, debug: bool = False):
        """
        Initializes the Backtester to load and update klines for multiple trading pairs.

        Args:
            symbols (List[str]): List of trading pairs (e.g., ['HBAR/USDT', 'BTC/USDT']).
            start_date (str): Start date for klines (e.g., '2024-01-01').
            end_date (str): End date for klines (e.g., '2024-12-31').
            debug (bool): Enable verbose logging if True.
        """
        self.symbols = symbols
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.debug = debug
        self.data_dir = "/home/jason/algorithmic_trading_binance/hbar_mainnet_bot/backtest_data"
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Extended start date for 1d klines
        self.extended_start_date_1d = self.start_date - pd.Timedelta(days=30)
        self.order_value = 0.0  # Single order value for all symbols

        # Initialize logging
        log_file = os.path.join(self.data_dir, "klines_update.log")
        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, mode='a'),
                logging.StreamHandler()
            ]
        )

        # Load API keys
        env_path = '/home/jason/api/binance/binance_us.env'
        key_loader = KeyLoader(env_path)
        if not key_loader.load_keys():
            raise ValueError("Failed to load API keys.")
        
        # Initialize exchange
        self.exchange = ccxt.binanceus({
            'apiKey': key_loader.api_key_rest,
            'secret': key_loader.secret_rest,
            'enableRateLimit': True,
            'asyncio_loop': asyncio.get_event_loop()
        })
        logging.info(f"Initialized exchange: {type(self.exchange)}")

        # Initialize IndicatorCalculator
        self.indicator_calculator = IndicatorCalculator(debug=debug)

        # Data dictionaries for each symbol
        self.klines_1d = {symbol: pd.DataFrame() for symbol in symbols}
        self.klines_1h = {symbol: pd.DataFrame() for symbol in symbols}
        self.klines_1m = {symbol: pd.DataFrame() for symbol in symbols}
        self.indicators_1d = {symbol: pd.DataFrame() for symbol in symbols}
        self.indicators_1h = {symbol: pd.DataFrame() for symbol in symbols}
        self.ticker_1m = {symbol: pd.DataFrame() for symbol in symbols}

    def get_file_path(self, symbol: str, timeframe: str, data_type: str) -> str:
        """Generate file path for CSV files."""
        symbol_clean = symbol.replace('/', '_')
        if data_type == 'klines':
            return os.path.join(self.data_dir, f"{symbol_clean}_{timeframe}_klines.csv")
        elif data_type == 'indicators':
            return os.path.join(self.data_dir, f"{symbol_clean}_{timeframe}_indicators.csv")
        elif data_type == 'market_states':
            return os.path.join(self.data_dir, f"{symbol_clean}_{timeframe}_market_states.csv")
        elif data_type == 'ticker':
            return os.path.join(self.data_dir, f"{symbol_clean}_1m_ticker.csv")
        else:
            raise ValueError(f"Invalid data_type: {data_type}")

    def load_existing_klines(self):
        """Load existing klines for each symbol."""
        logging.info("Loading existing klines...")
        expected_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for symbol in self.symbols:
            for timeframe in ['1d', '1h', '1m']:
                file_path = self.get_file_path(symbol, timeframe, 'klines')
                try:
                    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                    logging.info(f"{os.path.basename(file_path)} size: {file_size} bytes")
                    
                    df = pd.read_csv(file_path)
                    if not all(col in df.columns for col in expected_columns):
                        logging.error(f"Invalid columns in {file_path}: {df.columns}")
                        self.__dict__[f'klines_{timeframe}'][symbol] = pd.DataFrame()
                        continue
                    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                    if df['timestamp'].isna().any():
                        logging.error(f"Invalid timestamps in {file_path}")
                        self.__dict__[f'klines_{timeframe}'][symbol] = pd.DataFrame()
                        continue
                    
                    if timeframe == '1d':
                        df = df[(df['timestamp'] >= self.extended_start_date_1d) & (df['timestamp'] <= self.end_date)]
                    
                    self.__dict__[f'klines_{timeframe}'][symbol] = df
                    logging.info(f"Loaded {len(df)} {timeframe} klines for {symbol}")
                except FileNotFoundError:
                    logging.warning(f"No existing {timeframe} klines for {symbol}")
                    self.__dict__[f'klines_{timeframe}'][symbol] = pd.DataFrame()
                except Exception as e:
                    logging.error(f"Error loading {timeframe} klines for {symbol}: {e}")
                    self.__dict__[f'klines_{timeframe}'][symbol] = pd.DataFrame()

    def check_missing_dates(self, df: pd.DataFrame, timeframe: str, symbol: str) -> list:
        """Check for missing dates in the DataFrame."""
        if df.empty:
            logging.warning(f"No {timeframe} klines for {symbol}, all dates missing")
            start_date = self.extended_start_date_1d if timeframe == '1d' else self.start_date
            return pd.date_range(start=start_date, end=self.end_date, freq='1d' if timeframe == '1d' else '1h' if timeframe == '1h' else '1min').tolist()

        df = df.sort_values('timestamp')
        expected_freq = '1d' if timeframe == '1d' else '1h' if timeframe == '1h' else '1min'
        start_date = self.extended_start_date_1d if timeframe == '1d' else self.start_date
        expected_dates = pd.date_range(start=start_date, end=self.end_date, freq=expected_freq)
        existing_dates = pd.to_datetime(df['timestamp']).dt.floor('h' if timeframe == '1h' else 'D' if timeframe == '1d' else 'min')
        missing_dates = [d for d in expected_dates if d not in existing_dates.values]
        
        if missing_dates:
            logging.info(f"Found {len(missing_dates)} missing {timeframe} klines for {symbol}")
        else:
            logging.info(f"No missing {timeframe} klines for {symbol}")
        
        return missing_dates

    async def fetch_missing_klines(self, symbol: str, timeframe: str, missing_dates: list) -> pd.DataFrame:
        """Fetch klines for missing dates."""
        if not missing_dates:
            logging.info(f"No missing {timeframe} klines for {symbol}")
            return pd.DataFrame()

        start_date = self.extended_start_date_1d if timeframe == '1d' else self.start_date
        logging.info(f"Fetching {timeframe} klines for {symbol}...")
        
        klines = []
        total_fetched = 0
        missing_dates = sorted([d for d in missing_dates if start_date <= d <= self.end_date])
        if not missing_dates:
            logging.info(f"No missing {timeframe} dates for {symbol}")
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
            logging.info(f"Fetching {timeframe} klines for {symbol} from {start_date_range}")
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
                        logging.warning(f"No more {timeframe} klines for {symbol}")
                        break
                    batch = [k for k in batch if start_date.timestamp() * 1000 <= k[0] <= self.end_date.timestamp() * 1000]
                    klines.extend(batch)
                    total_fetched += len(batch)
                    if batch:
                        since = int(batch[-1][0]) + 1
                    else:
                        break
                    logging.info(f"Fetched {len(batch)} {timeframe} klines for {symbol}")
                    await asyncio.sleep(0.5)
                except Exception as e:
                    logging.error(f"Error fetching {timeframe} klines for {symbol}: {e}")
                    break

        if klines:
            df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= self.end_date)]
            logging.info(f"Fetched {len(df)} {timeframe} klines for {symbol}")
            return df
        else:
            logging.warning(f"No {timeframe} klines fetched for {symbol}")
            return pd.DataFrame()

    async def update_klines(self):
        """Update klines for all symbols."""
        logging.info("Updating klines for all symbols...")
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
                    combined_df.to_csv(file_path, index=False)
                    logging.info(f"Saved {len(combined_df)} {timeframe} klines for {symbol}")
                else:
                    logging.info(f"No new {timeframe} klines for {symbol}")

    async def validate_klines(self) -> bool:
        """Validate klines for all symbols."""
        logging.info("Validating klines...")
        for symbol in self.symbols:
            for df, timeframe in [
                (self.klines_1d[symbol], '1d'),
                (self.klines_1h[symbol], '1h'),
                (self.klines_1m[symbol], '1m')
            ]:
                if len(df) < (26 if timeframe in ['1d', '1h'] else 1):
                    logging.error(f"Insufficient {timeframe} klines for {symbol}: {len(df)} rows")
                    return False
        logging.info("Klines validation passed.")
        return True

    def calculate_indicators(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """Calculate market indicators."""
        logging.info(f"Calculating {timeframe} indicators for {symbol}...")
        klines = self.__dict__[f'klines_{timeframe}'][symbol]
        if klines.empty:
            logging.warning(f"No {timeframe} klines for {symbol}.")
            return pd.DataFrame()

        indicator_list = []
        for i in range(26, len(klines)):
            window = klines.iloc[:i + 1]
            if timeframe == '1d':
                indicators = self.indicator_calculator.calculate_1d_indicators(window, symbol)
            else:
                indicators = self.indicator_calculator.calculate_1h_indicators(window, symbol)
            
            if indicators:
                indicators['timestamp'] = klines['timestamp'].iloc[i]
                indicator_list.append(indicators)

        if indicator_list:
            indicators_df = pd.DataFrame(indicator_list)
            indicators_df = indicators_df[(indicators_df['timestamp'] >= self.start_date) & (indicators_df['timestamp'] <= self.end_date)]
            logging.info(f"Calculated {len(indicators_df)} {timeframe} indicators for {symbol}.")
            return indicators_df
        else:
            logging.warning(f"No {timeframe} indicators for {symbol}.")
            return pd.DataFrame()

    def calculate_emulated_ticker(self, symbol: str) -> pd.DataFrame:
        """Calculate emulated ticker."""
        logging.info(f"Calculating 1m ticker for {symbol}...")
        klines = self.klines_1m[symbol]
        if klines.empty:
            logging.warning(f"No 1m klines for {symbol}.")
            return pd.DataFrame()

        ticker_df = klines[['timestamp', 'close', 'volume']].copy()
        ticker_df = ticker_df.rename(columns={'close': 'price'})
        ticker_df = ticker_df[(ticker_df['timestamp'] >= self.start_date) & (ticker_df['timestamp'] <= self.end_date)]
        
        if not ticker_df.empty:
            logging.info(f"Calculated ticker with {len(ticker_df)} entries for {symbol}.")
        else:
            logging.warning(f"No ticker data for {symbol}.")
        
        return ticker_df

    def determine_market_state(self, indicators_df: pd.DataFrame, timeframe: str, symbol: str) -> pd.DataFrame:
        """Determine market state."""
        logging.info(f"Determining {timeframe} market states for {symbol}...")
        if indicators_df.empty:
            logging.warning(f"No {timeframe} indicators for {symbol}.")
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
        logging.info(f"Determined {len(states_df)} {timeframe} market states for {symbol}.")
        return states_df

    async def calculate_and_save_data(self):
        """Calculate and save indicators, market states, and ticker."""
        logging.info("Calculating and saving data...")
        for symbol in self.symbols:
            for timeframe in ['1d', '1h']:
                indicators_df = self.calculate_indicators(symbol, timeframe)
                self.__dict__[f'indicators_{timeframe}'][symbol] = indicators_df
                
                if not indicators_df.empty:
                    indicator_file = self.get_file_path(symbol, timeframe, 'indicators')
                    indicators_df.to_csv(indicator_file, index=False)
                    logging.info(f"Saved {len(indicators_df)} {timeframe} indicators for {symbol}")
                
                states_df = self.determine_market_state(indicators_df, timeframe, symbol)
                if not states_df.empty:
                    state_file = self.get_file_path(symbol, timeframe, 'market_states')
                    states_df.to_csv(state_file, index=False)
                    logging.info(f"Saved {len(states_df)} {timeframe} market states for {symbol}")

            self.ticker_1m[symbol] = self.calculate_emulated_ticker(symbol)
            if not self.ticker_1m[symbol].empty:
                ticker_file = self.get_file_path(symbol, '1m', 'ticker')
                self.ticker_1m[symbol].to_csv(ticker_file, index=False)
                logging.info(f"Saved {len(self.ticker_1m[symbol])} ticker entries for {symbol}")

    def calculate_order_value(self, balances: Dict[str, Tuple[float, float]], prices: Dict[str, float]) -> float:
        """Calculate a single order value based on total portfolio."""
        total_value = 0.0
        total_grid_levels = 15 * len(self.symbols)  # 15 levels per symbol
        
        for symbol in self.symbols:
            usdt_balance, token_balance = balances.get(symbol, (0.0, 0.0))
            price = prices.get(symbol, 0.0)
            total_value += usdt_balance + (token_balance * price)
        
        if total_value <= 0 or total_grid_levels <= 0:
            logging.warning("Invalid total value or grid levels, setting order value to 0")
            return 0.0
        
        order_value = (0.75 * total_value) / total_grid_levels
        logging.debug(f"Calculated order value: ${order_value:.2f} for {total_grid_levels} grid levels")
        return order_value

    def grid_manager_emulation(self, initial_balances: Dict[str, Tuple[float, float]], fee_rate: float = 0.001) -> Dict:
        """
        Emulates grid trading for multiple symbols.

        Args:
            initial_balances (Dict[str, Tuple[float, float]]): Initial USDT and token balances per symbol.
            fee_rate (float): Transaction fee rate.

        Returns:
            Dict: Performance metrics for each symbol and aggregate.
        """
        logging.info(f"Starting grid trading emulation for {len(self.symbols)} symbols")
        output_dir = "/home/jason/algorithmic_trading_binance/hbar_mainnet_bot/backtest_output"
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
            logging.info(f"Emulating grid trading for {symbol}")
            initial_usdt, initial_token = initial_balances.get(symbol, (1000.0, 0.0))
            token = symbol.split('/')[0]

            # Load data
            try:
                klines_1h = pd.read_csv(self.get_file_path(symbol, '1h', 'klines'))
                indicators_1h = pd.read_csv(self.get_file_path(symbol, '1h', 'indicators'))
                market_states_1d = pd.read_csv(self.get_file_path(symbol, '1d', 'market_states'))
                market_states_1h = pd.read_csv(self.get_file_path(symbol, '1h', 'market_states'))
                ticker_1m = pd.read_csv(self.get_file_path(symbol, '1m', 'ticker'))
            except FileNotFoundError as e:
                logging.error(f"Missing CSV file for {symbol}: {e}")
                continue

            for df in [klines_1h, indicators_1h, market_states_1d, market_states_1h, ticker_1m]:
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Initialize simulation
            usdt_balance = initial_usdt
            token_balance = initial_token
            orders = {}
            trades = []
            portfolio_values = []
            atr_multiplier = 2.0
            num_levels = 15
            atr_period = 14
            grid_levels = []

            trades_file = os.path.join(output_dir, f"{symbol.replace('/', '_')}_trades_{timestamp_str}.csv")
            portfolio_file = os.path.join(output_dir, f"{symbol.replace('/', '_')}_portfolio_{timestamp_str}.csv")

            def calculate_grid_levels(current_price: float, atr: float) -> List[float]:
                grid_spacing = atr * atr_multiplier
                min_distance = current_price * (0.002 + 0.01)
                if grid_spacing < min_distance:
                    grid_spacing = min_distance
                all_levels = []
                for i in range(1, 8):
                    level_below = current_price - (i - 0.5) * grid_spacing
                    level_above = current_price + (i - 0.5) * grid_spacing
                    if level_below > 0:
                        all_levels.append(level_below)
                    all_levels.append(level_above)
                unique_levels = sorted(list(set(all_levels)))
                return [round(level, 5) for level in unique_levels[:num_levels]]

            def get_latest_state(states_df: pd.DataFrame, timestamp: pd.Timestamp) -> Optional[str]:
                valid_states = states_df[states_df['timestamp'] <= timestamp]
                return valid_states['market_state'].iloc[-1] if not valid_states.empty else None

            def get_latest_atr(indicators_df: pd.DataFrame, timestamp: pd.Timestamp) -> float:
                valid_indicators = indicators_df[indicators_df['timestamp'] <= timestamp]
                return valid_indicators['atr14'].iloc[-1] if not valid_indicators.empty else 0.0001

            def check_grid_reset(ticker_df: pd.DataFrame, grid_levels: List[float], timestamp: pd.Timestamp) -> bool:
                if not grid_levels or len(ticker_df) < 30:
                    return False
                recent_ticks = ticker_df[ticker_df['timestamp'] <= timestamp].tail(30)
                if len(recent_ticks) < 30:
                    return False
                top_level = max(grid_levels)
                return all(recent_ticks['price'] > top_level)

            def update_orders(current_price: float):
                nonlocal orders
                active_levels = [level for level in sorted(grid_levels, reverse=True) if level < current_price][:5]
                above_level = next((level for level in sorted(grid_levels) if level > current_price), None)
                if above_level:
                    active_levels.append(above_level)
                
                for level in active_levels:
                    if level not in orders:
                        orders[level] = {
                            'buy_id': None, 'buy_state': None, 'buy_quantity': 0.0,
                            'sell_id': None, 'sell_state': None, 'sell_quantity': 0.0
                        }

            def prune_orders(current_price: float):
                nonlocal orders
                active_levels = [level for level in sorted(grid_levels, reverse=True) if level < current_price][:5]
                above_level = next((level for level in sorted(grid_levels) if level > current_price), None)
                if above_level:
                    active_levels.append(above_level)
                levels_to_remove = [level for level in orders if level not in active_levels and 
                                    orders[level]['buy_state'] != 'closed' and orders[level]['sell_state'] != 'open']
                for level in levels_to_remove:
                    del orders[level]
                    logging.debug(f"Pruned inactive order at {level:.5f} for {symbol}")

            def sell_all_assets(current_price: float):
                nonlocal usdt_balance, token_balance
                if token_balance > 0:
                    sale_value = token_balance * current_price * (1 - fee_rate)
                    usdt_balance += sale_value
                    trades.append({
                        'timestamp': timestamp,
                        'type': 'sell',
                        'price': current_price,
                        'quantity': token_balance,
                        'value': sale_value
                    })
                    logging.info(f"Sold {token_balance:.6f} {token} at {current_price:.5f}")
                    token_balance = 0.0

            # Initialize balances and prices for order value calculation
            current_balances = initial_balances.copy()
            current_prices = {symbol: ticker_1m['price'].iloc[0] if not ticker_1m.empty else 0.0}

            # Iterate through ticker
            for index, row in ticker_1m.iterrows():
                timestamp = row['timestamp']
                price = row['price']
                current_prices[symbol] = price
                current_balances[symbol] = (usdt_balance, token_balance)

                # Update order value once per timestamp
                if index == 0 or timestamp != ticker_1m.iloc[index - 1]['timestamp']:
                    self.order_value = self.calculate_order_value(current_balances, current_prices)
                    if self.order_value <= 0:
                        logging.warning(f"Zero order value for {symbol} at {timestamp}")
                        continue

                portfolio_value = usdt_balance + token_balance * price
                portfolio_values.append({
                    'timestamp': timestamp,
                    'usdt_balance': usdt_balance,
                    f'{token}_balance': token_balance,
                    'portfolio_value': portfolio_value
                })

                lt_state = get_latest_state(market_states_1d, timestamp)
                st_state = get_latest_state(market_states_1h, timestamp)

                if lt_state == 'downtrend':
                    sell_all_assets(price)
                    orders.clear()
                    grid_levels = []
                    logging.info(f"Long-term downtrend for {symbol} at {timestamp}")
                    continue
                if st_state == 'downtrend':
                    for level in list(orders.keys()):
                        if orders[level]['buy_state'] == 'open':
                            orders[level]['buy_id'] = None
                            orders[level]['buy_state'] = None
                            orders[level]['buy_quantity'] = 0.0
                    logging.info(f"Short-term downtrend for {symbol} at {timestamp}")
                    continue

                atr = get_latest_atr(indicators_1h, timestamp)
                if not grid_levels or check_grid_reset(ticker_1m, grid_levels, timestamp):
                    grid_levels = calculate_grid_levels(price, atr)
                    orders.clear()
                    logging.info(f"Reset grid for {symbol} at {timestamp}: {len(grid_levels)} levels")

                update_orders(price)
                if self.order_value <= 0:
                    logging.warning(f"Skipping order placement for {symbol} at {timestamp}: zero order value")
                    continue

                for level in list(orders.keys()):
                    order = orders[level]
                    next_level = next((l for l in sorted(grid_levels) if l > level), None)

                    if not order['buy_state'] and not order['sell_state']:
                        if level <= price or level == next((l for l in sorted(grid_levels) if l > price), None):
                            quantity = self.order_value / level
                            if usdt_balance >= self.order_value:
                                order['buy_id'] = f"buy_{timestamp}_{level}"
                                order['buy_state'] = 'open'
                                order['buy_quantity'] = quantity
                                logging.debug(f"Placed buy order for {symbol} at {level:.5f}")

                    if order['buy_state'] == 'open' and price <= level:
                        usdt_balance -= self.order_value * (1 + fee_rate)
                        token_balance += order['buy_quantity']
                        order['buy_state'] = 'closed'
                        trades.append({
                            'timestamp': timestamp,
                            'type': 'buy',
                            'price': level,
                            'quantity': order['buy_quantity'],
                            'value': self.order_value
                        })
                        logging.info(f"Buy order filled for {symbol} at {level:.5f}")

                    if order['buy_state'] == 'closed' and not order['sell_state'] and next_level:
                        quantity = self.order_value / next_level
                        order['sell_id'] = f"sell_{timestamp}_{next_level}"
                        order['sell_state'] = 'open'
                        order['sell_quantity'] = quantity
                        logging.debug(f"Placed sell order for {symbol} at {next_level:.5f}")

                    if order['sell_state'] == 'open' and price >= level:
                        usdt_balance += self.order_value * (1 - fee_rate)
                        token_balance -= order['sell_quantity']
                        trades.append({
                            'timestamp': timestamp,
                            'type': 'sell',
                            'price': level,
                            'quantity': order['sell_quantity'],
                            'value': self.order_value
                        })
                        logging.info(f"Sell order filled for {symbol} at {level:.5f}")
                        order['sell_id'] = None
                        order['sell_state'] = None
                        order['sell_quantity'] = 0.0
                        order['buy_id'] = None
                        order['buy_state'] = None
                        order['buy_quantity'] = 0.0

                prune_orders(price)

            # Save results
            trades_df = pd.DataFrame(trades)
            portfolio_df = pd.DataFrame(portfolio_values)
            trades_df.to_csv(trades_file, index=False)
            portfolio_df.to_csv(portfolio_file, index=False)
            logging.info(f"Saved {len(trades_df)} trades for {symbol}")
            logging.info(f"Saved {len(portfolio_df)} portfolio states for {symbol}")

            # Calculate metrics
            final_price = ticker_1m['price'].iloc[-1] if not ticker_1m.empty else 0.0
            initial_price = ticker_1m['price'].iloc[0] if not ticker_1m.empty else 0.0
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
                token = symbol.split('/')[0]
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
        logging.info("Starting backtest...")
        self.load_existing_klines()
        await self.update_klines()
        if await self.validate_klines():
            logging.info("Klines updated and validated.")
            await self.calculate_and_save_data()
            logging.info("Data calculated and saved.")
            metrics = self.grid_manager_emulation(initial_balances=initial_balances)
            logging.info("Grid trading emulation completed.")
        else:
            logging.error("Klines validation failed.")
        await self.exchange.close()