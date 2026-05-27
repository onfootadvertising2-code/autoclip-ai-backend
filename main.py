@app.post("/process/{job_id}")
def process(job_id: str):

    import whisper

    if job_id not in JOBS:
        return {"error": "job not found"}

    JOBS[job_id]["status"] = "processing"

    video_path = JOBS[job_id]["input"]

    # ------------------------
    # LOAD WHISPER MODEL
    # ------------------------
    model = whisper.load_model("base")

    # ------------------------
    # TRANSCRIBE VIDEO
    # ------------------------
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
