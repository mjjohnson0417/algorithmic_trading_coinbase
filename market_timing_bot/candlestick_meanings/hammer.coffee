The Hammer candlestick pattern is a single-candle bullish reversal signal that often appears at the end of a downtrend, indicating potential exhaustion of sellers and the start of buying pressure. Below, I’ll explain what the Hammer pattern tells a trader and how to trade it, formatted consistently with the Marubozu explanations provided earlier, tailored to the context of futures trading and your coinbaseMarketTimingBot.py project.
Hammer Pattern
What It Tells a Trader

    Definition: A Hammer is characterized by a small body (close near open, either bullish or bearish), a long lower shadow (at least 2x the body length), and a minimal or no upper shadow. It shows that sellers pushed prices lower during the session, but buyers strongly rejected those lows, closing near the open.
    Market Implication:
        Bullish Reversal Potential: Suggests that selling pressure is waning, and buyers are stepping in, often signaling a bottom or reversal from a downtrend to an uptrend.
        Buyer Strength: The long lower shadow indicates significant buying at lower prices, overpowering sellers by the session’s end.
        Context-Dependent: Most effective at key support levels (e.g., Fibonacci retracement, pivot points) or after a sustained decline. Less reliable in a strong uptrend or choppy market.
    Context Matters:
        At support levels (e.g., 38.2% Fibonacci or pivot S1), it’s a strong reversal signal.
        After a series of bearish candles, it suggests seller exhaustion.
        In overbought conditions (e.g., RSI > 70), it’s less reliable and may indicate a false signal.

How to Trade It

    Entry:
        Reversal: Enter a long position at the close of the Hammer or on confirmation (e.g., a bullish follow-up candle or breakout above the Hammer’s high). Ideal at support levels identified by pivot_points or fibonacci_levels from indicator_calculator.py.
        Pullback: If the Hammer forms at a support level, wait for a retest of the Hammer’s low or a nearby moving average (e.g., 20-EMA) to enter long, reducing risk.
        Breakout: If the Hammer coincides with a break above a resistance (e.g., bollinger_upper), enter long on a retest of the breakout level.
    Stop-Loss:
        Place below the Hammer’s low (e.g., 1-2x atr14 below the low) to account for volatility and avoid false breakdowns.
        For tighter stops, use a level just below a nearby support (e.g., pivot_points.s1).
    Take-Profit:
        Target the next resistance level (e.g., pivot_points.r1, 61.8% Fibonacci, or 2-3x initial risk).
        In a confirmed uptrend, trail the stop using a moving average (e.g., ema20) or a percentage of the move (e.g., 50% of gains).
    Confirmation:
        Use indicators from indicator_calculator.py:
            RSI: RSI between 30-50 supports a reversal; avoid if RSI < 20 (oversold exhaustion).
            ADX: ADX < 25 suggests a trend change; ADX > 25 after confirmation indicates a new uptrend.
            Volume: High volume_surge_ratio (>1.5) strengthens the signal, indicating buyer commitment.
            Order Book: Positive order_book_imbalance (>0.5) confirms buying pressure.
        Align with higher timeframes (e.g., 1h or 1d Hammer for 5m trades) for stronger signals.
        Check CandlestickPatterns.calculate_all_patterns for complementary patterns (e.g., marubozu_bullish after a Hammer).
    Risk Management:
        Risk 0.5-1% of account per trade to manage futures leverage risks.
        Avoid trading in low-volatility markets (e.g., narrow bollinger_upper/bollinger_lower or low atr14).
        Monitor bid_ask_spread for liquidity; avoid wide spreads in futures.
    Futures Trading Notes:
        Use low leverage (2-5x) to manage volatility, as Hammers can precede sharp reversals but also false signals.
        Set stops beyond the Hammer’s low to avoid stop-hunts, common in futures markets.
        Watch order_book_imbalance for sudden shifts, as futures are sensitive to liquidity changes.
        Confirm with data_manager.py’s kline updates to ensure the Hammer is based on fresh data, especially on lower timeframes like 1m.

Example

    Scenario: On a 15m chart for HBAR-USD, a Hammer forms at a 50% Fibonacci support ($0.185), with RSI at 35, ADX at 20, and volume_surge_ratio at 1.8. The 1h timeframe shows a downtrend.
    Trade:
        Enter long at the Hammer’s close ($0.1855) or on a bullish confirmation candle.
        Stop-loss at $0.1845 (below the Hammer’s low, ~1.5x atr14).
        Take-profit at $0.188 (next resistance, pivot_points.r1, ~3x risk).
        Confirm with order_book_imbalance > 0.5 and a 1h support level.