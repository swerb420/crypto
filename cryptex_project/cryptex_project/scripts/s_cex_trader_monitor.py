import os, requests, json, psycopg2
from typing import List, Dict, Any

def main() -> List[str]:
    print("INFO: [CEX Monitor] Fetching CEX top trader positions...")
    conn = psycopg2.connect(host='postgres', dbname='windmill', user='windmill', password='windmill')
    # This is a conceptual endpoint. The real Binance Leaderboard API is needed here.
    url = f"https://fapi.binance.com/fapi/v1/leaderboard/getOtherPosition?encryptedUid=4258234B3958932C2556734194539825"
    inserted_assets = []
    try:
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        positions = res.json().get('data', {}).get('otherPositionRetList', [])
        print(f"INFO: [CEX Monitor] Found {len(positions)} open positions.")
        with conn.cursor() as cur:
            for pos in positions:
                asset = pos.get("symbol")
                trade_event = {"trader_id": "BinanceWhale1", "asset": asset, "raw_pos": pos}
                cur.execute(
                    "INSERT INTO public.recent_trades (trader_id, asset, raw_data) VALUES (%s, %s, %s)",
                    (trade_event['trader_id'], trade_event['asset'], json.dumps(trade_event['raw_pos']))
                )
                inserted_assets.append(asset)
        conn.commit()
    except Exception as e:
        print(f"ERROR: [CEX Monitor] Could not fetch CEX trades. Error: {e}")
    finally:
        conn.close()
    return inserted_assets