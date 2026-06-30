import sys
import unittest
from decimal import Decimal
from datetime import datetime

# Ensure app can be imported
sys.path.append(".")

from app.database.session import SessionLocal, engine, Base
from app.models.product import Product
from app.models.shelf import Shelf
from app.models.inventory_mapping import InventoryMapping
from app.models.refill_log import RefillLog
from app.models.bill import Bill, BillItem
from app.services.shelf import ShelfService
from app.services.billing import BillingService

class TestShelfReplenishment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        # Ensure all tables exist
        Base.metadata.create_all(bind=engine)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def setUp(self):
        # We will create a clean test product and shelf mapping for each test
        self.test_barcode = "TEST-BARCODE-SHELF-99"
        self.test_shelf_num = "TEST-SHELF-NUM-99"
        
        # Cleanup first if any leftovers exist
        self.cleanup_test_data()

        # Insert test product
        self.product = Product(
            barcode=self.test_barcode,
            name="Test Chocolate Cookie",
            category="Biscuits & Snacks",
            price=Decimal("10.00"),
            quantity=100,  # Total stock
            reorder_level=10
        )
        self.db.add(self.product)
        self.db.flush()

        # Insert test shelf
        self.shelf = Shelf(
            floor_number=1,
            aisle="B01",
            rack="R01",
            shelf_number=self.test_shelf_num,
            category="Biscuits & Snacks"
        )
        self.db.add(self.shelf)
        self.db.flush()

        # Create mapping: capacity 20, shelf quantity 5 (low stock, min 8), warehouse stock 95
        self.mapping = InventoryMapping(
            product_id=self.product.id,
            shelf_id=self.shelf.id,
            shelf_capacity=20,
            current_shelf_quantity=5,
            warehouse_quantity=95,
            minimum_shelf_quantity=8
        )
        self.db.add(self.mapping)
        self.db.commit()

    def tearDown(self):
        self.cleanup_test_data()

    def cleanup_test_data(self):
        self.db.rollback()
        prod = self.db.query(Product).filter(Product.barcode == self.test_barcode).first()
        if prod:
            # Delete bill items referencing test product
            bitems = self.db.query(BillItem).filter(BillItem.product_id == prod.id).all()
            bill_ids = {bi.bill_id for bi in bitems}
            for bi in bitems:
                self.db.delete(bi)
            
            # Delete bills
            for b_id in bill_ids:
                bill = self.db.query(Bill).filter(Bill.id == b_id).first()
                if bill:
                    self.db.delete(bill)
            
            # Delete mapping and logs
            self.db.query(InventoryMapping).filter(InventoryMapping.product_id == prod.id).delete()
            self.db.query(RefillLog).filter(RefillLog.product_id == prod.id).delete()
            
            self.db.delete(prod)
        
        sh = self.db.query(Shelf).filter(Shelf.shelf_number == self.test_shelf_num).first()
        if sh:
            self.db.delete(sh)
            
        self.db.commit()

    def test_get_shelves(self):
        # Test fetching shelves
        results = ShelfService.get_shelves(self.db, floor_number=1, category="Biscuits & Snacks")
        self.assertTrue(len(results) >= 1)
        self.assertTrue(any(r.product_id == self.product.id for r in results))

    def test_get_low_stock_shelves(self):
        # Test low stock retrieval
        low_shelves = ShelfService.get_low_stock_shelves(self.db)
        self.assertTrue(len(low_shelves) >= 1)
        self.assertTrue(any(r.product_id == self.product.id for r in low_shelves))

    def test_refill_shelf_success(self):
        # Test refilling the shelf
        # Capacity is 20, current is 5, needs 15. Warehouse has 95.
        updated_mapping = ShelfService.refill_shelf(self.db, self.product.id)
        
        self.assertEqual(updated_mapping.current_shelf_quantity, 20)
        self.assertEqual(updated_mapping.warehouse_quantity, 80) # 95 - 15 = 80
        self.assertIsNotNone(updated_mapping.last_refilled_at)
        
        # Verify total product quantity remains 100 (20 + 80 = 100)
        prod = self.db.query(Product).filter(Product.id == self.product.id).first()
        self.assertEqual(prod.quantity, 100)
        
        # Check that refill log was written
        log = self.db.query(RefillLog).filter(RefillLog.product_id == self.product.id).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.quantity_moved, 15)
        self.assertEqual(log.before_quantity, 5)
        self.assertEqual(log.after_quantity, 20)
        self.assertEqual(log.warehouse_before, 95)
        self.assertEqual(log.warehouse_after, 80)

    def test_refill_shelf_already_full(self):
        # Make shelf full first
        self.mapping.current_shelf_quantity = 20
        self.db.commit()
        
        # Try to refill
        with self.assertRaises(Exception) as ctx:
            ShelfService.refill_shelf(self.db, self.product.id)
        self.assertIn("already full", str(ctx.exception))

    def test_refill_shelf_empty_warehouse(self):
        # Make warehouse quantity 0
        self.mapping.warehouse_quantity = 0
        self.db.commit()
        
        # Try to refill
        with self.assertRaises(Exception) as ctx:
            ShelfService.refill_shelf(self.db, self.product.id)
        self.assertIn("empty", str(ctx.exception))

    def test_billing_checkout_decrements_shelf(self):
        # Verify initial shelf quantity is 5
        self.assertEqual(self.mapping.current_shelf_quantity, 5)
        
        # Setup cart
        BillingService.clear_cart()
        BillingService._cart[self.test_barcode] = {
            "product_id": self.product.id,
            "product_name": self.product.name,
            "barcode": self.test_barcode,
            "quantity": 3,
            "unit_price": self.product.price,
            "subtotal": self.product.price * 3
        }
        
        # Generate bill
        BillingService.generate_bill(self.db)
        
        # Refresh mapping
        self.db.refresh(self.mapping)
        
        # Shelf quantity should decrease from 5 to 2
        self.assertEqual(self.mapping.current_shelf_quantity, 2)
        # Warehouse quantity should remain 95
        self.assertEqual(self.mapping.warehouse_quantity, 95)
        # Total product quantity should be 97 (2 + 95 = 97)
        self.db.refresh(self.product)
        self.assertEqual(self.product.quantity, 97)

if __name__ == "__main__":
    unittest.main()
