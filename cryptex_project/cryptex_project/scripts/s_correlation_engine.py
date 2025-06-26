import psycopg2, json
from typing import List

def main(assets_to_check: List[str]):
    print(f"INFO: [Correlation Engine] Checking for correlations for assets: {assets_to_check}")
    if not assets_to_check: return {"status": "no_assets_to_check"}
    
    conn = psycopg2.connect(host='postgres', dbname='windmill', user='windmill', password='windmill')
    signals = []
    with conn.cursor() as cur:
        for asset in assets_to_check:
            # This is a simplified correlation logic. A real one would be more complex.
            # Find a trade and a catalyst for the same asset within the last 5 minutes.
            query = """
            SELECT t.raw_data, c.raw_data FROM recent_trades t JOIN recent_catalysts c ON c.asset_tags @> ARRAY[%s]
            WHERE t.asset = %s AND t.ingested_at > (NOW() - INTERVAL '5 minutes') 
            AND c.ingested_at > (NOW() - INTERVAL '5 minutes');
            """
            cur.execute(query, (asset, asset))
            results = cur.fetchall()
            if results:
                print(f"SUCCESS: [Correlation Engine] Found {len(results)} correlated event(s) for {asset}!")
                for res in results:
                    # In a real system, you would pass this to the AI analysis and alerting flows
                    signals.append({"trade": res[0], "catalyst": res[1]})
    conn.close()
    
    # For now, we just return the found signals. Later, this will call other flows.
    return signals