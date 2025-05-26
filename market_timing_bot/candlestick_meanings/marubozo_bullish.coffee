Bullish Marubozu
What It Tells a Trader

    Definition: A Bullish Marubozu is a long bullish candle (close > open) with little to no shadows (wicks), where the open is near the low and the close is near the high. It indicates that buyers controlled the entire session, pushing prices up aggressively from start to finish.
    Market Implication:
        Strong Buying Pressure: Suggests overwhelming bullish sentiment, often at the start or continuation of an uptrend.
        Potential Trend Continuation: In an existing uptrend, it reinforces bullish momentum. In a downtrend, it may signal a reversal or exhaustion of sellers.
        Confidence: The lack of shadows shows no significant pullback, indicating buyer commitment.
    Context Matters:
        At support levels, it’s a stronger bullish signal.
        After a consolidation or pullback, it suggests a breakout or trend resumption.
        In overbought conditions (e.g., RSI > 70), it may warn of a potential exhaustion move.

How to Trade It

    Entry:
        Trend Continuation: In an uptrend, enter a long position at the close of the Marubozu or on a slight pullback to confirm support (e.g., near the Marubozu’s open or a moving average like the 20-EMA).
        Reversal: At a key support level (e.g., Fibonacci retracement or pivot point), enter a long after confirmation (e.g., a follow-up bullish candle or higher volume).
        Breakout: If the Marubozu breaks a resistance level (e.g., previous high or Bollinger Band upper), enter long on a retest of the breakout level.
    Stop-Loss:
        Place below the Marubozu’s low or a nearby support level (e.g., 1-2x ATR below the low) to protect against false breakouts or reversals.
    Take-Profit:
        Target the next resistance level (e.g., pivot point R1, Fibonacci extension, or a multiple of ATR).
        In a strong trend, trail the stop using a moving average (e.g., 20-EMA) or a fixed percentage (e.g., 2x initial risk).
    Confirmation:
        Use indicators from indicator_calculator.py:
            RSI: RSI > 50 supports bullish momentum; avoid if RSI > 70 (overbought).
            ADX: ADX > 25 confirms trend strength.
            Volume: High volume (e.g., volume_surge_ratio > 1.5) strengthens the signal.
        Check for alignment with higher timeframes (e.g., 1h or 1d Marubozu on 1m trades).
    Risk Management:
        Risk 0.5-1% of account per trade.
        Avoid trading in choppy markets (e.g., narrow Bollinger Bands or low ADX).
    Futures Trading Notes:
        Leverage increases risk/reward; use low leverage (e.g., 2-5x) for Marubozu trades to manage volatility.
        Monitor order book imbalance (order_book_imbalance > 0.5) for additional confirmation of buying pressure.
        Be cautious of stop-hunts in futures; set stops beyond key levels to avoid liquidation.

Example

    Scenario: On a 5m chart for HBAR-USD, a Bullish Marubozu forms at a 38.2% Fibonacci support, with RSI at 55, ADX at 30, and high volume.
    Trade:
        Enter long at the close ($0.185).
        Stop-loss at $0.183 (below the low, ~1 ATR).
        Take-profit at $0.189 (next resistance, ~2x risk).
        Confirm with a 1h uptrend and positive order book imbalance.

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