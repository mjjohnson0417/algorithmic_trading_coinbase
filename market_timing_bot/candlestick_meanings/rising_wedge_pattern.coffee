Rising Wedge Pattern Explanation

    Definition: A bearish reversal pattern (or continuation in downtrends) with converging trendlines sloping upward, formed by higher highs and higher lows, followed by a breakout below the lower trendline, signaling a potential downtrend.
    Criteria:
        Higher Highs: At least two highs, each higher than the previous, within a 20-kline window.
        Higher Lows: At least two lows, each higher than the previous.
        Converging Trendlines: The upper trendline (resistance, connecting highs) has a shallower slope than the lower trendline (support, connecting lows), with a convergence angle (e.g., slopes differ by at least 10%).
        Breakout: The latest kline closes below the lower trendline (extrapolated to the current kline).
    What It Tells a Trader:
        Bearish Reversal: Indicates weakening buying momentum as prices make higher highs with less conviction, with sellers taking control on the breakout, often after an uptrend.
        Continuation in Downtrends: In a downtrend, it signals continued selling pressure.
        Context-Dependent: Most reliable after an uptrend, at resistance levels (e.g., pivot_points.r1, 61.8% Fibonacci), or with high volume on breakout. Less effective in choppy or low-volume markets.
    How to Trade It:
        Entry: Short on breakout confirmation (e.g., close below the lower trendline with a bearish candle or increased volume).
        Stop-Loss: Above the most recent high within the wedge (1-2x atr14 from indicator_calculator.py) to protect against false breakouts.
        Take-Profit: Target the pattern’s height (distance from the highest high to the lowest low at the start of the wedge) projected downward from the breakout point, or next support (e.g., pivot_points.s1, 38.2% Fibonacci, 2-3x risk).
        Confirmation:
            RSI: 50–70, indicating overbought conditions before reversal.
            ADX: < 25 for reversal setup, > 25 post-breakout for trend strength.
            Volume: High volume_surge_ratio (>1.5) on breakout strengthens the signal.
            Order Book: Negative order_book_imbalance (<0.5) confirms selling pressure.
            Align with higher timeframes (e.g., 1h or 1d Rising Wedge for 5m trades).
        Futures Trading Notes:
            Use low leverage (2-5x) due to crypto volatility.
            Set stops beyond the recent high to avoid stop-hunts, common in futures.
            Monitor bid_ask_spread for liquidity, avoiding wide spreads.
            Confirm with data_manager.py’s kline updates for real-time breakout detection.
    Example:
        Scenario: On a 5m chart for HBAR-USD, a Rising Wedge forms with highs at $0.188 and $0.189, lows at $0.186 and $0.187, neckline at $0.1865, RSI at 65, and high volume on breakout below $0.1865.
        Trade:
            Enter short at $0.1863 (breakout close).
            Stop-loss at $0.1892 (above recent high, ~1.5x atr14).
            Take-profit at $0.1845 (breakout minus pattern height, ~2x risk).
            Confirm with order_book_imbalance < 0.5 and 1h resistance.