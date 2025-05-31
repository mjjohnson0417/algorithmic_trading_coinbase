# market_patterns.py
# Dictionaries categorizing chart patterns by market condition for trading analysis
# Each chart pattern includes nested candlestick patterns with their own confirmation indicators
# Chart patterns also have top-level indicators for market context

UPTREND_PATTERNS = {
    #buy low, sell high in this scenario
    "flag_bullish": { 
        "description": "Short-term consolidation after a sharp upward move, sloping downward",
        "implication": "Bullish continuation",
        "indicators": [
            {"name": "rsi14", "condition": "rsi14 > 50"},
            {"name": "macd_hist", "condition": "macd_hist > 0"},
            {"name": "pivot_points.r1", "condition": "current_price > pivot_points_r1"}
        ],        
        "candlestick_patterns": {
            #buy low, sell high if this candlestick and indicators are present
            "marubozu_bullish": {
                "type": "single",
                "indicators": [
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"},
                    {"name": "rsi14", "condition": "rsi14 > 50"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "hammer": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "engulfing_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "macd_hist", "condition": "macd_hist > 0"},
                    {"name": "obv", "condition": "obv > 0"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "three_white_soldiers": {
                "type": "multi",
                "indicators": [
                    {"name": "adx14", "condition": "adx14 > 25"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "rising_three_methods": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 50"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            }
        }
    },
    #buy low, sell high in this scenario
    "pennant_bullish": {
        "description": "Small symmetrical triangle after a sharp upward move",
        "implication": "Bullish continuation",
        "indicators": [
            {"name": "rsi14", "condition": "rsi14 > 50"},
            {"name": "macd_hist", "condition": "macd_hist > 0"},
            {"name": "pivot_points.r1", "condition": "current_price > pivot_points_r1"}
        ],
        "candlestick_patterns": {
            #buy low, sell high if this candlestick and indicators are present
            "marubozu_bullish": {
                "type": "single",
                "indicators": [
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"},
                    {"name": "rsi14", "condition": "rsi14 > 50"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "hammer": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "engulfing_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "macd_hist", "condition": "macd_hist > 0"},
                    {"name": "obv", "condition": "obv > 0"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "three_white_soldiers": {
                "type": "multi",
                "indicators": [
                    {"name": "adx14", "condition": "adx14 > 25"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "rising_three_methods": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 50"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            }
        }
    },
    #buy low, sell high in this scenario
    "triangle_ascending": {
        "description": "Flat resistance with higher lows, forming a triangle",
        "implication": "Bullish continuation or breakout",
        "indicators": [
            {"name": "rsi14", "condition": "rsi14 > 50"},
            {"name": "adx14", "condition": "adx14 > 25"},
            {"name": "bollinger_upper", "condition": "current_price >= 0.99 * bollinger_upper and current_price <= 1.01 * bollinger_upper"}
        ],
        "candlestick_patterns": {
            #buy low, sell high if this candlestick and indicators are present
            "marubozu_bullish": {
                "type": "single",
                "indicators": [
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"},
                    {"name": "rsi14", "condition": "rsi14 > 50"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "piercing_line": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 50"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "engulfing_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "macd_hist", "condition": "macd_hist > 0"},
                    {"name": "obv", "condition": "obv > 0"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "morning_star": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "macd_hist", "condition": "macd_hist > 0"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "inverted_hammer": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "doji_dragonfly": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "harami_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "macd_hist", "condition": "macd_hist > 0"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "tweezer_bottoms": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "stick_sandwich_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "rising_three_methods": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 50"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            }
        }
    },
    #sell tokens high, buy back low for accumulation
    "double_top": {
        "description": "Two price peaks at resistance, failing to break higher",
        "implication": "Bearish reversal",
        "indicators": [
            {"name": "rsi14", "condition": "rsi14 > 70"},
            {"name": "macd_hist", "condition": "macd_hist < 0"},
            {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
        ],
        "candlestick_patterns": {
            #sell high, buy back low if this candlestick and indicators are present
            "marubozu_bearish": {
                "type": "single",
                "indicators": [
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"},
                    {"name": "rsi14", "condition": "rsi14 > 70"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "shooting_star": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 70"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "engulfing_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "macd_hist", "condition": "macd_hist < 0"},
                    {"name": "obv", "condition": "obv < 0"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "evening_star": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 70"},
                    {"name": "macd_hist", "condition": "macd_hist < 0"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "doji_gravestone": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 70"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "harami_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 70"},
                    {"name": "macd_hist", "condition": "macd_hist < 0"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "tweezer_tops": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 70"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "stick_sandwich_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 70"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            }
        }
    },
    #sell tokens high, buy back low for accumulation
    "head_and_shoulders": {
        "description": "Peak (head) flanked by two lower peaks (shoulders)",
        "implication": "Bearish reversal",
        "candlestick_patterns": {
            #sell high, buy back low if this candlestick and indicators are present
            "marubozu_bearish": {
                "type": "single",
                "indicators": [
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"},
                    {"name": "rsi14", "condition": "rsi14 > 70"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "shooting_star": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 70"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "engulfing_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "macd_hist", "condition": "macd_hist < 0"},
                    {"name": "obv", "condition": "obv < 0"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "evening_star": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 70"},
                    {"name": "macd_hist", "condition": "macd_hist < 0"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "doji_gravestone": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 70"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "harami_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 70"},
                    {"name": "macd_hist", "condition": "macd_hist < 0"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "tweezer_tops": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 70"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "stick_sandwich_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 70"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            }
        },
        "indicators": [
            {"name": "rsi14", "condition": "rsi14 > 70"},
            {"name": "macd_hist", "condition": "macd_hist < 0"},
            {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
        ]
    },
    #sell tokens high, buy back low for accumulation
    "rising_wedge": {
        "description": "Narrowing pattern with higher highs and lows, tightening range",
        "implication": "Bearish reversal",
        "candlestick_patterns": {
            #sell high, buy back low if this candlestick and indicators are present
            "marubozu_bearish": {
                "type": "single",
                "indicators": [
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"},
                    {"name": "rsi14", "condition": "rsi14 > 70"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "shooting_star": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 70"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "engulfing_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "macd_hist", "condition": "macd_hist < 0"},
                    {"name": "obv", "condition": "obv < 0"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "evening_star": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 70"},
                    {"name": "macd_hist", "condition": "macd_hist < 0"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "doji_gravestone": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 70"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "harami_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 70"},
                    {"name": "macd_hist", "condition": "macd_hist < 0"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "tweezer_tops": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 70"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "stick_sandwich_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 70"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            }
        },        
        "indicators": [
            {"name": "rsi14", "condition": "rsi14 > 70"},
            {"name": "macd_hist", "condition": "macd_hist < 0"},
            {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
        ]
    },
    #buy low, sell high
    "rectangle_bullish": {
        "description": "Sideways movement between parallel support and resistance",
        "implication": "Neutral, potential bullish breakout",
        "candlestick_patterns": {
            #buy low, sell high if this candlestick and indicators are present
            "marubozu_bullish": {
                "type": "single",
                "indicators": [
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"},
                    {"name": "rsi14", "condition": "rsi14 >= 50 and rsi14 <= 60"}
                ]
            },
            #no action
            "doji_standard": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 >= 45 and rsi14 <= 55"},
                    {"name": "bollinger_upper", "condition": "current_price >= 0.99 * bollinger_upper and current_price <= 1.01 * bollinger_upper"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "engulfing_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "macd_hist", "condition": "macd_hist > 0"},
                    {"name": "obv", "condition": "obv > 0"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "three_inside_up": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 50"},
                    {"name": "pivot_points.r1", "condition": "current_price > pivot_points_r1"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "harami_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 >= 50 and rsi14 <= 60"},
                    {"name": "macd_hist", "condition": "macd_hist > 0"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "tweezer_bottoms": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 >= 50 and rsi14 <= 60"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "stick_sandwich_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 >= 50 and rsi14 <= 60"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            }
        },
        "indicators": [
            {"name": "rsi14", "condition": "rsi14 >= 50 and rsi14 <= 60"},
            {"name": "macd_hist", "condition": "macd_hist > 0"},
            {"name": "pivot_points.r1", "condition": "current_price > pivot_points_r1"}
        ]
    },
    #buy low, sell high or sell tokens, buy back low, depends on candlestick and indicators that hit
    "triangle_symmetrical": {
        "description": "Converging trendlines with lower highs and higher lows",
        "implication": "Neutral, awaiting breakout",
        "candlestick_patterns": {
            #buy low, sell high if this candlestick and indicators are present
            "marubozu_bullish": {
                "type": "single",
                "indicators": [
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"},
                    {"name": "rsi14", "condition": "rsi14 > 50"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "marubozu_bearish": {
                "type": "single",
                "indicators": [
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"},
                    {"name": "rsi14", "condition": "rsi14 < 50"}
                ]
            },
            #no action
            "doji_standard": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 >= 45 and rsi14 <= 55"},
                    {"name": "bollinger_upper", "condition": "current_price >= 0.99 * bollinger_upper and current_price <= 1.01 * bollinger_upper"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "engulfing_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "macd_hist", "condition": "macd_hist > 0"},
                    {"name": "obv", "condition": "obv > 0"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "engulfing_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "macd_hist", "condition": "macd_hist < 0"},
                    {"name": "obv", "condition": "obv < 0"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "harami_cross_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 50"},
                    {"name": "adx14", "condition": "adx14 < 20"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "harami_cross_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "adx14", "condition": "adx14 < 20"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "harami_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 50"},
                    {"name": "macd_hist", "condition": "macd_hist > 0"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "harami_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "macd_hist", "condition": "macd_hist < 0"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "tweezer_bottoms": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 50"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "tweezer_tops": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "stick_sandwich_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 50"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "stick_sandwich_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            }
        },
        "indicators": [
            {"name": "rsi14", "condition": "rsi14 >= 45 and rsi14 <= 55"},
            {"name": "adx14", "condition": "adx14 < 20"},
            {"name": "bollinger_upper", "condition": "current_price >= 0.99 * bollinger_upper and current_price <= 1.01 * bollinger_upper"},
            {"name": "bollinger_lower", "condition": "current_price >= 0.99 * bollinger_lower and current_price <= 1.01 * bollinger_lower"}
        ]
    }
}

DOWNTREND_PATTERNS = {
    #sell high, buy back low if this candlestick and indicators are present
    "flag_bearish": {
        "description": "Short-term consolidation after a sharp downward move, sloping upward",
        "implication": "Bearish continuation",
        "candlestick_patterns": {     
            #sell high, buy back low if this candlestick and indicators are present       
            "marubozu_bearish": {
                "type": "single",
                "indicators": [
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"},
                    {"name": "rsi14", "condition": "rsi14 < 50"}
                ]
            },
            #sell tokens high, buy back low for accumulation
            "hanging_man": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #sell tokens high, buy back low for accumulation
            "engulfing_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "macd_hist", "condition": "macd_hist < 0"},
                    {"name": "obv", "condition": "obv < 0"}
                ]
            },
            #sell tokens high, buy back low for accumulation
            "three_black_crows": {
                "type": "multi",
                "indicators": [
                    {"name": "adx14", "condition": "adx14 > 25"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "doji_gravestone": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "harami_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "macd_hist", "condition": "macd_hist < 0"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "tweezer_tops": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "on_neck": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "stick_sandwich_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "falling_three_methods": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            }
        },
        "indicators": [
            {"name": "rsi14", "condition": "rsi14 < 50"},
            {"name": "macd_hist", "condition": "macd_hist < 0"},
            {"name": "pivot_points.s1", "condition": "current_price < pivot_points_s1"}
        ]
    },
    #sell high, buy back low if this candlestick and indicators are present
    "triangle_descending": {
        "description": "Flat support with lower highs, forming a triangle",
        "implication": "Bearish continuation or breakout",
        "candlestick_patterns": {
            #sell high, buy back low if this candlestick and indicators are present
            "marubozu_bearish": {
                "type": "single",
                "indicators": [
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"},
                    {"name": "rsi14", "condition": "rsi14 < 50"}
                ]
            },
            #sell tokens high, buy back low for accumulation
            "dark_cloud_cover": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #sell tokens high, buy back low for accumulation
            "engulfing_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "macd_hist", "condition": "macd_hist < 0"},
                    {"name": "obv", "condition": "obv < 0"}
                ]
            },
            #sell tokens high, buy back low for accumulation
            "three_black_crows": {
                "type": "multi",
                "indicators": [
                    {"name": "adx14", "condition": "adx14 > 25"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "doji_gravestone": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "harami_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "macd_hist", "condition": "macd_hist < 0"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "tweezer_tops": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "on_neck": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "stick_sandwich_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "falling_three_methods": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            }
        },
        "indicators": [
            {"name": "rsi14", "condition": "rsi14 < 50"},
            {"name": "adx14", "condition": "adx14 > 25"},
            {"name": "bollinger_lower", "condition": "current_price >= 0.99 * bollinger_lower and current_price <= 1.01 * bollinger_lower"}
        ]
    },
    #sell high, buy back low if this candlestick and indicators are present
    "rectangle_bearish": {
        "description": "Sideways movement between parallel support and resistance",
        "implication": "Neutral, potential bearish continuation",
        "candlestick_patterns": {
            #sell tokens high, buy back low for accumulation
            "marubozu_bearish": {
                "type": "single",
                "indicators": [
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"},
                    {"name": "rsi14", "condition": "rsi14 < 50"}
                ]
            },
            #sell tokens high, buy back low for accumulation
            "hanging_man": {                
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #sell tokens high, buy back low for accumulation
            "engulfing_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "macd_hist", "condition": "macd_hist < 0"},
                    {"name": "obv", "condition": "obv < 0"}
                ]
            },
            #sell tokens high, buy back low for accumulation
            "three_inside_down": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "doji_gravestone": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "harami_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "macd_hist", "condition": "macd_hist < 0"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "tweezer_tops": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "on_neck": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "stick_sandwich_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            },
            #sell high, buy back low if this candlestick and indicators are present
            "falling_three_methods": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            }
        },
        "indicators": [
            {"name": "rsi14", "condition": "rsi14 < 50"},
            {"name": "macd_hist", "condition": "macd_hist < 0"},
            {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
        ]
    },
    #buy low, sell high 
    "double_bottom": {
        "description": "Two price troughs at support, failing to break below",
        "implication": "Bullish reversal",
        "candlestick_patterns": {
            #buy low, sell high if this candlestick and indicators are present
            "marubozu_bullish": {
                "type": "single",
                "indicators": [
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"},
                    {"name": "rsi14", "condition": "rsi14 < 30"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "hammer": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 30"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "engulfing_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "macd_hist", "condition": "macd_hist > 0"},
                    {"name": "obv", "condition": "obv > 0"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "morning_star": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 30"},
                    {"name": "macd_hist", "condition": "macd_hist > 0"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "inverted_hammer": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 30"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "doji_dragonfly": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 30"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "harami_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 30"},
                    {"name": "macd_hist", "condition": "macd_hist > 0"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "tweezer_bottoms": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 30"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "stick_sandwich_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 30"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            }
        },
        "indicators": [
            {"name": "rsi14", "condition": "rsi14 < 30"},
            {"name": "macd_hist", "condition": "macd_hist > 0"},
            {"name": "pivot_points.s1", "condition": "current_price > pivot_points_s1"}
        ]
    },
    #buy low, sell high 
    "inverse_head_and_shoulders": {
        "description": "Trough (head) flanked by two higher troughs (shoulders)",
        "implication": "Bullish reversal",
        "candlestick_patterns": {
            #buy low, sell high if this candlestick and indicators are present
            "marubozu_bullish": {
                "type": "single",
                "indicators": [
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"},
                    {"name": "rsi14", "condition": "rsi14 < 30"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "hammer": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 30"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "engulfing_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "macd_hist", "condition": "macd_hist > 0"},
                    {"name": "obv", "condition": "obv > 0"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "morning_star": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 30"},
                    {"name": "macd_hist", "condition": "macd_hist > 0"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "inverted_hammer": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 30"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "doji_dragonfly": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 30"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "harami_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 30"},
                    {"name": "macd_hist", "condition": "macd_hist > 0"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "tweezer_bottoms": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 30"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "stick_sandwich_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 30"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            }
        },
        "indicators": [
            {"name": "rsi14", "condition": "rsi14 < 30"},
            {"name": "macd_hist", "condition": "macd_hist > 0"},
            {"name": "pivot_points.s1", "condition": "current_price > pivot_points_s1"}
        ]
    },
    #buy low, sell high 
    "falling_wedge": {
        "description": "Narrowing pattern with lower highs and lows, tightening range",
        "implication": "Bullish reversal",
        "candlestick_patterns": {
            #buy low, sell high if this candlestick and indicators are present
            "marubozu_bullish": {
                "type": "single",
                "indicators": [
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"},
                    {"name": "rsi14", "condition": "rsi14 > 50"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "hammer": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "engulfing_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "macd_hist", "condition": "macd_hist > 0"},
                    {"name": "obv", "condition": "obv > 0"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "three_inside_up": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 50"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "inverted_hammer": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "doji_dragonfly": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "harami_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "macd_hist", "condition": "macd_hist > 0"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "tweezer_bottoms": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "stick_sandwich_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            }
        },
        "indicators": [
            {"name": "rsi14", "condition": "rsi14 > 50"},
            {"name": "macd_hist", "condition": "macd_hist > 0"},
            {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
        ]
    },
    #buy low, sell high or sell tokens, buy back low, depends on candlestick and indicator hits
    "triangle_symmetrical": {
        "description": "Converging trendlines with lower highs and higher lows",
        "implication": "Neutral, awaiting breakout",
        "candlestick_patterns": {
            #buy low, sell high if this candlestick and indicators are present
            "marubozu_bullish": {
                "type": "single",
                "indicators": [
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"},
                    {"name": "rsi14", "condition": "rsi14 > 50"}
                ]
            },
            #sell tokens high, buy back low if this candlestick and indicators are present
            "marubozu_bearish": {
                "type": "single",
                "indicators": [
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"},
                    {"name": "rsi14", "condition": "rsi14 < 50"}
                ]
            },
            #no action
            "doji_standard": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 >= 45 and rsi14 <= 55"},
                    {"name": "bollinger_upper", "condition": "current_price >= 0.99 * bollinger_upper and current_price <= 1.01 * bollinger_upper"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "engulfing_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "macd_hist", "condition": "macd_hist > 0"},
                    {"name": "obv", "condition": "obv > 0"}
                ]
            },
            #sell tokens high, buy back low if this candlestick and indicators are present
            "engulfing_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "macd_hist", "condition": "macd_hist < 0"},
                    {"name": "obv", "condition": "obv < 0"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "harami_cross_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 50"},
                    {"name": "adx14", "condition": "adx14 < 20"}
                ]
            },
            #sell tokens high, buy back low if this candlestick and indicators are present
            "harami_cross_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "adx14", "condition": "adx14 < 20"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "harami_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 50"},
                    {"name": "macd_hist", "condition": "macd_hist > 0"}
                ]
            },
            #sell tokens high, buy back low if this candlestick and indicators are present
            "harami_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "macd_hist", "condition": "macd_hist < 0"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "tweezer_bottoms": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 50"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #sell tokens high, buy back low if this candlestick and indicators are present
            "tweezer_tops": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "stick_sandwich_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 50"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            },
            #sell tokens high, buy back low if this candlestick and indicators are present
            "stick_sandwich_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            }
        },
        "indicators": [
            {"name": "rsi14", "condition": "rsi14 >= 45 and rsi14 <= 55"},
            {"name": "adx14", "condition": "adx14 < 20"},
            {"name": "bollinger_upper", "condition": "current_price >= 0.99 * bollinger_upper and current_price <= 1.01 * bollinger_upper"},
            {"name": "bollinger_lower", "condition": "current_price >= 0.99 * bollinger_lower and current_price <= 1.01 * bollinger_lower"}
        ]
    },
    #buy low, sell high 
    "rectangle_bullish": {
        "description": "Sideways movement between parallel support and resistance",
        "implication": "Neutral, potential bullish breakout",
        "candlestick_patterns": {
            #buy low, sell high if this candlestick and indicators are present
            "marubozu_bullish": {
                "type": "single",
                "indicators": [
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"},
                    {"name": "rsi14", "condition": "rsi14 >= 50 and rsi14 <= 60"}
                ]
            },
            #no action
            "doji_standard": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 >= 45 and rsi14 <= 55"},
                    {"name": "bollinger_upper", "condition": "current_price >= 0.99 * bollinger_upper and current_price <= 1.01 * bollinger_upper"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "engulfing_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "macd_hist", "condition": "macd_hist > 0"},
                    {"name": "obv", "condition": "obv > 0"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "three_inside_up": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 50"},
                    {"name": "pivot_points.r1", "condition": "current_price > pivot_points_r1"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "harami_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 >= 50 and rsi14 <= 60"},
                    {"name": "macd_hist", "condition": "macd_hist > 0"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "tweezer_bottoms": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 >= 50 and rsi14 <= 60"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #buy low, sell high if this candlestick and indicators are present
            "stick_sandwich_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 >= 50 and rsi14 <= 60"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            }
        },
        "indicators": [
            {"name": "rsi14", "condition": "rsi14 >= 50 and rsi14 <= 60"},
            {"name": "macd_hist", "condition": "macd_hist > 0"},
            {"name": "pivot_points.r1", "condition": "current_price > pivot_points_r1"}
        ]
    }
}

SIDEWAY_PATTERNS = {
    #buy low, sell high, or sell token high, buy back low, depends on candlestick and indicator
    "triangle_symmetrical": {
        "description": "Converging trendlines with lower highs and higher lows",
        "implication": "Neutral, awaiting breakout",
        "candlestick_patterns": {
            #buy low, sell high if this candlestick and indicators are present
            "marubozu_bullish": {
                "type": "single",
                "indicators": [
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"},
                    {"name": "rsi14", "condition": "rsi14 > 50"}
                ]
            },
            #sell token high, buy back low
            "marubozu_bearish": {
                "type": "single",
                "indicators": [
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"},
                    {"name": "rsi14", "condition": "rsi14 < 50"}
                ]
            },
            #no action
            "doji_standard": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 >= 45 and rsi14 <= 55"},
                    {"name": "bollinger_upper", "condition": "current_price >= 0.99 * bollinger_upper and current_price <= 1.01 * bollinger_upper"}
                ]
            },
            #buy low, sell high
            "engulfing_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "macd_hist", "condition": "macd_hist > 0"},
                    {"name": "obv", "condition": "obv > 0"}
                ]
            },
            #sell token high, buy back low
            "engulfing_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "macd_hist", "condition": "macd_hist < 0"},
                    {"name": "obv", "condition": "obv < 0"}
                ]
            },
            #buy low, sell high
            "harami_cross_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 50"},
                    {"name": "adx14", "condition": "adx14 < 20"}
                ]
            },
            #sell token high, buy back low
            "harami_cross_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "adx14", "condition": "adx14 < 20"}
                ]
            },
            #buy low, sell high
            "harami_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 50"},
                    {"name": "macd_hist", "condition": "macd_hist > 0"}
                ]
            },
            #sell token high, buy back low
            "harami_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "macd_hist", "condition": "macd_hist < 0"}
                ]
            },
            #buy low, sell high
            "tweezer_bottoms": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 50"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #sell token high, buy back low
            "tweezer_tops": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #buy low, sell high
            "stick_sandwich_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 50"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            },
            #sell token high, buy back low
            "stick_sandwich_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            }
        },
        "indicators": [
            {"name": "rsi14", "condition": "rsi14 >= 45 and rsi14 <= 55"},
            {"name": "adx14", "condition": "adx14 < 20"},
            {"name": "bollinger_upper", "condition": "current_price >= 0.99 * bollinger_upper and current_price <= 1.01 * bollinger_upper"},
            {"name": "bollinger_lower", "condition": "current_price >= 0.99 * bollinger_lower and current_price <= 1.01 * bollinger_lower"}
        ]
    },
    #buy low, sell high, or sell token high, buy back low, depends on candlestick and indicator
    "rectangle_bullish": {
        "description": "Sideways movement with potential for upside breakout",
        "implication": "Neutral, leans bullish",
        "candlestick_patterns": {
            #buy low, sell high if this candlestick and indicators are present
            "marubozu_bullish": {
                "type": "single",
                "indicators": [
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"},
                    {"name": "rsi14", "condition": "rsi14 >= 50 and rsi14 <= 60"}
                ]
            },
            #no action
            "doji_standard": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 >= 45 and rsi14 <= 55"},
                    {"name": "bollinger_upper", "condition": "current_price >= 0.99 * bollinger_upper and current_price <= 1.01 * bollinger_upper"}
                ]
            },
            #buy low, sell high
            "engulfing_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "macd_hist", "condition": "macd_hist > 0"},
                    {"name": "obv", "condition": "obv > 0"}
                ]
            },
            #buy low, sell high
            "three_inside_up": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 50"},
                    {"name": "pivot_points.r1", "condition": "current_price > pivot_points_r1"}
                ]
            },
            #buy low, sell high
            "harami_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 >= 50 and rsi14 <= 60"},
                    {"name": "macd_hist", "condition": "macd_hist > 0"}
                ]
            },
            #buy low, sell high
            "tweezer_bottoms": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 >= 50 and rsi14 <= 60"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #buy low, sell high
            "stick_sandwich_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 >= 50 and rsi14 <= 60"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            }
        },
        "indicators": [
            {"name": "rsi14", "condition": "rsi14 >= 50 and rsi14 <= 60"},
            {"name": "macd_hist", "condition": "macd_hist > 0"},
            {"name": "pivot_points.r1", "condition": "current_price > pivot_points_r1"}
        ]
    },
    #sell token high, buy back low, depends on candlestick and indicator
    "rectangle_bearish": {
        "description": "Sideways movement with potential for downside breakout",
        "implication": "Neutral, leans bearish",
        "candlestick_patterns": {
            #sell token high, buy back low
            "marubozu_bearish": {
                "type": "single",
                "indicators": [
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"},
                    {"name": "rsi14", "condition": "rsi14 < 50"}
                ]
            },
            #sell token high, buy back low
            "hanging_man": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #sell token high, buy back low
            "engulfing_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "macd_hist", "condition": "macd_hist < 0"},
                    {"name": "obv", "condition": "obv < 0"}
                ]
            },
            #sell token high, buy back low
            "three_inside_down": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #sell token high, buy back low
            "doji_gravestone": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #sell token high, buy back low
            "harami_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "macd_hist", "condition": "macd_hist < 0"}
                ]
            },
            #sell token high, buy back low
            "tweezer_tops": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #sell token high, buy back low
            "on_neck": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #sell token high, buy back low
            "stick_sandwich_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            },
            #sell token high, buy back low
            "falling_three_methods": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            }
        },
        "indicators": [
            {"name": "rsi14", "condition": "rsi14 < 50"},
            {"name": "macd_hist", "condition": "macd_hist < 0"},
            {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
        ]
    },
    #buy low, sell high
    "triangle_ascending": {
        "description": "Flat resistance with higher lows, potential bullish breakout",
        "implication": "Neutral, leans bullish",
        "candlestick_patterns": {
            #buy low, sell high if this candlestick and indicators are present
            "marubozu_bullish": {
                "type": "single",
                "indicators": [
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"},
                    {"name": "rsi14", "condition": "rsi14 > 50"}
                ]
            },
            #buy low, sell high
            "piercing_line": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 50"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #buy low, sell high
            "engulfing_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "macd_hist", "condition": "macd_hist > 0"},
                    {"name": "obv", "condition": "obv > 0"}
                ]
            },
            #buy low, sell high
            "morning_star": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "macd_hist", "condition": "macd_hist > 0"}
                ]
            },
            #buy low, sell high
            "inverted_hammer": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #buy low, sell high
            "doji_dragonfly": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #buy low, sell high
            "harami_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "macd_hist", "condition": "macd_hist > 0"}
                ]
            },
            #buy low, sell high
            "tweezer_bottoms": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #buy low, sell high
            "stick_sandwich_bullish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            },
            #buy low, sell high
            "rising_three_methods": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 > 50"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            }
        },
        "indicators": [
            {"name": "rsi14", "condition": "rsi14 > 50"},
            {"name": "adx14", "condition": "adx14 < 20"},
            {"name": "bollinger_upper", "condition": "current_price >= 0.99 * bollinger_upper and current_price <= 1.01 * bollinger_upper"}
        ]
    },
    #sell tokens high, buy back low
    "triangle_descending": {
        "description": "Flat support with lower highs, potential bearish breakout",
        "implication": "Neutral, leans bearish",
        "candlestick_patterns": {
            #sell tokens high, buy back low
            "marubozu_bearish": {
                "type": "single",
                "indicators": [
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"},
                    {"name": "rsi14", "condition": "rsi14 < 50"}
                ]
            },
            #sell tokens high, buy back low
            "dark_cloud_cover": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #sell tokens high, buy back low
            "engulfing_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "macd_hist", "condition": "macd_hist < 0"},
                    {"name": "obv", "condition": "obv < 0"}
                ]
            },
            #sell tokens high, buy back low
            "evening_star": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "macd_hist", "condition": "macd_hist < 0"}
                ]
            },
            #sell tokens high, buy back low
            "doji_gravestone": {
                "type": "single",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #sell tokens high, buy back low
            "harami_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "macd_hist", "condition": "macd_hist < 0"}
                ]
            },
            #sell tokens high, buy back low
            "tweezer_tops": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.r1", "condition": "current_price >= 0.99 * pivot_points_r1 and current_price <= 1.01 * pivot_points_r1"}
                ]
            },
            #sell tokens high, buy back low
            "on_neck": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "pivot_points.s1", "condition": "current_price >= 0.99 * pivot_points_s1 and current_price <= 1.01 * pivot_points_s1"}
                ]
            },
            #sell tokens high, buy back low
            "stick_sandwich_bearish": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            },
            #sell tokens high, buy back low
            "falling_three_methods": {
                "type": "multi",
                "indicators": [
                    {"name": "rsi14", "condition": "rsi14 < 50"},
                    {"name": "volume_surge_ratio", "condition": "volume_surge_ratio > 1.0"}
                ]
            }
        },
        "indicators": [
            {"name": "rsi14", "condition": "rsi14 < 50"},
            {"name": "adx14", "condition": "adx14 < 20"},
            {"name": "bollinger_lower", "condition": "current_price >= 0.99 * bollinger_lower and current_price <= 1.01 * bollinger_lower"}
        ]
    }
}