import sys
from decimal import Decimal

# Ensure app can be imported
sys.path.append(".")

from app.database.session import SessionLocal, engine, Base
from app.services.product import ProductService
from app.services.inventory import InventoryService
from app.schemas.product import ProductCreate, ProductUpdate
from app.models.product import Product

def run_tests():
    print("Starting correctness tests for Smart Retail backend services...")
    db = SessionLocal()
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    test_barcode = "TEST-BARCODE-999"
    test_product_id = None
    
    try:
        # 1. Clean up any existing test product first
        existing = ProductService.get_by_barcode(db, test_barcode)
        if existing:
            print(f"Found pre-existing test product ID {existing.id}. Deleting...")
            db.delete(existing)
            db.commit()
            
        # 2. Test Product Creation
        print("\n--- Testing Product Creation ---")
        product_data = ProductCreate(
            barcode=test_barcode,
            name="Test Crispy Chips",
            category="Snacks",
            price=Decimal("4.99"),
            quantity=15,
            reorder_level=5
        )
        
        created_prod = ProductService.create(db, product_data)
        test_product_id = created_prod.id
        print(f"Created Product successfully: ID={created_prod.id}, Name='{created_prod.name}'")
        assert created_prod.barcode == test_barcode
        assert created_prod.price == Decimal("4.99")
        assert created_prod.quantity == 15
        
        # 3. Test Duplicate Barcode Prevention
        print("\n--- Testing Duplicate Barcode Prevention ---")
        try:
            ProductService.create(db, product_data)
            print("ERROR: Duplicate barcode creation did not raise an exception!")
            sys.exit(1)
        except Exception as e:
            print(f"Success: Duplicate barcode raised expected exception: {e}")
            
        # 4. Test Retrieval
        print("\n--- Testing Product Retrieval ---")
        fetched = ProductService.get_by_id(db, test_product_id)
        print(f"Retrieved product by ID: ID={fetched.id}, Name='{fetched.name}'")
        assert fetched.name == "Test Crispy Chips"
        
        # 5. Test Search Functionality
        print("\n--- Testing Product Search ---")
        results = ProductService.search(db, "Crispy")
        print(f"Search results for 'Crispy': {[p.name for p in results]}")
        assert len(results) >= 1
        assert any(p.id == test_product_id for p in results)
        
        results_lower = ProductService.search(db, "crispy")
        assert len(results_lower) == len(results)
        print("Success: Search is case-insensitive")
        
        # 6. Test Low Stock Retrieval
        print("\n--- Testing Low Stock & Stats ---")
        initial_stats = InventoryService.get_dashboard_stats(db)
        print(f"Initial Dashboard Stats: {initial_stats}")
        
        low_stock_list = ProductService.get_low_stock(db)
        assert not any(p.id == test_product_id for p in low_stock_list)
        print("Success: Product is NOT marked as low stock (15 > 5)")
        
        # 7. Test Product Update to trigger low stock
        print("\n--- Testing Product Update & Low Stock State ---")
        update_data = ProductUpdate(
            quantity=3
        )
        updated_prod = ProductService.update(db, test_product_id, update_data)
        print(f"Updated product quantity: ID={updated_prod.id}, Qty={updated_prod.quantity}")
        assert updated_prod.quantity == 3
        
        low_stock_list = ProductService.get_low_stock(db)
        assert any(p.id == test_product_id for p in low_stock_list)
        print("Success: Product is now correctly marked as low stock (3 <= 5)")
        
        new_stats = InventoryService.get_dashboard_stats(db)
        print(f"Updated Dashboard Stats: {new_stats}")
        assert new_stats["low_stock_count"] >= 1
        
        # 8. Test Product Deletion
        print("\n--- Testing Product Deletion ---")
        del_result = ProductService.delete(db, test_product_id)
        print(f"Delete Result: {del_result}")
        assert del_result["message"] == "Product deleted successfully"
        
        try:
            ProductService.get_by_id(db, test_product_id)
            print("ERROR: Product still exists after deletion!")
            sys.exit(1)
        except Exception as e:
            print(f"Success: Product ID {test_product_id} no longer exists ({e})")
            test_product_id = None
            
        print("\n==============================================")
        print("ALL SERVICE LEVEL TESTS PASSED SUCCESSFULLY!")
        print("==============================================")
        
    except Exception as err:
        print(f"\nTEST FAILED WITH ERROR: {err}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if test_product_id:
            try:
                prod = db.query(Product).filter(Product.id == test_product_id).first()
                if prod:
                    db.delete(prod)
                    db.commit()
                    print("Cleanup: Deleted test product from database.")
            except Exception as e:
                print(f"Cleanup Error: {e}")
        db.close()

if __name__ == "__main__":
    run_tests()
