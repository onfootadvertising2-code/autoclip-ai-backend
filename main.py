from fastapi import FastAPI, UploadFile, File
import uuid
import os
import shutil
import whisper

app = FastAPI()

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

JOBS = {}

@app.get("/")
def home():
    return {"status": "Autoclip AI pipeline running"}

# ------------------------
# UPLOAD VIDEO
# ------------------------
@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):

    job_id = str(uuid.uuid4())

    file_path = f"{UPLOAD_DIR}/{job_id}.mp4"

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    JOBS[job_id] = {
        "status": "uploaded",
        "input": file_path,
        "clips": []
    }

    return {
        "job_id": job_id,
        "status": "uploaded"
    }

# ------------------------
# PROCESS VIDEO WITH WHISPER
# ------------------------
@app.post("/process/{job_id}")
def process(job_id: str):

    if job_id not in JOBS:
        return {"error": "job not found"}

    JOBS[job_id]["status"] = "processing"

    video_path = JOBS[job_id]["input"]

    # Load smaller Whisper model for Render stability
    model = whisper.load_model("tiny")

    # Transcribe video
    result = model.transcribe(video_path)

    segments = result["segments"]

    clips = []

    for i, seg in enumerate(segments):

        clip_data = {
            "clip_id": f"{job_id}_clip_{i}",
            "start": round(seg["start"], 2),
            "end": round(seg["end"], 2),
            "text": seg["text"].strip(),
            "output": f"/outputs/{job_id}_clip_{i}.mp4"
        }

        clips.append(clip_data)

    JOBS[job_id]["clips"] = clips
    JOBS[job_id]["status"] = "done"

    return {
        "job_id": job_id,
        "status": "done",
        "clips": clips
    }

# ------------------------
# CHECK STATUS
# ------------------------
@app.get("/status/{job_id}")
def status(job_id: str):

    return JOBS.get(job_id, {"error": "not found"})
