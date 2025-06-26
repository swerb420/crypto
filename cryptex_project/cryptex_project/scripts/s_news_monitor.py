import os, requests, json, psycopg2
from typing import List, Dict, Any

def main() -> List[str]:
    print("INFO: [News Monitor] Fetching latest news catalysts...")
    conn = psycopg2.connect(host='postgres', dbname='windmill', user='windmill', password='windmill')
    news_api_key = os.environ.get("WMILL_SECRET_NEWSAPI_KEY")
    if not news_api_key: raise ValueError("Secret 'NEWSAPI_KEY' is missing.")
    url = f"https://newsapi.org/v2/everything?q=crypto&language=en&sortBy=publishedAt&pageSize=20&apiKey={news_api_key}"
    inserted_assets = []
    try:
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        articles = res.json().get("articles", [])
        with conn.cursor() as cur:
            for article in articles:
                # In a real system, an AI would extract asset tags from the headline
                asset_tags = ["BTC", "ETH"] 
                cur.execute(
                    "INSERT INTO public.recent_catalysts (headline, source, asset_tags, raw_data) VALUES (%s, %s, %s, %s)",
                    (article.get('title'), article.get('source', {}).get('name'), asset_tags, json.dumps(article))
                )
                inserted_assets.extend(asset_tags)
        conn.commit()
    except Exception as e:
        print(f"ERROR: [News Monitor] Could not fetch news. Error: {e}")
    finally:
        conn.close()
    return list(set(inserted_assets)) # Return unique list of assets found