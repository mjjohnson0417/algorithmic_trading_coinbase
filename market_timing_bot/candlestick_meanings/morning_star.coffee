1. Morning Star

    Definition: A bullish reversal pattern with three candles: a long bearish candle, a short-bodied candle (indicating indecision), and a long bullish candle closing above the first candle’s midpoint.
    Criteria:
        First candle: Bearish (first_close < first_open).
        Second candle: Small body (abs(second_close - second_open) ≤ 30% of range), often gapping down.
        Third candle: Bullish (third_close > third_open), closing above first_midpoint = (first_open + first_close)/2.
    What It Tells a Trader:
        Bullish Reversal: Signals a shift from selling to buying pressure, often at a bottom.
        Indecision to Strength: The middle candle shows hesitation, followed by strong buying.
        Context-Dependent: Strong at support levels (e.g., fibonacci_levels, pivot_points.s1) after a downtrend.
    How to Trade It:
        Entry: Long at the third candle’s close or on confirmation (e.g., breakout above the third candle’s high).
        Stop-Loss: Below the second candle’s low (1-2x atr14).
        Take-Profit: Next resistance (pivot_points.r1, 61.8% Fibonacci, 2-3x risk).
        Confirmation: RSI 30-50, ADX < 25, high volume_surge_ratio (>1.5), order_book_imbalance > 0.5.
        Futures Notes: Use 2-5x leverage, set stops beyond the low, monitor bid_ask_spread.