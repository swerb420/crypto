import requests
from typing import Dict, Any

def main(analyzed_tx: Dict[str, Any]) -> Dict[str, Any]:
    print("INFO: [RiskAnalyzer] Starting security scan...")
    # This logic will be improved to robustly find the token address
    contract_address = analyzed_tx.get('trade', {}).get('raw_pos', {}).get('symbol', 'UNKNOWN_TOKEN')[:-4]
    
    api_url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
    try:
        res = requests.get(api_url, timeout=15)
        res.raise_for_status()
        data = res.json().get('pairs', [])
        if not data: raise ValueError("Token not found on DEX Screener.")
        main_pair = sorted(data, key=lambda x: float(x.get('liquidity', {}).get('usd', 0)), reverse=True)[0]
        liquidity_usd = float(main_pair.get('liquidity', {}).get('usd', 0))
        safety_rating = "SAFE" if liquidity_usd > 50000 else "CAUTION"
        analyzed_tx['risk_analysis'] = {"safety_rating": safety_rating, "liquidity_usd": liquidity_usd, "source": "DEX Screener"}
    except Exception as e:
        analyzed_tx['risk_analysis'] = {"safety_rating": "ERROR", "details": str(e)}
    print(f"INFO: [RiskAnalyzer] Scan complete. Safety Rating: {analyzed_tx['risk_analysis']['safety_rating']}")
    return analyzed_tx