import re
import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Extract YouTube Video ID from full URL or short ID
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

    payload = {
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "render": False
    }

    headers = {
        "Accept": "application/json",
        "Authorization": os.getenv("SMARTPROXY_AUTH_HEADER"),
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            "https://scraper-api.smartproxy.com/v2/scrape",
            json=payload,
            headers=headers
        )
        result = response.json()

        if response.status_code != 200:
            return jsonify({
                "error": f"Smartproxy failed with status {response.status_code}",
                "response": result,
                "video_id": video_id
            }), 500

        return jsonify({
            "video_id": video_id,
            "raw_html": result.get("content", "No content returned"),
            "status": "success"
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "video_id": video_id,
            "status": "exception"
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

