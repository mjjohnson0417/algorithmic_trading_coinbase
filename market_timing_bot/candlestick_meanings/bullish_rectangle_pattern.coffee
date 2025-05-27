Bullish Rectangle Pattern Explanation

    Definition: A bullish continuation pattern formed during an uptrend, where price consolidates within a horizontal channel defined by parallel support and resistance levels, followed by a breakout above the resistance level, signaling the resumption of the uptrend.
    Criteria:
        Support Level: At least two lows within 3% of each other, forming a horizontal support line.
        Resistance Level: At least two highs within 3% of each other, forming a horizontal resistance line.
        Channel Formation: Price oscillates between support and resistance over at least 10 klines, with at least two touches of each level.
        Breakout: The latest kline closes above the resistance level.
    What It Tells a Trader:
        Bullish Continuation: Indicates a pause in the uptrend as buyers and sellers reach equilibrium, followed by renewed buying pressure on the breakout, confirming the uptrend’s continuation.
        Consolidation Strength: The horizontal channel suggests accumulation by buyers at support, preparing for the next upward move.
        Context-Dependent: Most reliable in a clear uptrend, near support/resistance levels (e.g., pivot_points.r1, 61.8% Fibonacci), or with high volume on breakout. Less effective in downtrends or low-volume markets.
    How to Trade It:
        Entry: Long on breakout confirmation (e.g., close above the resistance level with a bullish candle or increased volume).
        Stop-Loss: Below the support level of the rectangle (1-2x atr14 from indicator_calculator.py) to protect against false breakouts.
        Take-Profit: Target the pattern’s height (distance from support to resistance) projected upward from the breakout point, or next resistance (e.g., pivot_points.r2, 78.6% Fibonacci, 2-3x risk).
        Confirmation:
            RSI: 40–60, indicating neutral conditions during consolidation, avoiding overbought signals (>70).
            ADX: > 25 during the prior uptrend, < 25 during consolidation, > 25 post-breakout for trend strength.
            Volume: High volume_surge_ratio (>1.5) on breakout strengthens the signal.
            Order Book: Positive order_book_imbalance (>0.5) confirms buying pressure.
            Align with higher timeframes (e.g., 1h or 1d Bullish Rectangle for 5m trades).
        Futures Trading Notes:
            Use low leverage (2-5x) due to crypto volatility.
            Set stops below the support level to avoid stop-hunts, common in futures.
            Monitor bid_ask_spread for liquidity, avoiding wide spreads.
            Confirm with data_manager.py’s kline updates for real-time breakout detection.