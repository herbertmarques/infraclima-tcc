import os
import tempfile
import unittest
from pathlib import Path

temporary_database = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
temporary_database.close()
os.environ["INFRACLIMA_DATABASE_URL"] = f"sqlite:///{temporary_database.name}"

from fastapi.testclient import TestClient

from backend.app import app
from backend.processing import normalize_rows, parse_file, run_analysis


class ProcessingTests(unittest.TestCase):
    def test_csv_brazilian_decimal_and_invalid_duplicate_counts(self):
        data = b"id;latitude;longitude;temperatura_c\nA;-3,1;-60,2;32,5\nB;-3,2;-60,3;33,5\nC;-3,3;-60,4;34,5\nD;bad;-60;35\nE;-3,1;-60,2;32,5"
        rows, invalid, duplicates = parse_file("sample.csv", data)
        self.assertEqual(len(rows), 3)
        self.assertEqual((invalid, duplicates), (1, 1))
        self.assertEqual(rows[0]["temp"], 32.5)

    def test_custom_field_mapping_and_date_validation(self):
        data = ("station;ycoord;xcoord;surface_value;observed_at\n"
                "A;-3.1;-60.2;32.5;2026-10-15T14:00:00-04:00\n"
                "B;-3.2;-60.3;33.5;15/10/2026\n"
                "C;-3.3;-60.4;34.5;2026-10-16\n"
                "D;-3.4;-60.5;35.5;not-a-date").encode()
        rows, invalid, duplicates = parse_file("custom.csv", data, {"id": "station", "lat": "ycoord", "lon": "xcoord", "temp": "surface_value", "observed_at": "observed_at"})
        self.assertEqual(len(rows), 3)
        self.assertEqual((invalid, duplicates), (1, 0))
        self.assertEqual(rows[0]["id"], "A")

    def test_bundled_synthetic_examples_import(self):
        root = Path(__file__).resolve().parents[1]
        for name in ("amostra_manaus_sintetica.csv", "amostra_manaus_sintetica.geojson"):
            rows, invalid, duplicates = parse_file(name, (root / "exemplos" / name).read_bytes())
            self.assertEqual((len(rows), invalid, duplicates), (12, 0, 0))

    def test_haversine_spatial_edges_are_in_kilometres(self):
        rows = [
            {"id": "A", "lat": 0, "lon": 0, "temp": 30},
            {"id": "B", "lat": 0, "lon": .001, "temp": 30.2},
            {"id": "C", "lat": 0, "lon": 2, "temp": 31},
        ]
        result = run_analysis(rows, eps=1, min_pts=2, radius_km=.2, features=["temp"])
        self.assertEqual(len(result["edges"]), 1)
        self.assertAlmostEqual(result["edges"][0]["km"], .1112, places=3)
        self.assertEqual(result["components"], 2)

    def test_synthetic_demo_is_repeatable_and_labeled(self):
        from backend.processing import demo_rows
        self.assertEqual(demo_rows(), demo_rows())
        self.assertEqual(len(demo_rows()), 48)
        self.assertNotEqual(demo_rows(42), demo_rows(43))

    def test_api_dataset_analysis_history_and_export(self):
        with TestClient(app) as client:
            self.assertEqual(client.get("/api/health").status_code, 200)
            page = client.get("/")
            self.assertEqual(page.status_code, 200)
            self.assertIn("InfraClima", page.text)
            self.assertIn("datasetSelect", page.text)
            self.assertEqual(client.get("/src/main.js").status_code, 200)
            datasets = client.get("/api/datasets").json()["items"]
            demo = next(item for item in datasets if item["kind"] == "demo")
            repeated_demo = client.post("/api/datasets/demo?seed=42").json()
            self.assertEqual(repeated_demo["id"], demo["id"])
            response = client.post("/api/analyses", json={"dataset_id": demo["id"], "eps": .9, "min_pts": 4, "radius_km": 1.5, "features": ["lat", "lon", "temp"]})
            self.assertEqual(response.status_code, 201, response.text)
            analysis = response.json()
            self.assertEqual(analysis["stats"]["count"], 48)
            self.assertEqual(client.get("/api/analyses/history").json()["items"][0]["id"], analysis["id"])
            exported = client.get(f"/api/analyses/{analysis['id']}/export?format=geojson")
            self.assertEqual(exported.status_code, 200)
            self.assertEqual(exported.json()["type"], "FeatureCollection")
            nodes_csv = client.get(f"/api/analyses/{analysis['id']}/export?format=nodes").text
            self.assertIn("eps,min_samples,raio_grafo_km", nodes_csv)
            self.assertIn("fonte,periodo,licenca", nodes_csv)
            self.assertTrue(client.get(f"/api/analyses/{analysis['id']}/export?format=edges").text.startswith("origem,destino"))
            self.assertIn("experimento,total", client.get(f"/api/analyses/{analysis['id']}/export?format=summary").text)
            self.assertEqual(client.get(f"/api/datasets/{demo['id']}/map").json()["metadata"]["analysisId"], analysis["id"])
            self.assertEqual(client.get(f"/api/datasets/{demo['id']}/graph").json()["metadata"]["analysisId"], analysis["id"])
            self.assertEqual(client.get(f"/api/datasets/{demo['id']}/stats").json()["stats"]["count"], 48)

    def test_imported_dataset_is_persisted_and_invalid_file_is_rejected(self):
        with TestClient(app) as client:
            sample = "id;latitude;longitude;temperatura_c\nA;-3,1;-60,2;32,5\nB;-3,2;-60,3;33,5\nC;-3,3;-60,4;34,5"
            response = client.post("/api/datasets/import", data={"source": "Arquivo de teste", "variable_type": "air"}, files={"file": ("amostra.csv", sample, "text/csv")})
            self.assertEqual(response.status_code, 201, response.text)
            dataset = response.json()
            rows = client.get(f"/api/datasets/{dataset['id']}/observations").json()["items"]
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0]["temp"], 32.5)
            invalid = client.post("/api/datasets/import", files={"file": ("malware.exe", "no", "application/octet-stream")})
            self.assertEqual(invalid.status_code, 400)
            wrong_unit = client.post("/api/datasets/import", data={"unit": "K"}, files={"file": ("amostra.csv", sample, "text/csv")})
            self.assertEqual(wrong_unit.status_code, 422)
            bad_analysis = client.post("/api/analyses", json={"dataset_id": dataset["id"], "eps": 0, "min_pts": 1, "radius_km": 1, "features": ["lat"]})
            self.assertEqual(bad_analysis.status_code, 422)


if __name__ == "__main__":
    unittest.main()
