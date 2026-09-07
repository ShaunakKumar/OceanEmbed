# Grid: North Indian Ocean
LAT_MIN, LAT_MAX = 5.0, 25.0
LON_MIN, LON_MAX = 60.0, 95.0
GRID_RES = 0.25  # degrees

# Standard depth levels (meters)
DEPTH_LEVELS = [0, 10, 20, 50, 100, 200, 400, 700, 1000]

# Physical constants
CP = 3993.0   # Specific heat of seawater, J/(kg·K)
RHO = 1025.0  # Density of seawater, kg/m³
TCHP_THRESHOLD = 50.0  # kJ/cm², rapid intensification risk
T_REF = 26.0  # Reference temperature for TCHP (°C)

# Forecast lead times (days)
LEAD_TIMES = [0, 1, 3, 7]

# Uncertainty scaling (sigma in °C) per lead time
UNCERTAINTY_SIGMA = {0: 0.3, 1: 0.5, 3: 0.8, 7: 1.2}

# Generate lat/lon arrays
import numpy as np
LATS = np.arange(LAT_MIN, LAT_MAX + GRID_RES, GRID_RES)
LONS = np.arange(LON_MIN, LON_MAX + GRID_RES, GRID_RES)
