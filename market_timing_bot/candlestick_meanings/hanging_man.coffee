Hanging Man Candlestick Pattern
Explanation

    Definition: The Hanging Man is a single-candle bearish reversal pattern that typically forms at the end of an uptrend. It has a small body (close near open, either bullish or bearish), a long lower shadow (at least 2x the body length), and a minimal or no upper shadow. It looks identical to a Hammer but appears in a different context (uptrend vs. downtrend), signaling potential seller strength.
    Criteria:
        Body: Small, with abs(close - open) ≤ 30% of the range (high - low).
        Lower Shadow: min(open, close) - low ≥ 2x body, indicating a significant intraday sell-off that was rejected by buyers.
        Upper Shadow: high - max(open, close) ≤ 0.5x body, showing limited upward movement.
        Context: Typically occurs after a price advance, suggesting buyers are losing control and sellers may take over.

What It Tells a Trader

    Market Implication:
        Bearish Reversal Potential: Indicates that buying pressure is weakening, and sellers are testing lower prices, often signaling a top or reversal from an uptrend to a downtrend.
        Seller Interest: The long lower shadow shows sellers pushed prices down significantly, but buyers managed to close near the open, suggesting a struggle that may favor sellers soon.
        Context-Dependent: Most effective at resistance levels (e.g., Fibonacci retracement, pivot points) or after a sustained rally. Less reliable in a strong downtrend or choppy market.
    Context Matters:
        At resistance levels (e.g., 61.8% Fibonacci or pivot_points.r1), it’s a strong bearish signal.
        After a series of bullish candles, it suggests buyer exhaustion.
        In oversold conditions (e.g., RSI < 30), it’s less reliable and may indicate a false signal.

How to Trade It

    Entry:
        Reversal: Enter a short position at the close of the Hanging Man or on confirmation (e.g., a bearish follow-up candle or breakdown below the Hanging Man’s low). Ideal at resistance levels identified by pivot_points or fibonacci_levels from indicator_calculator.py.
        Pullback: If the Hanging Man forms at a resistance, wait for a retest of the Hanging Man’s high or a nearby moving average (e.g., ema20) to enter short, reducing risk.
        Breakdown: If the Hanging Man coincides with a break below a support (e.g., bollinger_lower), enter short on a retest of the broken support.
    Stop-Loss:
        Place above the Hanging Man’s high (e.g., 1-2x atr14 above the high) to protect against false breakouts.
        For tighter stops, use a level just above a nearby resistance (e.g., pivot_points.r1).
    Take-Profit:
        Target the next support level (e.g., pivot_points.s1, 38.2% Fibonacci, or 2-3x initial risk).
        In a confirmed downtrend, trail the stop using a moving average (e.g., ema20) or a percentage of the move (e.g., 50% of gains).
    Confirmation:
        Use indicators from indicator_calculator.py:
            RSI: RSI between 50-70 supports a reversal; avoid if RSI > 80 (overbought exhaustion).
            ADX: ADX < 25 suggests a trend change; ADX > 25 after confirmation indicates a new downtrend.
            Volume: High volume_surge_ratio (>1.5) strengthens the signal, indicating seller interest.
            Order Book: Negative order_book_imbalance (<0.5) confirms selling pressure.
        Align with higher timeframes (e.g., 1h or 1d Hanging Man for 5m trades) for stronger signals.
        Check CandlestickPatterns.calculate_all_patterns for complementary patterns (e.g., marubozu_bearish after a Hanging Man).
    Risk Management:
        Risk 0.5-1% of account per trade to manage futures leverage risks.
        Avoid trading in low-volatility markets (e.g., narrow bollinger_upper/bollinger_lower or low atr14).
        Monitor bid_ask_spread for liquidity; avoid wide spreads in futures.
    Futures Trading Notes:
        Use low leverage (2-5x) to manage volatility, as Hanging Man patterns can precede sharp reversals but also false signals.
        Set stops beyond the Hanging Man’s high to avoid stop-hunts, common in futures markets.
        Watch order_book_imbalance for sudden shifts, as futures are sensitive to liquidity changes.
        Confirm with data_manager.py’s kline updates to ensure the Hanging Man is based on fresh data, especially on lower timeframes like 1m.

Example

    Scenario: On a 5m chart for HBAR-USD, a Hanging Man forms at a 61.8% Fibonacci resistance ($0.188), with RSI at 65, ADX at 22, and volume_surge_ratio at 1.7. The 1h timeframe shows an uptrend.
    Trade:
        Enter short at the Hanging Man’s close ($0.1875) or on a bearish confirmation candle.
        Stop-loss at $0.1885 (above the high, ~1.5x atr14).
        Take-profit at $0.185 (next support, pivot_points.s1, ~3x risk).
        Confirm with order_book_imbalance < 0.5 and a 1h resistance level.