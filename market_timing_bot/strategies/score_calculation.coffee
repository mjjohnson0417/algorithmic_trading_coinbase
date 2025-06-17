The methods that calculate scores are:

assess_market_context: Computes a trend alignment score.
identify_key_levels: Computes a proximity score for support/resistance (S/R) levels.
identify_candlestick_patterns: Computes a candlestick pattern score.
identify_chart_patterns: Computes a chart pattern score.
calculate_risk_reward_score: Computes a risk-reward (R:R) score.
calculate_confluence_score: Computes an overall confluence score combining the above.
For each method, I’ll explain:

How the score is calculated: Step-by-step process and code logic.
What the score represents: The metric’s meaning and role in trading decisions.
Good vs. bad score: Thresholds or ranges indicating strong or weak setups.
Bullish vs. bearish: How the score or associated data indicates market direction.
1. assess_market_context
Purpose: Computes a trend alignment score (TrendAlignmentScore) based on market state alignment across timeframes (15m, 1h, 6h, 1d).

Code:

python

Collapse

Wrap

Run

Copy
def assess_market_context(self, symbol: str) -> Dict[str, Any]:
    market_states = self.get_market_state(symbol)
    states = [market_states.get(tf, 'unknown') for tf in ['1d', '6h', '1h', '15m']]
    if all(state == 'unknown' for state in states):
        self.logger.debug(f"No valid market states for {symbol}, skipping")
        return {}
    valid_states = [s for s in states if s != 'unknown']
    if not valid_states:
        return {}
    primary_state = market_states.get('1h', valid_states[0])
    if primary_state == 'unknown':
        state_counts = Counter(valid_states)
        primary_state = max(state_counts, key=state_counts.get, default=valid_states[0])
    alignment = sum(1 for state in states if state == primary_state)
    score = 5 if alignment >= 4 else 3 if alignment == 3 else 1 if alignment == 2 else 0
    self.logger.info(f"Market context for {symbol}: States={market_states}, TrendAlignmentScore={score}")
    return {'trend_score': score}
How the Score is Calculated:

Retrieve Market States: Calls get_market_state(symbol) to get states (uptrend, downtrend, sideways, unknown) for 15m, 1h, 6h, 1d. States are based on indicators (EMA10, EMA20, ADX14, MACD histogram) from get_market_state.
Check Validity: If all states are unknown, returns an empty dict (score effectively 0).
Select Primary State: Prioritizes 1h state, or uses the most common valid state if 1h is unknown.
Count Alignment: Counts how many timeframes match the primary state.
Assign Score:
4/4 alignment: score = 5
3/4 alignment: score = 3
2/4 alignment: score = 1
<2 alignment: score = 0
Example (SUI-USD at 09:01:59, assuming similar at 09:16:20):

Log: States={'15m': 'sideways', '1h': 'downtrend', '6h': 'sideways', '1d': 'downtrend'}, TrendAlignmentScore=1
States: ['downtrend', 'sideways', 'downtrend', 'sideways']
Primary state (1h): downtrend
Alignment: 2 (1h, 1d = downtrend)
Score: 1 (2/4 alignment)
What the Score Represents:

Measures trend consistency across timeframes. A higher score indicates a stronger, more reliable trend, increasing confidence in trading decisions aligned with the primary trend (e.g., buy in uptrend, sell in downtrend).
Used in calculate_confluence_score to contribute to the overall setup viability.
Good vs. Bad Score:

Good: 5 (4/4 alignment) or 3 (3/4 alignment) – strong trend, high confidence.
Bad: 1 (2/4 alignment) or 0 (<2 alignment) – weak or conflicting trend, low confidence.
Example: Score of 1 for SUI-USD suggests a weak trend, reducing setup reliability.
Bullish vs. Bearish:

Determined by the primary state:
uptrend: Bullish (price likely to rise).
downtrend: Bearish (price likely to fall).
sideways: Neutral (no clear direction).
For SUI-USD, primary state downtrend is bearish, suggesting potential sell setups.
Contribution to Confluence: Converts to 0.5 points (score=1) in calculate_confluence_score.

2. identify_key_levels
Purpose: Computes a proximity score for S/R levels based on the current price’s closeness to primary, secondary, and tertiary levels.

Code (abridged for clarity):

python

Collapse

Wrap

Run

