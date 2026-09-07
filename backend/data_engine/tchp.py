"""
OceanEmbed Tropical Cyclone Heat Potential (TCHP) Calculator
============================================================
Derives TCHP = C_p * ∫_0^{d_26} ρ * (T(z) - 26) dz (in kJ/cm²)
and identifies Rapid Intensification Risk zones (> 50 kJ/cm²).
"""

import numpy as np
from typing import Dict, Any, List

from backend.config import LAT_MIN, LAT_MAX, LON_MIN, LON_MAX, CP, RHO, TCHP_THRESHOLD, T_REF
from backend.data_engine.subsurface import generate_subsurface_profile


def integrate_trapezoid(y: np.ndarray, x: np.ndarray) -> float:
    """Trapezoidal integration compatible with NumPy 1.x and 2.x."""
    if hasattr(np, "trapezoid"):
        return float(np.trapezoid(y, x))
    return float(np.trapz(y, x))


def compute_tchp_at_point(lat: float, lon: float, lead_time: int = 0) -> Dict[str, Any]:
    """
    Compute TCHP at a specific point.
    Integrates from surface (z=0) down to the 26 °C isotherm depth (d26).
    """
    profile_data = generate_subsurface_profile(lat, lon, lead_time)
    d26 = profile_data["d26"]
    mld = profile_data["mld"]
    sst = profile_data["sst"]
    
    tchp = 0.0
    if d26 > 1.0:
        # Fine vertical resolution (1m) for numerical integration
        fine_z = np.linspace(0.0, d26, max(int(d26) + 1, 20))
        
        is_bob = (lon > 80.0) and (lat < 20.0)
        z_thermo = 88.0 if is_bob else 108.0
        delta = 38.0 if is_bob else 42.0
        t_deep = 5.2
        
        fine_temp = t_deep + (sst - t_deep) * 0.5 * (1.0 - np.tanh((fine_z - z_thermo) / delta))
        integrand = np.maximum(fine_temp - T_REF, 0.0)
        integral_val = integrate_trapezoid(integrand, fine_z)
        
        # Scale: J/m² to kJ/cm² via 1e-7 factor
        tchp = (CP * RHO / 1e7) * integral_val
        
    # Categorize hazard severity
    if tchp < 30.0:
        severity = "Low"
        risk_status = "Sub-Critical Heat Content"
    elif tchp < 50.0:
        severity = "Moderate"
        risk_status = "Elevated Cyclone Energy"
    elif tchp < 80.0:
        severity = "High"
        risk_status = "Rapid Intensification Risk"
    else:
        severity = "Critical"
        risk_status = "Severe Rapid Intensification Risk"
        
    return {
        "tchp": float(round(tchp, 2)),
        "mld": float(round(mld, 1)),
        "d26": float(round(d26, 1)),
        "sst": float(round(sst, 2)),
        "severity": severity,
        "risk_status": risk_status,
        "is_rapid_intensification_risk": bool(tchp >= TCHP_THRESHOLD)
    }


def get_region_label(lat: float, lon: float) -> str:
    """Classify sub-basin region for North Indian Ocean."""
    if lon >= 80.0:
        if lat >= 18.0:
            return "Northern Bay of Bengal (Bengal Basin)"
        elif lat >= 12.0:
            return "Central Bay of Bengal (Warm Core Pool)"
        else:
            return "South Bay of Bengal / Andaman Sea"
    else:
        if lat >= 18.0:
            return "Northern Arabian Sea (Oman / Gujarat Coast)"
        elif lat >= 12.0:
            return "Central Arabian Sea Open Waters"
        else:
            return "South-Eastern Arabian Sea (Mini Warm Pool)"


def compute_tchp_grid(lead_time: int = 0) -> Dict[str, Any]:
    """
    Compute TCHP spatial grid and return flagged high-risk zones.
    Evaluated over a regular 2.0° grid for responsive map rendering.
    """
    grid_step = 2.0
    coarse_lats = np.arange(LAT_MIN, LAT_MAX + 0.1, grid_step)
    coarse_lons = np.arange(LON_MIN, LON_MAX + 0.1, grid_step)
    
    n_lat = len(coarse_lats)
    n_lon = len(coarse_lons)
    
    tchp_grid = np.zeros((n_lat, n_lon))
    mld_grid = np.zeros((n_lat, n_lon))
    d26_grid = np.zeros((n_lat, n_lon))
    
    high_risk_zones: List[Dict[str, Any]] = []
    
    for i, lat in enumerate(coarse_lats):
        for j, lon in enumerate(coarse_lons):
            # Exclude land coordinates of Indian subcontinent
            if 10.0 < lat < 24.0 and 73.0 < lon < 84.0 and not (lat < 14.0 and lon > 80.0):
                # Central land area
                continue
                
            res = compute_tchp_at_point(float(lat), float(lon), lead_time)
            tchp_val = res["tchp"]
            mld_val = res["mld"]
            d26_val = res["d26"]
            
            tchp_grid[i, j] = tchp_val
            mld_grid[i, j] = mld_val
            d26_grid[i, j] = d26_val
            
            if tchp_val >= TCHP_THRESHOLD:
                high_risk_zones.append({
                    "lat": float(round(lat, 2)),
                    "lon": float(round(lon, 2)),
                    "tchp_value": float(round(tchp_val, 1)),
                    "mld": float(round(mld_val, 1)),
                    "d26": float(round(d26_val, 1)),
                    "severity": res["severity"],
                    "risk_status": res["risk_status"],
                    "label": get_region_label(lat, lon)
                })
                
    # Sort risk zones descending by TCHP value
    high_risk_zones.sort(key=lambda x: x["tchp_value"], reverse=True)
    
    return {
        "lats": [round(float(x), 2) for x in coarse_lats],
        "lons": [round(float(x), 2) for x in coarse_lons],
        "tchp": [[round(float(v), 2) for v in row] for row in tchp_grid],
        "mld": [[round(float(v), 1) for v in row] for row in mld_grid],
        "d26": [[round(float(v), 1) for v in row] for row in d26_grid],
        "high_risk_threshold": TCHP_THRESHOLD,
        "high_risk_zones": high_risk_zones,
        "lead_time": lead_time
    }
