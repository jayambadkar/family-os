from flask import Flask, request, abort
import requests, os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

load_dotenv()
app = Flask(__name__)

FOUNDRY_URL = os.getenv("FOUNDRY_URL")
FOUNDRY_TOKEN = os.getenv("FOUNDRY_TOKEN")

@app.route("/tg-hook", methods=["POST"])
def tg_hook():
    update = request.get_json(force=True)
    if not update:
        abort(400)

    # Wrap in Foundry’s “records” envelope:
    payload = {"records": [update]}

    # Forward to Foundry with Bearer auth:
    resp = requests.post(
        FOUNDRY_URL,
        json=payload,
        headers={
            "Authorization": f"Bearer {FOUNDRY_TOKEN}",
            "Content-Type": "application/json"
        },
        timeout=5
    )
    # You may choose to log resp.status_code / resp.text here.
    if resp.ok:
        logger.info(f"Processed payload with result {resp.status_code}: {resp.text}")
    else:
        logger.error(f"Issue processing payload. Result {resp.status_code}: {resp.text}")

    # Always return 200 to Telegram so it won’t retry
    return ("", 200)

@app.route("/", methods=["GET"])
def get():
    return("OK", 400)

if __name__ == "__main__":
    app.run()

# command for updating Telegram URL
"""
curl -X POST https://api.telegram.org/bot<bot-token>/setWebhook \       ─╯
     -F "url=<ngrok-url>/tg-hook"
"""