Copy
def identify_key_levels(self, symbol: str) -> Dict[str, Any]:
    # Get current price
    ticker = self.get_ticker_buffer(symbol)
    if ticker.empty or 'last_price' not in ticker.columns:
        return {}
    current_price = float(ticker['last_price'].iloc[-1])
    # Collect indicator data
    market_data = self.collect_market_data(symbol)
    indicators = market_data.get('indicators', {})
    # Gather levels (primary, secondary, tertiary)
    levels = []
    # Primary (3 points): pivot S1/R1, Fib 50%, VWAP, horizontal S/R
    if '1d' in indicators:
        pivot_points = indicators['1d'].get('pivot_points', {})
        for name in ['s1', 'r1']:
            if name in pivot_points and pivot_points[name] > 0:
                is_support = name == 's1'
                levels.append((float(pivot_points[name]), f'pivot_{name}_1d', is_support))
        fib_levels = indicators['1d'].get('fibonacci_levels', {})
        if '50%' in fib_levels and fib_levels['50%'] > 0:
            levels.append((float(fib_levels['50%']), 'fib_50%_1d', None))
        vwap = indicators['1d'].get('vwap', 0.0)
        if vwap > 0:
            levels.append((float(vwap), 'vwap_1d', None))
    if '1h' in indicators:
        horizontal_sr = indicators['1h'].get('horizontal_sr', [])
        for sr in horizontal_sr:
            level = sr.get('level', 0.0)
            sr_type = sr.get('type', '')
            if level > 0:
                is_support = sr_type == 'support'
                levels.append((float(level), f'horizontal_{sr_type}', is_support))
    # Secondary (2 points): Fib 38.2%/61.8%, EMA20, Volume HVN, weekly proxy
    for tf in ['1h', '6h', '1d']:
        if tf in indicators:
            fib_levels = indicators[tf].get('fibonacci_levels', {})
            for fib in ['38.2%', '61.8%']:
                if fib in fib_levels and fib_levels[fib] > 0:
                    levels.append((float(fib_levels[fib]), f'fib_{fib}_{tf}', None))
            ema20 = indicators[tf].get('ema20', 0.0)
            if ema20 > 0:
                levels.append((float(ema20), f'ema20_{tf}', None))
            volume_profile = indicators[tf].get('volume_profile', {}).get('hvn_levels', [])
            for price, _ in volume_profile:
                if price > 0:
                    levels.append((float(price), f'volume_hvn_{tf}', None))
    # Tertiary (1 point): EMA10, SMA20, Pivot S2/R2, trendlines
    for tf in ['1h', '6h', '1d']:
        if tf in indicators:
            ema10 = indicators[tf].get('ema10', 0.0)
            if ema10 > 0:
                levels.append((float(ema10), f'ema10_{tf}', None))
            sma20 = indicators[tf].get('sma20', 0.0)
            if sma20 > 0:
                levels.append((float(sma20), f'sma20_{tf}', None))
            pivot_points = indicators[tf].get('pivot_points', {})
            for name in ['s2', 'r2']:
                if name in pivot_points and pivot_points[name] > 0:
                    is_support = name == 's2'
                    levels.append((float(pivot_points[name]), f'pivot_{name}_{tf}', is_support))
            trendlines = indicators[tf].get('trendlines', {})
            for tl in ['support', 'resistance']:
                if tl in trendlines and trendlines[tl] > 0:
                    is_support = tl == 'support'
                    levels.append((float(trendlines[tl]), f'trendline_{tl}_{tf}', is_support))
    # Proximity check and scoring
    nearby_levels = []
    proximity_score = 0.0
    min_threshold = 0.001  # 0.1%
    max_threshold = 0.005  # 0.5%
    point_map = {
        'pivot_s1_1d': 3, 'pivot_r1_1d': 3, 'fib_50%_1d': 3, 'vwap_1d': 3, 'horizontal': 3,
        'fib_38.2%': 2, 'fib_61.8%': 2, 'ema20': 2, 'volume_hvn': 2, 'weekly_proxy': 2,
        'ema10': 1, 'sma20': 1, 'pivot_s2': 1, 'pivot_r2': 1, 'trendline': 1
    }
    for level, name, is_support in levels:
        distance_pct = abs(current_price - level) / current_price
        if min_threshold <= distance_pct <= max_threshold:
            base_points = next((points for key, points in point_map.items() if key in name), 1)
            multiplier = 1 - (distance_pct - min_threshold) / (max_threshold - min_threshold) * 0.8
            score = base_points * multiplier
            nearby_level = {
                'name': name,
                'level': level,
                'points': round(score, 2),
                'distance_pct': round(distance_pct, 4),
                'is_support': is_support
            }
            nearby_levels.append(nearby_level)
            proximity_score += score
    # Clustering bonus
    if len(nearby_levels) > 1:
        clustering_bonus = (len(nearby_levels) - 1) * 1.0
        proximity_score += clustering_bonus
    result = {
        'nearby_levels': sorted(nearby_levels, key=lambda x: x['distance_pct']),
        'proximity_score': round(proximity_score, 2)
    }
    return result
