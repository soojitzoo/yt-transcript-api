import re
import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

def get_video_id(url_or_id):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url_or_id)
    return match.group(1) if match else url_or_id

@app.route("/")
def index():
    return "YouTube Transcript API is live!"

@app.route("/get-transcript", methods=["POST"])
def get_transcript():
    data = request.json
    url_or_id = data.get("video_url", "")
    video_id = get_video_id(url_or_id)

    try:
        # Smartproxy auth
        auth_header = os.getenv("SMARTPROXY_AUTH_HEADER")

        if not auth_header:
            return jsonify({
                "error": "Missing Smartproxy credentials in environment variables.",
                "video_id": video_id
            }), 500

        smartproxy_payload = {
            "url": f"https://www.youtube.com/watch?v={video_id}"
        }

        response = requests.post(
            "https://scraper-api.smartproxy.com/v2/scrape",
            headers={
                "Accept": "application/json",
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/json"
            },
            json=smartproxy_payload
        )

        response_data = response.json()

        if response.status_code != 200:
            return jsonify({
                "error": f"Smartproxy failed with status {response.status_code}",
                "response": response_data,
                "video_id": video_id
            }), 500

        return jsonify({
            "video_id": video_id,
            "scraped_html": response_data,
            "status": "Smartproxy success"
        })

    except Exception as e:
        return jsonify({
            "video_id": video_id,
            "error": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)


