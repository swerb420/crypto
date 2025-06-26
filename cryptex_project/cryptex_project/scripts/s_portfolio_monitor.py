import psycopg2, ccxt, os
from typing import Dict, Any

def main() -> Dict[str, Any]:
    print("INFO: [PortfolioMonitor] Starting check of open positions...")
    conn = psycopg2.connect(host='postgres', dbname='windmill', user='windmill', password='windmill')

    open_positions = []
    with conn.cursor() as cur:
        # Assumes your 'trading_signals' table has a 'trade_status' column
        cur.execute("SELECT id, asset, direction, entry_price, trade_size_usd FROM public.trading_signals WHERE trade_status = 'OPEN';")
        open_positions = cur.fetchall()

    if not open_positions:
        print("INFO: [PortfolioMonitor] No open positions to monitor.")
        conn.close()
        return {"status": "no_open_positions"}

    print(f"INFO: [PortfolioMonitor] Found {len(open_positions)} open positions to track.")

    # Initialize one exchange to get prices from
    exchange = ccxt.binance()
    portfolio_pnl = 0.0

    for pos in open_positions:
        pos_id, asset, direction, entry_price, size = pos
        try:
            current_price = exchange.fetch_ticker(asset)['last']

            if direction.upper() == 'LONG':
                pnl = (current_price - entry_price) * (size / entry_price)
            else: # SHORT
                pnl = (entry_price - current_price) * (size / entry_price)

            portfolio_pnl += pnl
            print(f"INFO: [PortfolioMonitor] Position ID {pos_id} ({asset}) current PnL: ${pnl:,.2f}")

            # Here you could add logic for trailing stop-losses or profit-taking alerts

        except Exception as e:
            print(f"ERROR: [PortfolioMonitor] Could not get price for {asset}. Error: {e}")
            continue

    conn.close()
    print(f"INFO: [PortfolioMonitor] Total Portfolio PnL: ${portfolio_pnl:,.2f}")
    return {"total_pnl": portfolio_pnl, "tracked_positions": len(open_positions)}