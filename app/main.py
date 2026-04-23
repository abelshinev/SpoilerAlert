from fastapi import FastAPI
from app.routes import ingest, devices, items, feedback

app = FastAPI(title="Spoiler Alert Backend")

app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
app.include_router(devices.router, prefix="/devices", tags=["devices"])
app.include_router(items.router, prefix="/items", tags=["items"])
app.include_router(feedback.router, prefix="/feedback", tags=["feedback"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
