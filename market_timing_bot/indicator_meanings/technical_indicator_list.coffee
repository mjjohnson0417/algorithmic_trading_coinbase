List of Technical Indicators for Futures Trading

Below is a comprehensive list of indicators, grouped by category, with their data requirements, recommended timeframes, and WebSocket subscriptions. I’ve included all major indicators used in futures trading, ensuring coverage for momentum, trend, volatility, volume, and support/resistance, as these are critical for timing entries/exits in markets like crypto futures.
1. Momentum Indicators

These measure the speed or strength of price movements, identifying overbought/oversold conditions or momentum shifts.

    Relative Strength Index (RSI):
        Purpose: Identifies overbought (>70) or oversold (<30) conditions for entry/exit signals.
        Data Input: Closing prices.
        Kline Timeframes:
            Day trading: 1-minute, 5-minute, 15-minute (fast signals for scalping).
            Swing trading: 1-hour, 4-hour (smoother signals).
            Common period: 14 (adjust to 9 or 21 for sensitivity).
        Calculation: RSI = 100 - (100 / (1 + RS)), where RS = (Average Gain / Average Loss) over n periods.
        WebSocket Subscriptions:
            kline (e.g., candle channel on Coinbase WebSocket for BTC/USD perpetual futures, 1m/5m/15m intervals).
            Example: wss://ws-feed.pro.coinbase.com with {"type": "subscribe", "channels": [{"name": "candles", "product_ids": ["BTC-USD-PERP"], "interval": "1m"}]}.
    Stochastic Oscillator:
        Purpose: Compares closing price to price range, signaling overbought (>80) or oversold (<20).
        Data Input: High, Low, Close prices.
        Kline Timeframes: 1-minute, 5-minute, 15-minute (day trading); 1-hour (swing trading).
            Common settings: %K period = 14, %D period = 3, smoothing = 3.
        Calculation: %K = [(Close - Lowest Low) / (Highest High - Lowest Low)] * 100; %D = SMA of %K.
        WebSocket Subscriptions: kline (1m/5m/15m).
    Commodity Channel Index (CCI):
        Purpose: Measures deviation from average price, identifying overbought (>100) or oversold (<-100).
        Data Input: Typical Price (High + Low + Close) / 3, SMA of Typical Price.
        Kline Timeframes: 5-minute, 15-minute (day trading); 1-hour (swing trading).
            Common period: 20.
        Calculation: CCI = (Typical Price - SMA of Typical Price) / (0.015 * Mean Deviation).
        WebSocket Subscriptions: kline (5m/15m).
    Williams %R:
        Purpose: Similar to Stochastic, measures overbought (>-20) or oversold (<-80).
        Data Input: High, Low, Close prices.
        Kline Timeframes: 1-minute, 5-minute (scalping); 15-minute (day trading).
            Common period: 14.
        Calculation: %R = [(Highest High - Close) / (Highest High - Lowest Low)] * -100.
        WebSocket Subscriptions: kline (1m/5m).

2. Trend Indicators

These identify the direction and strength of price trends, guiding entries in trending markets.

    Moving Averages (SMA, EMA):
        Purpose: Smooths price data to identify trends; crossovers signal entries/exits.
        Data Input: Closing prices.
        Kline Timeframes:
            SMA: 15-minute, 1-hour (trend confirmation).
            EMA: 1-minute, 5-minute (fast signals for day trading).
            Common periods: 10, 20, 50 (short-term); 100, 200 (long-term).
        Calculation:
            SMA = Sum of Closing Prices / n.
            EMA = (Close * k) + (Previous EMA * (1 - k)), where k = 2 / (n + 1).
        WebSocket Subscriptions: kline (1m/5m/15m).
    MACD (Moving Average Convergence Divergence):
        Purpose: Tracks trend momentum via EMA differences; crossovers signal entries.
        Data Input: Closing prices.
        Kline Timeframes: 5-minute, 15-minute (day trading); 1-hour (swing trading).
            Common settings: Fast EMA = 12, Slow EMA = 26, Signal Line = 9.
        Calculation: MACD = 12-EMA - 26-EMA; Signal = 9-EMA of MACD; Histogram = MACD - Signal.
        WebSocket Subscriptions: kline (5m/15m).
    Average Directional Index (ADX):
        Purpose: Measures trend strength (>25 indicates strong trend).
        Data Input: High, Low, Close prices.
        Kline Timeframes: 15-minute, 1-hour (trend confirmation).
            Common period: 14.
        Calculation: ADX = Smoothed (+DI - -DI) / (+DI + -DI), where DI = Directional Indicators.
        WebSocket Subscriptions: kline (15m).

3. Volatility Indicators

