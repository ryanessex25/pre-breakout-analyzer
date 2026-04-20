"""
Report Generator for Early Breakout Scanner
Creates human-readable detailed reports for alerted stocks
"""

from datetime import datetime
import os
import config


def generate_report(results, output_format='txt'):
    """
    Generate detailed report for alerted stocks
    
    Args:
        results (list): List of scan result dictionaries
        output_format (str): 'txt' or 'md' (markdown)
    
    Returns:
        str: Path to generated report file
    """
    
    # Filter for only alerted stocks (high_priority + watch_list)
    alerted = [r for r in results if r['alert_level'] in ['high_priority', 'watch_list']]
    
    if not alerted:
        print("ℹ️  No alerted stocks to generate report for")
        return None
    
    # Sort by score (highest first)
    alerted.sort(key=lambda x: x['total_score'], reverse=True)
    
    # Generate report content
    report_lines = []
    
    # Header
    report_lines.append("=" * 80)
    report_lines.append("EARLY BREAKOUT SCANNER - DETAILED REPORT")
    report_lines.append("=" * 80)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Total Alerted Stocks: {len(alerted)}")
    report_lines.append(f"High Priority: {sum(1 for r in alerted if r['alert_level'] == 'high_priority')}")
    report_lines.append(f"Watch List: {sum(1 for r in alerted if r['alert_level'] == 'watch_list')}")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    # Generate detailed breakdown for each stock
    for rank, stock in enumerate(alerted, 1):
        report_lines.extend(generate_stock_detail(stock, rank))
        report_lines.append("")  # Blank line between stocks
    
    # Footer
    report_lines.append("=" * 80)
    report_lines.append("END OF REPORT")
    report_lines.append("=" * 80)
    
    # Save to file
    os.makedirs(config.RESULTS_FOLDER, exist_ok=True)
    filename = f"{config.RESULTS_FOLDER}/scan_report_{datetime.now().strftime('%Y-%m-%d')}.{output_format}"
    
    with open(filename, 'w') as f:
        f.write('\n'.join(report_lines))
    
    print(f"📄 Detailed report saved to: {filename}")
    return filename


