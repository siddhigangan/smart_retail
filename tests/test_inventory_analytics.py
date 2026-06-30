import sys
import unittest
from decimal import Decimal
from datetime import date

# Ensure app can be imported
sys.path.append(".")

from app.database.session import SessionLocal, engine, Base
from app.models.product import Product
from app.models.inventory_mapping import InventoryMapping
from app.models.shelf import Shelf
from app.services.analytics import AnalyticsService
from fastapi.testclient import TestClient
from app.main import app

class TestInventoryAnalytics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def setUp(self):
        self.cleanup_test_data()

        # Insert test Shelf
        self.shelf = Shelf(
            floor_number=1,
            aisle="Aisle A",
            rack="Rack B",
            shelf_number="SH-99-TEST",
            category="TestCategory"
        )
        self.db.add(self.shelf)
        self.db.commit()

        # Insert test Product
        self.product = Product(
            barcode="BARCODE-ANALYTICS-99",
            name="Test Apple Pie",
            category="TestCategory",
            price=Decimal("150.00"),
            cost_price=Decimal("100.00"),
            quantity=25,
            reorder_level=5,
            movement_class="Fast",
            max_stock_capacity=100,
            expiry_date=date(2027, 6, 30)
        )
        self.db.add(self.product)
        self.db.commit()

        # Insert test InventoryMapping
        self.mapping = InventoryMapping(
            product_id=self.product.id,
            shelf_id=self.shelf.id,
            shelf_capacity=20,
            current_shelf_quantity=15,
            warehouse_quantity=10,
            minimum_shelf_quantity=5
        )
        self.db.add(self.mapping)
        self.db.commit()

        # Insert a mock Bill and BillItem to register sales
        from app.models.bill import Bill, BillItem
        self.bill = Bill(
            total_amount=Decimal("150.00"),
            customer_name="Test Customer",
            customer_phone="9988776655"
        )
        self.db.add(self.bill)
        self.db.commit()

        self.bill_item = BillItem(
            bill_id=self.bill.id,
            product_id=self.product.id,
            quantity=99999,
            unit_price=Decimal("150.00"),
            subtotal=Decimal("150.00")
        )
        self.db.add(self.bill_item)
        self.db.commit()

    def tearDown(self):
        self.cleanup_test_data()

    def cleanup_test_data(self):
        self.db.rollback()
        # Find product and map first
        prod = self.db.query(Product).filter(Product.barcode == "BARCODE-ANALYTICS-99").first()
        if prod:
            from app.models.bill import Bill, BillItem
            bitems = self.db.query(BillItem).filter(BillItem.product_id == prod.id).all()
            for bi in bitems:
                self.db.delete(bi)
            
            bills = self.db.query(Bill).filter(Bill.customer_phone == "9988776655").all()
            for b in bills:
                self.db.delete(b)

            maps = self.db.query(InventoryMapping).filter(InventoryMapping.product_id == prod.id).all()
            for m in maps:
                self.db.delete(m)
            self.db.delete(prod)

        shelf = self.db.query(Shelf).filter(Shelf.shelf_number == "SH-99-TEST").first()
        if shelf:
            self.db.delete(shelf)
            
        self.db.commit()

    def test_analytics_kpi_calculations(self):
        # Retrieve analytics data for TestCategory
        data = AnalyticsService.get_dashboard_data(self.db, category="TestCategory")
        
        # Verify cards calculations
        cards = data["cards"]
        self.assertEqual(cards["total_products"], 1)
        # Value = 25 qty * 100 cost_price = 2500
        self.assertEqual(cards["inventory_value"], 2500.0)
        
        # Shelf utilization = (15 current / 20 capacity) * 100 = 75.0%
        self.assertEqual(cards["shelf_utilization"], 75.0)

        # Warehouse capacity = 100 max - 20 shelf = 80 capacity
        # Warehouse qty = 10
        # Warehouse utilization = (10 / 80) * 100 = 12.5%
        self.assertEqual(cards["warehouse_utilization"], 12.5)

    def test_analytics_filters(self):
        # Filter matching
        data_match = AnalyticsService.get_dashboard_data(self.db, category="TestCategory", floor=1, movement_class="Fast")
        self.assertEqual(data_match["cards"]["total_products"], 1)

        # Filter not matching
        data_no_match = AnalyticsService.get_dashboard_data(self.db, category="TestCategory", floor=2)
        self.assertEqual(data_no_match["cards"]["total_products"], 0)

    def test_web_endpoint(self):
        # Verify endpoint returns status 200
        response = self.client.get("/inventory-analytics?category=TestCategory&floor=1")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Test Apple Pie", response.text)

if __name__ == "__main__":
    unittest.main()
