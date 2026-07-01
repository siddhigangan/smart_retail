import os
import sys
import unittest
from decimal import Decimal

sys.path.append(".")

from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal
from app.models.product import Product
from app.models.shelf import Shelf
from app.models.inventory_mapping import InventoryMapping
from app.models.adjustment_log import AdjustmentLog

class TestProductManagement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        # Seed a test shelf for biscuits
        cls.shelf = Shelf(
            floor_number=1,
            aisle="Aisle A1",
            rack="Rack R2",
            shelf_number="SH-BISCUIT-TEST",
            category="Biscuits"
        )
        cls.db.add(cls.shelf)
        cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        # Cleanup seeded records
        cls.db.query(AdjustmentLog).delete()
        
        # We need to query and delete mappings and products matching test prefixes
        mappings = cls.db.query(InventoryMapping).join(Product).filter(Product.barcode.like("TEST-%")).all()
        for m in mappings:
            cls.db.delete(m)
        
        cls.db.query(Product).filter(Product.barcode.like("TEST-%")).delete()
        
        # Cleanup shelves
        cls.db.query(Shelf).filter(Shelf.shelf_number == "SH-BISCUIT-TEST").delete()
        
        cls.db.commit()
        cls.db.close()

    def test_01_shelf_recommendations(self):
        resp = self.client.get("/api/products-management/recommend-shelves?category=Biscuits")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(len(data) >= 1)
        # Verify first recommended is our SH-BISCUIT-TEST
        first_recom = data[0]
        self.assertEqual(first_recom["shelf_number"], "SH-BISCUIT-TEST")
        self.assertEqual(first_recom["status"], "🟢 Recommended")

    def test_02_manual_add_product(self):
        payload = {
            "barcode": "TEST-PM-0001",
            "name": "Biscuit Delight",
            "brand": "BiscuitCo",
            "category": "Biscuits",
            "sub_category": "Sweet Biscuit",
            "supplier": "Nagpur Bakers",
            "unit": "Pkt",
            "pack_size": "200g",
            "mrp": 30.00,
            "selling_price": 28.00,
            "cost_price": 20.00,
            "gst": 18.00,
            "hsn_code": "1905",
            "reorder_level": 5,
            "expiry_required": False,
            "expiry_date": None,
            "shelf_id": self.shelf.id,
            "quantity": 100,
            "shelf_capacity": 20,
            "current_shelf_quantity": 20,
            "warehouse_quantity": 80,
            "minimum_shelf_quantity": 5
        }

        resp = self.client.post("/api/products-management/manual-add", json=payload)
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["status"], "success")

        # Verify database entities
        prod = self.db.query(Product).filter(Product.barcode == "TEST-PM-0001").first()
        self.assertIsNotNone(prod)
        self.assertEqual(prod.name, "Biscuit Delight")
        self.assertEqual(prod.quantity, 100)
        
        mapping = self.db.query(InventoryMapping).filter(InventoryMapping.product_id == prod.id).first()
        self.assertIsNotNone(mapping)
        self.assertEqual(mapping.current_shelf_quantity, 20)
        self.assertEqual(mapping.warehouse_quantity, 80)

    def test_03_inventory_adjustment(self):
        payload = {
            "barcode": "TEST-PM-0001",
            "quantity_changed": -5,
            "reason": "Damaged"
        }

        resp = self.client.post("/api/products-management/adjust", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")

        # Verify quantities updated
        prod = self.db.query(Product).filter(Product.barcode == "TEST-PM-0001").first()
        self.assertEqual(prod.quantity, 95)

        mapping = self.db.query(InventoryMapping).filter(InventoryMapping.product_id == prod.id).first()
        self.assertEqual(mapping.warehouse_quantity, 75)

        # Verify adjustment logs
        log = self.db.query(AdjustmentLog).filter(AdjustmentLog.barcode == "TEST-PM-0001").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.quantity_changed, -5)
        self.assertEqual(log.reason, "Damaged")

    def test_04_bulk_stock_update(self):
        payload = {
            "updates": [
                {
                    "barcode": "TEST-PM-0001",
                    "new_quantity": 110,
                    "reason": "Supplier Delivery"
                }
            ]
        }

        resp = self.client.post("/api/products-management/bulk-update", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")

        # Verify updated quantities
        prod = self.db.query(Product).filter(Product.barcode == "TEST-PM-0001").first()
        self.assertEqual(prod.quantity, 110)

        # Delta was +15, warehouse goes from 75 to 90
        mapping = self.db.query(InventoryMapping).filter(InventoryMapping.product_id == prod.id).first()
        self.assertEqual(mapping.warehouse_quantity, 90)

    def test_05_product_profile(self):
        prod = self.db.query(Product).filter(Product.barcode == "TEST-PM-0001").first()
        resp = self.client.get(f"/api/products-management/profile/{prod.id}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        
        self.assertEqual(data["barcode"], "TEST-PM-0001")
        self.assertEqual(data["name"], "Biscuit Delight")
        self.assertTrue(len(data["adjustment_history"]) >= 1)

if __name__ == "__main__":
    unittest.main()
