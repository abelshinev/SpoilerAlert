from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import ingest, devices, items, feedback, api
from init_db import main as init_db_main
from fastapi.staticfiles import StaticFiles


app = FastAPI(title="Spoiler Alert Backend")

# Enable CORS for demo purposes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers - paths are explicit in the route files
app.include_router(ingest.router, tags=["ingest"])
app.include_router(devices.router, tags=["devices"])
app.include_router(items.router, tags=["items"])
app.include_router(feedback.router, tags=["feedback"])
app.include_router(api.router)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.on_event("startup")
async def startup_event():
    """Initialize the database when the server starts."""
    await init_db_main()

@app.get("/")
async def root():
    """Base health check."""
    return {"status": "ok"}
