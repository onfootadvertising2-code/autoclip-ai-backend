from fastapi import FastAPI, UploadFile, File
import uuid
import os

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def home():
    return {"status": "Autoclip AI backend running"}

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):

    job_id = str(uuid.uuid4())

    file_path = f"{UPLOAD_DIR}/{job_id}.mp4"

    with open(file_path, "wb") as f:
        f.write(await file.read())

    return {
        "message": "video uploaded",
        "job_id": job_id,
        "file_path": file_path
    }
