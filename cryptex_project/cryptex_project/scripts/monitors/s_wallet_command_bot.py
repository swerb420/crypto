import os, json, psycopg2
from typing import Dict, Any

# This script now reads and writes to your Postgres database.
def main(body: Dict[str, Any]) -> Dict[str, Any]:
    message = body.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "").strip()
    if not chat_id or not text: return {"status": "ignored"}

    response_text = "Unknown command. Use /addwallet, /removewallet, /listwallets."
    args = text.split()
    command = args[0]
    conn = psycopg2.connect(host='postgres', dbname='windmill', user='windmill', password='windmill')

    try:
        with conn.cursor() as cur:
            if command == "/addwallet" and len(args) == 4:
                address, chain, desc = args[1], args[2], args[3]
                cur.execute("INSERT INTO public.monitored_traders (identifier, exchange, description) VALUES (%s, %s, %s) ON CONFLICT (identifier) DO NOTHING;", (address, chain, desc))
                conn.commit()
                response_text = f"✅ Wallet added: `{address}`"
            
            elif command == "/removewallet" and len(args) == 2:
                address = args[1]
                cur.execute("DELETE FROM public.monitored_traders WHERE identifier = %s;", (address,))
                conn.commit()
                response_text = f"🗑️ Wallet removed: `{address}`"

            elif command == "/listwallets":
                cur.execute("SELECT identifier, exchange, description FROM public.monitored_traders WHERE is_active = TRUE;")
                wallets = cur.fetchall()
                if wallets:
                    response_text = "📋 Tracked Wallets:\n" + "\n".join([f"`{w[0]}` ({w[1]}) - {w[2]}" for w in wallets])
                else:
                    response_text = "📭 No wallets currently tracked."
    except Exception as e:
        response_text = f"ERROR: {e}"
    finally:
        conn.close()

    bot_token = os.environ.get("WMILL_SECRET_TELEGRAM_CRYPTEX_BOT_TOKEN")
    requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={"chat_id": chat_id, "text": response_text, "parse_mode": "Markdown"})
    return {"status": "ok"}