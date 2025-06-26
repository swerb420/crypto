import ccxt.pro as ccxt
import asyncio
from typing import List, Dict, Any

async def fetch_ticker(exchange_name, symbol):
    exchange = getattr(ccxt, exchange_name)()
    try:
        ticker = await exchange.fetch_ticker(symbol)
        await exchange.close()
        return {"exchange": exchange.id, "price": ticker['last'], "status": "success"}
    except Exception:
        await exchange.close()
        return {"exchange": exchange.id, "price": None, "status": "error"}

async def fetch_all_tickers(symbol: str) -> List[Dict[str, Any]]:
    exchanges_to_check = ['kraken', 'coinbase', 'binance']
    tasks = [fetch_ticker(ex_name, symbol) for ex_name in exchanges_to_check]
    results = await asyncio.gather(*tasks)
    return [res for res in results if res['status'] == 'success']

def main(trade_idea: Dict[str, Any]) -> Dict[str, Any]:
    asset_symbol_map = {"ETH": "ETH/USDT", "BTC": "BTC/USDT"} # Simple mapping
    asset_symbol = asset_symbol_map.get(trade_idea.get('asset'))
    if not asset_symbol: raise ValueError("Asset not supported for price checks.")
    
    print(f"INFO: [PriceEngine] Getting live prices for {asset_symbol}...")
    live_prices = asyncio.run(fetch_all_tickers(asset_symbol))
    
    trade_idea['live_prices'] = live_prices
    if live_prices:
        live_prices.sort(key=lambda x: x['price'])
        trade_idea['best_price'] = live_prices[0]['price']
        
    return trade_idea