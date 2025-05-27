Bullish Flag Pattern Explanation

    Definition: A bullish continuation pattern formed during a strong uptrend, consisting of a sharp price rise (flagpole) followed by a brief consolidation in a downward-sloping channel (flag), and a breakout above the upper boundary of the flag, signaling the resumption of the uptrend.
    Criteria:
        Flagpole: A significant price increase (e.g., >5% gain over 3–5 klines) indicating a strong uptrend.
        Flag: At least two lower highs and two lower lows forming a parallel, downward-sloping channel over 5–10 klines, with the upper and lower trendlines having similar negative slopes.
        Breakout: The latest kline closes above the upper trendline of the flag.
    What It Tells a Trader:
        Bullish Continuation: Indicates a temporary pause in a strong uptrend as buyers consolidate, followed by renewed buying pressure on the breakout, confirming the uptrend’s continuation.
        Momentum Confirmation: The flagpole shows strong bullish momentum, and the flag’s tight consolidation suggests buyers are accumulating before pushing higher.
        Context-Dependent: Most reliable in a clear uptrend, near support levels (e.g., pivot_points.s1, 50% Fibonacci retracement), or with high volume on breakout. Less effective in downtrends or low-momentum markets.
    How to Trade It:
        Entry: Long on breakout confirmation (e.g., close above the upper trendline with a bullish candle or increased volume).
        Stop-Loss: Below the lowest low of the flag (1-2x atr14 from indicator_calculator.py) to protect against false breakouts.
        Take-Profit: Target the flagpole’s height (distance from the start of the flagpole to its peak) projected upward from the breakout point, or next resistance (e.g., pivot_points.r1, 61.8% Fibonacci, 2-3x risk).
        Confirmation:
            RSI: 50–70, indicating bullish momentum without overbought conditions (>80).
            ADX: > 25 during the flagpole, < 25 during consolidation, > 25 post-breakout for trend strength.
            Volume: High volume_surge_ratio (>1.5) on breakout strengthens the signal; lower volume during the flag consolidation is typical.
            Order Book: Positive order_book_imbalance (>0.5) confirms buying pressure.
            Align with higher timeframes (e.g., 1h or 1d Bullish Flag for 5m trades).
        Futures Trading Notes:
            Use low leverage (2-5x) due to crypto volatility.
            Set stops below the flag’s lowest low to avoid stop-hunts, common in futures.
            Monitor bid_ask_spread for liquidity, avoiding wide spreads.
            Confirm with data_manager.py’s kline updates for real-time breakout detection.
    Example:
        Scenario: On a 5m chart for HBAR-USD, a Bullish Flag forms in an uptrend with a flagpole from $0.184 to $0.187, flag consolidation between $0.1865 and $0.186, RSI at 60, and high volume on breakout above $0.1865.
        Trade:
            Enter long at $0.1867 (breakout close).
            Stop-loss at $0.1858 (below flag low, ~1.5x atr14).
            Take-profit at $0.1897 (breakout plus flagpole height, ~2x risk).
            Confirm with order_book_imbalance > 0.5 and 1h uptrend.