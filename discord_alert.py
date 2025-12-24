"""
Discord alert module for sending notifications
"""

import requests
import json
from datetime import datetime
import config


def send_discord_alert(results):
    """
    Send alert to Discord for stocks meeting criteria (2 out of 3 signals)
    
    Args:
        results (list): List of dictionaries with scan results
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    if not results:
        print("ℹ️  No alerts to send")
        return False
    
    # Check if webhook URL is configured
    if config.DISCORD_WEBHOOK_URL == "https://canary.discord.com/api/webhooks/1451719046990135507/ewPUTmwI5HMTQtQEM2ZA-ZrnOe7bSMqorvKFI6iwwhz1g1XyYimjg0jkAukhnYff0zxY":
        print("⚠️  Discord webhook URL not configured. Skipping alerts.")
        return False
    
    try:
        # Sort by score and take top 10 only
        top_alerts = sorted(results, key=lambda x: x.get('total_score', 0), reverse=True)[:10]
        
        # Create embed message
        embed = {
            "title": "🚨 Early Breakout Scanner - Top 10 Alerts",
            "description": f"Found **{len(results)}** total alerts. Showing top 10 by score.",
            "color": 5814783,  # Green color
            "timestamp": datetime.utcnow().isoformat(),
            "fields": []
        }
        
        # Add each stock as a field with detailed info
        for i, stock in enumerate(top_alerts, 1):
            signals_met = []
            
            # Volume Dry-Up
            if stock.get('step1_signal'):
                signals_met.append("✅ Vol Dry-Up")
                vol_details = f"(Ratio: {stock.get('step1_red_volume_ratio', 0):.2f})"
            else:
                vol_details = f"❌ Vol (Ratio: {stock.get('step1_red_volume_ratio', 0):.2f})"
            
            # Divergences
            if stock.get('step2_signal'):
                signals_met.append("✅ Divergences")
                div_details = f"(RSI: {stock.get('step2_rsi', 0):.1f})"
            else:
                div_details = f"❌ Div (RSI: {stock.get('step2_rsi', 0):.1f})"
            
            # Relative Strength
            if stock.get('step3_signal'):
                signals_met.append("✅ Rel Strength")
                rs_details = f"(+{stock.get('step3_outperformance', 0):.1f}% vs SPY)"
            else:
                rs_details = f"❌ RS ({stock.get('step3_outperformance', 0):.1f}% vs SPY)"
            
            # Build field value with all details
            field_value = "\n".join(signals_met)
            field_value += f"\n\n**Score:** {stock.get('total_score', 0):.0f}/30"
            field_value += f"\n**Price:** ${stock.get('current_price', 0):.2f}"
            field_value += f"\n**Volume:** {stock.get('volume', 0):,.0f}"
            field_value += f"\n\n{vol_details}"
            field_value += f"\n{div_details}"
            field_value += f"\n{rs_details}"
            
            embed["fields"].append({
                "name": f"#{i} - {stock['ticker']}",
                "value": field_value,
                "inline": True
            })
        
        # Add footer
        embed["footer"] = {
            "text": f"Early Breakout Scanner • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
        
        # Send to Discord
        payload = {
            "embeds": [embed]
        }
        
        response = requests.post(
            config.DISCORD_WEBHOOK_URL,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 204:
            print(f"✅ Discord alert sent successfully for top 10 stocks (out of {len(results)} total)")
            return True
        else:
            print(f"❌ Discord alert failed: {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Error sending Discord alert: {str(e)}")
        return False


def send_summary_alert(total_scanned, alerts_count, scan_duration):
    """
    Send summary message after scan completes
    
    Args:
        total_scanned (int): Total number of stocks scanned
        alerts_count (int): Number of stocks that triggered alerts
        scan_duration (float): Time taken to scan in seconds
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    if config.DISCORD_WEBHOOK_URL == "YOUR_DISCORD_WEBHOOK_URL_HERE":
        return False
    
    try:
        embed = {
            "title": "📊 Scan Complete",
            "color": 3447003,  # Blue color
            "timestamp": datetime.utcnow().isoformat(),
            "fields": [
                {
                    "name": "Stocks Scanned",
                    "value": str(total_scanned),
                    "inline": True
                },
                {
                    "name": "Alerts Generated",
                    "value": str(alerts_count),
                    "inline": True
                },
                {
                    "name": "Scan Duration",
                    "value": f"{scan_duration:.1f}s",
                    "inline": True
                }
            ],
            "footer": {
                "text": f"Early Breakout Scanner • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
        }
        
        payload = {"embeds": [embed]}
        
        response = requests.post(
            config.DISCORD_WEBHOOK_URL,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )
        
        return response.status_code == 204
    
    except Exception as e:
        print(f"❌ Error sending summary alert: {str(e)}")
        return False