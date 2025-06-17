# Dictionary of candlestick patterns for technical analysis trading
# Includes type, implication, description, recommended kline timeframes, and confirmation details
# Patterns are designed to be traded without requiring a larger chart pattern
# Confirmation conditions are structured for easy code evaluation

CANDLESTICK_PATTERNS = {
    "marubozu_bullish": {
        "type": "single",
        "implication": "Bullish continuation or reversal",
        "description": "Long bullish candle with little to no shadows, indicating strong buying pressure",
        "kline_timeframes": [
            "15-minute: For intraday breakouts in forex/crypto",
            "1-hour: Reliable for swing trading",
            "4-hour: Strong for short-term trends",
            "Daily: High reliability for position trading"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "higher", "reference": "close"},
            "volume": {"threshold": 1.0, "strict": True},
            "market_indicators": [
                {"rsi": [{"operator": ">", "value": 50}, {"operator": "<", "value": 30}]},
                {"pivot_points.s1": {"operator": "near", "value": 0.0025}},
                {"pivot_points.r1": {"operator": "near", "value": 0.0025}}
            ],
            "context": "Reliable in uptrends or downtrend reversals"
        }
    },
    "marubozu_bearish": {
        "type": "single",
        "implication": "Bearish continuation or reversal",
        "description": "Long bearish candle with little to no shadows, indicating strong selling pressure",
        "kline_timeframes": [
            "15-minute: For intraday shorting in volatile markets",
            "1-hour: Effective for swing trading",
            "4-hour: Strong for bearish momentum",
            "Daily: Reliable for position trading"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "lower", "reference": "close"},
            "volume": {"threshold": 1.0, "strict": True},
            "market_indicators": [
                {"rsi": [{"operator": "<", "value": 50}, {"operator": ">", "value": 70}]},
                {"pivot_points.r1": {"operator": "near", "value": 0.0025}}
            ],
            "context": "Effective in downtrends or uptrend reversals"
        }
    },
    "hammer": {
        "type": "single",
        "implication": "Bullish reversal",
        "description": "Small body, long lower shadow (2x body), little to no upper shadow, after a downtrend",
        "kline_timeframes": [
            "1-hour: Good for intraday reversals",
            "4-hour: Highly reliable for swing trading",
            "Daily: Strong for position trading",
            "Weekly: Very reliable for long-term reversals"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "higher", "reference": "high"},
            "volume": {"threshold": 1.0, "strict": False},
            "market_indicators": [
                {"rsi": [{"operator": "<", "value": 50}, {"operator": "<", "value": 30}]},
                {"pivot_points.s1": {"operator": "near", "value": 0.0025}},
                {"macd_hist": {"operator": ">", "value": 0}}
            ],
            "context": "Strong at support after a downtrend"
        }
    },
    "inverted_hammer": {
        "type": "single",
        "implication": "Bullish reversal",
        "description": "Small body, long upper shadow (2x body), little to no lower shadow, after a downtrend",
        "kline_timeframes": [
            "1-hour: For intraday reversals",
            "4-hour: Reliable for swing trading",
            "Daily: Effective for position trading",
            "Weekly: Strong for long-term setups"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "higher", "reference": "high"},
            "volume": {"threshold": 1.0, "strict": False},
            "market_indicators": [
                {"rsi": [{"operator": "<", "value": 50}, {"operator": "<", "value": 30}]},
                {"pivot_points.s1": {"operator": "near", "value": 0.0025}}
            ],
            "context": "Reliable at support in downtrends"
        }
    },
    "hanging_man": {
        "type": "single",
        "implication": "Bearish reversal",
        "description": "Small body, long lower shadow (2x body), little to no upper shadow, after an uptrend",
        "kline_timeframes": [
            "1-hour: For intraday reversals",
            "4-hour: Strong for swing trading",
            "Daily: Reliable for position trading",
            "Weekly: Significant for long-term reversals"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "lower", "reference": "low"},
            "volume": {"threshold": 1.0, "strict": False},
            "market_indicators": [
                {"rsi": {"operator": "<", "value": 50}},
                {"pivot_points.r1": {"operator": "near", "value": 0.0025}}
            ],
            "context": "Effective at resistance in uptrends"
        }
    },
    "shooting_star": {
        "type": "single",
        "implication": "Bearish reversal",
        "description": "Small body, long upper shadow (2x body), little to no lower shadow, after an uptrend",
        "kline_timeframes": [
            "1-hour: Good for intraday reversals",
            "4-hour: Highly reliable for swing trading",
            "Daily: Strong for position trading",
            "Weekly: Very reliable for long-term reversals"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "lower", "reference": "low"},
            "volume": {"threshold": 1.0, "strict": False},
            "market_indicators": [
                {"rsi": {"operator": ">", "value": 70}},
                {"pivot_points.r1": {"operator": "near", "value": 0.0025}}
            ],
            "context": "Strong at resistance after an uptrend"
        }
    },
    "doji_standard": {
        "type": "single",
        "implication": "Neutral, indecision",
        "description": "Candle with very small body where open and close are nearly equal",
        "kline_timeframes": [
            "5-minute: For scalping in high-liquidity markets",
            "15-minute: Good for intraday breakouts",
            "1-hour: Reliable for short-term indecision",
            "4-hour: Strong in sideways markets"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "any", "reference": "close"},
            "volume": {"threshold": 1.0, "strict": True},
            "market_indicators": [
                {"rsi": {"operator": "between", "value": [45, 55]}},
                {"bollinger_upper": {"operator": "near", "value": 0.0025}},
                {"bollinger_lower": {"operator": "near", "value": 0.0025}}
            ],
            "context": "Signals indecision, often precedes breakout"
        }
    },
    "doji_dragonfly": {
        "type": "single",
        "implication": "Bullish reversal",
        "description": "Doji with long lower shadow, no upper shadow, after a downtrend",
        "kline_timeframes": [
            "1-hour: For intraday reversals",
            "4-hour: Reliable for swing trading",
            "Daily: Strong for position trading",
            "Weekly: Significant for long-term reversals"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "higher", "reference": "high"},
            "volume": {"threshold": 1.0, "strict": False},
            "market_indicators": [
                {"rsi": [{"operator": "<", "value": 50}, {"operator": "<", "value": 30}]},
                {"pivot_points.s1": {"operator": "near", "value": 0.0025}}
            ],
            "context": "Strong at support in downtrends"
        }
    },
    "doji_gravestone": {
        "type": "single",
        "implication": "Bearish reversal",
        "description": "Doji with long upper shadow, no lower shadow, after an uptrend",
        "kline_timeframes": [
            "1-hour: For intraday reversals",
            "4-hour: Reliable for swing trading",
            "Daily: Strong for position trading",
            "Weekly: Significant for long-term reversals"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "lower", "reference": "low"},
            "volume": {"threshold": 1.0, "strict": False},
            "market_indicators": [
                {"rsi": [{"operator": ">", "value": 70}, {"operator": "<", "value": 50}]},
                {"pivot_points.r1": {"operator": "near", "value": 0.0025}}
            ],
            "context": "Effective at resistance in uptrends"
        }
    },
    "engulfing_bullish": {
        "type": "multi",
        "implication": "Bullish reversal",
        "description": "Small bearish candle followed by a larger bullish candle that engulfs it",
        "kline_timeframes": [
            "1-hour: For intraday reversals",
            "4-hour: Highly reliable for swing trading",
            "Daily: Very strong for position trading",
            "Weekly: Powerful for long-term reversals"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "higher", "reference": "close"},
            "volume": {"threshold": 1.0, "strict": True},
            "market_indicators": [
                {"macd_hist": {"operator": ">", "value": 0}},
                {"obv": {"operator": ">", "value": 0}},
                {"rsi": [{"operator": "<", "value": 50}, {"operator": "<", "value": 30}]},
                {"pivot_points.s1": {"operator": "near", "value": 0.0025}},
                {"pivot_points.r1": {"operator": "near", "value": 0.0025}}
            ],
            "context": "Very reliable at support after a downtrend"
        }
    },
    "engulfing_bearish": {
        "type": "multi",
        "implication": "Bearish reversal",
        "description": "Small bullish candle followed by a larger bearish candle that engulfs it",
        "kline_timeframes": [
            "1-hour: For intraday reversals",
            "4-hour: Highly reliable for swing trading",
            "Daily: Strong for position trading",
            "Weekly: Powerful for long-term reversals"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "lower", "reference": "close"},
            "volume": {"threshold": 1.0, "strict": True},
            "market_indicators": [
                {"macd_hist": {"operator": "<", "value": 0}},
                {"obv": {"operator": "<", "value": 0}},
                {"rsi": [{"operator": ">", "value": 70}, {"operator": "<", "value": 50}]},
                {"pivot_points.r1": {"operator": "near", "value": 0.0025}}
            ],
            "context": "Very reliable at resistance after an uptrend"
        }
    },
    "piercing_line": {
        "type": "multi",
        "implication": "Bullish reversal",
        "description": "Bearish candle followed by a bullish candle that opens lower and closes above the midpoint of the prior candle",
        "kline_timeframes": [
            "1-hour: For intraday reversals",
            "4-hour: Reliable for swing trading",
            "Daily: Strong for position trading",
            "Weekly: Effective for long-term setups"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "higher", "reference": "close"},
            "volume": {"threshold": 1.0, "strict": False},
            "market_indicators": [
                {"rsi": [{"operator": ">", "value": 50}, {"operator": "<", "value": 50}]},
                {"pivot_points.r1": {"operator": "near", "value": 0.0025}}
            ],
            "context": "Effective at support in uptrends or sideways markets"
        }
    },
    "dark_cloud_cover": {
        "type": "multi",
        "implication": "Bearish reversal",
        "description": "Bullish candle followed by a bearish candle that opens higher and closes below the midpoint of the prior candle",
        "kline_timeframes": [
            "1-hour: For intraday reversals",
            "4-hour: Reliable for swing trading",
            "Daily: Strong for position trading",
            "Weekly: Significant for long-term reversals"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "lower", "reference": "close"},
            "volume": {"threshold": 1.0, "strict": False},
            "market_indicators": [
                {"rsi": {"operator": "<", "value": 50}},
                {"pivot_points.s1": {"operator": "near", "value": 0.0025}}
            ],
            "context": "Strong at resistance in downtrends or sideways markets"
        }
    },
    "morning_star": {
        "type": "multi",
        "implication": "Bullish reversal",
        "description": "Bearish candle, small-bodied candle (doji/spinning top), then bullish candle closing above midpoint of first candle",
        "kline_timeframes": [
            "4-hour: Highly reliable for swing trading",
            "Daily: Very strong for position trading",
            "Weekly: Powerful for long-term reversals",
            "1-hour: Effective in liquid markets"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "higher", "reference": "close"},
            "volume": {"threshold": 1.0, "strict": True},
            "market_indicators": [
                {"rsi": [{"operator": "<", "value": 50}, {"operator": "<", "value": 30}]},
                {"macd_hist": {"operator": ">", "value": 0}}
            ],
            "context": "Reliable at support after a downtrend"
        }
    },
    "evening_star": {
        "type": "multi",
        "implication": "Bearish reversal",
        "description": "Bullish candle, small-bodied candle (doji/spinning top), then bearish candle closing below midpoint of first candle",
        "kline_timeframes": [
            "4-hour: Highly reliable for swing trading",
            "Daily: Very strong for position trading",
            "Weekly: Powerful for long-term reversals",
            "1-hour: Effective in liquid markets"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "lower", "reference": "close"},
            "volume": {"threshold": 1.0, "strict": True},
            "market_indicators": [
                {"rsi": [{"operator": ">", "value": 70}, {"operator": "<", "value": 50}]},
                {"macd_hist": {"operator": "<", "value": 0}}
            ],
            "context": "Strong at resistance after an uptrend"
        }
    },
    "three_white_soldiers": {
        "type": "multi",
        "implication": "Bullish continuation",
        "description": "Three consecutive long bullish candles with higher closes",
        "kline_timeframes": [
            "1-hour: For intraday trends",
            "4-hour: Reliable for swing trading",
            "Daily: Strong for position trading",
            "Weekly: Very reliable for long-term trends"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "higher", "reference": "close"},
            "volume": {"threshold": 1.0, "strict": True},
            "market_indicators": [
                {"adx": {"operator": ">", "value": 25}},
                {"rsi": {"operator": ">", "value": 50}}
            ],
            "context": "Very reliable in strong uptrends"
        }
    },
    "three_black_crows": {
        "type": "multi",
        "implication": "Bearish continuation",
        "description": "Three consecutive long bearish candles with lower closes",
        "kline_timeframes": [
            "1-hour: For intraday trends",
            "4-hour: Reliable for swing trading",
            "Daily: Strong for position trading",
            "Weekly: Very reliable for long-term trends"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "lower", "reference": "close"},
            "volume": {"threshold": 1.0, "strict": True},
            "market_indicators": [
                {"adx": {"operator": ">", "value": 25}},
                {"rsi": {"operator": "<", "value": 50}}
            ],
            "context": "Very reliable in strong downtrends"
        }
    },
    "rising_three_methods": {
        "type": "multi",
        "implication": "Bullish continuation",
        "description": "Long bullish candle, three small bearish candles within its range, then another long bullish candle",
        "kline_timeframes": [
            "1-hour: For intraday continuation",
            "4-hour: Highly reliable for swing trading",
            "Daily: Strong for position trading",
            "Weekly: Effective for long-term trends"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "higher", "reference": "high"},
            "volume": {"threshold": 1.0, "strict": True},
            "market_indicators": [
                {"rsi": {"operator": ">", "value": 50}},
                {"adx": {"operator": ">", "value": 25}}
            ],
            "context": "Effective in established uptrends"
        }
    },
    "falling_three_methods": {
        "type": "multi",
        "implication": "Bearish continuation",
        "description": "Long bearish candle, three small bullish candles within its range, then another long bearish candle",
        "kline_timeframes": [
            "1-hour: For intraday continuation",
            "4-hour: Highly reliable for swing trading",
            "Daily: Strong for position trading",
            "Weekly: Effective for long-term trends"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "lower", "reference": "low"},
            "volume": {"threshold": 1.0, "strict": True},
            "market_indicators": [
                {"rsi": {"operator": "<", "value": 50}},
                {"adx": {"operator": ">", "value": 25}}
            ],
            "context": "Effective in established downtrends"
        }
    },
    "harami_bullish": {
        "type": "multi",
        "implication": "Bullish reversal",
        "description": "Large bearish candle followed by a smaller bullish candle contained within its body",
        "kline_timeframes": [
            "1-hour: For intraday reversals",
            "4-hour: Reliable for swing trading",
            "Daily: Strong for position trading",
            "Weekly: Reliable for long-term setups"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "higher", "reference": "close"},
            "volume": {"threshold": 1.0, "strict": False},
            "market_indicators": [
                {"rsi": [{"operator": "<", "value": 50}, {"operator": "<", "value": 30}]},
                {"macd_hist": {"operator": ">", "value": 0}}
            ],
            "context": "Reliable at support or in consolidations"
        }
    },
    "harami_bearish": {
        "type": "multi",
        "implication": "Bearish reversal",
        "description": "Large bullish candle followed by a smaller bearish candle contained within its body",
        "kline_timeframes": [
            "1-hour: For intraday reversals",
            "4-hour: Reliable for swing trading",
            "Daily: Strong for position trading",
            "Weekly: Reliable for long-term setups"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "lower", "reference": "close"},
            "volume": {"threshold": 1.0, "strict": False},
            "market_indicators": [
                {"rsi": [{"operator": ">", "value": 70}, {"operator": "<", "value": 50}]},
                {"macd_hist": {"operator": "<", "value": 0}}
            ],
            "context": "Effective at resistance or in consolidations"
        }
    },
    "harami_cross_bullish": {
        "type": "multi",
        "implication": "Bullish reversal",
        "description": "Large bearish candle followed by a doji contained within its body",
        "kline_timeframes": [
            "1-hour: For intraday reversals",
            "4-hour: Reliable in sideways markets",
            "Daily: Strong for position trading",
            "Weekly: Effective for long-term setups"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "higher", "reference": "close"},
            "volume": {"threshold": 1.0, "strict": False},
            "market_indicators": [
                {"rsi": {"operator": ">", "value": 50}},
                {"adx": {"operator": "<", "value": 20}}
            ],
            "context": "Strong in sideways markets or at support"
        }
    },
    "harami_cross_bearish": {
        "type": "multi",
        "implication": "Bearish reversal",
        "description": "Large bullish candle followed by a doji contained within its body",
        "kline_timeframes": [
            "1-hour: For intraday reversals",
            "4-hour: Reliable in sideways markets",
            "Daily: Strong for position trading",
            "Weekly: Effective for long-term setups"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "lower", "reference": "close"},
            "volume": {"threshold": 1.0, "strict": False},
            "market_indicators": [
                {"rsi": {"operator": "<", "value": 50}},
                {"adx": {"operator": "<", "value": 20}}
            ],
            "context": "Strong in sideways markets or at resistance"
        }
    },
    "tweezer_bottoms": {
        "type": "multi",
        "implication": "Bullish reversal",
        "description": "Two candles with similar lows, one bearish and one bullish, signaling rejection of lower prices",
        "kline_timeframes": [
            "1-hour: For intraday reversals",
            "4-hour: Reliable for swing trading",
            "Daily: Strong for position trading",
            "Weekly: Reliable for long-term setups"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "higher", "reference": "close"},
            "volume": {"threshold": 1.0, "strict": False},
            "market_indicators": [
                {"rsi": [{"operator": "<", "value": 50}, {"operator": "<", "value": 30}]},
                {"pivot_points.s1": {"operator": "near", "value": 0.0025}}
            ],
            "context": "Reliable at support in any market condition"
        }
    },
    "tweezer_tops": {
        "type": "multi",
        "implication": "Bearish reversal",
        "description": "Two candles with similar highs, one bullish and one bearish, signaling rejection of higher prices",
        "kline_timeframes": [
            "1-hour: For intraday reversals",
            "4-hour: Reliable for swing trading",
            "Daily: Strong for position trading",
            "Weekly: Reliable for long-term setups"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "lower", "reference": "close"},
            "volume": {"threshold": 1.0, "strict": False},
            "market_indicators": [
                {"rsi": [{"operator": ">", "value": 70}, {"operator": "<", "value": 50}]},
                {"pivot_points.r1": {"operator": "near", "value": 0.0025}}
            ],
            "context": "Effective at resistance in any market condition"
        }
    },
    "three_inside_up": {
        "type": "multi",
        "implication": "Bullish reversal",
        "description": "Bearish candle, smaller bullish candle within its body, then bullish candle closing higher",
        "kline_timeframes": [
            "1-hour: For intraday reversals",
            "4-hour: Reliable for swing trading",
            "Daily: Strong for position trading",
            "Weekly: Effective for long-term setups"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "higher", "reference": "close"},
            "volume": {"threshold": 1.0, "strict": False},
            "market_indicators": [
                {"rsi": {"operator": ">", "value": 50}},
                {"pivot_points.r1": {"operator": ">", "value": 0}}
            ],
            "context": "Strong in sideways or downtrend markets at support"
        }
    },
    "three_inside_down": {
        "type": "multi",
        "implication": "Bearish reversal",
        "description": "Bullish candle, smaller bearish candle within its body, then bearish candle closing lower",
        "kline_timeframes": [
            "1-hour: For intraday reversals",
            "4-hour: Reliable for swing trading",
            "Daily: Strong for position trading",
            "Weekly: Effective for long-term setups"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "lower", "reference": "close"},
            "volume": {"threshold": 1.0, "strict": False},
            "market_indicators": [
                {"rsi": {"operator": "<", "value": 50}},
                {"pivot_points.s1": {"operator": "near", "value": 0.0025}}
            ],
            "context": "Strong in sideways or uptrend markets at resistance"
        }
    },
    "stick_sandwich_bullish": {
        "type": "multi",
        "implication": "Bullish reversal",
        "description": "Bearish candle, bullish candle, then bearish candle with similar close to first, signaling reversal",
        "kline_timeframes": [
            "1-hour: For intraday reversals",
            "4-hour: Reliable for swing trading",
            "Daily: Strong for position trading",
            "Weekly: Reliable for long-term setups"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "higher", "reference": "close"},
            "volume": {"threshold": 1.0, "strict": True},
            "market_indicators": [
                {"rsi": [{"operator": "<", "value": 50}, {"operator": "<", "value": 30}]},
                {"macd_hist": {"operator": ">", "value": 0}}
            ],
            "context": "Reliable at support in any market condition"
        }
    },
    "stick_sandwich_bearish": {
        "type": "multi",
        "implication": "Bearish reversal",
        "description": "Bullish candle, bearish candle, then bullish candle with similar close to first, signaling reversal",
        "kline_timeframes": [
            "1-hour: For intraday reversals",
            "4-hour: Reliable for swing trading",
            "Daily: Strong for position trading",
            "Weekly: Reliable for long-term setups"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "lower", "reference": "close"},
            "volume": {"threshold": 1.0, "strict": True},
            "market_indicators": [
                {"rsi": [{"operator": ">", "value": 70}, {"operator": "<", "value": 50}]},
                {"macd_hist": {"operator": "<", "value": 0}}
            ],
            "context": "Effective at resistance in any market condition"
        }
    },
    "on_neck": {
        "type": "multi",
        "implication": "Bearish continuation",
        "description": "Bearish candle followed by a bullish candle that closes at the prior candle's low",
        "kline_timeframes": [
            "1-hour: For intraday continuation",
            "4-hour: Reliable for swing trading",
            "Daily: Strong for position trading",
            "Weekly: Effective for long-term trends"
        ],
        "confirmation": {
            "subsequent_candlestick": {"direction": "lower", "reference": "close"},
            "volume": {"threshold": 1.0, "strict": False},
            "market_indicators": [
                {"rsi": {"operator": "<", "value": 50}},
                {"pivot_points.s1": {"operator": "near", "value": 0.0025}}
            ],
            "context": "Reliable in downtrends or sideways markets at resistance"
        }
    }
}