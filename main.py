import re
import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Extracts YouTube video ID from full URL or short ID
def get_video_id(url_or_id):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url_or_id)
    return match.group(1) if match else url_or_id

@app.route("/")
def index():
    return "✅ YouTube Transcript API via Smartproxy is live!"

@app.route("/get-transcript", methods=["POST"])
def get_transcript():
    data = request.json
    url_or_id = data.get("video_url", "")
    if not url_or_id:
        return jsonify({
            "error": "Missing 'video_url' in request body."
        }), 400

    video_id = get_video_id(url_or_id)

    # Auth: Get Smartproxy credentials from environment
    auth_header = os.getenv("SMARTPROXY_AUTH_HEADER")
    if not auth_header:
        return jsonify({
            "error": "Missing SMARTPROXY_AUTH_HEADER in environment variables.",
            "video_id": video_id
        }), 500

    # Payload sent to Smartproxy scraping API
    smartproxy_payload = {
        "url": f"https://www.youtube.com/watch?v={video_id}"
    }

    try:
        response = requests.post(
            "https://scraper-api.smartproxy.com/v2/scrape",
            headers={
                "Accept": "application/json",
                "Authorization": auth_header,
                "Content-Type": "application/json"
            },
            json=smartproxy_payload,
            timeout=30
        )

        # Try to parse the response as JSON (Smartproxy sometimes fails cleanly)
        try:
            response_data = response.json()
        except Exception:
            response_data = {"raw_text": response.text}

        if response.status_code != 200:
            return jsonify({
                "error": f"Smartproxy returned status {response.status_code}",
                "response": response_data,
                "video_id": video_id
            }), response.status_code

        return jsonify({
            "status": "Smartproxy success",
            "video_id": video_id,
            "raw_html": response_data.get("content") or response_data
        })

    except requests.exceptions.RequestException as e:
        return jsonify({
            "video_id": video_id,
            "error": f"Request to Smartproxy failed: {str(e)}"
        }), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)


