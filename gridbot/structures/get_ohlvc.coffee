get_ohlvc = [
    [
        TIMESTAMP,      # (int) Unix timestamp in milliseconds
        OPEN,           # (float) Opening price
        HIGH,           # (float) Highest price
        LOW,            # (float) Lowest price
        CLOSE,          # (float) Closing price
        VOLUME,         # (float) Volume traded
    ],
    [
        TIMESTAMP,
        OPEN,
        HIGH,
        LOW,
        CLOSE,
        VOLUME,
    ],
    ...,
]

Details

    List of Lists: The response is a list of lists. Each inner list represents one OHLCV candle/bar.

    OHLCV Data: Each candle/bar provides the open, high, low, and close prices, along with the trading volume for that period.

    Timestamp: The timestamp is in milliseconds, representing the beginning of the time period for the candle.

    Data Types: Prices (open, high, low, close) and volume are floating-point numbers.