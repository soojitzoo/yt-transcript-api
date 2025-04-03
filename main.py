from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
import re
import os

app = Flask(__name__)

def get_video_id(url_or_id):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url_or_id)
    return match.group(1) if match else url_or_id

@app.route("/")
def index():
    return "YouTube Transcript API is live with Smartproxy!"

@app.route("/get-transcript", methods=["POST"])
def get_transcript():
    data = request.json
    url_or_id = data.get("video_url", "")
    video_id = get_video_id(url_or_id)

    try:
        # Load Smartproxy credentials from environment
        proxy_user = os.environ.get("SMARTPROXY_USERNAME")
        proxy_pass = os.environ.get("SMARTPROXY_PASSWORD")
        proxy_host = os.environ.get("SMARTPROXY_HOST")
        proxy_port = os.environ.get("SMARTPROXY_PORT")

        proxy_url = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
        proxies = {
            "http": proxy_url,
            "https": proxy_url
        }

        # Use proxy when calling the YouTube Transcript API
        transcript = YouTubeTranscriptApi.list_transcripts(video_id, proxies=proxies)
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

    except Exception as e:
        return jsonify({
            "video_id": video_id,
            "error": f"Unhandled error: {str(e)}"
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

