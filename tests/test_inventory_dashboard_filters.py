import sys
import unittest

sys.path.append(".")

from fastapi.testclient import TestClient
from app.main import app

class TestInventoryDashboardFilters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_filter_all(self):
        response = self.client.get("/inventory/filter?type=all")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("products", data)
        self.assertIn("counts", data)
        self.assertIn("all", data["counts"])

    def test_filter_low_stock(self):
        response = self.client.get("/inventory/filter?type=low_stock")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("products", data)
        self.assertIn("counts", data)

    def test_filter_overstocked(self):
        response = self.client.get("/inventory/filter?type=overstocked")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("products", data)

    def test_filter_warehouse_empty(self):
        response = self.client.get("/inventory/filter?type=warehouse_empty")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("products", data)

    def test_filter_shelf_refill_needed(self):
        response = self.client.get("/inventory/filter?type=shelf_refill_needed")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("products", data)

    def test_placeholder_messages(self):
        # If fast_moving doesn't exist, check placeholder is returned
        response = self.client.get("/inventory/filter?type=fast_moving")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Should either list products OR return placeholder
        if data.get("placeholder_message"):
            self.assertIn("Fast moving analytics", data["placeholder_message"])

if __name__ == "__main__":
    unittest.main()
