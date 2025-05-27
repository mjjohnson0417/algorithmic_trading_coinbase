Bearish Rectangle Pattern Explanation

    Definition: A bearish continuation pattern formed during a downtrend, where price consolidates within a horizontal channel defined by parallel support and resistance levels, followed by a breakout below the support level, signaling the resumption of the downtrend.
    Criteria:
        Support Level: At least two lows within 3% of each other, forming a horizontal support line.
        Resistance Level: At least two highs within 3% of each other, forming a horizontal resistance line.
        Channel Formation: Price oscillates between support and resistance over at least 10 klines, with at least two touches of each level.
        Breakout: The latest kline closes below the support level.
    What It Tells a Trader:
        Bearish Continuation: Indicates a pause in the downtrend as sellers and buyers reach equilibrium, followed by renewed selling pressure on the breakout, confirming the downtrend’s continuation.
        Consolidation Strength: The horizontal channel suggests distribution by sellers at resistance, preparing for the next downward move.
        Context-Dependent: Most reliable in a clear downtrend, near support/resistance levels (e.g., pivot_points.s1, 38.2% Fibonacci), or with high volume on breakout. Less effective in uptrends or low-volume markets.
    How to Trade It:
        Entry: Short on breakout confirmation (e.g., close below the support level with a bearish candle or increased volume).
        Stop-Loss: Above the resistance level of the rectangle (1-2x atr14 from indicator_calculator.py) to protect against false breakouts.
        Take-Profit: Target the pattern’s height (distance from resistance to support) projected downward from the breakout point, or next support (e.g., pivot_points.s2, 23.6% Fibonacci, 2-3x risk).
        Confirmation:
            RSI: 40–60, indicating neutral conditions during consolidation, avoiding oversold signals (<30).
            ADX: > 25 during the prior downtrend, < 25 during consolidation, > 25 post-breakout for trend strength.
            Volume: High volume_surge_ratio (>1.5) on breakout strengthens the signal.
            Order Book: Negative order_book_imbalance (<0.5) confirms selling pressure.
            Align with higher timeframes (e.g., 1h or 1d Bearish Rectangle for 5m trades).
        Futures Trading Notes:
            Use low leverage (2-5x) due to crypto volatility.
            Set stops above the resistance level to avoid stop-hunts, common in futures.
            Monitor bid_ask_spread for liquidity, avoiding wide spreads.
            Confirm with data_manager.py’s kline updates for real-time breakout detection.
    Example:
        Scenario: On a 5m chart for HBAR-USD, a Bearish Rectangle forms in a downtrend with support at $0.186, resistance at $0.187, RSI at 45, and high volume on breakout below $0.186.
        Trade:
            Enter short at $0.1858 (breakout close).
            Stop-loss at $0.1872 (above resistance, ~1.5x atr14).
            Take-profit at $0.1848 (breakout minus pattern height, ~2x risk).
            Confirm with order_book_imbalance < 0.5 and 1h downtrend.