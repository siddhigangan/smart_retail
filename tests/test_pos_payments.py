import sys
import unittest
from decimal import Decimal
from datetime import datetime

# Ensure app can be imported
sys.path.append(".")

from app.database.session import SessionLocal, engine, Base
from app.models.product import Product
from app.models.bill import Bill, BillItem
from app.models.customer import Customer
from app.services.billing import BillingService
from app.schemas.billing import GenerateBillRequest
from pydantic import ValidationError

class TestPOSPayments(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        Base.metadata.create_all(bind=engine)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def setUp(self):
        self.test_barcode = "TEST-BARCODE-PAY-99"
        self.cleanup_test_data()

        # Insert test product
        self.product = Product(
            barcode=self.test_barcode,
            name="Test Apple Juice",
            category="Beverages",
            price=Decimal("150.00"),
            quantity=10,
            reorder_level=2
        )
        self.db.add(self.product)
        self.db.commit()

    def tearDown(self):
        self.cleanup_test_data()

    def cleanup_test_data(self):
        self.db.rollback()
        prod = self.db.query(Product).filter(Product.barcode == self.test_barcode).first()
        if prod:
            bitems = self.db.query(BillItem).filter(BillItem.product_id == prod.id).all()
            bill_ids = {bi.bill_id for bi in bitems}
            for bi in bitems:
                self.db.delete(bi)
            
            for b_id in bill_ids:
                bill = self.db.query(Bill).filter(Bill.id == b_id).first()
                if bill:
                    self.db.delete(bill)
            
            # Clean test customer if created
            cust = self.db.query(Customer).filter(Customer.phone == "9988776655").first()
            if cust:
                self.db.delete(cust)
            
            self.db.delete(prod)
        self.db.commit()

    def test_schema_validations(self):
        # 1. Invalid phone number digit count (should raise validation error)
        with self.assertRaises(ValidationError):
            GenerateBillRequest(
                customer_name="Test Customer",
                customer_phone="12345",
                payment_method="Cash"
            )

        # 2. Invalid phone format non-digit (should raise validation error)
        with self.assertRaises(ValidationError):
            GenerateBillRequest(
                customer_name="Test Customer",
                customer_phone="12345678ab",
                payment_method="Cash"
            )

        # 3. Missing customer name
        with self.assertRaises(ValidationError):
            GenerateBillRequest(
                customer_name="",
                customer_phone="9988776655",
                payment_method="Cash"
            )

    def test_cash_payment_bill_generation(self):
        # Setup cart
        BillingService.clear_cart()
        BillingService._cart[self.test_barcode] = {
            "product_id": self.product.id,
            "product_name": self.product.name,
            "barcode": self.test_barcode,
            "quantity": 2,
            "unit_price": self.product.price,
            "subtotal": self.product.price * 2  # ₹300.00
        }

        # Generate bill with cash received = 500, change = 200
        bill_data = BillingService.generate_bill(
            self.db,
            customer_name="Test Customer",
            customer_phone="9988776655",
            payment_method="Cash",
            cash_received=500.00,
            change_returned=200.00
        )

        self.assertIsNotNone(bill_data["id"])
        self.assertEqual(bill_data["total_amount"], Decimal("300.00"))
        
        # Load from DB and verify payment columns
        db_bill = self.db.query(Bill).filter(Bill.id == bill_data["id"]).first()
        self.assertEqual(db_bill.payment_method, "Cash")
        self.assertEqual(db_bill.cash_received, Decimal("500.00"))
        self.assertEqual(db_bill.change_returned, Decimal("200.00"))

    def test_split_payment_bill_generation(self):
        # Setup cart
        BillingService.clear_cart()
        BillingService._cart[self.test_barcode] = {
            "product_id": self.product.id,
            "product_name": self.product.name,
            "barcode": self.test_barcode,
            "quantity": 2,
            "unit_price": self.product.price,
            "subtotal": self.product.price * 2  # ₹300.00
        }

        # Generate split bill: Cash 100, UPI 200
        bill_data = BillingService.generate_bill(
            self.db,
            customer_name="Test Customer",
            customer_phone="9988776655",
            payment_method="Split",
            split_cash=100.00,
            split_upi=200.00
        )

        # Load from DB and verify split columns
        db_bill = self.db.query(Bill).filter(Bill.id == bill_data["id"]).first()
        self.assertEqual(db_bill.payment_method, "Split")
        self.assertEqual(db_bill.split_cash, Decimal("100.00"))
        self.assertEqual(db_bill.split_upi, Decimal("200.00"))
        self.assertIsNone(db_bill.split_card)

if __name__ == "__main__":
    unittest.main()
