from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.product import Product
from app.models.bill import Bill, BillItem
from app.services.product import ProductService
from app.services.customer import CustomerService
from app.services.email_service import EmailService
from app.services.sms_service import SMSService


class BillingService:
    # Class-level in-memory cart dictionary: barcode -> cart_item_dict
    _cart = {}

    @classmethod
    def add_to_cart(cls, db: Session, barcode: str, quantity: int) -> dict:
        """
        Add a product to the cart by barcode.
        Checks for product existence and verifies stock levels.
        """
        product = ProductService.get_by_barcode(db, barcode)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with barcode '{barcode}' not found"
            )

        current_quantity = cls._cart.get(barcode, {}).get("quantity", 0)
        requested_total = current_quantity + quantity

        if requested_total > product.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient Stock"
            )

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
        """Remove a product from the cart by barcode."""
        if barcode not in cls._cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with barcode '{barcode}' is not in the cart"
            )
        del cls._cart[barcode]
        return {"message": "Product removed from cart"}

    @classmethod
    def get_cart(cls) -> list[dict]:
        """Retrieve all items currently in the cart."""
        return list(cls._cart.values())

    @classmethod
    def clear_cart(cls):
        """Clear the in-memory cart contents."""
        cls._cart.clear()

    @classmethod
    def generate_bill(
        cls,
        db: Session,
        customer_name: str = None,
        customer_phone: str = None,
        customer_email: str = None
    ) -> dict:
        """
        Generates a bill from the current cart items.
        Decrements product stock, links customer, awards loyalty points,
        then sends SMS + email receipts (failures don't roll back the bill).
        """
        if not cls._cart:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty"
            )

        try:
            # 1. Validate all stock before writing anything
            for barcode, item in cls._cart.items():
                product = db.query(Product).filter(Product.id == item["product_id"]).with_for_update().first()
                if not product or product.quantity < item["quantity"]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Insufficient Stock"
                    )

            # 2. Resolve customer (only when phone is provided)
            customer_id = None
            customer_obj = None
            if customer_phone:
                customer_obj = CustomerService.get_or_create(
                    db,
                    phone=customer_phone,
                    name=customer_name,
                    email=customer_email
                )
                customer_id = customer_obj.id

            # 3. Create Bill record
            total_amount = sum(item["subtotal"] for item in cls._cart.values())
            db_bill = Bill(
                total_amount=total_amount,
                customer_id=customer_id,
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_email=customer_email
            )
            db.add(db_bill)
            db.flush()  # Get bill ID

            # 4. Create BillItems + decrement stock
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

            # 5. Award loyalty points
            loyalty_points_earned = 0
            customer_total_points = 0
            if customer_id:
                loyalty_points_earned = CustomerService.add_points(db, customer_id, float(total_amount))
                db.refresh(customer_obj)
                customer_total_points = customer_obj.total_points

            # 6. Commit everything
            db.commit()
            db.refresh(db_bill)
            cls.clear_cart()

            # 7. Build item list for notifications (after commit)
            items_for_notify = [
                {
                    "product_id": item["product_id"],
                    "name": item["product_name"],
                    "quantity": item["quantity"],
                    "unit_price": item["unit_price"],
                    "subtotal": item["subtotal"]
                }
                for item in cls._cart.values()  # already cleared — use pre-clear snapshot via db_bill.items
            ]
            # Use bill items from DB for accuracy
            items_for_notify = [
                {
                    "product_id": bi.product_id,
                    "name": next(
                        (v["product_name"] for v in [{**v, "pid": v["product_id"]} for v in []] if False),
                        f"Product #{bi.product_id}"
                    ),
                    "quantity": bi.quantity,
                    "unit_price": float(bi.unit_price),
                    "subtotal": float(bi.subtotal)
                }
                for bi in db_bill.items
            ]

            # 8. Send email receipt (non-blocking failure)
            email_sent = False
            sms_sent = False
            send_to_email = customer_email or (customer_obj.email if customer_obj else None)
            send_to_phone = customer_phone

            if send_to_email:
                email_sent = EmailService.send_bill(
                    to_email=send_to_email,
                    bill_id=db_bill.id,
                    total_amount=float(total_amount),
                    items=items_for_notify,
                    customer_name=customer_name,
                    loyalty_points_earned=loyalty_points_earned,
                    customer_total_points=customer_total_points
                )

            # 9. Send SMS receipt (non-blocking failure)
            if send_to_phone:
                sms_sent = SMSService.send_bill(
                    to_phone=send_to_phone,
                    bill_id=db_bill.id,
                    total_amount=float(total_amount),
                    customer_name=customer_name,
                    loyalty_points_earned=loyalty_points_earned
                )

            return {
                "id": db_bill.id,
                "total_amount": db_bill.total_amount,
                "created_at": db_bill.created_at,
                "items": db_bill.items,
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "customer_email": customer_email,
                "loyalty_points_earned": loyalty_points_earned,
                "customer_total_points": customer_total_points,
                "email_sent": email_sent,
                "sms_sent": sms_sent
            }

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
        """Retrieve bill records history."""
        return db.query(Bill).order_by(Bill.created_at.desc()).all()