How the Score is Calculated:

Get Current Price: Retrieves last_price from get_ticker_buffer. If empty, returns {} (score 0).
Collect Levels:
Primary (3 points): Daily pivot S1/R1, Fib 50%, VWAP (1d), horizontal S/R (1h).
Secondary (2 points): Fib 38.2%/61.8%, EMA20, Volume Profile HVN, weekly proxy S1/R1.
Tertiary (1 point): EMA10, SMA20, Pivot S2/R2, trendlines.
Proximity Check: For each level, if distance to current price is 0.1%–0.5%:
Base points: 3 (primary), 2 (secondary), 1 (tertiary).
Multiplier: 1 - 0.8 * (distance_pct - 0.001) / (0.005 - 0.001), scaling score by closeness.
Score: base_points * multiplier.
Clustering Bonus: Adds 1.0 * (len(nearby_levels) - 1) if multiple levels are nearby.
Proximity Score: Sum of individual level scores plus clustering bonus.
Example (SUI-USD at 09:16:20):

Log: hammer near support at 3.202974, hanging_man near resistance at 3.205129.
Assume current_price ≈ 3.204 (midpoint).
From market_timing_bot.log (1h):
Horizontal S/R: Support at 3.20335375, resistance at 3.20541625.
Pivot points (1d): s1=3.1733, r1=3.3144.
Fib 50% (1d): 3.5376.
Levels within 0.1%–0.5%:
Support 3.20335375: distance_pct = |3.204 - 3.20335375| / 3.204 ≈ 0.0002 (0.02%, <0.1%, excluded).
Resistance 3.20541625: distance_pct ≈ 0.00047 (0.047%, <0.1%, excluded).
No levels qualify (all <0.1%), so nearby_levels = [].
Clustering bonus: 0 (no levels).
proximity_score = 0.
What the Score Represents:

Indicates price significance near S/R levels. A higher score suggests the current price is at a key level (support for buys, resistance for sells), increasing setup reliability.
Used in calculate_confluence_score and pattern confirmation (e.g., hammer near support).
Good vs. Bad Score:

Good: >3 (multiple primary levels or clustering), strong S/R confluence.
Bad: 0–1 (no or weak levels), low confidence.
Example: Score of 0 for SUI-USD suggests no significant S/R, reducing setup strength.
Bullish vs. Bearish:

Bullish: High score with is_support=True levels (price near support, e.g., hammer at 3.202974).
Bearish: High score with is_support=False levels (price near resistance, e.g., hanging_man at 3.205129).
For SUI-USD, no score, but log suggests both bullish (hammer near support) and bearish (hanging_man near resistance) signals, mixed direction.
Contribution to Confluence: 0 points in this case (used directly in calculate_confluence_score).

3. identify_candlestick_patterns
Purpose: Computes a candlestick pattern score based on detected patterns in 1h and 15m timeframes.

Code:

python

Collapse

Wrap

Run

Copy
def identify_candlestick_patterns(self, symbol: str) -> dict:
    result = {'detected_patterns': [], 'pattern_score': 0}
    ticker = self.get_ticker_buffer(symbol)
    current_price = None
    if not ticker.empty and 'last_price' in ticker.columns:
        current_price = float(ticker['last_price'].iloc[-1])
    else:
        klines_1m = self.data_manager.get_buffer(symbol, 'klines_1m')
        if not klines_1m.empty:
            current_price = float(klines_1m['close'].iloc[-1])
    market_data = self.collect_market_data(symbol)
    candlestick_patterns = market_data.get('candlestick_patterns', {})
    key_levels = market_data.get('indicators', {}).get('1h', {}).get('horizontal_sr', [])
    for timeframe in ['1h', '15m']:
        if timeframe not in candlestick_patterns:
            continue
        tf_patterns = candlestick_patterns[timeframe]
        for pattern_name, is_detected in tf_patterns.items():
            if not is_detected:
                continue
            pattern_info = CANDLESTICK_PATTERNS.get(pattern_name, {'score': 1.0, 'is_bullish': False})
            score = pattern_info.get('score', 1.0)
            is_bullish = pattern_info.get('is_bullish', False)
            confirmation_score = 0
            if current_price and key_levels:
                for level in key_levels:
                    level_price = float(level['level'])
                    if abs(current_price - level_price) / current_price < 0.01:
                        if (is_bullish and level['type'] == 'support') or (not is_bullish and level['type'] == 'resistance'):
                            confirmation_score += 0.5
            if current_price:
                klines_tf = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
                if not klines_tf.empty:
                    last_close = float(klines_tf['close'].iloc[-1])
                    if (is_bullish and last_close > current_price) or (not is_bullish and last_close < current_price):
                        confirmation_score += 0.5
            if score > 0:
                pattern_data = {
                    'name': pattern_name,
                    'timeframe': timeframe,
                    'score': score + confirmation_score,
                    'is_bullish': is_bullish,
                    'confirmation_score': confirmation_score
                }
                result['detected_patterns'].append(pattern_data)
                result['pattern_score'] += score + confirmation_score
    return result
