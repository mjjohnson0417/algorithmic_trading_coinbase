import re
import pandas as pd
from datetime import datetime
import json

def parse_log(log_file):
    orders = []
    prices = []
    duplicates = []
    
    # Regex patterns
    order_pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*Order Added: ID=([^,]+), Symbol=([^,]+), TriggerTimeframe=([^,]+), Pattern=([^,]+), Candlestick=([^,]+), Indicators=\[(.*?)\], Buy=([\d.]+), Sell=([\d.]+), Stop-Loss=([^,]+), IsBullish=(True|False), Quantity=([\d.]+)"
    price_pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*\s+([^:]+): ([\d.]+)"
    duplicate_pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*Duplicate order detected: NewID=([^,]+), DuplicateID=([^,]+), Symbol=([^,]+), Timeframe=([^,]+), Pattern=([^,]+), Candlestick=([^,]+), Price=([\d.]+)"
    
    with open(log_file, 'r') as f:
        for line in f:
            # Parse orders
            order_match = re.search(order_pattern, line)
            if order_match:
                orders.append({
                    'timestamp': datetime.strptime(order_match.group(1), '%Y-%m-%d %H:%M:%S'),
                    'order_id': order_match.group(2),
                    'symbol': order_match.group(3),
                    'timeframe': order_match.group(4),
                    'pattern': order_match.group(5),
                    'candlestick': order_match.group(6),
                    'indicators': order_match.group(7).split(', ') if order_match.group(7) else [],
                    'buy_price': float(order_match.group(8)),
                    'sell_price': float(order_match.group(9)),
                    'stop_loss': float(order_match.group(10)) if order_match.group(10) != 'None' else None,
                    'is_bullish': order_match.group(11) == 'True',
                    'quantity': float(order_match.group(12))
                })
            
            # Parse prices
            price_match = re.search(price_pattern, line)
            if price_match:
                prices.append({
                    'timestamp': datetime.strptime(price_match.group(1), '%Y-%m-%d %H:%M:%S'),
                    'symbol': price_match.group(2),
                    'price': float(price_match.group(3))
                })
            
            # Parse duplicates
            duplicate_match = re.search(duplicate_pattern, line)
            if duplicate_match:
                duplicates.append({
                    'timestamp': datetime.strptime(duplicate_match.group(1), '%Y-%m-%d %H:%M:%S'),
                    'new_id': duplicate_match.group(2),
                    'duplicate_id': duplicate_match.group(3),
                    'symbol': duplicate_match.group(4),
                    'timeframe': duplicate_match.group(5),
                    'pattern': duplicate_match.group(6),
                    'candlestick': duplicate_match.group(7),
                    'price': float(duplicate_match.group(8))
                })
    
    return orders, prices, duplicates

def simulate_trades(orders, prices, order_size=100):
    trades = []
    price_df = pd.DataFrame(prices).pivot(index='timestamp', columns='symbol', values='price').sort_index()
    
    for order in orders:
        symbol = order['symbol']
        entry_time = order['timestamp']
        is_bullish = order['is_bullish']
        entry_price = order['buy_price'] if is_bullish else order['sell_price']
        target_price = order['sell_price'] if is_bullish else order['buy_price']
        stop_loss = order['stop_loss'] if is_bullish else None
        
        # Get price history after entry
        price_history = price_df[symbol][price_df.index >= entry_time].dropna()
        outcome = None
        exit_price = None
        exit_time = None
        
        for ts, price in price_history.items():
            if is_bullish:
                if price >= target_price:
                    outcome = 'filled'
                    exit_price = target_price
                    exit_time = ts
                    break
                elif stop_loss and price <= stop_loss:
                    outcome = 'stopped'
                    exit_price = stop_loss
                    exit_time = ts
                    break
            else:
                if price <= target_price:
                    outcome = 'filled'
                    exit_price = target_price
                    exit_time = ts
                    break
        
        # Calculate P/L
        if outcome:
            if is_bullish:
                pl = (exit_price - entry_price) * order_size
            else:
                pl = (entry_price - exit_price) * order_size
            trades.append({
                'order_id': order['order_id'],
                'symbol': symbol,
                'timeframe': order['timeframe'],
                'pattern': order['pattern'],
                'candlestick': order['candlestick'],
                'indicators': order['indicators'],
                'entry_time': entry_time,
                'exit_time': exit_time,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'outcome': outcome,
                'pl': pl
            })
    
    return trades

def analyze_trades(trades, duplicates):
    trades_df = pd.DataFrame(trades)
    duplicates_df = pd.DataFrame(duplicates)
    
    # Unprofitable trades
    unprofitable = trades_df[trades_df['pl'] < 0]
    unprofitable_summary = unprofitable.groupby(['symbol', 'timeframe', 'pattern', 'candlestick'])['pl'].agg(['count', 'sum', 'mean']).reset_index()
    unprofitable_summary.columns = ['symbol', 'timeframe', 'pattern', 'candlestick', 'trade_count', 'total_pl', 'avg_pl']
    
    # Duplicate counts
    duplicate_summary = duplicates_df.groupby(['symbol', 'timeframe', 'pattern', 'candlestick'])['new_id'].count().reset_index(name='duplicate_count')
    
    print("Unprofitable Trades Summary:")
    print(unprofitable_summary)
    print("\nDuplicate Orders Summary:")
    print(duplicate_summary)
    
    # Save to CSV
    unprofitable_summary.to_csv('unprofitable_trades.csv', index=False)
    duplicate_summary.to_csv('duplicate_orders.csv', index=False)

if __name__ == "__main__":
    log_file = "logs/market_timing_manager.log"
    orders, prices, duplicates = parse_log(log_file)
    trades = simulate_trades(orders, prices, order_size=100)
    analyze_trades(trades, duplicates)