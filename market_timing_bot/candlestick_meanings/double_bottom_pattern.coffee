Double Bottom Pattern Explanation

    Definition: A bullish reversal pattern with two troughs (bottoms) at similar price levels, separated by a peak (neckline), followed by a breakout above the neckline, signaling a potential uptrend.
    Criteria:
        First Bottom: A local low (low within bottom 10% of recent lows over 15 klines).
        Peak (Neckline): A local high (high within top 10% of range) after the first bottom.
        Second Bottom: A second low within 3% of the first bottom’s price.
        Breakout: The latest kline closes above the neckline (peak’s high).
    What It Tells a Trader:
        Bullish Reversal: Indicates sellers failed to push prices lower at support, with buyers taking control on the breakout.
        Support Confirmation: The two bottoms confirm a strong support level, often at a technical or psychological barrier (e.g., pivot_points.s1).
        Context-Dependent: Most reliable after a sustained downtrend, at support levels (e.g., 38.2% Fibonacci, round numbers), or with high volume on breakout.
    How to Trade It:
        Entry: Long on breakout confirmation (e.g., close above neckline with a bullish candle or increased volume).
        Stop-Loss: Below the second bottom’s low (1-2x atr14 from indicator_calculator.py) to protect against false breakouts.
        Take-Profit: Target the pattern’s height (distance from bottoms to neckline) projected upward, or next resistance (e.g., pivot_points.r1, 61.8% Fibonacci, 2-3x risk).
        Confirmation:
            RSI: 30–50, indicating oversold conditions before reversal.
            ADX: < 25 for reversal setup, > 25 post-breakout for trend strength.
            Volume: High volume_surge_ratio (>1.5) on breakout strengthens the signal.
            Order Book: Positive order_book_imbalance (>0.5) confirms buying pressure.
            Align with higher timeframes (e.g., 1h or 1d Double Bottom for 5m trades).
        Futures Trading Notes:
            Use low leverage (2-5x) due to crypto volatility.
            Set stops beyond the second bottom to avoid stop-hunts, common in futures.
            Monitor bid_ask_spread for liquidity, avoiding wide spreads.
            Confirm with data_manager.py’s kline updates for real-time breakout detection.
    Example:
        Scenario: On a 5m chart for HBAR-USD, a Double Bottom forms at $0.184 (38.2% Fibonacci support), with a neckline at $0.186, RSI at 35, and high volume on breakout above $0.186.
        Trade:
            Enter long at $0.1862 (breakout close).
            Stop-loss at $0.1835 (below second bottom, ~1.5x atr14).
            Take-profit at $0.188 (neckline plus pattern height, ~2x risk).
            Confirm with order_book_imbalance > 0.5 and 1h support.