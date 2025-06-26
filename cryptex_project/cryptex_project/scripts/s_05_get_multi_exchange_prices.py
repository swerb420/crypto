# File: cryptex_project/scripts/s_get_multi_exchange_prices.py
# --- UPGRADED VERSION ---
import ccxt.pro as ccxt
import asyncio
from typing import List, Dict, Any

async def fetch_ticker(exchange_name, symbol):
    """Async function to fetch a ticker from a single exchange."""
    exchange = getattr(ccxt, exchange_name)()
    try:
        ticker = await exchange.fetch_ticker(symbol)
        await exchange.close()
        return {"exchange": exchange.id, "price": ticker['last'], "status": "success"}
    except Exception:
        await exchange.close()
        return {"exchange": exchange.id, "price": None, "status": "error"}

async def fetch_all_tickers(symbol: str) -> List[Dict[str, Any]]:
    """Fetches a symbol's price from multiple exchanges concurrently."""
    # List of reliable exchanges, including your US-based ones.
    exchanges_to_check = ['kraken', 'coinbase', 'binance', 'bybit', 'kucoin']
    
    tasks = [fetch_ticker(ex_name, symbol) for ex_name in exchanges_to_check]
    results = await asyncio.gather(*tasks)
    return [res for res in results if res['status'] == 'success']

def main(trade_idea: Dict[str, Any]) -> Dict[str, Any]:
    asset_symbol = trade_idea.get('asset')
    if not asset_symbol: raise ValueError("Input must contain an 'asset' key.")
    
    print(f"INFO: [PriceEngine] Getting live prices for {asset_symbol}...")
    live_prices = asyncio.run(fetch_all_tickers(asset_symbol))
    
    if not live_prices:
        print(f"WARN: [PriceEngine] Could not fetch live price for {asset_symbol}.")
        trade_idea['live_prices'] = []
    else:
        live_prices.sort(key=lambda x: x['price'])
        print(f"INFO: [PriceEngine] Prices found: {live_prices}")
        trade_idea['live_prices'] = live_prices
        
    return trade_idea