def generate_stock_detail(stock, rank):
    """
    Generate detailed breakdown for a single stock
    
    Args:
        stock (dict): Stock result dictionary
        rank (int): Ranking position
    
    Returns:
        list: Lines of formatted text
    """
    
    lines = []
    
    # Header
    alert_emoji = "✅" if stock['alert_level'] == 'high_priority' else "👀"
    alert_label = "HIGH PRIORITY" if stock['alert_level'] == 'high_priority' else "WATCH LIST"
    
    lines.append("=" * 80)
    lines.append(f"{alert_emoji} {stock['ticker']} - ${stock['current_price']:.2f} | {stock['total_score']} POINTS | RANK #{rank} | {alert_label}")
    lines.append("=" * 80)
    lines.append("")
    
    # Overall Scores
    lines.append("OVERALL SCORES:")
    lines.append(f"  Total Score:      {stock['total_score']}/35 points ({stock['total_score']/35*100:.0f}%)")
    lines.append(f"  Alert Level:      {alert_label}")
    lines.append(f"  Volume Score:     {stock['volume_score']}/15 points")
    lines.append(f"  Momentum Score:   {stock['momentum_score']}/12 points")
    lines.append(f"  RS Score:         {stock['rs_score']}/8 points")
    lines.append("")
    
    # Volume Metrics Section
    lines.append("-" * 80)
    lines.append(f"VOLUME METRICS ({stock['volume_score']}/15 points)")
    lines.append("-" * 80)
    
    red_vol_ratio = stock['red_volume_ratio']
    red_avg = stock['red_day_avg_volume']
    green_avg = stock['green_day_avg_volume']
    spread_ratio = green_avg / red_avg if red_avg > 0 else 0
    
    lines.append(f"  Red Volume Ratio:         {red_vol_ratio:.3f}x (red days vs 20-day avg)")
    lines.append(f"  Red Day Avg Volume:       {red_avg:,.0f} shares")
    lines.append(f"  Green Day Avg Volume:     {green_avg:,.0f} shares")
    lines.append(f"  Volume Spread:            Green days {spread_ratio:.2f}x heavier than red days")
    lines.append(f"  Price Above 21 EMA:       {'YES ✓' if stock['price_above_ema'] else 'NO ✗'}")
    lines.append("")
    
    # Volume quality interpretation
    if red_vol_ratio < 0.15:
        vol_quality = "Exceptional dry-up"
        vol_points_est = "10/10"
    elif red_vol_ratio < 0.30:
        vol_quality = "Outstanding dry-up"
        vol_points_est = "8/10"
    elif red_vol_ratio < 0.50:
        vol_quality = "Strong dry-up"
        vol_points_est = "6/10"
    elif red_vol_ratio < 0.70:
        vol_quality = "Moderate dry-up"
        vol_points_est = "4/10"
    elif red_vol_ratio < 0.85:
        vol_quality = "Slight dry-up"
        vol_points_est = "2/10"
    else:
        vol_quality = "No meaningful dry-up"
        vol_points_est = "0/10"
    
    lines.append("  Breakdown:")
    lines.append(f"    • Red volume ratio: {vol_quality} (~{vol_points_est})")
    lines.append(f"    • Price above EMA: {'3/3 points' if stock['price_above_ema'] else '0/3 points'}")
    
    if spread_ratio > 2.0:
        lines.append(f"    • Red/green spread: 2/2 points (huge {spread_ratio:.2f}x spread)")
    elif spread_ratio > 1.5:
        lines.append(f"    • Red/green spread: 1/2 points (good {spread_ratio:.2f}x spread)")
    else:
        lines.append(f"    • Red/green spread: 0/2 points (minimal {spread_ratio:.2f}x spread)")
    
    lines.append("")
    
    # Momentum Metrics Section
    lines.append("-" * 80)
    lines.append(f"MOMENTUM METRICS ({stock['momentum_score']}/12 points)")
    lines.append("-" * 80)
    
    rsi = stock['rsi_current']
    rsi_slope = stock['rsi_slope']
    macd = stock['macd_histogram']
    obv_days = stock['obv_days_rising']
    
    lines.append(f"  RSI Current:              {rsi:.2f}")
    lines.append(f"  RSI Slope (5-day):        {rsi_slope:.3f} ({'rising' if rsi_slope > 0 else 'falling'})")
    
    # RSI zone interpretation
    if 40 <= rsi <= 65:
        rsi_zone = "ACCUMULATION ZONE ✓ (ideal range)"
        rsi_zone_points = "2/2"
    elif 35 <= rsi < 40:
        rsi_zone = "Early recovery (possibly too early)"
        rsi_zone_points = "0/2"
    elif 65 < rsi <= 70:
        rsi_zone = "Getting extended (late)"
        rsi_zone_points = "0/2"
    elif rsi > 70:
        rsi_zone = "OVERBOUGHT ⚠️ (too late)"
        rsi_zone_points = "0/2"
    else:
        rsi_zone = "Oversold (too early)"
        rsi_zone_points = "0/2"
    
    lines.append(f"  RSI Zone:                 {rsi_zone}")
    lines.append("")
    
    lines.append(f"  MACD Histogram:           {macd:.4f}")
    
    if macd > 0:
        macd_status = "POSITIVE ✓"
        macd_points_est = "3/3"
    elif macd > -0.1 and rsi_slope > 0:
        macd_status = "Improving from negative"
        macd_points_est = "2/3"
    else:
        macd_status = "Negative"
        macd_points_est = "0-1/3"
    
    lines.append(f"  MACD Status:              {macd_status}")
    lines.append("")
    
    lines.append(f"  OBV Days Rising:          {obv_days} out of 5 days")
    
    if obv_days >= 5:
        obv_quality = "Excellent accumulation"
        obv_points_est = "3/3"
    elif obv_days >= 4:
        obv_quality = "Good accumulation"
        obv_points_est = "2/3"
    elif obv_days >= 3:
        obv_quality = "Moderate accumulation"
        obv_points_est = "1/3"
    else:
        obv_quality = "Weak/no accumulation"
        obv_points_est = "0/3"
    
    lines.append(f"  OBV Quality:              {obv_quality}")
    lines.append("")
    
    # Momentum breakdown
    if rsi_slope > 2:
        rsi_div_quality = "Strong divergence"
        rsi_div_points = "4/4"
    elif rsi_slope > 1:
        rsi_div_quality = "Moderate divergence"
        rsi_div_points = "3/4"
    elif rsi_slope > 0.5:
        rsi_div_quality = "Slight divergence"
        rsi_div_points = "2/4"
    elif rsi_slope > 0:
        rsi_div_quality = "Weak divergence"
        rsi_div_points = "2/4"
    else:
        rsi_div_quality = "No divergence"
        rsi_div_points = "0/4"
    
    lines.append("  Breakdown:")
    lines.append(f"    • RSI divergence: {rsi_div_quality} (~{rsi_div_points})")
    lines.append(f"    • RSI accumulation zone: {rsi_zone_points} points")
    lines.append(f"    • MACD status: ~{macd_points_est} points")
    lines.append(f"    • OBV consistency: ~{obv_points_est} points")
    lines.append("")
    
    # Relative Strength Section
    lines.append("-" * 80)
    lines.append(f"RELATIVE STRENGTH METRICS ({stock['rs_score']}/8 points)")
    lines.append("-" * 80)
    
    rs_slope = stock['rs_slope']
    outperf = stock['outperformance']
    
    lines.append(f"  RS Slope (5-day):         {rs_slope:.8f}")
    
    if rs_slope > 0.005:
        rs_quality = "Strongly positive"
        rs_points_est = "4/4"
    elif rs_slope > 0.002:
        rs_quality = "Moderately positive"
        rs_points_est = "3/4"
    elif rs_slope > 0:
        rs_quality = "Slightly positive"
        rs_points_est = "2/4"
    else:
        rs_quality = "Negative/flat"
        rs_points_est = "0/4"
    
    lines.append(f"  RS Slope Quality:         {rs_quality}")
    lines.append("")
    
    lines.append(f"  Outperformance vs SPY:    {outperf:+.2f}%")
    
    if outperf > 5:
        outperf_quality = "Strong outperformance"
        outperf_points_est = "4/4"
    elif outperf > 3:
        outperf_quality = "Solid outperformance"
        outperf_points_est = "3/4"
    elif outperf > 1:
        outperf_quality = "Moderate outperformance"
        outperf_points_est = "2/4"
    elif outperf > 0:
        outperf_quality = "Slight outperformance"
        outperf_points_est = "1/4"
    else:
        outperf_quality = "Underperforming SPY"
        outperf_points_est = "0/4"
    
    lines.append(f"  Outperformance Quality:   {outperf_quality}")
    lines.append("")
    
    lines.append("  Breakdown:")
    lines.append(f"    • RS slope: {rs_quality} (~{rs_points_est})")
    lines.append(f"    • Outperformance: {outperf_quality} (~{outperf_points_est})")
    lines.append("")
    
    # Price & Volume Info
    lines.append("-" * 80)
    lines.append("PRICE & VOLUME INFO")
    lines.append("-" * 80)
    lines.append(f"  Current Price:    ${stock['current_price']:.2f}")
    lines.append(f"  Current Volume:   {stock['volume']:,.0f} shares")
    lines.append(f"  Date:             {stock['date']}")
    lines.append("")
    
    lines.append("=" * 80)
    
    return lines


def generate_report_from_csv(csv_path, output_format='txt'):
    """
    Generate report from existing CSV file
    
    Args:
        csv_path (str): Path to CSV file
        output_format (str): 'txt' or 'md'
    
    Returns:
        str: Path to generated report
    """
    import pandas as pd
    
    df = pd.read_csv(csv_path)
    results = df.to_dict('records')
    
    return generate_report(results, output_format)