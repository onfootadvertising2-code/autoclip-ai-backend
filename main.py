from fastapi import FastAPI, UploadFile, File
import uuid
import os
import shutil

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
# 1. UPLOAD VIDEO
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

    return {"job_id": job_id, "status": "uploaded"}

# ------------------------
# 2. PROCESS PIPELINE (SIMULATED AI FOR NOW)
# ------------------------
@app.post("/process/{job_id}")
def process(job_id: str):

    if job_id not in JOBS:
        return {"error": "job not found"}

    JOBS[job_id]["status"] = "processing"

    # ------------------------
    # STEP 1: Simulated transcript
    # ------------------------
    transcript = [
        {"start": 0, "end": 20, "text": "Intro hook moment"},
        {"start": 20, "end": 45, "text": "Main talking point"},
        {"start": 45, "end": 70, "text": "Strong conclusion"}
    ]

    # ------------------------
    # STEP 2: Generate "clips"
    # ------------------------
    clips = []

    for i, seg in enumerate(transcript):

        clip_data = {
            "clip_id": f"{job_id}_clip_{i}",
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"],
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
# 3. GET STATUS
# ------------------------
@app.get("/status/{job_id}")
def status(job_id: str):

    return JOBS.get(job_id, {"error": "not found"})
