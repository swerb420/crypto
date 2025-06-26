import psycopg2, ccxt, os
from typing import Dict, Any

def main() -> Dict[str, Any]:
    print("INFO: [PortfolioMonitor] Starting check of open positions...")
    conn = psycopg2.connect(host='postgres', dbname='windmill', user='windmill', password='windmill')
    open_positions = []
    with conn.cursor() as cur:
        cur.execute("SELECT asset, direction, entry_price, trade_size_usd FROM public.trading_signals WHERE trade_status = 'OPEN';")
        open_positions = cur.fetchall()
    conn.close()

    if not open_positions: return {"status": "no_open_positions"}

    exchange = ccxt.kraken({'apiKey': os.environ.get("WMILL_SECRET_KRAKEN_API_KEY"), 'secret': os.environ.get("WMILL_SECRET_KRAKEN_PRIVATE_KEY")})
    portfolio_pnl = 0.0
    
    for pos in open_positions:
        asset, direction, entry_price, size = pos
        asset_symbol = f"{asset}/USD" # Assumes USD pair
        try:
            current_price = exchange.fetch_ticker(asset_symbol)['last']
            pnl = (current_price - entry_price) * (size / entry_price) if direction.upper() == 'LONG' else (entry_price - current_price) * (size / entry_price)
            portfolio_pnl += pnl
            print(f"INFO: [PortfolioMonitor] PnL for {asset}: ${pnl:,.2f}")
        except Exception as e:
            print(f"ERROR: [PortfolioMonitor] Could not get price for {asset}. Error: {e}")
            continue
    
    print(f"INFO: [PortfolioMonitor] Total Portfolio PnL: ${portfolio_pnl:,.2f}")
    return {"total_pnl": portfolio_pnl, "tracked_positions": len(open_positions)}