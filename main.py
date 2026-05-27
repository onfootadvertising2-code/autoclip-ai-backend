from fastapi import FastAPI, UploadFile, File
import uuid
import os
import shutil
import json
import whisper

app = FastAPI()

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
JOB_FILE = "jobs.json"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ------------------------
# JOB STORAGE (PERSISTENT)
# ------------------------
def load_jobs():
    try:
        with open(JOB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_jobs(jobs):
    with open(JOB_FILE, "w") as f:
        json.dump(jobs, f)


JOBS = load_jobs()


# ------------------------
# HEALTH CHECK
# ------------------------
@app.get("/")
def home():
    return {"status": "Autoclip AI pipeline running"}


# ------------------------
# UPLOAD VIDEO
# ------------------------
@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):

    global JOBS

    job_id = str(uuid.uuid4())
    file_path = f"{UPLOAD_DIR}/{job_id}.mp4"

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    JOBS[job_id] = {
        "status": "uploaded",
        "input": file_path,
        "clips": []
    }

    save_jobs(JOBS)

    return {
        "job_id": job_id,
        "status": "uploaded"
    }


# ------------------------
# PROCESS VIDEO (WHISPER SAFE)
# ------------------------
@app.post("/process/{job_id}")
def process(job_id: str):

    global JOBS
    JOBS = load_jobs()

    if job_id not in JOBS:
        return {"error": "job not found"}

    JOBS[job_id]["status"] = "processing"
    save_jobs(JOBS)

    video_path = JOBS[job_id]["input"]

    try:
        # Load lightweight model (Render-safe)
        model = whisper.load_model("tiny")

        result = model.transcribe(video_path)
        segments = result["segments"]

        clips = []

        for i, seg in enumerate(segments):

            clips.append({
                "clip_id": f"{job_id}_clip_{i}",
                "start": round(seg["start"], 2),
                "end": round(seg["end"], 2),
                "text": seg["text"].strip()
            })

        JOBS[job_id]["clips"] = clips
        JOBS[job_id]["status"] = "done"
        save_jobs(JOBS)

        return {
            "job_id": job_id,
            "status": "done",
            "clips": clips
        }

    except Exception as e:
        JOBS[job_id]["status"] = "error"
        save_jobs(JOBS)

        return {
            "job_id": job_id,
            "status": "error",
            "message": str(e)
        }


# ------------------------
# STATUS CHECK
# ------------------------
@app.get("/status/{job_id}")
def status(job_id: str):

    global JOBS
    JOBS = load_jobs()

    return JOBS.get(job_id, {"error": "not found"})
