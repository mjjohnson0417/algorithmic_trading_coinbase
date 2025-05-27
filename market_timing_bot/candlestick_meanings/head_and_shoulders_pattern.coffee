Head and Shoulders Pattern Explanation

    Definition: A bearish reversal pattern with three peaks: a central higher peak (head) flanked by two lower peaks (shoulders), separated by troughs forming a neckline, followed by a breakout below the neckline, signaling a potential downtrend.
    Criteria:
        Left Shoulder: A local high (high within top 10% of recent highs over 25 klines).
        First Trough: A local low after the left shoulder.
        Head: A higher peak (high exceeding the left shoulder).
        Second Trough: A local low after the head, near the first trough’s level (within 3% tolerance).
        Right Shoulder: A third peak, lower than the head but within 3% of the left shoulder’s high.
        Breakout: The latest kline closes below the neckline (average of the two troughs).
    What It Tells a Trader:
        Bearish Reversal: Indicates buyers failed to sustain higher prices, with sellers gaining control on the breakout, often marking the end of an uptrend.
        Resistance Zone: The shoulders and head confirm a resistance zone, typically at technical levels (e.g., pivot_points.r1, 61.8% Fibonacci).
        Context-Dependent: Most reliable after a sustained uptrend, at resistance levels, or with high volume on breakout. Less effective in choppy markets.
    How to Trade It:
        Entry: Short on breakout confirmation (e.g., close below neckline with a bearish candle or increased volume).
        Stop-Loss: Above the right shoulder’s high (1-2x atr14 from indicator_calculator.py) to protect against false breakouts.
        Take-Profit: Target the pattern’s height (distance from head to neckline) projected downward, or next support (e.g., pivot_points.s1, 38.2% Fibonacci, 2-3x risk).
        Confirmation:
            RSI: 50–70, indicating overbought conditions before reversal.
            ADX: < 25 for reversal setup, > 25 post-breakout for trend strength.
            Volume: High volume_surge_ratio (>1.5) on breakout strengthens the signal.
            Order Book: Negative order_book_imbalance (<0.5) confirms selling pressure.
            Align with higher timeframes (e.g., 1h or 1d Head and Shoulders for 5m trades).
        Futures Trading Notes:
            Use low leverage (2-5x) due to crypto volatility.
            Set stops beyond the right shoulder to avoid stop-hunts, common in futures.
            Monitor bid_ask_spread for liquidity, avoiding wide spreads.
            Confirm with data_manager.py’s kline updates for real-time breakout detection.
    Example:
        Scenario: On a 15m chart for HBAR-USD, a Head and Shoulders forms with the head at $0.189 (61.8% Fibonacci resistance), shoulders at $0.187, neckline at $0.185, RSI at 68, and high volume on breakout below $0.185.
        Trade:
            Enter short at $0.1848 (breakout close).
            Stop-loss at $0.1875 (above right shoulder, ~1.5x atr14).
            Take-profit at $0.182 (neckline minus pattern height, ~2x risk).
            Confirm with order_book_imbalance < 0.5 and 1h resistance.