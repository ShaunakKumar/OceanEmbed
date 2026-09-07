"""
OceanEmbed Hazard API Routes
------------------------------
GET /api/v1/hazards/tchp — Spatial TCHP grid with high-risk zone alerts
"""

from fastapi import APIRouter, Query

from backend.data_engine.tchp import compute_tchp_grid

router = APIRouter(prefix="/api/v1/hazards", tags=["Hazards"])


@router.get("/tchp")
async def get_tchp_hazards(
    lead_time: int = Query(0, description="Forecast lead time in days (0, 1, 3, or 7)"),
):
    """
    Return a spatial grid of Tropical Cyclone Heat Potential (kJ/cm²)
    and Mixed Layer Depth (m), along with flagged high-risk rapid-
    intensification zones.
    """
    if lead_time not in (0, 1, 3, 7):
        return {"error": "lead_time must be one of 0, 1, 3, 7"}

    data = compute_tchp_grid(lead_time=lead_time)
    return data
