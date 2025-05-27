Bearish Pennant Pattern Explanation

    Definition: A bearish continuation pattern formed during a strong downtrend, consisting of a sharp price decline (flagpole) followed by a brief consolidation in a converging, triangular channel (pennant), and a breakout below the lower boundary of the pennant, signaling the resumption of the downtrend.
    Criteria (as implemented in the method):
        Flagpole: A price decrease of at least 5% over the first 3–5 klines, indicating a strong downtrend.
        Pennant: At least two higher highs and two lower lows in the subsequent klines, forming converging trendlines (upper trendline with positive slope, lower trendline with negative slope), creating a small symmetrical triangle over 5–8 klines.
        Breakout: The latest kline closes below the lower trendline of the pennant.
    What It Tells a Trader:
        Bearish Continuation: Signals a brief pause in a strong downtrend, with sellers consolidating in a tightening range, followed by a breakout indicating continued downward momentum.
        Momentum Confirmation: The flagpole reflects strong selling pressure, and the pennant’s converging structure suggests sellers are accumulating with reduced volatility before pushing lower.
        Context-Dependent: Most reliable in a clear downtrend, often after a breakdown from a previous pattern (e.g., rectangle_bearish), near resistance levels (e.g., pivot_points.r1, 61.8% Fibonacci), or with high volume on breakout. Less effective in uptrends or low-momentum markets.
    How to Trade It:
        Entry: Short on breakout confirmation (e.g., close below the lower trendline with a bearish candle or increased volume).
        Stop-Loss: Above the highest high of the pennant (1-2x atr14 from indicator_calculator.py) to protect against false breakouts.
        Take-Profit: Target the flagpole’s height (distance from the start of the flagpole to its low) projected downward from the breakout point, or next support (e.g., pivot_points.s1, 38.2% Fibonacci, 2-3x risk).
        Confirmation:
            RSI: 30–50, indicating bearish momentum without oversold conditions (<20).
            ADX: > 25 during the flagpole, < 25 during consolidation, > 25 post-breakout for trend strength.
            Volume: High volume_surge_ratio (>1.5) on breakout strengthens the signal; lower volume during the pennant is typical.
            Order Book: Negative order_book_imbalance (<0.5) confirms selling pressure.
            Align with higher timeframes (e.g., 1h or 1d Bearish Pennant for 5m trades).
        Futures Trading Notes:
            Use low leverage (2-5x) due to crypto volatility.
            Set stops above the pennant’s highest high to avoid stop-hunts, common in futures.
            Monitor bid_ask_spread for liquidity, avoiding wide spreads.
            Use data_manager.py for real-time breakout detection.
    Example:
        Scenario: On a 5m chart for HBAR-USD, a Bearish Pennant forms in a downtrend with a flagpole from $0.187 to $0.184, pennant consolidation between $0.1845 and $0.185, RSI at 35, and high volume on breakout below $0.1845.