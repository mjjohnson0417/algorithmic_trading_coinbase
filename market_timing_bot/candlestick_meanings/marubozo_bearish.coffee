Bearish Marubozu
What It Tells a Trader

    Definition: A Bearish Marubozu is a long bearish candle (close < open) with little to no shadows, where the open is near the high and the close is near the low. It shows sellers dominated the session, driving prices down consistently.
    Market Implication:
        Strong Selling Pressure: Indicates aggressive bearish sentiment, often at the start or continuation of a downtrend.
        Potential Trend Continuation: In a downtrend, it reinforces bearish momentum. In an uptrend, it may signal a reversal or buyer exhaustion.
        Conviction: Minimal shadows suggest no significant buying resistance, showing seller confidence.
    Context Matters:
        At resistance levels, it’s a stronger bearish signal.
        After a rally or consolidation, it suggests a breakdown or trend reversal.
        In oversold conditions (e.g., RSI < 30), it may indicate a potential exhaustion move.

How to Trade It

    Entry:
        Trend Continuation: In a downtrend, enter a short position at the close of the Marubozu or on a pullback to resistance (e.g., near the Marubozu’s open or a moving average).
        Reversal: At a key resistance level (e.g., Fibonacci retracement or pivot point), enter short after confirmation (e.g., a follow-up bearish candle or increased volume).
        Breakdown: If the Marubozu breaks a support level (e.g., previous low or Bollinger Band lower), enter short on a retest of the broken support.
    Stop-Loss:
        Place above the Marubozu’s high or a nearby resistance level (e.g., 1-2x ATR above the high) to protect against false breakdowns.
    Take-Profit:
        Target the next support level (e.g., pivot point S1, Fibonacci extension, or a multiple of ATR).
        In a strong downtrend, trail the stop using a moving average (e.g., 20-EMA) or a fixed percentage.
    Confirmation:
        Use indicator_calculator.py indicators:
            RSI: RSI < 50 supports bearish momentum; avoid if RSI < 30 (oversold).
            ADX: ADX > 25 confirms trend strength.
            Volume: High volume (volume_surge_ratio > 1.5) strengthens the signal.
        Align with higher timeframes (e.g., 1h or 1d Marubozu for 1m trades).
    Risk Management:
        Risk 0.5-1% of account per trade.
        Avoid trading in range-bound markets (e.g., low ADX or tight Bollinger Bands).
    Futures Trading Notes:
        Use low leverage (2-5x) to manage volatility in futures.
        Monitor order book imbalance (order_book_imbalance < 0.5) for selling pressure confirmation.
        Set stops beyond key levels to avoid stop-hunts and liquidations.

Example

    Scenario: On a 15m chart for HBAR-USD, a Bearish Marubozu forms at a 61.8% Fibonacci resistance, with RSI at 45, ADX at 28, and high volume.
    Trade:
        Enter short at the close ($0.187).
        Stop-loss at $0.189 (above the high, ~1 ATR).
        Take-profit at $0.183 (next support, ~2x risk).
        Confirm with a 1h downtrend and negative order book imbalance.

General Trading Considerations

    Context is Key: Both patterns are stronger when aligned with trend direction (e.g., Bullish Marubozu in an uptrend, Bearish Marubozu in a downtrend) and key levels (support/resistance, Fibonacci, pivots).
    Confirmation Reduces Risk: Wait for additional signals (e.g., volume spike, breakout confirmation, or multi-timeframe alignment) to avoid false signals.
    Market Conditions: Marubozu patterns are less reliable in choppy or low-liquidity markets. Use indicator_calculator.py’s bollinger_upper/bollinger_lower or atr14 to assess volatility.
    Futures-Specific Risks: In futures trading, leverage amplifies gains and losses. Use atr14 from indicator_calculator.py to set stop-losses proportional to volatility, and monitor order_book_imbalance for liquidity shifts.
    Timeframe Impact: Patterns on higher timeframes (e.g., 1h, 1d) are more significant but slower to confirm. Lower timeframes (e.g., 1m, 5m) offer faster entries but higher noise. Your CandlestickPatterns class supports all timeframes, so test patterns across 1m to 1d.