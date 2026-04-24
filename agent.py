import os
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def analyze_with_llm(result):
    """
    Takes a scan result dict and gets Claude's trade decision
    """
    
    prompt = f"""
You are a disciplined swing trading analyst specializing in 
pre-breakout setups with a 2 week hold target. Be direct and 
only recommend trades with clear risk/reward of at least 2:1.

HARD DISQUALIFIERS — if ANY of these are true, decision MUST be PASS, no exceptions:
- Red volume ratio above 0.85 (selling pressure not drying up)
- ATR today is greater than ATR lookback (volatility expanding, not compressing)
- Price is more than 30% below 52-week high (too much overhead supply)

Stock: {result['ticker']}
Current price: ${result['current_price']:.2f}

Volume:
- Red volume ratio: {result['red_volume_ratio']:.3f} (lower = better dry-up, must be below 0.85)
- Price above 21 EMA: {result['price_above_ema']}
- Red day avg volume: {result['red_day_avg_volume']:,.0f}
- Red day volume slope: {result['red_day_volume_slope']:.2f} (negative = drying up)
- Red day stepdown count: {result['red_day_stepdown_count']} of {result['red_day_count'] - 1 if result['red_day_count'] > 1 else 0} possible

Momentum:
- RSI current: {result['rsi_current']:.1f}
- RSI slope: {result['rsi_slope']:.3f} (positive = rising)
- Price slope: {result['price_slope']:.3f}
- MACD histogram: {result['macd_histogram']:.4f}
- MACD histogram prev: {result['macd_histogram_prev']:.4f}
- OBV days rising: {result['obv_days_rising']}/5

Relative Strength vs SPY:
- Short-term outperformance (2 weeks): {result['outperformance_short']:.2f}%
- Long-term outperformance (3 months): {result['outperformance_long']:.2f}%
- Short-term RS slope: {result['rs_slope_short']:.8f}
- Long-term RS slope: {result['rs_slope_long']:.8f}

Compression:
- ATR contracting: {result['atr_contracting']}
- ATR today: {f"{result['atr_today']:.2f}" if result['atr_today'] else 'N/A'}
- ATR lookback: {f"{result['atr_lookback']:.2f}" if result['atr_lookback'] else 'N/A'}
- Near recent high (10d/20d): {result['near_recent_high']}
- % from 10d high: {f"{result['pct_from_high_10d']*100:.1f}%" if result['pct_from_high_10d'] is not None else 'N/A'}
- % from 20d high: {f"{result['pct_from_high_20d']*100:.1f}%" if result['pct_from_high_20d'] is not None else 'N/A'}
- 52-week high: {f"${result['week_52_high']:.2f}" if result['week_52_high'] else 'N/A'}
- % from 52w high: {f"{result['pct_from_52w_high']*100:.1f}%" if result['pct_from_52w_high'] is not None else 'N/A'}
- Near 52w high: {result['near_52w_high']}

Return your response in exactly this format:
Decision: BUY or PASS
Confidence: 1-10
Entry zone: $
Stop loss: $
Target: $
Reasoning:
Risks:

Raw Metrics:
Red volume ratio: {result['red_volume_ratio']:.3f}
Red day avg volume: {result['red_day_avg_volume']:,.0f}
Red day volume slope: {result['red_day_volume_slope']:.2f}
Red day stepdown count: {result['red_day_stepdown_count']} of {result['red_day_count'] - 1 if result['red_day_count'] > 1 else 0}
Price above EMA: {result['price_above_ema']}
RSI current: {result['rsi_current']:.1f}
RSI slope: {result['rsi_slope']:.3f}
Price slope: {result['price_slope']:.3f}
MACD histogram: {result['macd_histogram']:.4f}
MACD histogram prev: {result['macd_histogram_prev']:.4f}
OBV days rising: {result['obv_days_rising']}/5
Outperformance short: {result['outperformance_short']:.2f}%
Outperformance long: {result['outperformance_long']:.2f}%
RS slope short: {result['rs_slope_short']:.8f}
RS slope long: {result['rs_slope_long']:.8f}
ATR contracting: {result['atr_contracting']}
ATR today: {f"{result['atr_today']:.2f}" if result['atr_today'] else 'N/A'}
ATR lookback: {f"{result['atr_lookback']:.2f}" if result['atr_lookback'] else 'N/A'}
Near recent high: {result['near_recent_high']}
Pct from 10d high: {f"{result['pct_from_high_10d']*100:.1f}%" if result['pct_from_high_10d'] is not None else 'N/A'}
Pct from 20d high: {f"{result['pct_from_high_20d']*100:.1f}%" if result['pct_from_high_20d'] is not None else 'N/A'}
52-week high: {f"${result['week_52_high']:.2f}" if result['week_52_high'] else 'N/A'}
Pct from 52w high: {f"{result['pct_from_52w_high']*100:.1f}%" if result['pct_from_52w_high'] is not None else 'N/A'}
Near 52w high: {result['near_52w_high']}
Current price: ${result['current_price']:.2f}
Volume: {result['volume']:,.0f}
"""
    
    #sonnet is cheaper than opus 
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return message.content[0].text


def run_agent(results):
    """
    Takes scanner results and runs each through the LLM
    """
    decisions = []
    
    for result in results:
        print(f"\nAnalyzing {result['ticker']}...")
        decision = analyze_with_llm(result)
        
        print(f"\n{result['ticker']} Decision:")
        print(decision)
        print("-" * 50)
        
        decisions.append({
            'ticker': result['ticker'],
            'decision': decision
        })
    
    return decisions