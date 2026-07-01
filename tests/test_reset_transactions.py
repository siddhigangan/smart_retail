import os
import sys
import unittest
from decimal import Decimal

sys.path.append(".")

from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal
from app.models.bill import Bill, BillItem
from app.models.invoice import Invoice
from app.models.customer import Customer
from app.models.product import Product

class TestResetTransactions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        # 1. Insert mock customer
        cls.customer = Customer(
            name="Test Reset Customer",
            phone="9911882277",
            total_points=80
        )
        cls.db.add(cls.customer)
        cls.db.commit()

        # 2. Insert test product (required for foreign keys in bill_items if any, though not strictly required depending on constraints, let's create to be safe)
        cls.product = Product(
            barcode="TEST-RESET-PROD",
            name="Reset Test Item",
            category="Food",
            price=Decimal("100.00"),
            cost_price=Decimal("80.00"),
            quantity=10,
            reorder_level=2,
            movement_class="Medium",
            max_stock_capacity=20
        )
        cls.db.add(cls.product)
        cls.db.commit()

        # 3. Create mock Bill & BillItem
        cls.bill = Bill(
            total_amount=Decimal("200.00"),
            customer_id=cls.customer.id,
            customer_name=cls.customer.name,
            customer_phone=cls.customer.phone,
            payment_method="Cash",
            cash_received=200.00,
            change_returned=0.00
        )
        cls.db.add(cls.bill)
        cls.db.commit()

        cls.bill_item = BillItem(
            bill_id=cls.bill.id,
            product_id=cls.product.id,
            quantity=2,
            unit_price=Decimal("100.00"),
            subtotal=Decimal("200.00")
        )
        cls.db.add(cls.bill_item)
        cls.db.commit()

        # 4. Create mock Invoice
        cls.mock_pdf_path = "app/static/invoices/INV-TEST-RESET-FILE.pdf"
        os.makedirs("app/static/invoices", exist_ok=True)
        with open(cls.mock_pdf_path, "wb") as f:
            f.write(b"MOCK PDF DATA FOR RESET TEST")

        cls.invoice = Invoice(
            invoice_number="INV-TEST-RESET-FILE",
            invoice_url="/static/invoices/INV-TEST-RESET-FILE.pdf",
            pdf_path=cls.mock_pdf_path,
            customer_name=cls.customer.name,
            customer_phone=cls.customer.phone,
            total_amount=Decimal("200.00"),
            whatsapp_status="MOCK_SENT"
        )
        cls.db.add(cls.invoice)
        cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        # Clean up the customer and product
        cust = cls.db.query(Customer).filter(Customer.phone == "9911882277").first()
        if cust:
            cls.db.delete(cust)
        prod = cls.db.query(Product).filter(Product.barcode == "TEST-RESET-PROD").first()
        if prod:
            cls.db.delete(prod)
        
        # Ensure pdf is deleted
        if os.path.exists("app/static/invoices/INV-TEST-RESET-FILE.pdf"):
            try:
                os.remove("app/static/invoices/INV-TEST-RESET-FILE.pdf")
            except:
                pass

        cls.db.commit()
        cls.db.close()

    def test_reset_transactional_data(self):
        # Trigger the reset transactions POST request
        resp = self.client.post("/admin/reset-transactions")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"], "All transactional data cleared successfully.")

        # Verify bills, items, and invoices are deleted
        bills_count = self.db.query(Bill).count()
        bill_items_count = self.db.query(BillItem).count()
        invoices_count = self.db.query(Invoice).count()

        self.assertEqual(bills_count, 0)
        self.assertEqual(bill_items_count, 0)
        self.assertEqual(invoices_count, 0)

        # Verify customer total_points are reset to 0
        db_cust = self.db.query(Customer).filter(Customer.phone == "9911882277").first()
        self.assertIsNotNone(db_cust)
        self.assertEqual(db_cust.total_points, 0)

        # Verify local PDF file is deleted from filesystem
        self.assertFalse(os.path.exists(self.mock_pdf_path))

if __name__ == "__main__":
    unittest.main()
