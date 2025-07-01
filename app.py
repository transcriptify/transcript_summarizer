from flask import Flask, render_template, request
from youtube_transcript_api import YouTubeTranscriptApi
from pytube import YouTube
import openai
import os
import re

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_video_id(url):
    match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
    if match:
        return match.group(1)
    return None

def fetch_transcript(video_id):
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    return " ".join([entry["text"] for entry in transcript])

def fetch_video_metadata(video_url):
    yt = YouTube(video_url)
    return yt.title, yt.description

def summarize_text(title, description, transcript):
    prompt = f"""
Summarize the following YouTube video content in clear, structured English using bullet points.  
Do not use emojis. Focus on the key points and insights.  
Include relevant context from the video title and description.

Title: {title}

Description: {description}

Transcript:
{transcript}

Summary:
"""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0.5
    )
    return response.choices[0].message.content.strip()

@app.route("/", methods=["GET", "POST"])
def index():
    summary = None
    error = None
    if request.method == "POST":
        video_url = request.form.get("video_url")
        if not video_url:
            error = "Please provide a YouTube URL."
            return render_template("index.html", summary=summary, error=error)
        video_id = get_video_id(video_url)
        if not video_id:
            error = "Invalid YouTube URL."
            return render_template("index.html", summary=summary, error=error)
        try:
            transcript = fetch_transcript(video_id)
            title, description = fetch_video_metadata(video_url)
            summary = summarize_text(title, description, transcript)
        except Exception as e:
            error = f"Error: {str(e)}"
    return render_template("index.html", summary=summary, error=error)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)


