Symmetrical Triangle Pattern Explanation

    Definition: A neutral continuation pattern formed by converging trendlines with lower highs and higher lows, creating a triangular shape, followed by a breakout in the direction of the prevailing trend (bullish in uptrends, bearish in downtrends), signaling a continuation of the trend.
    Criteria (as implemented in the method):
        Converging Resistance: At least two highs, each lower than the previous, forming a downward-sloping resistance line with a negative slope.
        Converging Support: At least two lows, each higher than the previous, forming an upward-sloping support line with a positive slope.
        Triangle Formation: Price oscillates between support and resistance over at least 10 klines, with at least two touches of each level.
        Breakout: The latest kline closes above the upper trendline (bullish) or below the lower trendline (bearish). The method checks for either breakout to identify the pattern’s presence.
    What It Tells a Trader:
        Neutral Continuation: Indicates a pause in the prevailing trend (uptrend or downtrend) as buyers and sellers consolidate, with a breakout confirming the trend’s continuation.
        Trend Direction: In an uptrend, a bullish breakout (above resistance) is expected; in a downtrend, a bearish breakout (below support) is likely. The pattern itself is neutral until the breakout direction is confirmed.
        Context-Dependent: Most reliable in a clear trend (up or down), near key levels (e.g., pivot_points.r1, pivot_points.s1), or with high volume on breakout. Less effective in choppy or trendless markets.
    How to Trade It:
        Entry:
            Bullish Breakout: Long on confirmation of a close above the upper trendline with a bullish candle or increased volume.
            Bearish Breakout: Short on confirmation of a close below the lower trendline with a bearish candle or increased volume.
        Stop-Loss:
            Bullish: Below the most recent low of the triangle’s support line (1-2x atr14 from indicator_calculator.py).
            Bearish: Above the most recent high of the triangle’s resistance line (1-2x atr14).
        Take-Profit:
            Target the triangle’s height (distance from the highest high to the lowest low at the start of the triangle) projected from the breakout point in the direction of the breakout.
            Bullish: Next resistance (e.g., pivot_points.r1, 61.8% Fibonacci, 2-3x risk).
            Bearish: Next support (e.g., pivot_points.s1, 38.2% Fibonacci, 2-3x risk).
        Confirmation:
            RSI: 40–60 during consolidation, indicating neutral conditions; post-breakout, RSI > 50 for bullish, < 50 for bearish.
            ADX: > 25 in the prior trend, < 25 during consolidation, > 25 post-breakout for trend strength.
            Volume: High volume_surge_ratio (>1.5) on breakout strengthens the signal; decreasing volume during consolidation is typical.
            Order Book: Positive order_book_imbalance (>0.5) for bullish breakouts; negative (<0.5) for bearish breakouts.
            Align with higher timeframes (e.g., 1h or 1d trend direction for 5m trades).
        Futures Trading Notes:
            Use low leverage (2-5x) due to crypto volatility.
            Set stops beyond the triangle’s support (bullish) or resistance (bearish) to avoid stop-hunts.
            Monitor bid_ask_spread for liquidity, avoiding wide spreads.
            Confirm with data_manager.py’s kline updates for real-time breakout detection.
    Example:
        Bullish Scenario: On a 5m chart for HBAR-USD in an uptrend, a Symmetrical Triangle forms with resistance declining from $0.187 to $0.1865, support rising from $0.185 to $0.1855, RSI at 55, and high volume on breakout above $0.1865.
            Trade:
                Enter long at $0.1867 (breakout close).
                Stop-loss at $0.1854 (below recent support low, ~1.5x atr14).
                Take-profit at $0.1887 (breakout plus triangle height, ~2x risk).
                Confirm with order_book_imbalance > 0.5 and 1h uptrend.
        Bearish Scenario: In a downtrend, breakout below $0.1855.
            Trade:
                Enter short at $0.1853 (breakout close).
                Stop-loss at $0.1866 (above recent resistance high, ~1.5x atr14).
                Take-profit at $0.1833 (breakout minus triangle height, ~2x risk).
                Confirm with order_book_imbalance < 0.5 and 1h downtrend.