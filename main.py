from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
import re

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

