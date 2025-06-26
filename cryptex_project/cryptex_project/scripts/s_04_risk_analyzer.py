# File: s_risk_analyzer.py
# --- FINAL VERSION ---
# This version uses the public DexScreener API which does not require a key.

import requests
from typing import Dict, Any
from datetime import datetime, timedelta

def main(analyzed_tx: Dict[str, Any]) -> Dict[str, Any]:
    tx_hash = analyzed_tx.get('signatures', [None])[0]
    print(f"INFO: [RiskAnalyzer] Starting security scan for {tx_hash[:10]}...")

    try:
        # This logic finds the primary token address from the transaction data
        contract_address = next(
            addr for addr in analyzed_tx.get('account_keys', []) 
            if addr.get('signer') is False and addr.get('writable') is True
        ).get('account')
        
        if not contract_address: raise ValueError("Could not determine token contract address.")
             
    except (IndexError, ValueError) as e:
        print(f"WARN: [RiskAnalyzer] Could not find token contract address. Skipping. Details: {e}")
        analyzed_tx['risk_analysis'] = {"safety_rating": "UNKNOWN", "details": "Could not identify token contract."}
        return analyzed_tx

    api_url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
    
    try:
        res = requests.get(api_url, timeout=15)
        res.raise_for_status()
        data = res.json().get('pairs', [])
        
        if not data:
            raise ValueError("Token not found on DEX Screener or has no trading pairs.")

        main_pair = sorted(data, key=lambda x: float(x.get('liquidity', {}).get('usd', 0)), reverse=True)[0]
        
        liquidity_usd = float(main_pair.get('liquidity', {}).get('usd', 0))
        pair_created_at = datetime.fromtimestamp(main_pair.get('pairCreatedAt', 0) / 1000)
        
        # --- Risk Logic ---
        safety_rating = "SAFE"
        warnings = []
        
        if liquidity_usd < 50000:
            safety_rating = "CAUTION"
            warnings.append(f"Low liquidity (${liquidity_usd:,.0f})")
        if pair_created_at > (datetime.now() - timedelta(days=1)):
            safety_rating = "DANGER"
            warnings.append("Token pair is less than 24 hours old.")

        analyzed_tx['risk_analysis'] = {
            "safety_rating": safety_rating,
            "liquidity_usd": liquidity_usd,
            "pair_created_at": pair_created_at.isoformat(),
            "warnings": warnings,
            "source": "DEX Screener"
        }
        print(f"INFO: [RiskAnalyzer] Scan complete. Safety Rating: {safety_rating}")

    except Exception as e:
        print(f"ERROR: [RiskAnalyzer] Failed to get security data. Error: {e}")
        analyzed_tx['risk_analysis'] = {"safety_rating": "ERROR", "details": str(e)}

    return analyzed_tx