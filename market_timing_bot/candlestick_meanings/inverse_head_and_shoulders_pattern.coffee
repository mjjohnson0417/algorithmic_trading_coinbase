Inverse Head and Shoulders Pattern Explanation

    Definition: A bullish reversal pattern with three troughs: a central lower trough (head) flanked by two higher troughs (shoulders), separated by peaks forming a neckline, followed by a breakout above the neckline, signaling a potential uptrend.
    Criteria:
        Left Shoulder: A local low (low within bottom 10% of recent lows over 25 klines).
        First Peak: A local high after the left shoulder.
        Head: A lower trough (low below the left shoulder).
        Second Peak: A local high after the head, near the first peak’s level (within 3% tolerance).
        Right Shoulder: A third trough, higher than the head but within 3% of the left shoulder’s low.
        Breakout: The latest kline closes above the neckline (average of the two peaks).
    What It Tells a Trader:
        Bullish Reversal: Indicates sellers failed to sustain lower prices, with buyers gaining control on the breakout, often marking the end of a downtrend.
        Support Zone: The shoulders and head confirm a support zone, typically at technical levels (e.g., pivot_points.s1, 38.2% Fibonacci).
        Context-Dependent: Most reliable after a sustained downtrend, at support levels, or with high volume on breakout. Less effective in choppy markets.
    How to Trade It:
        Entry: Long on breakout confirmation (e.g., close above neckline with a bullish candle or increased volume).
        Stop-Loss: Below the right shoulder’s low (1-2x atr14 from indicator_calculator.py) to protect against false breakouts.
        Take-Profit: Target the pattern’s height (distance from head to neckline) projected upward, or next resistance (e.g., pivot_points.r1, 61.8% Fibonacci, 2-3x risk).
        Confirmation:
            RSI: 30–50, indicating oversold conditions before reversal.
            ADX: < 25 for reversal setup, > 25 post-breakout for trend strength.
            Volume: High volume_surge_ratio (>1.5) on breakout strengthens the signal.
            Order Book: Positive order_book_imbalance (>0.5) confirms buying pressure.
            Align with higher timeframes (e.g., 1h or 1d Inverse Head and Shoulders for 5m trades).
        Futures Trading Notes:
            Use low leverage (2-5x) due to crypto volatility.
            Set stops beyond the right shoulder to avoid stop-hunts, common in futures.
            Monitor bid_ask_spread for liquidity, avoiding wide spreads.
            Confirm with data_manager.py’s kline updates for real-time breakout detection.
    Example:
        Scenario: On a 15m chart for HBAR-USD, an Inverse Head and Shoulders forms with the head at $0.183 (38.2% Fibonacci support), shoulders at $0.185, neckline at $0.187, RSI at 32, and high volume on breakout above $0.187.
        Trade:
            Enter long at $0.1872 (breakout close).
            Stop-loss at $0.1845 (below right shoulder, ~1.5x atr14).
            Take-profit at $0.189 (neckline plus pattern height, ~2x risk).
            Confirm with order_book_imbalance > 0.5 and 1h support.