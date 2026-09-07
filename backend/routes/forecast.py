"""
OceanEmbed Forecast API Routes
-------------------------------
GET  /api/v1/forecast/surface        — Gridded 2D surface parameters
GET  /api/v1/forecast/subsurface     — Depth profile with uncertainty bounds (Query params)
POST /api/v1/forecast/subsurface     — Depth profile with uncertainty bounds (JSON body)
GET  /api/v1/forecast/export/netcdf  — CF-compliant NetCDF binary export (.nc)
"""

from fastapi import APIRouter, Query, Response, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from backend.data_engine.surface import generate_surface_fields
from backend.data_engine.subsurface import generate_subsurface_profile
from backend.data_engine.netcdf_export import export_netcdf_bytes

router = APIRouter(prefix="/api/v1/forecast", tags=["Forecast"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class SubsurfaceRequest(BaseModel):
    """Request body for subsurface depth profile."""
    lat: float = Field(..., ge=5.0, le=25.0, description="Latitude (°N)")
    lon: float = Field(..., ge=60.0, le=95.0, description="Longitude (°E)")
    lead_time: int = Field(0, description="Forecast lead time in days (0, 1, 3, or 7)")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/surface")
async def get_surface_forecast(
    date: Optional[str] = Query(None, description="Date string YYYY-MM-DD (defaults to current)"),
    lead_time: int = Query(0, description="Forecast lead time in days (0, 1, 3, or 7)"),
    lat_min: Optional[float] = Query(None, ge=5.0, le=25.0),
    lat_max: Optional[float] = Query(None, ge=5.0, le=25.0),
    lon_min: Optional[float] = Query(None, ge=60.0, le=95.0),
    lon_max: Optional[float] = Query(None, ge=60.0, le=95.0),
):
    """
    Return gridded 2D surface fields (SST, SSS, SSH anomaly, winds, currents)
    for the North Indian Ocean domain.
    """
    data = generate_surface_fields(
        date_str=date,
        lat_min=lat_min if lat_min is not None else 5.0,
        lat_max=lat_max if lat_max is not None else 25.0,
        lon_min=lon_min if lon_min is not None else 60.0,
        lon_max=lon_max if lon_max is not None else 95.0,
    )
    data["lead_time"] = lead_time
    return data


@router.get("/subsurface")
async def get_subsurface_profile_get(
    lat: float = Query(..., ge=5.0, le=25.0, description="Latitude (°N)"),
    lon: float = Query(..., ge=60.0, le=95.0, description="Longitude (°E)"),
    lead_time: int = Query(0, description="Forecast lead time in days (0, 1, 3, or 7)"),
):
    """
    Return a depth-vs-temperature profile (0–1000 m) at the requested
    coordinate via GET query parameters with mean prediction and calibrated
    5th/95th percentile uncertainty bounds.
    """
    if lead_time not in (0, 1, 3, 7):
        raise HTTPException(status_code=400, detail="lead_time must be one of 0, 1, 3, or 7")

    return generate_subsurface_profile(lat=lat, lon=lon, lead_time=lead_time)


@router.post("/subsurface")
async def get_subsurface_profile_post(req: SubsurfaceRequest):
    """
    Return a depth-vs-temperature profile (0–1000 m) at the requested
    coordinate via POST JSON body with mean prediction and calibrated
    5th/95th percentile uncertainty bounds.
    """
    if req.lead_time not in (0, 1, 3, 7):
        raise HTTPException(status_code=400, detail="lead_time must be one of 0, 1, 3, or 7")

    return generate_subsurface_profile(
        lat=req.lat,
        lon=req.lon,
        lead_time=req.lead_time,
    )


@router.get("/export/netcdf")
async def download_forecast_netcdf(
    lead_time: int = Query(0, description="Forecast lead time in days (0, 1, 3, or 7)")
):
    """
    Generate and stream a CF-1.8 compliant binary NetCDF (.nc) file containing
    the full 3D subsurface temperature grid, surface fields, and TCHP hazard metrics.
    """
    if lead_time not in (0, 1, 3, 7):
        raise HTTPException(status_code=400, detail="lead_time must be one of 0, 1, 3, or 7")
        
    try:
        nc_bytes = export_netcdf_bytes(lead_time=lead_time)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate NetCDF file: {str(exc)}")
        
    filename = f"oceanembed_forecast_T{lead_time}d.nc"
    return Response(
        content=nc_bytes,
        media_type="application/x-netcdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-CF-Convention": "CF-1.8",
            "Content-Length": str(len(nc_bytes)),
        },
    )
