# File: s_telegram_alerter.py
# This script is now correctly linked to the cryptex-specific Telegram secrets.
import os
import requests

def main(signal: dict):
    if not signal:
        print("INFO: [Cryptex-Alerter] No new signal to alert on.")
        return {"status": "no_signal"}

    print("INFO: [Cryptex-Alerter] Sending high-confidence signal to Cryptex channel.")

    # --- UPDATED LINES ---
    bot_token = os.environ.get("WMILL_SECRET_TELEGRAM_CRYPTEX_BOT_TOKEN")
    chat_id = os.environ.get("WMILL_SECRET_TELEGRAM_CRYPTEX_CHAT_ID")
    # ---------------------

    if not all([bot_token, chat_id]):
        raise ValueError("Cryptex Telegram secrets are missing. Please set them in the Windmill UI.")

    message = f"🚨 **Cryptex Signal Detected** 🚨\n\n" \
              f"**Trader:** `{signal['trader_wallet']}` on *{signal['exchange']}*\n" \
              f"**Trade:** `{signal['direction']}` **{signal['asset']}**\n" \
              f"**Size:** `${signal['trade_size_usd']:,.2f}` at `{signal['leverage']}x` leverage\n\n" \
              f"**Catalyst:** {signal['catalyst_headline']}\n\n" \
              f"**Confidence:** `{signal['ai_confidence_score']}%`"

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}

    try:
        res = requests.post(url, json=payload, timeout=10)
        res.raise_for_status()
        print("INFO: [Cryptex-Alerter] Telegram alert sent successfully.")
        return {"status": "alert_sent"}
    except Exception as e:
        print(f"ERROR: [Cryptex-Alerter] Failed to send Telegram alert. Error: {e}")
        return {"status": "alert_failed"}