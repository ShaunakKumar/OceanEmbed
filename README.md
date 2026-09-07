# 🌊 OceanEmbed — Subsurface Ocean Temperature Forecasting

**Problem Statement:** SIH26066 | **Team:** Geeks for weaks  
**Domain:** North Indian Ocean (Arabian Sea & Bay of Bengal: 5°N–25°N, 60°E–95°E)

A spatial-AI prototype web application for subsurface ocean temperature forecasting (0–1000 m) with calibrated uncertainty bounds and Tropical Cyclone Heat Potential (TCHP) hazard alerts.

---

## 🏛️ Architecture & System Design

```
┌─────────────────────────────────────────────────────────────────────────┐
│              Executive React Dashboard (Tailwind Dark Mode)             │
│  • Leaflet 2D Ocean Map (SST & TCHP Heatmaps, Argo Markers, Risk Pins)  │
│  • Plotly Subsurface Depth vs. Temp (Mean, 95% CI, Argo Ground Truth)   │
│  • Cyclone Risk Alert Drawer (Click to inspect high-TCHP anomaly zones) │
│  • Live Surface Metocean Readout (SST, SSS, SSH anomaly, Winds, Currents)│
│  • CF-1.8 NetCDF (.nc) Export Button & Lead Time Selector (T+0 to T+7)  │
├─────────────────────────────────────────────────────────────────────────┤
│                         FastAPI REST Engine                             │
│  • GET  /api/v1/forecast/surface         (0.25° gridded 2D metocean)    │
│  • GET/POST /api/v1/forecast/subsurface  (Depth profile 0–1000m + 95% CI│
│  • GET  /api/v1/hazards/tchp             (TCHP grid + high-risk alerts) │
│  • GET  /api/v1/validation/argo          (20 simulated floats, RMSE<1°C)│
│  • GET  /api/v1/forecast/export/netcdf   (CF-compliant NetCDF download) │
├─────────────────────────────────────────────────────────────────────────┤
│                     Synthetic Ocean Data Engine                         │
│  • Hyperbolic Tangent Thermocline Physics Model                         │
│  • Trapezoidal Integration for TCHP: C_p ∫_0^{d_26} ρ (T(z) - 26) dz    │
│  • Lead-time Uncertainty Scaling: T+0 (0.3°C) → T+7 (1.2°C)             │
│  • xarray Dataset Assembly (lat, lon, depth, time dimensions)           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Project Structure

```
OceanEmbed/
├── backend/
│   ├── app.py                   # FastAPI application entry point
│   ├── config.py                # Domain grid, oceanic depth levels & constants
│   ├── requirements.txt         # Python dependencies
│   ├── data_engine/
│   │   ├── surface.py           # 2D SST, SSS, SSH, wind, current generator (0.25° grid)
│   │   ├── subsurface.py        # 0–1000m thermocline profile engine & uncertainty bounds
│   │   ├── tchp.py              # TCHP numerical integration & rapid intensification zones
│   │   ├── validation.py        # Simulated Argo float benchmark generator (RMSE < 1.0°C)
│   │   └── netcdf_export.py     # xarray CF-1.8 NetCDF (.nc) export utility
│   └── routes/
│       ├── forecast.py          # /api/v1/forecast/* routes (surface, subsurface, netcdf)
│       ├── hazards.py           # /api/v1/hazards/tchp route
│       └── validation.py        # /api/v1/validation/argo route
├── frontend/
│   └── index.html               # Single-page executive React dashboard (Tailwind, Leaflet, Plotly)
├── test_api.py                  # Automated test suite (12 tests verifying physics & endpoints)
├── run.bat                      # Windows quick-start script
└── README.md                    # System documentation
```

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.10+** (Tested with Python 3.14 on Windows)
- Modern web browser (Chrome, Edge, Firefox)

### 2. Install Dependencies
From the `OceanEmbed` folder:
```powershell
pip install -r backend\requirements.txt
```

### 3. Run the Application
**Option A — Windows Quick-Start:**
Double click `run.bat` or execute in PowerShell:
```powershell
.\run.bat
```

**Option B — Direct Command:**
```powershell
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Access the Dashboard
Open your browser and navigate to:
👉 **`http://localhost:8000`** (or `http://127.0.0.1:8000`)

---

## 🧪 Verification & Automated Testing