How the Score is Calculated:

Get Current Price: Uses get_ticker_buffer or falls back to klines_1m['close'].
Retrieve Patterns: Gets cached patterns from collect_market_data for 1h and 15m.
Score Patterns:
For each detected pattern, retrieves score and is_bullish from CANDLESTICK_PATTERNS.
Adds confirmation score:
+0.5 if price is within 1% of a matching S/R level (support for bullish, resistance for bearish).
+0.5 if follow-through confirmed (last close > current price for bullish, < for bearish).
Pattern Score: Sum of score + confirmation_score for all detected patterns.
Example (SUI-USD at 09:16:20):

Log:
text

Collapse

Wrap

Copy
{'detected_patterns': [
    {'name': 'hammer', 'timeframe': '15m', 'score': 1.5, 'is_bullish': True, 'confirmation_score': 0.0},
    {'name': 'hanging_man', 'timeframe': '15m', 'score': 1.5, 'is_bullish': False, 'confirmation_score': 0.0}
], 'pattern_score': 3.0}
Patterns: hammer (score 1.5, bullish), hanging_man (score 1.5, bearish).
Confirmation: confirmation_score = 0.0 (no S/R proximity or follow-through, possibly due to current_price unavailability or strict 1% threshold).
pattern_score = 1.5 + 1.5 = 3.0.
What the Score Represents:

Measures pattern significance in recent price action. A higher score indicates stronger or multiple candlestick patterns, suggesting potential reversals or continuations.
Used in calculate_confluence_score to contribute to setup viability.
Good vs. Bad Score:

Good: >3 (multiple strong patterns or confirmed patterns), high confidence.
Bad: 0–1 (no or weak patterns), low confidence.
Example: Score of 3.0 is moderate, indicating notable patterns but no confirmation.
Bullish vs. Bearish:

Bullish: Patterns with is_bullish=True (e.g., hammer).
Bearish: Patterns with is_bullish=False (e.g., hanging_man).
For SUI-USD, mixed signals: hammer (bullish) and hanging_man (bearish).
Contribution to Confluence: Scaled to 1.5 points (pattern_score / 2) in calculate_confluence_score with require_pattern_alignment=False.

4. identify_chart_patterns
Purpose: Computes a chart pattern score based on detected patterns in 6h and 1h timeframes.

Code (abridged):

python

Collapse

Wrap

Run

