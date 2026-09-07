"""
OceanEmbed — FastAPI Application Entry Point
=============================================
Serves the REST API and static frontend files.

Run from the OceanEmbed root directory:
    uvicorn backend.app:app --reload --port 8000
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.routes import forecast, hazards, validation

# ---------------------------------------------------------------------------
# App initialisation
# ---------------------------------------------------------------------------
app = FastAPI(
    title="OceanEmbed API",
    description=(
        "Spatial-AI framework for subsurface ocean temperature forecasting "
        "with calibrated uncertainty bounds and TCHP hazard alerts over the "
        "North Indian Ocean."
    ),
    version="1.0.0",
)

# CORS — allow all origins during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# API routers
# ---------------------------------------------------------------------------
app.include_router(forecast.router)
app.include_router(hazards.router)
app.include_router(validation.router)

# ---------------------------------------------------------------------------
# Static frontend files
# ---------------------------------------------------------------------------
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/", include_in_schema=False)
async def serve_index():
    """Serve the main dashboard page."""
    return FileResponse(FRONTEND_DIR / "index.html")


# Mount static files (CSS, JS, images if any) — after the root route
app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR)),
    name="static",
)
