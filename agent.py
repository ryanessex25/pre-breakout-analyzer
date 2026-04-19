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

Stock: {result['ticker']}
Current price: ${result['current_price']:.2f}

Signal Scores:
- Volume dry-up: {result['volume_score']}/15
- Momentum divergence: {result['momentum_score']}/12
- Relative strength vs SPY: {result['rs_score']}/8
- Total score: {result['total_score']}/35

Raw Metrics:
- RSI current: {result['rsi_current']:.1f}
- Outperformance vs SPY: {result['outperformance']:.2f}%
- Price above 21 EMA: {result['price_above_ema']}
- OBV days rising: {result['obv_days_rising']}/5

Return your response in exactly this format:
Decision: BUY or PASS
Confidence: 1-10
Entry zone: $
Stop loss: $
Target: $
Reasoning:
Risks:
"""

    message = client.messages.create(
        model="claude-opus-4-6",
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
            'score': result['total_score'],
            'decision': decision
        })
    
    return decisions