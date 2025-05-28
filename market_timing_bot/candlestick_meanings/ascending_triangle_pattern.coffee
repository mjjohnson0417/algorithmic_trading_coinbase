Ascending Triangle Pattern Explanation

    Definition: A bullish continuation pattern (or reversal in downtrends) formed by a flat resistance level and a rising support level, creating a triangular shape, followed by a breakout above the resistance level, signaling a potential uptrend.
    Criteria (as implemented in the method):
        Flat Resistance: At least two highs within 3% of each other, forming a horizontal resistance line (mean of highs).
        Rising Support: At least two lows, each higher than the previous, forming an upward-sloping support line with a positive slope.
        Triangle Formation: Price oscillates between resistance and support over at least 10 klines, with at least two touches of each level.
        Breakout: The latest kline closes above the resistance level.
    What It Tells a Trader:
        Bullish Continuation: Indicates a pause in an uptrend as buyers test a resistance level, with rising support showing increasing buying pressure, and a breakout confirming the uptrend’s continuation.
        Reversal Potential: In a downtrend, it can signal a reversal if formed at a key support level (e.g., pivot_points.s1).
        Context-Dependent: Most reliable in an uptrend, near resistance levels (e.g., pivot_points.r1, 61.8% Fibonacci), or with high volume on breakout. Less effective in choppy or low-volume markets.
    How to Trade It:
        Entry: Long on breakout confirmation (e.g., close above the resistance level with a bullish candle or increased volume).
        Stop-Loss: Below the most recent low of the triangle’s support line (1-2x atr14 from indicator_calculator.py) to protect against false breakouts.
        Take-Profit: Target the triangle’s height (distance from the highest high to the lowest low at the start of the triangle) projected upward from the breakout point, or next resistance (e.g., pivot_points.r2, 78.6% Fibonacci, 2-3x risk).
        Confirmation:
            RSI: 50–70, indicating bullish momentum without overbought conditions (>80).
            ADX: > 25 during the prior uptrend, < 25 during consolidation, > 25 post-breakout for trend strength.
            Volume: High volume_surge_ratio (>1.5) on breakout strengthens the signal; increasing volume toward the breakout is ideal.
            Order Book: Positive order_book_imbalance (>0.5) confirms buying pressure.
            Align with higher timeframes (e.g., 1h or 1d Ascending Triangle for 5m trades).
        Futures Trading Notes:
            Use low leverage (2-5x) due to crypto volatility.
            Set stops below the support line to avoid stop-hunts, common in futures.
            Monitor bid_ask_spread for liquidity, avoiding wide spreads.
            Confirm with data_manager.py’s kline updates for real-time breakout detection.
    Example:
        Scenario: On a 5m chart for HBAR-USD, an Ascending Triangle forms in an uptrend with resistance at $0.187, support rising from $0.185 to $0.186, RSI at 60, and high volume on breakout above $0.187.
        Trade:
            Enter long at $0.1872 (breakout close).
            Stop-loss at $0.1858 (below recent support low, ~1.5x atr14).
            Take-profit at $0.1892 (breakout plus triangle height, ~2x risk).
            Confirm with order_book_imbalance > 0.5 and 1h uptrend.