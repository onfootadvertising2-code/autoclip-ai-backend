import redis
import json
import time
import whisper
import subprocess
import os
import requests

# -----------------------
# CONFIG
# -----------------------
REDIS_HOST = "localhost"
QUEUE_NAME = "autoclip_jobs"
API_URL = "https://autoclip-ai-backend.onrender.com"

r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

model = whisper.load_model("tiny")

print("🔥 Worker started - waiting for jobs...")


# -----------------------
# MAIN LOOP
# -----------------------
while True:

    try:
        job_data = r.brpop(QUEUE_NAME)

        if not job_data:
            continue

        job = json.loads(job_data[1])
        job_id = job["job_id"]
        video_path = job["input"]

        print(f"🎬 Processing job: {job_id}")

        # -----------------------
        # UPDATE STATUS
        # -----------------------
        requests.post(f"{API_URL}/update/{job_id}", json={
            "status": "processing"
        })

        # -----------------------
        # WHISPER TRANSCRIPTION
        # -----------------------
        result = model.transcribe(video_path)

        segments = result["segments"]

        clips = []

        for i, seg in enumerate(segments):

            start = seg["start"]
            end = seg["end"]

            output_file = f"clip_{job_id}_{i}.mp4"

            # -----------------------
            # FFmpeg clip creation
            # -----------------------
            cmd = [
                "ffmpeg",
                "-y",
                "-i", video_path,
                "-ss", str(start),
                "-to", str(end),
                "-c", "copy",
                output_file
            ]

            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            clips.append({
                "clip_id": f"{job_id}_clip_{i}",
                "start": start,
                "end": end,
                "text": seg["text"].strip(),
                "file": output_file
            })

        # -----------------------
        # SEND RESULTS BACK TO API
        # -----------------------
        requests.post(f"{API_URL}/update/{job_id}", json={
            "status": "done",
            "clips": clips
        })

        print(f"✅ Job complete: {job_id}")

    except Exception as e:

        print("❌ Error:", str(e))
        time.sleep(2)
