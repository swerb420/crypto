import os, json, psycopg2
from openai import OpenAI
from typing import Dict, Any

# Placeholder functions for the new checks
def check_legitimacy(catalyst_headline: str) -> int:
    # In a real system, this would use NewsAPI/GDELT to verify the news
    print(f"INFO: [Assess-AI] Verifying legitimacy of: {catalyst_headline[:30]}...")
    return 95 # Assume legitimate for now

def check_herd_behavior(conn, asset: str, direction: str) -> int:
    # In a real system, this queries the `recent_trades` table
    print(f"INFO: [Assess-AI] Checking for herd behavior on {asset}...")
    return 78 # Assume 78% of other wallets are doing the same

def check_historical_precedent(conn, trader_id: str, catalyst_type: str) -> int:
    # In a real system, this queries a historical outcomes table
    print(f"INFO: [Assess-AI] Checking historical win rate for {trader_id} on {catalyst_type} events...")
    return 85 # Assume this pattern has worked 85% of the time

def main(correlated_event: dict) -> dict:
    print("INFO: [Assess-AI] Starting historical assessment...")
    openai_key = os.environ.get("WMILL_SECRET_OPENAI_API_KEY")
    if not openai_key: raise ValueError("OpenAI Key is missing")

    client = OpenAI(api_key=openai_key)
    conn = psycopg2.connect(host='postgres', dbname='windmill', user='windmill', password='windmill')

    trade = correlated_event.get("trade", {})
    catalyst = correlated_event.get("catalyst", {})

    # --- Execute all checks ---
    legitimacy = check_legitimacy(catalyst.get("headline"))
    herd_index = check_herd_behavior(conn, trade.get("asset"), trade.get("direction"))
    win_rate = check_historical_precedent(conn, trade.get("trader_id"), "Partnership News")

    # --- Final AI Synthesis ---
    synthesis_prompt = f"""
    You are a master risk analyst. Synthesize the following data points into a final confidence score and a one-sentence summary.
    - Trade Details: {json.dumps(trade)}
    - Catalyst: {catalyst.get("headline")} (Legitimacy Score: {legitimacy}/100)
    - Herd Index (other smart money making similar trades): {herd_index}%
    - Historical Win Rate for this pattern: {win_rate}%

    Based on this, what is the final confidence score (0-100) and a summary for a Telegram alert?
    Respond ONLY with a valid JSON object with keys "confidence_score" and "summary".
    """

    response = client.chat.completions.create(
        model='gpt-4o',
        messages=[{'role':'system', 'content': "You only respond with perfect JSON."}, {'role':'user', 'content':synthesis_prompt}],
        response_format={"type": "json_object"}
    )
    ai_verdict = json.loads(response.choices[0].message.content)

    # --- Assemble the final, enriched signal ---
    enriched_signal = {
        "signal_id": f"{trade.get('trader_id', 'N/A')}-{trade.get('asset')}-{catalyst.get('timestamp')}",
        "trader_id": trade.get('trader_id'),
        "exchange": "Binance",
        "asset": trade.get("asset"),
        "direction": "LONG",
        "trade_size_usd": 100000,
        "leverage": 10,
        "catalyst_headline": catalyst.get("headline"),
        "legitimacy_score": legitimacy,
        "herd_index": herd_index,
        "historical_win_rate": win_rate,
        "safety_rating": "SAFE", # Placeholder for GoPlus integration
        "ai_confidence_score": ai_verdict.get("confidence_score"),
        "ai_summary": ai_verdict.get("summary")
    }

    # --- Save the final signal to the database ---
    with conn.cursor() as cur:
        # Note: The data types in the query must match the table schema exactly
        insert_query = """
        INSERT INTO public.trading_signals (signal_id, trader_id, exchange, asset, direction, trade_size_usd, leverage, catalyst_headline, legitimacy_score, herd_index, historical_win_rate, safety_rating, ai_confidence_score, ai_summary)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (signal_id) DO NOTHING;
        """
        cur.execute(insert_query, (
            enriched_signal['signal_id'], enriched_signal['trader_id'], enriched_signal['exchange'], enriched_signal['asset'],
            enriched_signal['direction'], enriched_signal['trade_size_usd'], enriched_signal['leverage'],
            enriched_signal['catalyst_headline'], enriched_signal['legitimacy_score'], enriched_signal['herd_index'],
            enriched_signal['historical_win_rate'], enriched_signal['safety_rating'], enriched_signal['ai_confidence_score'],
            enriched_signal['ai_summary']
        ))
    conn.commit()
    conn.close()

    print(f"INFO: [Assess-AI] Successfully assessed and saved signal {enriched_signal['signal_id']}")
    return enriched_signal