Copy
def identify_chart_patterns(self, symbol: str) -> Dict[str, Any]:
    result = {'detected_patterns': [], 'pattern_score': 0}
    ticker = self.get_ticker_buffer(symbol)
    current_price = float(ticker['last_price'].iloc[-1])
    key_levels = self.identify_key_levels(symbol)
    nearby_levels = key_levels.get('nearby_levels', [])
    market_states = self.get_market_state(symbol)
    market_data = self.collect_market_data(symbol)
    chart_patterns = market_data.get('chart_patterns', {})
    bullish_patterns = {'flag_bullish': 2, 'pennant_bullish': 2, 'triangle_ascending': 2, 'rectangle_bullish': 2,
                        'double_bottom': 3, 'inverse_head_and_shoulders': 3, 'falling_wedge': 2}
    bearish_patterns = {'double_top': 3, 'head_and_shoulders': 3, 'rising_wedge': 2, 'flag_bearish': 2,
                        'triangle_descending': 2, 'rectangle_bearish': 2}
    neutral_patterns = {'triangle_symmetrical': 2}
    timeframe_multipliers = {'6h': 1.5, '1h': 1.0}
    patterns_by_type = {'6h': set(), '1h': set()}
    for timeframe in ['6h', '1h']:
        if timeframe not in chart_patterns:
            continue
        tf_patterns = chart_patterns[timeframe]
        klines = self.data_manager.get_buffer(symbol, f'klines_{timeframe}')
        avg_volume = klines['volume'].tail(20).mean() if not klines.empty else 1.0
        for pattern_name, pattern_data in tf_patterns.items():
            if not pattern_data.get('detected', False):
                continue
            is_bullish = pattern_name in bullish_patterns
            is_bearish = pattern_name in bearish_patterns
            base_points = bullish_patterns.get(pattern_name, bearish_patterns.get(pattern_name, neutral_patterns.get(pattern_name, 0)))
            if pattern_name == 'triangle_symmetrical':
                breakout_price = pattern_data.get('breakout_price', 0.0)
                is_bullish = current_price > breakout_price if breakout_price else False
                is_bearish = current_price < breakout_price if breakout_price else False
            confirmation_status = 'unconfirmed'
            confirmation_multiplier = 0.5
            indicators = pattern_data.get('indicators', [])
            matched_indicators = 0
            total_indicators = len(indicators)
            tf_indicators = self.indicators_cache.get(symbol, {}).get(timeframe, {})
            for indicator in indicators:
                name = indicator['name'].split('.')[0]
                condition = indicator['condition']
                value = tf_indicators.get(name, 0.0)
                try:
                    if '>' in condition:
                        threshold = float(condition.split('>')[1])
                        if value > threshold:
                            matched_indicators += 1
                    elif '<' in condition:
                        threshold = float(condition.split('<')[1])
                        if value < threshold:
                            matched_indicators += 1
                    elif 'and' in condition:
                        parts = condition.split('and')
                        if all(eval(part.replace('current_price', str(current_price)).replace(name, str(value))) for part in parts):
                            matched_indicators += 1
                except Exception:
                    pass
            if total_indicators > 0:
                if matched_indicators == total_indicators:
                    confirmation_status = 'fully_confirmed'
                    confirmation_multiplier = 1.5
                elif matched_indicators > 0:
                    confirmation_status = 'partially_confirmed'
                    confirmation_multiplier = 1.0
            breakout_bonus = 0.0
            breakout_price = pattern_data.get('breakout_price', 0.0)
            volume_ratio = pattern_data.get('volume_ratio', klines['volume'].iloc[-1] / avg_volume if not klines.empty else 1.0)
            if breakout_price:
                if (is_bullish and current_price > breakout_price) or (is_bearish and current_price < breakout_price):
                    if volume_ratio > 1.5:
                        breakout_bonus = 1.0
            sr_multiplier = 1.0
            for level in nearby_levels:
                level_price = level.get('level', 0.0)
                level_is_support = level.get('is_support', None)
                distance_pct = abs(current_price - level_price) / current_price
                if distance_pct <= 0.005:
                    if is_bullish and level_is_support is True:
                        sr_multiplier = 1.5
                    elif is_bearish and level_is_support is False:
                        sr_multiplier = 1.5
            score = base_points * confirmation_multiplier * timeframe_multipliers[timeframe] * sr_multiplier + breakout_bonus
            detected_pattern = {
                'name': pattern_name,
                'timeframe': timeframe,
                'score': round(score, 2),
                'is_bullish': is_bullish,
                'confirmation_status': confirmation_status
            }
            detected_patterns.append(detected_pattern)
            pattern_score += score
            patterns_by_type[timeframe].add(pattern_name)
    common_patterns = patterns_by_type['6h'] & patterns_by_type['1h']
    if common_patterns:
        confluence_bonus = 2.0 * len(common_patterns)
        pattern_score += confluence_bonus
    result = {
        'detected_patterns': detected_patterns,
        'pattern_score': round(pattern_score, 2)
    }
    return result
How the Score is Calculated:

Get Current Price and Data: Uses get_ticker_buffer, identify_key_levels, get_market_state, collect_market_data.
Retrieve Patterns: Gets cached patterns for 6h and 1h.
Score Patterns:
Base points: 3 (high reliability, e.g., double_top), 2 (moderate, e.g., rectangle_bearish).
Confirmation multiplier: 1.5 (fully confirmed), 1.0 (partially), 0.5 (unconfirmed) based on indicators.
Timeframe multiplier: 1.5 (6h), 1.0 (1h).
S/R multiplier: 1.5 if near matching S/R level (within 0.5%).
Breakout bonus: +1.0 if breakout with volume >1.5x average.
Score: base_points * confirmation_multiplier * timeframe_multipliers * sr_multiplier + breakout_bonus.
Confluence Bonus: +2.0 per pattern common to 6h and 1h.
Pattern Score: Sum of individual pattern scores plus confluence bonus.
Example (SUI-USD at 09:16:20):

