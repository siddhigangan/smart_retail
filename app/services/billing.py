from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.product import Product
from app.models.bill import Bill, BillItem
from app.services.product import ProductService

class BillingService:
    # Class-level in-memory cart dictionary: barcode -> cart_item_dict
    _cart = {}

    @classmethod
    def add_to_cart(cls, db: Session, barcode: str, quantity: int) -> dict:
        """
        Add a product to the cart by barcode.
        Checks for product existence and verifies stock levels.
        """
        # Find product by barcode
        product = ProductService.get_by_barcode(db, barcode)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with barcode '{barcode}' not found"
            )

        # Calculate total quantity in cart for this product
        current_quantity = cls._cart.get(barcode, {}).get("quantity", 0)
        requested_total = current_quantity + quantity

        # Validate against database stock
        if requested_total > product.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient Stock"
            )

        # Add or update item in cart
        cls._cart[barcode] = {
            "product_id": product.id,
            "product_name": product.name,
            "barcode": barcode,
            "quantity": requested_total,
            "unit_price": product.price,
            "subtotal": product.price * requested_total
        }

        return {"message": "Product added to cart"}

    @classmethod
    def remove_from_cart(cls, barcode: str) -> dict:
        """
        Remove a product from the cart by barcode.
        """
        if barcode not in cls._cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with barcode '{barcode}' is not in the cart"
            )

        del cls._cart[barcode]
        return {"message": "Product removed from cart"}

    @classmethod
    def get_cart(cls) -> list[dict]:
        """
        Retrieve all items currently in the cart.
        """
        return list(cls._cart.values())

    @classmethod
    def clear_cart(cls):
        """
        Clear the in-memory cart contents.
        """
        cls._cart.clear()

    @classmethod
    def generate_bill(cls, db: Session) -> Bill:
        """
        Generates a bill from the current cart items.
        Decrements product stock and persists the records in a single database transaction.
        """
        if not cls._cart:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty"
            )

        try:
            # 1. Validate stock for all items before writing any data (prevent partial updates)
            for barcode, item in cls._cart.items():
                product = db.query(Product).filter(Product.id == item["product_id"]).with_for_update().first()
                if not product or product.quantity < item["quantity"]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Insufficient Stock"
                    )

            # 2. Create the Bill record
            total_amount = sum(item["subtotal"] for item in cls._cart.values())
            db_bill = Bill(total_amount=total_amount)
            db.add(db_bill)
            db.flush()  # Populate DB auto-generated primary key (id)

            # 3. Create BillItem records and update product stock
            for barcode, item in cls._cart.items():
                product = db.query(Product).filter(Product.id == item["product_id"]).first()
                product.quantity -= item["quantity"]

                db_bill_item = BillItem(
                    bill_id=db_bill.id,
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    unit_price=item["unit_price"],
                    subtotal=item["subtotal"]
                )
                db.add(db_bill_item)

            # 4. Commit transaction & clear local cart
            db.commit()
            db.refresh(db_bill)
            cls.clear_cart()
            return db_bill

        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate bill: {str(e)}"
            )

    @classmethod
    def get_history(cls, db: Session) -> list[Bill]:
        """
        Retrieve bill records history.
        """
        return db.query(Bill).order_by(Bill.created_at.desc()).all()
