Bullish Pennant Pattern Explanation

    Definition: A bullish continuation pattern formed during a strong uptrend, consisting of a sharp price rise (flagpole) followed by a brief consolidation in a converging, triangular channel (pennant), and a breakout above the upper boundary of the pennant, signaling the resumption of the uptrend.
    Criteria (as implemented in the method):
        Flagpole: A price increase of at least 5% over the first 3–5 klines, indicating a strong uptrend.
        Pennant: At least two lower highs and two higher lows in the subsequent klines, forming converging trendlines (upper trendline with negative slope, lower trendline with positive slope), creating a small symmetrical triangle over 5–8 klines.
        Breakout: The latest kline closes above the upper trendline of the pennant.
    What It Tells a Trader:
        Bullish Continuation: Signals a brief pause in a strong uptrend, with buyers consolidating in a tightening range, followed by a breakout indicating continued upward momentum.
        Momentum Confirmation: The flagpole reflects strong buying pressure, and the pennant’s converging structure suggests buyers are accumulating with reduced volatility before pushing higher.
        Context-Dependent: Most reliable in a strong uptrend, often after a breakout from a previous pattern (e.g., rectangle_bullish), near support levels (e.g., pivot_points.s1, 50% Fibonacci retracement), or with high volume on breakout. Less effective in downtrends or low-momentum markets.
    How to Trade It:
        Entry: Long on breakout confirmation (e.g., close above the upper trendline with a bullish candle or increased volume).
        Stop-Loss: Below the lowest low of the pennant (1-2x atr14 from indicator_calculator.py) to protect against false breakouts.
        Take-Profit: Target the flagpole’s height (distance from the start of the flagpole to its peak) projected upward from the breakout point, or next resistance (e.g., pivot_points.r1, 61.8% Fibonacci, 2-3x risk).
        Confirmation:
            RSI: 50–70, indicating bullish momentum without overbought conditions (>80).
            ADX: > 25 during the flagpole, < 25 during consolidation, > 25 post-breakout for trend strength.
            Volume: High volume_surge_ratio (>1.5) on breakout strengthens the signal; lower volume during the pennant is typical.
            Order Book: Positive order_book_imbalance (>0.5) confirms buying pressure.
            Align with higher timeframes (e.g., 1h or 1d Bullish Pennant for 5m trades).
        Futures Trading Notes:
            Use low leverage (2-5x) due to crypto volatility.
            Set stops below the pennant’s lowest low to avoid stop-hunts, common in futures.
            Monitor bid_ask_spread for liquidity, avoiding wide spreads.
            Use data_manager.py for real-time breakout detection.
    Example:
        Scenario: On a 5m chart for HBAR-USD, a Bullish Pennant forms in an uptrend with a flagpole from $0.184 to $0.187, pennant consolidation between $0.1865 and $0.186, RSI at 65, and high volume on breakout above $0.1865.