Log (market_timing_bot.log at 10:01:57):
1h: rectangle_bearish (detected).
No 6h patterns.
Assume rectangle_bearish:
Base points: 2.
Confirmation: Assume unconfirmed (confirmation_multiplier = 0.5, no indicator data in log).
Timeframe: 1h (timeframe_multipliers = 1.0).
S/R: No qualifying levels from identify_key_levels (sr_multiplier = 1.0).
Breakout: No breakout data (breakout_bonus = 0).
Score: 2 * 0.5 * 1.0 * 1.0 + 0 = 1.0.
Confluence bonus: 0 (no common patterns).
pattern_score = 1.0.
What the Score Represents:

Measures technical pattern strength indicating potential price movements. A higher score suggests reliable patterns (e.g., breakouts or reversals).
Used in calculate_confluence_score.
Good vs. Bad Score:

Good: >4 (confirmed patterns, S/R, confluence), strong setup.
Bad: 0–2 (unconfirmed or few patterns), weak setup.
Example: Score of 1.0 is weak, indicating a single unconfirmed pattern.
Bullish vs. Bearish:

Bullish: is_bullish=True (e.g., rectangle_bullish).
Bearish: is_bullish=False (e.g., rectangle_bearish).
For SUI-USD, rectangle_bearish is bearish, suggesting a sell setup.
Contribution to Confluence: Scaled to 0.5 points (pattern_score / 2) in calculate_confluence_score.

5. calculate_risk_reward_score
Purpose: Computes a risk-reward (R:R) score based on the ratio of potential reward to risk.

Code:

python

Collapse

Wrap

Run

Copy
def calculate_risk_reward_score(self, entry_price: float, stop_loss: float, target_price: float, is_bullish: bool) -> Dict[str, Any]:
    try:
        if is_bullish:
            risk = entry_price - stop_loss
            reward = target_price - entry_price
        else:
            risk = stop_loss - entry_price
            reward = entry_price - target_price
        if risk <= 0 or reward <= 0:
            return {'rr_ratio': 0, 'rr_points': 0}
        rr_ratio = reward / risk
        rr_points = 2 if rr_ratio >= 2 else 0  # Enforce R:R >= 2:1
        result = {'rr_ratio': round(rr_ratio, 2), 'rr_points': rr_points}
        return result
    except Exception:
        return {'rr_ratio': 0, 'rr_points': 0}
How the Score is Calculated:

Calculate Risk and Reward:
Bullish: risk = entry_price - stop_loss, reward = target_price - entry_price.
Bearish: risk = stop_loss - entry_price, reward = entry_price - target_price.
Compute R:R Ratio: rr_ratio = reward / risk.
Assign Points: rr_points = 2 if rr_ratio >= 2, else 0.
Example (SUI-USD at 09:16:20):

Not directly called in calculate_confluence_score, but assume from determine_trade_levels:
entry_price = 3.204, stop_loss = 3.172 (1% below), target_price = 3.236 (1% above).
Bullish: risk = 3.204 - 3.172 = 0.032, reward = 3.236 - 3.204 = 0.032.
rr_ratio = 0.032 / 0.032 = 1.0.
rr_points = 0 (since rr_ratio < 2).
What the Score Represents:

Measures trade profitability relative to risk. A higher R:R ratio indicates a better reward for the risk taken.
Used to filter trades in trading logic (not directly in calculate_confluence_score).
Good vs. Bad Score:

Good: rr_points = 2 (rr_ratio >= 2), favorable trade.
Bad: rr_points = 0 (rr_ratio < 2), unfavorable trade.
Example: Score of 0 indicates a poor R:R, discouraging the trade.
Bullish vs. Bearish:

Bullish: is_bullish=True, expects price to rise.
Bearish: is_bullish=False, expects price to fall.
Example assumes bullish, but SUI-USD’s mixed signals suggest bearish may apply.
Contribution to Confluence: Not used in calculate_confluence_score.

6. calculate_confluence_score
Purpose: Computes an overall confluence score combining trend, candlestick patterns, chart patterns, S/R proximity, and indicators.

Code (abridged):

python

Collapse

Wrap

