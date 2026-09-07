import numpy as np
from scipy.ndimage import gaussian_filter
import hashlib
from typing import Dict, Any, Optional

from backend.config import LAT_MIN, LAT_MAX, LON_MIN, LON_MAX, GRID_RES, LATS, LONS

def generate_surface_fields(date_str: Optional[str] = None, 
                          lat_min: float = LAT_MIN, lat_max: float = LAT_MAX, 
                          lon_min: float = LON_MIN, lon_max: float = LON_MAX) -> Dict[str, Any]:
    """
    Generate synthetic 2D surface fields on the 0.25° grid.
    
    Args:
        date_str: Optional date string for reproducible seeding
        lat_min: Minimum latitude
        lat_max: Maximum latitude
        lon_min: Minimum longitude
        lon_max: Maximum longitude
        
    Returns:
        Dictionary containing lats, lons, sst, sss, ssh, wind_speed, wind_dir, current_u, current_v
    """
    if date_str:
        seed = int(hashlib.md5(date_str.encode()).hexdigest()[:8], 16)
        np.random.seed(seed)
        
    lats = np.arange(lat_min, lat_max + GRID_RES, GRID_RES)
    lons = np.arange(lon_min, lon_max + GRID_RES, GRID_RES)
    
    n_lat = len(lats)
    n_lon = len(lons)
    
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    
    # SST
    base_sst = 30.0 - (lat_grid - lat_min) * (3.0 / (lat_max - lat_min))
    noise = np.random.randn(n_lat, n_lon) * 1.5
    sst_anomaly = gaussian_filter(noise, sigma=2.0)
    sst = np.clip(base_sst + sst_anomaly, 24.0, 31.0)
    
    # SSS
    base_sss = np.ones((n_lat, n_lon)) * 35.0
    bob_mask = (lon_grid > 80.0) & (lat_grid < 20.0)
    arabian_mask = (lon_grid <= 80.0)
    
    base_sss[bob_mask] -= 2.0  # Lower salinity in BoB
    base_sss[arabian_mask] += 0.5  # Higher in Arabian Sea
    
    sss_noise = np.random.randn(n_lat, n_lon) * 0.5
    sss = base_sss + gaussian_filter(sss_noise, sigma=3.0)
    sss = np.clip(sss, 32.0, 37.0)
    
    # SSH
    ssh_noise = np.random.randn(n_lat, n_lon) * 0.5
    ssh = gaussian_filter(ssh_noise, sigma=3.0)
    ssh = np.clip(ssh, -0.3, 0.3)
    
    # Wind speed
    wind_noise = np.random.randn(n_lat, n_lon) * 5.0
    wind_speed = 7.0 + gaussian_filter(wind_noise, sigma=2.0)
    wind_speed = np.clip(wind_speed, 3.0, 15.0)
    
    # Wind direction
    wind_dir_noise = np.random.rand(n_lat, n_lon) * 360.0
    wind_dir = gaussian_filter(wind_dir_noise, sigma=4.0) % 360.0
    
    # Currents
    u_noise = np.random.randn(n_lat, n_lon) * 0.5
    v_noise = np.random.randn(n_lat, n_lon) * 0.5
    current_u = gaussian_filter(u_noise, sigma=2.0)
    current_v = gaussian_filter(v_noise, sigma=2.0)
    
    return {
        'lats': lats.tolist(),
        'lons': lons.tolist(),
        'sst': sst.tolist(),
        'sss': sss.tolist(),
        'ssh': ssh.tolist(),
        'wind_speed': wind_speed.tolist(),
        'wind_dir': wind_dir.tolist(),
        'current_u': current_u.tolist(),
        'current_v': current_v.tolist()
    }
