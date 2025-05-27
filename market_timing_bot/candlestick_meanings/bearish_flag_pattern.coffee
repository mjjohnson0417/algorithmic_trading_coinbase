Bearish Flag Pattern Explanation

    Definition: A bearish continuation pattern formed during a strong downtrend, consisting of a sharp price decline (flagpole) followed by a brief consolidation in an upward-sloping channel (flag), and a breakout below the lower boundary of the flag, signaling the resumption of the downtrend.
    Criteria (as implemented in the method):
        Flagpole: A price decrease of at least 5% over the first 3–5 klines, indicating a strong downtrend.
        Flag: At least two higher highs and two higher lows in the subsequent klines, forming a parallel, upward-sloping channel with similar positive slopes (within 10% tolerance).
        Breakout: The latest kline closes below the lower trendline of the flag.
    What It Tells a Trader:
        Bearish Continuation: Signals a temporary pause in a strong downtrend, with sellers regrouping during the flag consolidation, followed by a breakout indicating continued downward momentum.
        Momentum Confirmation: The flagpole shows strong selling pressure, and the flag’s tight consolidation suggests sellers are preparing for another push lower.
        Context-Dependent: Most reliable in a clear downtrend, often after a breakdown from a previous pattern (e.g., rectangle_bearish), near resistance levels (e.g., pivot_points.r1), or with high volume on breakout. Less effective in uptrends or low-momentum markets.
    How to Trade It:
        Entry: Short on breakout confirmation (e.g., close below the lower trendline with a bearish candle or increased volume).
        Stop-Loss: Above the highest high of the flag (1-2x atr14 from indicator_calculator.py) to protect against false breakouts.
        Take-Profit: Target the flagpole’s height (distance from the start of the flagpole to its low) projected downward from the breakout point, or next support (e.g., pivot_points.s1, 38.2% Fibonacci, 2-3x risk).
        Confirmation:
            RSI: 30–50, indicating bearish momentum without oversold conditions (<20).
            ADX: > 25 during the flagpole, < 25 during consolidation, > 25 post-breakout for trend strength.
            Volume: High volume_surge_ratio (>1.5) on breakout strengthens the signal; lower volume during the flag is typical.
            Order Book: Negative order_book_imbalance (<0.5) confirms selling pressure.
            Align with higher timeframes (e.g., 1h or 1d Bearish Flag for 5m trades).
        Futures Trading Notes:
            Use low leverage (2-5x) due to crypto volatility.
            Set stops above the flag’s high to avoid stop-hunts, common in futures.
            Monitor bid_ask_spread for liquidity, avoiding wide spreads.
            Use data_manager.py for real-time breakout detection.
    Example:
        Scenario: On a 5m chart for HBAR-USD, a Bearish Flag forms in a downtrend with a flagpole from $0.187 to $0.184, flag consolidation between $0.1845 and $0.185, RSI at 40, and high volume on breakout below $0.1845.
        Trade:
            Enter short at $0.1843 (breakout close).
            Stop-loss at $0.1852 (above flag high, ~1.5x atr14).
            Take-profit at $0.1813 (breakout minus flagpole height, ~2x risk).
            Confirm with order_book_imbalance < 0.5 and 1h downtrend.