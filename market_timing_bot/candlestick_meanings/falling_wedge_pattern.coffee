Falling Wedge Pattern Explanation

    Definition: A bullish reversal pattern (or continuation in uptrends) with converging trendlines sloping downward, formed by lower highs and lower lows, followed by a breakout above the upper trendline, signaling a potential uptrend.
    Criteria:
        Lower Highs: At least two highs, each lower than the previous, within a 20-kline window.
        Lower Lows: At least two lows, each lower than the previous.
        Converging Trendlines: The upper trendline (resistance, connecting highs) has a steeper negative slope than the lower trendline (support, connecting lows), with a convergence angle (e.g., slopes differ by at least 10%).
        Breakout: The latest kline closes above the upper trendline (extrapolated to the current kline).
    What It Tells a Trader:
        Bullish Reversal: Indicates weakening selling momentum as prices make lower lows with less conviction, with buyers taking control on the breakout, often after a downtrend.
        Continuation in Uptrends: In an uptrend, it signals continued buying pressure.
        Context-Dependent: Most reliable after a downtrend, at support levels (e.g., pivot_points.s1, 38.2% Fibonacci), or with high volume on breakout. Less effective in choppy or low-volume markets.
    How to Trade It:
        Entry: Long on breakout confirmation (e.g., close above the upper trendline with a bullish candle or increased volume).
        Stop-Loss: Below the most recent low within the wedge (1-2x atr14 from indicator_calculator.py) to protect against false breakouts.
        Take-Profit: Target the pattern’s height (distance from the highest high to the lowest low at the start of the wedge) projected upward from the breakout point, or next resistance (e.g., pivot_points.r1, 61.8% Fibonacci, 2-3x risk).
        Confirmation:
            RSI: 30–50, indicating oversold conditions before reversal.
            ADX: < 25 for reversal setup, > 25 post-breakout for trend strength.
            Volume: High volume_surge_ratio (>1.5) on breakout strengthens the signal.
            Order Book: Positive order_book_imbalance (>0.5) confirms buying pressure.
            Align with higher timeframes (e.g., 1h or 1d Falling Wedge for 5m trades).
        Futures Trading Notes:
            Use low leverage (2-5x) due to crypto volatility.
            Set stops beyond the recent low to avoid stop-hunts, common in futures.
            Monitor bid_ask_spread for liquidity, avoiding wide spreads.
            Confirm with data_manager.py’s kline updates for real-time breakout detection.
    Example:
        Scenario: On a 5m chart for HBAR-USD, a Falling Wedge forms with highs at $0.186 and $0.185, lows at $0.184 and $0.1835, upper trendline at $0.1848, RSI at 35, and high volume on breakout above $0.1848.
        Trade:
            Enter long at $0.1850 (breakout close).
            Stop-loss at $0.1833 (below recent low, ~1.5x atr14).
            Take-profit at $0.1867 (breakout plus pattern height, ~2x risk).
            Confirm with order_book_imbalance > 0.5 and 1h support.