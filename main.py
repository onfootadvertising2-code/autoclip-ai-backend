from fastapi import FastAPI, UploadFile, File
import uuid
import os
import shutil
import json
import redis

app = FastAPI()

UPLOAD_DIR = "uploads"
JOB_FILE = "jobs.json"

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ----------------------------
# REDIS (QUEUE SYSTEM)
# ----------------------------
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

QUEUE_NAME = "autoclip_jobs"


# ----------------------------
# LOCAL JOB STORE (fallback)
# ----------------------------
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


# ----------------------------
# HEALTH CHECK
# ----------------------------
@app.get("/")
def home():
    return {"status": "Autoclip AI production API running"}


# ----------------------------
# UPLOAD VIDEO → CREATE JOB
# ----------------------------
@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):

    global JOBS

    job_id = str(uuid.uuid4())
    file_path = f"{UPLOAD_DIR}/{job_id}.mp4"

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    job_data = {
        "job_id": job_id,
        "status": "queued",
        "input": file_path
    }

    JOBS[job_id] = job_data
    save_jobs(JOBS)

    # PUSH TO REDIS QUEUE (worker will pick this up later)
    r.lpush(QUEUE_NAME, json.dumps(job_data))

    return {
        "job_id": job_id,
        "status": "queued"
    }


# ----------------------------
# GET JOB STATUS
# ----------------------------
@app.get("/status/{job_id}")
def status(job_id: str):

    global JOBS
    JOBS = load_jobs()

    return JOBS.get(job_id, {"error": "not found"})


# ----------------------------
# WORKER UPDATE ENDPOINT (used by backend worker later)
# ----------------------------
@app.post("/update/{job_id}")
def update_job(job_id: str, data: dict):

    global JOBS
    JOBS = load_jobs()

    if job_id not in JOBS:
        return {"error": "job not found"}

    JOBS[job_id].update(data)
    save_jobs(JOBS)

    return {"status": "updated", "job_id": job_id}
