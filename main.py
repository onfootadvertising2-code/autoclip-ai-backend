from fastapi import FastAPI, UploadFile, File
import uuid
import os
import shutil
import json

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
# PROCESS (SAFE VERSION - NO CRASHES)
# ------------------------
@app.post("/process/{job_id}")
def process(job_id: str):

    global JOBS
    JOBS = load_jobs()

    if job_id not in JOBS:
        return {"error": "job not found"}

    JOBS[job_id]["status"] = "processing"
    save_jobs(JOBS)

    # SAFE MODE (prevents Render 502 crashes)
    return {
        "job_id": job_id,
        "status": "processing_started",
        "note": "AI processing is currently disabled for stability"
    }


# ------------------------
# STATUS CHECK
# ------------------------
@app.get("/status/{job_id}")
def status(job_id: str):

    global JOBS
    JOBS = load_jobs()

    return JOBS.get(job_id, {"error": "not found"})
