from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Autoclip AI backend running"}
