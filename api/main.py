from fastapi import FastAPI, UploadFile, File
from uuid import uuid4
import shutil
import os

from worker.tasks import transcribe  # Will exist after next step

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from WSL FastAPI!"}

@app.post("/jobs")
async def create_job(file: UploadFile = File(...)):
    job_id = str(uuid4())
    upload_path = f"uploads/{job_id}_{file.filename}"

    os.makedirs("uploads", exist_ok=True)

    with open(upload_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    transcribe.delay(job_id, upload_path)

    return {"job_id": job_id}
