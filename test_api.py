"""
OceanEmbed Verification & Test Suite
====================================
Validates all core scientific calculations, data engine models,
xarray NetCDF generation, and FastAPI endpoints.
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
from fastapi.testclient import TestClient

from backend.config import DEPTH_LEVELS, LAT_MIN, LAT_MAX, LON_MIN, LON_MAX, TCHP_THRESHOLD
from backend.data_engine.surface import generate_surface_fields
from backend.data_engine.subsurface import generate_subsurface_profile, compute_mld, compute_d26
from backend.data_engine.tchp import compute_tchp_at_point, compute_tchp_grid
from backend.data_engine.validation import generate_argo_validation
from backend.data_engine.netcdf_export import build_forecast_dataset, export_netcdf_bytes
from backend.app import app


class TestOceanEmbedDataEngine(unittest.TestCase):

    def test_01_surface_fields(self):
        """Verify 2D surface fields generation on 0.25° grid."""
        fields = generate_surface_fields(date_str="2026-09-07")
        self.assertIn("sst", fields)
        self.assertIn("sss", fields)
        self.assertIn("ssh", fields)
        self.assertIn("wind_speed", fields)
        self.assertIn("current_u", fields)

        sst_arr = np.array(fields["sst"])
        self.assertTrue(np.all((sst_arr >= 23.5) & (sst_arr <= 32.0)), "SST out of realistic range")

        sss_arr = np.array(fields["sss"])
        self.assertTrue(np.all((sss_arr >= 31.0) & (sss_arr <= 38.0)), "SSS out of realistic range")

        ssh_arr = np.array(fields["ssh"])
        self.assertTrue(np.all((ssh_arr >= -0.35) & (ssh_arr <= 0.35)), "SSH anomaly out of range")

    def test_02_subsurface_profile_and_depths(self):
        """Verify 0–1000m vertical profile and realistic thermocline behavior."""
        lat, lon = 15.0, 88.0  # Bay of Bengal
        profile = generate_subsurface_profile(lat=lat, lon=lon, lead_time=0)

        self.assertEqual(profile["depths"], DEPTH_LEVELS, "Depth steps must match oceanic standard")
        self.assertEqual(len(profile["mean_temperature"]), len(DEPTH_LEVELS))

        # Check thermocline decay: surface temp >> 1000m temp
        temps = profile["mean_temperature"]
        self.assertGreater(temps[0], 27.0, "Surface temp should be warm in North Indian Ocean")
        self.assertLess(temps[-1], 6.5, "1000m deep temp should be decayed to 4–6°C")
        self.assertGreater(temps[-1], 3.5, "1000m temp should remain above freezing")

        # Monotonically non-increasing temperature with depth
        for i in range(len(temps) - 1):
            self.assertGreaterEqual(temps[i], temps[i + 1] - 0.05, "Temperature inverted abnormally")

        # Check MLD and D26
        self.assertGreater(profile["mld"], 10.0)
        self.assertLess(profile["mld"], 120.0)
        self.assertGreater(profile["d26"], 20.0)

    def test_03_temporal_uncertainty_expansion(self):
        """Verify uncertainty bounds expand monotonically from T+0 to T+7."""
        lat, lon = 15.0, 88.0
        sigmas = []
        bound_widths = []

        for lt in [0, 1, 3, 7]:
            prof = generate_subsurface_profile(lat=lat, lon=lon, lead_time=lt)
            upper_t = np.array(prof["upper_bound"])
            lower_t = np.array(prof["lower_bound"])

            width = float(np.mean(upper_t - lower_t))
            bound_widths.append(width)
            sigmas.append(float(np.mean(prof["uncertainty_sigma"])))

        # Check strict expansion of confidence bound width with lead time
        for i in range(len(bound_widths) - 1):
            self.assertLess(bound_widths[i], bound_widths[i + 1],
                            f"Uncertainty must expand from T+{i} to next lead time")

    def test_04_tchp_hazard_calculation(self):
        """Verify TCHP integration and rapid-intensification risk threshold flagging."""
        # Tropical warm pool point in Bay of Bengal
        res = compute_tchp_at_point(lat=14.0, lon=88.0, lead_time=0)
        self.assertIn("tchp", res)
        self.assertIn("mld", res)
        self.assertIn("d26", res)
        self.assertGreater(res["tchp"], 40.0, "Warm pool point should have high TCHP")

        # Coarse grid computation
        grid_data = compute_tchp_grid(lead_time=0)
        self.assertIn("high_risk_zones", grid_data)
        self.assertGreater(len(grid_data["high_risk_zones"]), 0, "Should detect at least one high-risk zone")

        for zone in grid_data["high_risk_zones"]:
            self.assertGreaterEqual(zone["tchp_value"], TCHP_THRESHOLD,
                                    "Flagged zone must exceed 50 kJ/cm² threshold")
            self.assertIn(zone["severity"], ["Moderate", "High", "Critical"])

    def test_05_argo_validation(self):
        """Verify simulated Argo observations and model accuracy benchmark (RMSE < 1.0°C)."""
        val_data = generate_argo_validation()
        self.assertIn("floats", val_data)
        self.assertIn("aggregate", val_data)

        self.assertEqual(len(val_data["floats"]), 20)
        mean_rmse = val_data["aggregate"]["mean_rmse"]
        mean_mae = val_data["aggregate"]["mean_mae"]

        self.assertLess(mean_rmse, 1.0, f"Benchmark required RMSE < 1.0°C, got {mean_rmse:.3f}°C")
        self.assertLess(mean_mae, mean_rmse, "MAE should be <= RMSE")

    def test_06_netcdf_dataset_and_export(self):
        """Verify xarray Dataset structure and CF-1.8 NetCDF byte export."""
        ds = build_forecast_dataset(lead_time=0)
        self.assertIn("temperature_mean", ds)
        self.assertIn("tchp", ds)
        self.assertIn("mld", ds)
        self.assertEqual(ds.attrs["Conventions"], "CF-1.8")
        self.assertEqual(len(ds.coords["depth"]), len(DEPTH_LEVELS))

        # Check binary export
        nc_bytes = export_netcdf_bytes(lead_time=0)
        self.assertGreater(len(nc_bytes), 1000, "NetCDF binary export must not be empty")


class TestOceanEmbedEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_root_html(self):
        """Root should serve index.html with HTTP 200."""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/html", resp.headers.get("content-type", ""))
        self.assertIn("OceanEmbed", resp.text)

    def test_02_surface_endpoint(self):
        """GET /api/v1/forecast/surface."""
        resp = self.client.get("/api/v1/forecast/surface?lead_time=0")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("sst", data)
        self.assertIn("lats", data)
        self.assertIn("lons", data)

    def test_03_subsurface_endpoint_get_and_post(self):
        """GET & POST /api/v1/forecast/subsurface."""
        # Test POST
        resp_post = self.client.post("/api/v1/forecast/subsurface", json={"lat": 15.0, "lon": 88.0, "lead_time": 1})
        self.assertEqual(resp_post.status_code, 200)
        data_post = resp_post.json()
        self.assertEqual(data_post["depths"], DEPTH_LEVELS)
        self.assertIn("mean_temperature", data_post)
        self.assertIn("lower_bound", data_post)
        self.assertIn("upper_bound", data_post)

        # Test GET
        resp_get = self.client.get("/api/v1/forecast/subsurface?lat=15.0&lon=88.0&lead_time=1")
        self.assertEqual(resp_get.status_code, 200)
        data_get = resp_get.json()
        self.assertEqual(data_get["depths"], DEPTH_LEVELS)

    def test_04_tchp_hazards_endpoint(self):
        """GET /api/v1/hazards/tchp."""
        resp = self.client.get("/api/v1/hazards/tchp?lead_time=0")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("tchp", data)
        self.assertIn("high_risk_zones", data)

    def test_05_argo_validation_endpoint(self):
        """GET /api/v1/validation/argo."""
        resp = self.client.get("/api/v1/validation/argo")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("floats", data)
        self.assertIn("aggregate", data)
        self.assertLess(data["aggregate"]["mean_rmse"], 1.0)

    def test_06_netcdf_export_endpoint(self):
        """GET /api/v1/forecast/export/netcdf."""
        resp = self.client.get("/api/v1/forecast/export/netcdf?lead_time=0")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("application/x-netcdf", resp.headers.get("content-type", ""))
        self.assertIn("attachment; filename=", resp.headers.get("content-disposition", ""))
        self.assertGreater(len(resp.content), 1000)


if __name__ == "__main__":
    print("=" * 70)
    print("🌊 Running OceanEmbed Comprehensive Verification Suite...")
    print("=" * 70)
    suite = unittest.TestSuite()
    loader = unittest.defaultTestLoader
    suite.addTest(loader.loadTestsFromTestCase(TestOceanEmbedDataEngine))
    suite.addTest(loader.loadTestsFromTestCase(TestOceanEmbedEndpoints))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
    print("\n✅ All OceanEmbed Verification Tests Passed Successfully!")
