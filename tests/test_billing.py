import sys
from decimal import Decimal

# Ensure app can be imported
sys.path.append(".")

from app.database.session import SessionLocal, engine, Base
from app.services.product import ProductService
from app.services.billing import BillingService
from app.schemas.product import ProductCreate
from app.models.product import Product
from app.models.bill import Bill, BillItem

def run_billing_tests():
    print("Starting integration tests for Smart Retail Billing services...")
    db = SessionLocal()
    
    # Ensure tables exist (specifically new bills & bill_items)
    Base.metadata.create_all(bind=engine)
    
    # Test barcodes
    barcode_1 = "BILL-TEST-BARCODE-1"
    barcode_2 = "BILL-TEST-BARCODE-2"
    
    prod1_id = None
    prod2_id = None
    test_bill_id = None
    
    try:
        # 1. Clean up any leftover test data
        for bc in [barcode_1, barcode_2]:
            existing = ProductService.get_by_barcode(db, bc)
            if existing:
                db.delete(existing)
        db.commit()
        BillingService.clear_cart()

        # 2. Create test products
        print("\n--- 1. Creating Test Products ---")
        p1_data = ProductCreate(
            barcode=barcode_1,
            name="Test Apple Juice",
            category="Beverages",
            price=Decimal("10.00"),
            quantity=5,  # low stock
            reorder_level=2
        )
        p2_data = ProductCreate(
            barcode=barcode_2,
            name="Test Bread Roll",
            category="Bakery",
            price=Decimal("5.50"),
            quantity=2,  # very low stock
            reorder_level=1
        )
        
        prod1 = ProductService.create(db, p1_data)
        prod1_id = prod1.id
        prod2 = ProductService.create(db, p2_data)
        prod2_id = prod2.id
        print(f"Created Product 1: ID={prod1.id}, Barcode='{prod1.barcode}', Qty={prod1.quantity}")
        print(f"Created Product 2: ID={prod2.id}, Barcode='{prod2.barcode}', Qty={prod2.quantity}")

        # 3. Test Add to Cart & Validation
        print("\n--- 2. Testing Add to Cart & Stock Validation ---")
        # Add 2 items of Prod 1 (stock is 5). Should succeed.
        res1 = BillingService.add_to_cart(db, barcode_1, 2)
        print(f"Add product 1 (qty 2) response: {res1}")
        assert res1["message"] == "Product added to cart"
        
        # Verify cart content
        cart = BillingService.get_cart()
        assert len(cart) == 1
        assert cart[0]["product_id"] == prod1_id
        assert cart[0]["quantity"] == 2
        assert cart[0]["subtotal"] == Decimal("20.00")
        print("Cart validated successfully after first add.")

        # Try to add 4 more items of Prod 1 (current cart 2 + 4 = 6, stock is 5). Should raise Insufficient Stock.
        try:
            BillingService.add_to_cart(db, barcode_1, 4)
            print("ERROR: Adding exceeding quantity did not raise exception!")
            sys.exit(1)
        except Exception as e:
            assert "Insufficient Stock" in str(e)
            print(f"Success: Correctly raised exception on exceeding stock: {e}")

        # Add 1 item of Prod 2 (stock is 2). Should succeed.
        res2 = BillingService.add_to_cart(db, barcode_2, 1)
        print(f"Add product 2 (qty 1) response: {res2}")
        assert res2["message"] == "Product added to cart"

        # Verify cart contains 2 items
        cart = BillingService.get_cart()
        assert len(cart) == 2
        print(f"Cart items count is {len(cart)} (expected 2)")

        # 4. Test Remove from Cart
        print("\n--- 3. Testing Cart Item Removal ---")
        # Remove Prod 2 from cart
        rem_res = BillingService.remove_from_cart(barcode_2)
        print(f"Remove product 2 response: {rem_res}")
        assert rem_res["message"] == "Product removed from cart"

        # Verify cart is back to 1 item (Prod 1 with quantity 2)
        cart = BillingService.get_cart()
        assert len(cart) == 1
        assert cart[0]["barcode"] == barcode_1
        print("Success: Item correctly removed from cart.")

        # 5. Test Generate Bill (persists bill, decrements stock, clears cart)
        print("\n--- 4. Testing Bill Generation ---")
        bill = BillingService.generate_bill(db)
        test_bill_id = bill.id
        print(f"Bill generated successfully: ID={bill.id}, TotalAmount={bill.total_amount}")
        assert bill.total_amount == Decimal("20.00")
        
        # Verify product stock reduction in DB
        db.refresh(prod1)
        db.refresh(prod2)
        print(f"After purchase: Product 1 Stock={prod1.quantity} (Expected 3)")
        print(f"After purchase: Product 2 Stock={prod2.quantity} (Expected 2)")
        assert prod1.quantity == 3
        assert prod2.quantity == 2  # Product 2 was removed, so quantity remains unchanged

        # Verify cart is empty
        cart = BillingService.get_cart()
        assert len(cart) == 0
        print("Success: Cart cleared successfully after checkout.")

        # Verify database Bill & BillItems persistence
        db_bill = db.query(Bill).filter(Bill.id == test_bill_id).first()
        assert db_bill is not None
        assert len(db_bill.items) == 1
        assert db_bill.items[0].product_id == prod1_id
        assert db_bill.items[0].quantity == 2
        assert db_bill.items[0].unit_price == Decimal("10.00")
        assert db_bill.items[0].subtotal == Decimal("20.00")
        print("Success: Bill and Bill Items verified in database.")

        # 6. Test Billing History API
        print("\n--- 5. Testing Billing History Retrieval ---")
        history = BillingService.get_history(db)
        print(f"Billing History Count: {len(history)}")
        assert any(b.id == test_bill_id for b in history)
        
        matched_bill = next(b for b in history if b.id == test_bill_id)
        assert matched_bill.total_amount == Decimal("20.00")
        print("Success: Bill correctly listed in billing history.")

        print("\n==============================================")
        print("ALL BILLING INTEGRATION TESTS PASSED!")
        print("==============================================")

    except Exception as err:
        print(f"\nTEST FAILED WITH ERROR: {err}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup test records from DB to prevent pollution
        print("\n--- Cleaning up test records ---")
        if test_bill_id:
            bill_record = db.query(Bill).filter(Bill.id == test_bill_id).first()
            if bill_record:
                db.delete(bill_record)
        if prod1_id:
            p1 = db.query(Product).filter(Product.id == prod1_id).first()
            if p1:
                db.delete(p1)
        if prod2_id:
            p2 = db.query(Product).filter(Product.id == prod2_id).first()
            if p2:
                db.delete(p2)
        db.commit()
        db.close()
        print("Cleanup completed.")

if __name__ == "__main__":
    run_billing_tests()
