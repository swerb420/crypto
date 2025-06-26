import os, json, psycopg2
from typing import Dict, Any

def execute_db_query(query: str, params: tuple = None, fetch: str = None):
    conn = psycopg2.connect(host='postgres', dbname='windmill', user='windmill', password='windmill')
    with conn.cursor() as cur:
        cur.execute(query, params or ())
        if fetch == 'one':
            result = cur.fetchone()
        elif fetch == 'all':
            result = cur.fetchall()
        else:
            result = None
    conn.commit()
    conn.close()
    return result

def main(body: Dict[str, Any]) -> Dict[str, Any]:
    message = body.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "").strip()
    if not chat_id or not text: return {"status": "ignored"}

    response_text = "Unknown command. Try /addwallet, /removewallet, or /wallets."
    args = text.split()
    command = args[0]

    if command == "/addwallet" and len(args) == 3:
        address, chain = args[1], args[2]
        query = "INSERT INTO public.monitored_traders (identifier, exchange, description, is_active) VALUES (%s, %s, %s, %s) ON CONFLICT (identifier) DO NOTHING;"
        execute_db_query(query, (address, chain, f"Added via Telegram by {message.get('from',{}).get('username')}", True))
        response_text = f"✅ Wallet added: `{address}` on {chain}"
    
    elif command == "/removewallet" and len(args) == 2:
        address = args[1]
        query = "DELETE FROM public.monitored_traders WHERE identifier = %s;"
        execute_db_query(query, (address,))
        response_text = f"🗑️ Wallet removed: `{address}`"

    elif command == "/wallets":
        wallets = execute_db_query("SELECT identifier, exchange FROM public.monitored_traders WHERE is_active = TRUE;", fetch='all')
        if wallets:
            response_text = "📋 Tracked Wallets:\n" + "\n".join([f"`{w[0]}` ({w[1]})" for w in wallets])
        else:
            response_text = "📭 No wallets currently tracked."

    # Send response back to Telegram
    bot_token = os.environ.get("WMILL_SECRET_TELEGRAM_CRYPTEX_BOT_TOKEN")
    requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={"chat_id": chat_id, "text": response_text, "parse_mode": "Markdown"})
    return {"status": "ok"}