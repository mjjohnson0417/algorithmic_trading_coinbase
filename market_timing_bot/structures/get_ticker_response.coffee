get_ticker_response = {
    'symbol': 'HBARUSDT',       # (string)  Market symbol on Binance.us
    'timestamp': 1698765432100,     # (int)     Unix timestamp in milliseconds
    'datetime':  '2023-11-01T12:34:56.789Z',      # (string)  ISO8601 datetime string
    'high': 0.075,    # (float)   Highest price in the last 24 hours
    'low':  0.070,     # (float)   Lowest price in the last 24 hours
    'bid':  0.072,     # (float)   Current highest bid price
    'bidVolume': 10000,    # (float)   Volume at the highest bid price
    'ask':  0.073,     # (float)   Current lowest ask price
    'askVolume': 12000,    # (float)   Volume at the lowest ask price
    'vwap': 0.0725,          # (float)   Volume Weighted Average Price
    'open': 0.071,    # (float)   Opening price of the last 24 hours
    'close': 0.072,   # (float)   Closing price of the last 24 hours
    'last': 0.0725,    # (float)   Last traded price
    'average': 0.07225, # (float)   Average price
    'baseVolume': 1000000,  # (float)   HBAR volume traded in the last 24 hours
    'quoteVolume': 72500, # (float)   USDT volume traded in the last 24 hours
    'change': 0.0015,        # (float)   Price change since opening
    'percentage': 2.07,    # (float)   Price change percentage since opening
    'info': {  # (dict) Exchange-specific data from Binance.us
        'symbol': 'HBARUSDT',
        'priceChange': '0.00150000',
        'priceChangePercent': '2.070',
        'weightedAvgPrice': '0.07250000',
        'prevClosePrice': '0.07100000',
        'lastPrice': '0.07250000',
        'lastQty': '100.00000000',
        'bidPrice': '0.07200000',
        'bidQty': '10000.00000000',
        'askPrice': '0.07300000',
        'askQty': '12000.00000000',
        'openPrice': '0.07100000',
        'highPrice': '0.07500000',
        'lowPrice': '0.07000000',
        'volume': '1000000.00000000',
        'quoteVolume': '72500.00000000',
        'openTime': 1698679200000,
        'closeTime': 1698765599999,
        'firstId': 123456789,  # First trade ID
        'lastId': 123456799,   # Last trade ID
        'count': 10,        # Number of trades
    }
}