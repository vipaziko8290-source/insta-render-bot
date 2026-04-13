import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "")
IG_ACCOUNT_ID = os.getenv("IG_ACCOUNT_ID", "")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
TRIGGER_WORD = os.getenv("TRIGGER_WORD", "prompt").lower()
TELEGRAM_LINK = os.getenv("TELEGRAM_LINK", "https://t.me/your_link")

GRAPH_VERSION = "v25.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"


def send_private_reply(comment_id: str, text: str):
    if not IG_ACCOUNT_ID or not INSTAGRAM_ACCESS_TOKEN:
        print("IG_ACCOUNT_ID yoki INSTAGRAM_ACCESS_TOKEN yo'q.")
        return None

    url = f"{GRAPH_BASE}/{IG_ACCOUNT_ID}/messages"
    payload = {
        "recipient": {
            "comment_id": comment_id
        },
        "message": {
            "text": text
        },
        "messaging_type": "RESPONSE"
    }

    resp = requests.post(
        url,
        params={"access_token": INSTAGRAM_ACCESS_TOKEN},
        json=payload,
        timeout=30
    )
    print("META STATUS:", resp.status_code)
    print("META BODY:", resp.text)
    return resp


@app.get("/")
def home():
    return "Instagram Render bot ishlayapti.", 200


@app.get("/callback")
def callback():
    full_url = request.url
    return f"Callback OK<br><br>{full_url}", 200


@app.get("/webhook")
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge or "", 200

    return "Verification failed", 403


@app.post("/webhook")
def receive_webhook():
    data = request.get_json(silent=True) or {}
    print("WEBHOOK:", json.dumps(data, ensure_ascii=False))

    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") == "comments":
                value = change.get("value", {})
                comment_id = value.get("id")
                text = (value.get("text") or "").strip().lower()

                if comment_id and text == TRIGGER_WORD:
                    reply_text = f"Mana Telegram havola: {TELEGRAM_LINK}"
                    send_private_reply(comment_id, reply_text)

    return jsonify({"ok": True}), 200


@app.get("/deauthorize")
@app.post("/deauthorize")
def deauthorize():
    return jsonify({"status": "ok"}), 200


@app.get("/data-deletion")
@app.post("/data-deletion")
def data_deletion():
    return jsonify({
        "status": "received",
        "message": "Data deletion request endpoint is working."
    }), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