A dedicated test suite validates all scientific calculations, physical boundaries, and API routes:
```powershell
python test_api.py
```

### Test Coverage (12 passing tests):
1. `test_01_surface_fields`: Verifies realistic ranges for SST (24–31°C), SSS (32–37 PSU), SSH anomaly (-0.3 to +0.3 m).
2. `test_02_subsurface_profile_and_depths`: Verifies exact standard depth steps `[0, 10, 20, 50, 100, 200, 400, 700, 1000]`, thermocline decline, and deep ocean decay to 4–6°C.
3. `test_03_temporal_uncertainty_expansion`: Verifies calibrated uncertainty widening monotonically from $T+0 \rightarrow T+1 \rightarrow T+3 \rightarrow T+7$.
4. `test_04_tchp_hazard_calculation`: Verifies trapezoidal integration of $TCHP = C_p \int_0^{d_{26}} \rho (T-26) dz$ and flagging of zones $> 50\text{ kJ/cm}^2$.
5. `test_05_argo_validation`: Verifies autonomous profiling float simulation achieving aggregate $RMSE < 1.0^\circ\text{C}$.
6. `test_06_netcdf_dataset_and_export`: Validates `xarray.Dataset` assembly with CF-1.8 attributes and binary NetCDF byte serialization.
7. `test_01_root_html` to `test_06_netcdf_export_endpoint`: Full HTTP status 200 and schema validation across all endpoints.

---

## 📐 Scientific & Mathematical Formulations

### 1. Thermocline Profile Physics
Oceanic temperature variation with depth $z$ is modeled using a continuous hyperbolic tangent parameterization combined with deep-ocean exponential decay:
$$T(z) = T_{\text{deep}} + (SST - T_{\text{deep}}) \cdot \frac{1}{2} \left[1 - \tanh\left(\frac{z - z_{\text{thermo}}}{\delta}\right)\right]$$
- **Mixed Layer (0–50 m):** High, quasi-isothermal temperature.
- **Thermocline (50–200 m):** Rapid temperature drop centered at $z_{\text{thermo}}$ ($88\text{ m}$ in Bay of Bengal, $108\text{ m}$ in Arabian Sea).
- **Deep Ocean (200–1000 m):** Gradual decay asymptotically approaching $4.5\text{–}5.5^\circ\text{C}$.

### 2. Tropical Cyclone Heat Potential (TCHP)
TCHP measures the integrated thermal energy available to sustain and rapidly intensify tropical cyclones:
$$TCHP = C_p \int_{0}^{d_{26}} \rho \cdot [T(z) - 26] \, dz$$
- $C_p = 3993\text{ J/(kg}\cdot\text{K)}$ (specific heat capacity of seawater)
- $\rho = 1025\text{ kg/m}^3$ (reference seawater density)
- $d_{26}$: Depth of the $26^\circ\text{C}$ isotherm
- Conversion factor to oceanic standard unit $\text{kJ/cm}^2$: $1\text{ J/m}^2 = 10^{-7}\text{ kJ/cm}^2$
- **Rapid Intensification (RI) Alert:** Regions where $TCHP \ge 50\text{ kJ/cm}^2$ are tagged with Critical/High cyclone rapid intensification warnings.

### 3. Mixed Layer Depth (MLD)
Defined using the standard oceanographic criterion:
$$\text{MLD} = z \quad \text{where} \quad T(z) = SST - 0.5^\circ\text{C}$$

### 4. Calibrated Uncertainty Modeling
Forecast degradation is captured by expanding the standard error $\sigma(t, z)$:
$$\sigma(t, z) = \sigma_{\text{lead}}(t) \cdot \left[1 + 0.65 \exp\left(-\frac{(z - z_{\text{thermo}})^2}{2 \times 35^2}\right)\right]$$
Where $\sigma_{\text{lead}} \in \{0.3^\circ\text{C at } T+0, \, 0.5^\circ\text{C at } T+1, \, 0.8^\circ\text{C at } T+3, \, 1.2^\circ\text{C at } T+7\}$.  
5th and 95th percentile uncertainty envelopes are bounded by $\pm 1.645\sigma(t, z)$ ($\pm 1.96\sigma$ for 95% two-sided confidence).

---

## 🔌 API Reference Guide