These measure price volatility to identify breakout opportunities or set stop-losses.

    Bollinger Bands:
        Purpose: Indicates volatility and overbought/oversold levels; bands widen in volatility, narrow in consolidation.
        Data Input: Closing prices, Standard Deviation.
        Kline Timeframes: 5-minute, 15-minute (day trading); 1-hour (swing trading).
            Common settings: Period = 20, Multiplier = 2.
        Calculation: Middle Band = 20-SMA; Upper/Lower Bands = Middle ± (2 * StdDev).
        WebSocket Subscriptions: kline (5m/15m).
    Average True Range (ATR):
        Purpose: Measures volatility for stop-loss placement or breakout confirmation.
        Data Input: High, Low, Close prices.
        Kline Timeframes: 5-minute, 15-minute (day trading).
            Common period: 14.
        Calculation: ATR = SMA of True Range (max of |High-Low|, |High-PrevClose|, |Low-PrevClose|).
        WebSocket Subscriptions: kline (5m/15m).
    Keltner Channels:
        Purpose: Similar to Bollinger Bands, indicates volatility and trend direction.
        Data Input: Typical Price, ATR.
        Kline Timeframes: 5-minute, 15-minute (day trading).
            Common settings: Period = 20, Multiplier = 2.
        Calculation: Middle = 20-EMA; Upper/Lower = Middle ± (2 * ATR).
        WebSocket Subscriptions: kline (5m/15m).

4. Volume Indicators

These analyze trading volume to confirm price movements or signal reversals.

    Volume Weighted Average Price (VWAP):
        Purpose: Acts as dynamic support/resistance; price above VWAP suggests bullishness.
        Data Input: Price (Typical Price), Volume.
        Kline Timeframes: 1-minute, 5-minute (intraday trading).
            Reset daily for futures.
        Calculation: VWAP = Cumulative (Typical Price * Volume) / Cumulative Volume.
        WebSocket Subscriptions:
            kline (1m/5m) for price and volume.
            trade (real-time trades for tick-by-tick VWAP updates).
            Example: {"type": "subscribe", "channels": [{"name": "trades", "product_ids": ["BTC-USD-PERP"]}]}.
    On-Balance Volume (OBV):
        Purpose: Tracks volume flow to confirm trends; rising OBV with price confirms strength.
        Data Input: Closing prices, Volume.
        Kline Timeframes: 5-minute, 15-minute (day trading).
        Calculation: OBV = Previous OBV + (Volume if Close > PrevClose, -Volume if Close < PrevClose, 0 if equal).
        WebSocket Subscriptions: kline (5m/15m).
    Accumulation/Distribution Line (A/D):
        Purpose: Measures buying/selling pressure based on price and volume.
        Data Input: High, Low, Close, Volume.
        Kline Timeframes: 5-minute, 15-minute (day trading).
        Calculation: Money Flow Multiplier = [(Close - Low) - (High - Close)] / (High - Low); A/D = Previous A/D + (MFM * Volume).
        WebSocket Subscriptions: kline (5m/15m).

5. Support/Resistance Indicators

These identify key price levels for entry/exit or stop placement.

    Fibonacci Retracement:
        Purpose: Identifies potential support/resistance levels based on price retracements.
        Data Inputcontreparty: High, Low prices over a swing (manual input or automated swing detection).
        Kline Timeframes: 15-minute, 1-hour (day trading); 4-hour, daily (swing trading).
            Common levels: 23.6%, 38.2%, 50%, 61.8%, 100%.
        Calculation: Levels calculated as percentages of the swing high-low range.
        WebSocket Subscriptions: kline (15m/1h) for swing detection.
    Pivot Points:
        Purpose: Provides daily/weekly support/resistance levels for intraday trading.
        Data Input: High, Low, Close of previous period (daily, weekly).
        Kline Timeframes: 1-minute, 5-minute (day trading, using daily pivots).
            Common formula: Pivot = (High + Low + Close) / 3; S1/R1 = (2 * Pivot) - High/Low.
        Calculation: Recalculated daily/weekly from prior period’s data.
        WebSocket Subscriptions: kline (daily for prior H/L/C, 1m/5m for real-time trading).
    Order Book Imbalance:
        Purpose: Measures buy/sell pressure from order book depth; high imbalance signals potential reversals.
        Data Input: Order book (bid/ask volumes at top levels, e.g., 10 levels).
        Timeframes: Real-time snapshots (every 100ms or per update).
            Example: Imbalance = (Bid Volume - Ask Volume) / (Bid + Ask Volume).
        Calculation: Sum bid vs. ask volumes at specified depth; ratio indicates pressure.
        WebSocket Subscriptions:
            order_book (depth updates, e.g., 10 levels).
            Example: {"type": "subscribe", "channels": [{"name": "level2", "product_ids": ["BTC-USD-PERP"], "depth": 10}]}.

6. Other Useful Indicators

    Ichimoku Cloud:
        Purpose: Comprehensive indicator for trend, momentum, and support/resistance.
        Data Input: High, Low, Close prices.
        Kline Timeframes: 15-minute, 1-hour (day trading); 4-hour (swing trading).
            Settings: Tenkan-sen = 9, Kijun-sen = 26, Senkou Span B = 52.
        Calculation: Multiple lines (Tenkan, Kijun, Senkou A/B, Chikou); cloud signals trend strength.
        WebSocket Subscriptions: kline (15m/1h).
    Parabolic SAR:
        Purpose: Identifies trend direction and potential reversals; dots above/below price signal bearish/bullish.
        Data Input: High, Low prices.
        Kline Timeframes: 5-minute, 15-minute (day trading).
            Settings: Step = 0.02, Max Step = 0.2.
        Calculation: SAR adjusts based on price movement and acceleration factor.
        WebSocket Subscriptions: kline (5m/15m).