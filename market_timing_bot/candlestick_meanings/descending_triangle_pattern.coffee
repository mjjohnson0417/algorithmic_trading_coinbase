Descending Triangle Pattern Explanation

    Definition: A bearish continuation pattern (or reversal in uptrends) formed by a flat support level and a declining resistance level, creating a triangular shape, followed by a breakout below the support level, signaling a potential downtrend.
    Criteria (as implemented in the method):
        Flat Support: At least two lows within 3% of each other, forming a horizontal support line (mean of lows).
        Declining Resistance: At least two highs, each lower than the previous, forming a downward-sloping resistance line with a negative slope.
        Triangle Formation: Price oscillates between support and resistance over at least 10 klines, with at least two touches of each level.
        Breakout: The latest kline closes below the support level.
    What It Tells a Trader:
        Bearish Continuation: Indicates a pause in a downtrend as sellers test a support level, with declining resistance showing weakening buying pressure, and a breakout confirming the downtrend’s continuation.
        Reversal Potential: In an uptrend, it can signal a reversal if formed at a key resistance level (e.g., pivot_points.r1).
        Context-Dependent: Most reliable in a downtrend, near support levels (e.g., pivot_points.s1, 38.2% Fibonacci), or with high volume on breakout. Less effective in choppy or low-volume markets.
    How to Trade It:
        Entry: Short on breakout confirmation (e.g., close below the support level with a bearish candle or increased volume).
        Stop-Loss: Above the most recent high of the triangle’s resistance line (1-2x atr14 from indicator_calculator.py) to protect against false breakouts.
        Take-Profit: Target the triangle’s height (distance from the highest high to the lowest low at the start of the triangle) projected downward from the breakout point, or next support (e.g., pivot_points.s2, 23.6% Fibonacci, 2-3x risk).
        Confirmation:
            RSI: 30–50, indicating bearish momentum without oversold conditions (<20).
            ADX: > 25 during the prior downtrend, < 25 during consolidation, > 25 post-breakout for trend strength.
            Volume: High volume_surge_ratio (>1.5) on breakout strengthens the signal; increasing volume toward the breakout is ideal.
            Order Book: Negative order_book_imbalance (<0.5) confirms selling pressure.
            Align with higher timeframes (e.g., 1h or 1d Descending Triangle for 5m trades).
        Futures Trading Notes:
            Use low leverage (2-5x) due to crypto volatility.
            Set stops above the resistance line to avoid stop-hunts, common in futures.
            Monitor bid_ask_spread for liquidity, avoiding wide spreads.
            Confirm with data_manager.py’s kline updates for real-time breakout detection.
    Example:
        Scenario: On a 5m chart for HBAR-USD, a Descending Triangle forms in a downtrend with support at $0.186, resistance declining from $0.187 to $0.1865, RSI at 40, and high volume on breakout below $0.186.
        Trade:
            Enter short at $0.1858 (breakout close).
            Stop-loss at $0.1867 (above recent resistance high, ~1.5x atr14).
            Take-profit at $0.1843 (breakout minus triangle height, ~2x risk).
            Confirm with order_book_imbalance < 0.5 and 1h downtrend.