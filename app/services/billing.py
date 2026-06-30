from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from app.models.product import Product
from app.models.bill import Bill, BillItem
from app.models.inventory_mapping import InventoryMapping
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
        customer_email: str = None,
        payment_method: str = "Cash",
        cash_received: float = None,
        change_returned: float = None,
        split_cash: float = None,
        split_upi: float = None,
        split_card: float = None
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
                customer_email=customer_email,
                payment_method=payment_method,
                cash_received=cash_received,
                change_returned=change_returned,
                split_cash=split_cash,
                split_upi=split_upi,
                split_card=split_card
            )
            db.add(db_bill)
            db.flush()  # Get bill ID

            # 4. Create BillItems + decrement stock
            for barcode, item in cls._cart.items():
                product = db.query(Product).filter(Product.id == item["product_id"]).first()
                product.quantity -= item["quantity"]

                # Hook: Decrement shelf quantity
                mapping = db.query(InventoryMapping).filter(InventoryMapping.product_id == product.id).first()
                if mapping:
                    mapping.current_shelf_quantity = max(0, mapping.current_shelf_quantity - item["quantity"])

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

            # 5b. Generate PDF Invoice & save metadata (before commit)
            import os
            from datetime import datetime
            from app.models.invoice import Invoice
            from app.services.pdf_generator import PDFGenerator
            from app.services.invoice_storage import InvoiceStorageService

            # Generate unique invoice number: INV-YYYYMMDD-0001
            today_str = datetime.now().strftime("%Y%m%d")
            prefix = f"INV-{today_str}-"
            count = db.query(func.count(Invoice.id)).filter(Invoice.invoice_number.like(f"{prefix}%")).scalar() or 0
            serial = str(count + 1).zfill(4)
            invoice_number = f"{prefix}{serial}"

            # Prepare items for PDF generator
            pdf_items = []
            for barcode, item in cls._cart.items():
                pdf_items.append({
                    "barcode": item["barcode"],
                    "product_name": item["product_name"],
                    "quantity": item["quantity"],
                    "unit_price": item["unit_price"],
                    "subtotal": item["subtotal"]
                })

            # Generate PDF
            pdf_bytes = PDFGenerator.generate(
                invoice_number=invoice_number,
                customer_name=customer_name or "Walk-in Customer",
                customer_phone=customer_phone or "0000000000",
                total_amount=float(total_amount),
                cart_items=pdf_items,
                loyalty_points=loyalty_points_earned
            )

            # Save PDF
            filename = f"{invoice_number}.pdf"
            invoice_url = InvoiceStorageService.save_invoice(filename, pdf_bytes)
            pdf_path = os.path.join("app/static/invoices", filename)

            # Create Invoice record
            db_invoice = Invoice(
                invoice_number=invoice_number,
                invoice_url=invoice_url,
                pdf_path=pdf_path,
                customer_name=customer_name or "Walk-in Customer",
                customer_phone=customer_phone or "0000000000",
                total_amount=total_amount,
                whatsapp_status="MOCK_SENT"
            )
            db.add(db_invoice)
            db.flush()

            # 6. Commit everything
            db.commit()
            db.refresh(db_bill)

            # Format payment summary dynamically
            payment_summary = ""
            if payment_method == "Cash":
                cr = float(cash_received) if cash_received is not None else 0.0
                ch = float(change_returned) if change_returned is not None else 0.0
                payment_summary = f"Cash Payment: ₹{cr:.2f}\nChange Returned: ₹{ch:.2f}"
            elif payment_method == "UPI":
                payment_summary = f"UPI Payment: ₹{float(total_amount):.2f}"
            elif payment_method == "Card":
                payment_summary = f"Card Payment: ₹{float(total_amount):.2f}"
            elif payment_method == "Split":
                sc = float(split_cash) if split_cash is not None else 0.0
                su = float(split_upi) if split_upi is not None else 0.0
                scard = float(split_card) if split_card is not None else 0.0
                payment_summary = f"Split Payment:\nCash: ₹{sc:.2f}\nUPI: ₹{su:.2f}\nCard: ₹{scard:.2f}"

            now = datetime.now()
            bill_date = now.strftime("%Y-%m-%d")
            bill_time = now.strftime("%I:%M %p")
            total_items = len(pdf_items)
            total_quantity_val = sum(item["quantity"] for item in pdf_items)
            
            local_invoice_url = f"http://127.0.0.1:8000/invoice/{invoice_number}"

            whatsapp_message = f"""🛒 Smart Retail

Thank you for shopping with us, {customer_name or 'Walk-in Customer'}!

🧾 Invoice Number:
{invoice_number}

📅 Date:
{bill_date}

⏰ Time:
{bill_time}

📱 Customer Contact:
{customer_phone or '0000000000'}

💳 Payment:
{payment_summary}

🛍 Items Purchased:
{total_items}

📦 Total Quantity:
{total_quantity_val}

💰 Bill Summary:
Subtotal: ₹{float(total_amount):.2f}
Discount: ₹0.00
GST: ₹0.00
Grand Total: ₹{float(total_amount):.2f}

🎁 Loyalty:
Points Earned: {loyalty_points_earned}
Total Points: {customer_total_points}

📄 View / Download Invoice:
{local_invoice_url}

Thank you for visiting Smart Retail.
Have a great day! 😊"""

            whatsapp_status = "MOCK_SENT"

            # Print mock WhatsApp message in terminal
            print("\n" + "="*80)
            print("[MOCK WHATSAPP MESSAGE SENT]")
            print(f"To: {customer_phone or '0000000000'}")
            print("Message:")
            try:
                print(whatsapp_message)
            except UnicodeEncodeError:
                # Replace unsupported unicode symbols with safe ASCII placeholders for console logging
                print(whatsapp_message.encode('ascii', errors='replace').decode('ascii'))
            print("="*80 + "\n")

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
                "sms_sent": sms_sent,
                "payment_method": db_bill.payment_method,
                "cash_received": db_bill.cash_received,
                "change_returned": db_bill.change_returned,
                "split_cash": db_bill.split_cash,
                "split_upi": db_bill.split_upi,
                "split_card": db_bill.split_card,
                "invoice_number": invoice_number,
                "invoice_url": invoice_url,
                "whatsapp_message": whatsapp_message,
                "whatsapp_status": whatsapp_status
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
