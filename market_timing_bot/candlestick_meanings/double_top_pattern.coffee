Double Top Pattern Explanation

    Definition: A bearish reversal pattern with two peaks (tops) at similar price levels, separated by a trough (neckline), followed by a breakout below the neckline, signaling a potential downtrend.
    Criteria:
        First Top: A local high (high within top 10% of recent highs over 15 klines).
        Trough (Neckline): A local low (low within bottom 10% of range) after the first top.
        Second Top: A second high within 3% of the first top’s price.
        Breakout: The latest kline closes below the neckline (trough’s low).
    What It Tells a Trader:
        Bearish Reversal: Indicates buyers failed to push prices higher at resistance, with sellers taking control on the breakout.
        Resistance Confirmation: The two tops confirm a strong resistance level, often at a psychological or technical barrier (e.g., pivot_points.r1).
        Context-Dependent: Most reliable after a sustained uptrend, at resistance levels (e.g., 61.8% Fibonacci, round numbers), or with high volume on breakout.
    How to Trade It:
        Entry: Short on breakout confirmation (e.g., close below neckline with a bearish candle or increased volume).
        Stop-Loss: Above the second top’s high (1-2x atr14 from indicator_calculator.py) to protect against false breakouts.
        Take-Profit: Target the pattern’s height (distance from tops to neckline) projected downward, or next support (e.g., pivot_points.s1, 38.2% Fibonacci, 2-3x risk).
        Confirmation:
            RSI: 50–70, indicating overbought conditions before reversal.
            ADX: < 25 for reversal setup, > 25 post-breakout for trend strength.
            Volume: High volume_surge_ratio (>1.5) on breakout strengthens the signal.
            Order Book: Negative order_book_imbalance (<0.5) confirms selling pressure.
            Align with higher timeframes (e.g., 1h or 1d Double Top for 5m trades).
        Futures Trading Notes:
            Use low leverage (2-5x) due to crypto volatility.
            Set stops beyond the second top to avoid stop-hunts, common in futures.
            Monitor bid_ask_spread for liquidity, avoiding wide spreads.
            Confirm with data_manager.py’s kline updates for real-time breakout detection.
    Example:
        Scenario: On a 5m chart for HBAR-USD, a Double Top forms at $0.188 (61.8% Fibonacci resistance), with a neckline at $0.186, RSI at 65, and high volume on breakout below $0.186.
        Trade:
            Enter short at $0.1858 (breakout close).
            Stop-loss at $0.1885 (above second top, ~1.5x atr14).
            Take-profit at $0.184 (neckline minus pattern height, ~2x risk).
            Confirm with order_book_imbalance < 0.5 and 1h resistance.