Run

Copy
def calculate_confluence_score(self, symbol: str, market_data: dict, context: dict, require_pattern_alignment: bool = True) -> dict:
    trend_points = 0
    pattern_points = 0
    sr_points = 0
    indicator_points = 0
    is_bullish = False
    components = {}
    # Trend scoring
    trend_score = context.get('trend_score', 0)
    if trend_score >= 3:
        trend_points = 2
    elif trend_score == 2:
        trend_points = 1
    elif trend_score == 1:
        trend_points = 0.5
    components['trend'] = trend_points
    # Candlestick patterns
    candlestick_patterns = market_data.get('candlestick_patterns', {})
    pattern_score = candlestick_patterns.get('pattern_score', 0)
    detected_patterns = candlestick_patterns.get('detected_patterns', [])
    if pattern_score > 0:
        if require_pattern_alignment:
            patterns_1h = [p for p in detected_patterns if p['timeframe'] == '1h']
            patterns_15m = [p for p in detected_patterns if p['timeframe'] == '15m']
            if patterns_1h and patterns_15m:
                pattern_points = min(pattern_score / 2, 3)
            else:
                pattern_points = min(pattern_score / 4, 1.5)
        else:
            pattern_points = min(pattern_score / 2, 3)
        is_bullish = any(p['is_bullish'] for p in detected_patterns)
        components['candlestick_patterns'] = pattern_points
    # Chart patterns
    chart_patterns = market_data.get('chart_patterns', {})
    chart_pattern_score = sum(
        2 if p['detected'] else 0
        for tf in ['1h', '15m']
        for p in chart_patterns.get(tf, {}).values()
    )
    if chart_pattern_score > 0:
        pattern_points += min(chart_pattern_score / 2, 2)
        components['chart_patterns'] = min(chart_pattern_score / 2, 2)
    # Support/Resistance proximity
    ticker = self.get_ticker_buffer(symbol)
    current_price = None
    if not ticker.empty and 'last_price' in ticker.columns:
        current_price = float(ticker['last_price'].iloc[-1])
    else:
        klines_1m = self.data_manager.get_buffer(symbol, 'klines_1m')
        if not klines_1m.empty:
            current_price = float(klines_1m['close'].iloc[-1])
    if current_price:
        key_levels = market_data.get('indicators', {}).get('1h', {}).get('horizontal_sr', [])
        for level in key_levels:
            level_price = float(level['level'])
            if abs(current_price - level_price) / current_price < 0.01:
                sr_points += 1 if level['type'] == 'support' else -1
                components[f"sr_{level['type']}"] = sr_points
    # Indicator scoring
    indicators = market_data.get('indicators', {})
    for tf in ['1h', '15m']:
        tf_indicators = indicators.get(tf, {})
        rsi = float(tf_indicators.get('rsi14', 50))
        macd_hist = float(tf_indicators.get('macd_hist', 0))
        if rsi > 70 or rsi < 30:
            indicator_points += 0.5
        if macd_hist > 0:
            indicator_points += 0.5
        elif macd_hist < 0:
            indicator_points -= 0.5
        components[f"indicators_{tf}"] = indicator_points
    # Total score
    total_score = trend_points + pattern_points + sr_points + indicator_points
    total_score = max(total_score, 0.1)
    is_bullish = total_score > 0 and (trend_points > 0 or pattern_points > 0 or sr_points > 0)
    status = "Viable" if abs(total_score) >= 2 else "Weak" if abs(total_score) >= 1 else "Not Viable"
    # Risk-reward calculation
    rr_ratio = 0
    entry_price = current_price if current_price else 0
    stop_loss = entry_price * 0.99 if is_bullish else entry_price * 1.01 if entry_price else 0
    target_price = entry_price * 1.02 if is_bullish else entry_price * 0.98 if entry_price else 0
    if stop_loss != 0:
        rr_ratio = abs((target_price - entry_price) / (entry_price - stop_loss))
    result = {
        'total_score': total_score,
        'components': components,
        'is_bullish': is_bullish,
        'rr_ratio': rr_ratio,
        'entry_price': entry_price,
        'stop_loss': stop_loss,
        'target_price': target_price,
        'status': status
    }
    return result
How the Score is Calculated:

