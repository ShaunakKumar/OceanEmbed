import numpy as np
from typing import Dict, Any
import time

from backend.config import LAT_MIN, LAT_MAX, LON_MIN, LON_MAX, DEPTH_LEVELS
from backend.data_engine.subsurface import generate_subsurface_profile

def generate_argo_validation() -> Dict[str, Any]:
    """
    Simulate Argo float observations and compare with model predictions.
    """
    np.random.seed(int(time.time()) % 10000)
    
    num_floats = 20
    floats = []
    
    rmses = []
    maes = []
    
    i = 0
    while len(floats) < num_floats:
        lat = np.random.uniform(LAT_MIN, LAT_MAX)
        lon = np.random.uniform(LON_MIN, LON_MAX)
        
        # Heuristic to avoid Indian subcontinent landmass
        if lat > 20.0 and 65.0 < lon < 85.0:
            continue
            
        model_data = generate_subsurface_profile(lat, lon, lead_time=0)
        predicted = np.array(model_data['mean_temperature'])
        
        noise = np.random.randn(len(predicted)) * 0.4
        observed = predicted + noise
        observed = np.maximum(observed, 1.0)
        
        rmse = np.sqrt(np.mean((predicted - observed)**2))
        mae = np.mean(np.abs(predicted - observed))
        
        rmses.append(rmse)
        maes.append(mae)
        
        float_id = f"ARGO-2901{i:03d}"
        
        floats.append({
            'id': float_id,
            'lat': float(lat),
            'lon': float(lon),
            'depths': DEPTH_LEVELS,
            'observed': observed.tolist(),
            'predicted': predicted.tolist(),
            'rmse': float(rmse),
            'mae': float(mae)
        })
        i += 1
        
    return {
        'floats': floats,
        'aggregate': {
            'mean_rmse': float(np.mean(rmses)),
            'mean_mae': float(np.mean(maes)),
            'n_floats': num_floats
        }
    }
