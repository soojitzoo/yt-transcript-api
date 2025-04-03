import re
import os
import requests
from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable

app = Flask(__name__)

def get_video_id(url_or_id):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url_or_id)
    return match.group(1) if match else url_or_id

@app.route("/")
def index():
    return "YouTube Transcript API via Smartproxy is live!"

@app.route("/get-transcript", methods=["POST"])
def get_transcript():
    data = request.json
    url_or_id = data.get("video_url", "")
    video_id = get_video_id(url_or_id)

    try:
        # Smartproxy config (from Render environment variables)
        smartproxy_url = "https://scraper-api.smartproxy.com/v2/scrape"
        smartproxy_auth = os.getenv("SMARTPROXY_AUTH")  # "Basic base64encodedstring"
        target_url = f"https://www.youtube.com/watch?v={video_id}"

        # Smartproxy request payload
        proxy_payload = {
            "url": target_url
        }

        headers = {
            "Accept": "application/json",
            "Authorization": smartproxy_auth,
            "Content-Type": "application/json"
        }

        proxy_response = requests.post(smartproxy_url, json=proxy_payload, headers=headers)

        if proxy_response.status_code != 200:
            return jsonify({
                "video_id": video_id,
                "error": f"Smartproxy failed with status {proxy_response.status_code}",
                "response": proxy_response.text
            }), 500

        # Proceed to transcript retrieval using original YouTubeTranscriptApi
        transcript = YouTubeTranscriptApi.list_transcripts(video_id)
        en_transcript = transcript.find_transcript(['en'])
        segments = en_transcript.fetch()
        flat_text = " ".join([seg['text'] for seg in segments])

        return jsonify({
            "video_id": video_id,
            "transcript_segments": segments,
            "full_transcript_text": flat_text,
            "language_available": True
        })

    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as e:
        return jsonify({
            "video_id": video_id,
            "error": str(e),
            "transcript_segments": [],
            "full_transcript_text": "",
            "language_available": False
        }), 400

app.run(host="0.0.0.0", port=8000)