### 1. `GET /api/v1/forecast/surface`
Returns 2D surface parameter arrays on the $0.25^\circ$ grid.
- **Query params:** `date` (YYYY-MM-DD), `lead_time` (0, 1, 3, 7), `lat_min`, `lat_max`, `lon_min`, `lon_max`
- **Output:** `lats`, `lons`, `sst`, `sss`, `ssh`, `wind_speed`, `wind_dir`, `current_u`, `current_v`

### 2. `GET` & `POST /api/v1/forecast/subsurface`
Returns 0–1000m vertical profile and confidence bounds at a chosen coordinate.
- **GET params:** `?lat=15.0&lon=88.0&lead_time=1`
- **POST body:** `{"lat": 15.0, "lon": 88.0, "lead_time": 1}`
- **Output:**
  ```json
  {
    "lat": 15.0,
    "lon": 88.0,
    "lead_time": 1,
    "depths": [0, 10, 20, 50, 100, 200, 400, 700, 1000],
    "mean_temperature": [30.2, 30.1, 29.8, 28.5, 21.4, 11.2, 7.1, 5.8, 5.1],
    "lower_bound": [29.3, 29.2, 28.9, 27.4, 19.8, 10.3, 6.4, 5.1, 4.4],
    "upper_bound": [31.1, 31.0, 30.7, 29.6, 23.0, 12.1, 7.8, 6.5, 5.8],
    "sst": 30.2,
    "sss": 33.2,
    "ssh": 0.05,
    "wind_speed": 7.2,
    "wind_dir": 240.0,
    "current_speed": 0.31,
    "mld": 42.0,
    "d26": 82.0
  }
  ```

### 3. `GET /api/v1/hazards/tchp`
Returns spatial TCHP grid and flagged rapid intensification hotspot clusters.
- **Query params:** `lead_time` (0, 1, 3, 7)
- **Output:** `lats`, `lons`, `tchp`, `mld`, `d26`, `high_risk_zones`

### 4. `GET /api/v1/validation/argo`
Returns 20 simulated autonomous Argo float vertical profiles, observed vs. predicted temperatures, and aggregate metrics.
- **Output:** `floats` (array with `id`, `lat`, `lon`, `observed`, `predicted`, `rmse`, `mae`), `aggregate` (`mean_rmse`, `mean_mae`, `n_floats`)

### 5. `GET /api/v1/forecast/export/netcdf`
Generates and downloads a CF-1.8 compliant `.nc` file containing 3D temperature grids and 2D metocean parameters.
- **Query params:** `lead_time` (0, 1, 3, 7)
- **Headers returned:** `Content-Type: application/x-netcdf`, `Content-Disposition: attachment; filename=oceanembed_forecast_T0d.nc`

---

## 💻 Interactive Dashboard UI Capabilities

1. **Executive Operations Banner:** Displays live UTC timestamp, active operational basin ("North Indian Ocean"), and engine status.
2. **Lead Time Slider (T+0 to T+7):** Instantaneously updates model predictions and progressively widens uncertainty envelopes.
3. **Multi-layer Leaflet Ocean Map:**
   - Smooth heatmaps for SST (24–31°C) and TCHP (0–100+ kJ/cm²).
   - Hotspot markers with pulsing animation indicating locations exceeding $50\text{ kJ/cm}^2$.
   - Interactive Argo float markers with Pass/Warn precision status.
   - Interactive coordinate picker pin.
4. **Subsurface Depth vs. Temperature Chart (Plotly):**
   - Inverted Y-axis (0m down to 1000m).
   - Mean temperature spline with shaded 95% confidence interval band.
   - Ground-truth comparison line when clicking any Argo float marker ($RMSE < 1.0^\circ\text{C}$).
   - Visual reference lines for MLD (Mixed Layer Depth) and D26 (26°C isotherm).
5. **In-Situ Metocean Point Readout:** Displays local SST, Salinity, SSH anomaly, Wind velocity, Ocean currents, MLD, and D26.
6. **Cyclone Rapid Intensification Drawer:** Ranked high-risk clusters in the Bay of Bengal & Arabian Sea; clicking "Inspect Profile" flies the map to the hotspot and renders its depth profile.
7. **Argo Float Validation Benchmarks:** Table of active profiling floats with click-to-compare capability.
8. **Export NetCDF (.nc) Button:** Directly streams model forecasts as standard NetCDF format for oceanographic research.

---

## 📜 License & Credits

Built for **Smart India Hackathon (SIH26066)**  
Team: **Geeks for weaks**