Trend Scoring:
From assess_market_context: trend_score = 1 → trend_points = 0.5.
Candlestick Pattern Scoring:
From identify_candlestick_patterns: pattern_score = 3.0.
With require_pattern_alignment=False (from run): pattern_points = min(3.0 / 2, 3) = 1.5.
Chart Pattern Scoring:
From identify_chart_patterns: chart_pattern_score = 2 (rectangle_bearish in 1h).
pattern_points += min(2 / 2, 2) = 1.
S/R Proximity Scoring:
Assume current_price ≈ 3.204.
S/R levels: Support 3.20335375, resistance 3.20541625.
Distances: Support 0.00026% (<0.01%), resistance 0.00033% (<0.01%).
No levels qualify (sr_points = 0).
Indicator Scoring:
For 1h: rsi14=39.16 (neutral), macd_hist=-0.00557 (-0.5 points).
For 15m: rsi14=42.15 (neutral), macd_hist=0.00136 (+0.5 points).
indicator_points = -0.5 + 0.5 = 0.
Total Score:
total_score = 0.5 + (1.5 + 1) + 0 + 0 = 3.0.
total_score = max(3.0, 0.1) = 3.0.
Bullish/Bearish and Status:
is_bullish = True (due to hammer).
status = "Viable" (since abs(3.0) >= 2).
Risk-Reward:
entry_price = 3.204, stop_loss = 3.172 (0.99 * 3.204), target_price = 3.236 (1.02 * 3.204).
rr_ratio = |(3.236 - 3.204) / (3.204 - 3.172)| = 0.032 / 0.032 = 1.0.
Example Result:

python

Collapse

Wrap

Run

Copy
{
    'total_score': 3.0,
    'components': {
        'trend': 0.5,
        'candlestick_patterns': 1.5,
        'chart_patterns': 1.0,
        'indicators_1h': 0,
        'indicators_15m': 0
    },
    'is_bullish': True,
    'rr_ratio': 1.0,
    'entry_price': 3.204,
    'stop_loss': 3.172,
    'target_price': 3.236,
    'status': 'Viable'
}
What the Score Represents:

Combines multiple technical signals to assess trade setup viability. A higher score indicates stronger confluence of trend, patterns, and indicators, increasing confidence in entering a trade.
Used in run to determine setup status: “High Confidence” (≥8), “Viable” (≥6), “Not Viable” (<6).
Good vs. Bad Score:

Good: ≥6 (Viable), ≥8 (High Confidence), strong setup for trading.
Bad: <2 (Not Viable or Weak), avoid trading.
Example: Score of 3.0 is Viable but moderate, suggesting a trade with caution.
Bullish vs. Bearish:

Bullish: is_bullish=True if any bullish patterns or positive trend/S/R points.
Bearish: is_bullish=False if bearish signals dominate.
For SUI-USD, is_bullish=True due to hammer, but mixed signals (hanging_man, rectangle_bearish) suggest caution.
Summary Table

Method	Score Type	Represents	Good Score	Bad Score	Bullish	Bearish	SUI-USD Example (09:16:20)
assess_market_context	TrendAlignmentScore	Trend consistency	3–5	0–1	Uptrend	Downtrend	1 (0.5 points)
identify_key_levels	Proximity Score	S/R significance	>3	0–1	Near support	Near resistance	0 (0 points)
identify_candlestick_patterns	Pattern Score	Candlestick pattern strength	>3	0–1	Bullish patterns (e.g., hammer)	Bearish patterns (e.g., hanging_man)	3.0 (1.5 points)
identify_chart_patterns	Pattern Score	Chart pattern strength	>4	0–2	Bullish patterns	Bearish patterns	1.0 (0.5 points)
calculate_risk_reward_score	R:R Points	Trade profitability	2	0	High R:R (buy)	High R:R (sell)	0 (not used)
calculate_confluence_score	Confluence Score	Overall setup viability	≥6	<2	Bullish signals dominate	Bearish signals dominate	3.0 (Viable)
Final Notes
SUI-USD at 09:16:20:
Total confluence score of 3.0 is moderate, indicating a viable but not high-confidence setup.
Mixed bullish (hammer) and bearish (hanging_man, rectangle_bearish) signals suggest caution.
Weak trend alignment (TrendAlignmentScore=1) and no S/R or indicator points reduce confidence.
Good Scores: High scores across methods indicate strong, reliable setups. For confluence, aim for ≥6.
Bad Scores: Low scores suggest weak or conflicting signals, avoid trading.
Bullish/Bearish: Determined by pattern types, trend direction, and S/R context. Mixed signals require careful analysis.
If you need further details (e.g., CANDLESTICK_PATTERNS structure, specific log analysis), please share additional files or logs, and I’ll refine the explanation. Thank you for your patience!