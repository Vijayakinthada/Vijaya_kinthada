from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.middleware.scoping import ScopingMiddleware
from src.routes import router

app = FastAPI(
    title="Gentle Activity & Wellness API",
    description=(
        "Standalone wellness-only activity API. "
        "For general wellness — not a substitute for professional medical care."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ScopingMiddleware)
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "module": "gentle-activity"}
