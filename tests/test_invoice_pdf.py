import os
import sys
import unittest
from decimal import Decimal

sys.path.append(".")

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.database.session import SessionLocal
from app.models.product import Product
from app.models.invoice import Invoice
from app.models.bill import Bill, BillItem

class TestInvoicePDF(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        # Insert test Product
        cls.product = Product(
            barcode="TEST-BARCODE-INV",
            name="Test Invoice Product",
            category="Beverages",
            price=Decimal("150.00"),
            cost_price=Decimal("100.00"),
            quantity=50,
            reorder_level=5,
            movement_class="Fast",
            max_stock_capacity=100
        )
        cls.db.add(cls.product)
        cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        # Cleanup test Product
        prod = cls.db.query(Product).filter(Product.barcode == "TEST-BARCODE-INV").first()
        if prod:
            # Delete corresponding bill items and invoices
            invoices = cls.db.query(Invoice).filter(Invoice.customer_phone == "9988776622").all()
            for inv in invoices:
                # Remove local file
                if os.path.exists(inv.pdf_path):
                    try:
                        os.remove(inv.pdf_path)
                    except:
                        pass
                cls.db.delete(inv)

            bills = cls.db.query(Bill).filter(Bill.customer_phone == "9988776622").all()
            for bill in bills:
                bitems = cls.db.query(BillItem).filter(BillItem.bill_id == bill.id).all()
                for bi in bitems:
                    cls.db.delete(bi)
                cls.db.delete(bill)

            cls.db.delete(prod)
        cls.db.commit()
        cls.db.close()

    def test_invoice_generation_and_lookup(self):
        # 1. Clear cart
        from app.services.billing import BillingService
        BillingService.clear_cart()

        # 2. Add product to cart
        add_resp = self.client.post("/billing/cart/add", json={
            "barcode": "TEST-BARCODE-INV",
            "quantity": 2
        })
        self.assertEqual(add_resp.status_code, 200)

        # 3. Perform checkout
        checkout_payload = {
            "customer_name": "Test Invoice Customer",
            "customer_phone": "9988776622",
            "payment_method": "Cash",
            "cash_received": 300.00,
            "change_returned": 0.00
        }
        checkout_resp = self.client.post("/billing/generate", json=checkout_payload)
        if checkout_resp.status_code != 201:
            print(f"FAIL DETAILS: {checkout_resp.text}")
        self.assertEqual(checkout_resp.status_code, 201)
        
        data = checkout_resp.json()
        self.assertIn("invoice_number", data)
        self.assertIn("invoice_url", data)
        self.assertIn("whatsapp_message", data)
        self.assertIn("whatsapp_status", data)

        self.assertEqual(data["whatsapp_status"], "MOCK_SENT")
        self.assertIn("Smart Retail", data["whatsapp_message"])
        self.assertIn(data["invoice_number"], data["whatsapp_message"])

        inv_num = data["invoice_number"]
        inv_url = data["invoice_url"]

        # 4. Check that PDF invoice file actually exists on filesystem
        expected_pdf_path = os.path.join("app/static/invoices", f"{inv_num}.pdf")
        self.assertTrue(os.path.exists(expected_pdf_path), f"PDF file does not exist at {expected_pdf_path}")

        # 5. Check metadata record in DB
        db_inv = self.db.query(Invoice).filter(Invoice.invoice_number == inv_num).first()
        self.assertIsNotNone(db_inv)
        self.assertEqual(db_inv.customer_phone, "9988776622")
        self.assertEqual(db_inv.whatsapp_status, "MOCK_SENT")
        self.assertEqual(float(db_inv.total_amount), 300.00)

        # 6. Retrieve rendered invoice page
        view_resp = self.client.get(f"/invoice/{inv_num}")
        self.assertEqual(view_resp.status_code, 200)
        self.assertIn("Smart Retail", view_resp.text)
        self.assertIn(inv_num, view_resp.text)
        self.assertIn("Test Invoice Customer", view_resp.text)

if __name__ == "__main__":
    unittest.main()
