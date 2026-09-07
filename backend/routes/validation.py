"""
OceanEmbed Validation API Routes
----------------------------------
GET /api/v1/validation/argo — Simulated Argo Float observation comparisons
"""

from fastapi import APIRouter

from backend.data_engine.validation import generate_argo_validation

router = APIRouter(prefix="/api/v1/validation", tags=["Validation"])


@router.get("/argo")
async def get_argo_validation():
    """
    Return simulated Argo Float observations compared against
    model predictions, including per-float and aggregate RMSE / MAE.
    """
    data = generate_argo_validation()
    return data
