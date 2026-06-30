from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.billing import CartAdd, CartRemove, CartItemResponse, BillResponse, BillHistoryResponse, GenerateBillRequest
from app.services.billing import BillingService

router = APIRouter(
    prefix="/billing",
    tags=["Billing"]
)

@router.post("/cart/add", status_code=status.HTTP_200_OK)
def add_to_cart(cart_in: CartAdd, db: Session = Depends(get_db)):
    """
    Add a product to the cart by barcode.
    Verifies stock level and raises 'Insufficient Stock' if quantity is too high.
    """
    return BillingService.add_to_cart(db, cart_in.barcode, cart_in.quantity)

@router.post("/cart/remove", status_code=status.HTTP_200_OK)
def remove_from_cart(cart_in: CartRemove):
    """
    Remove a product from the cart by barcode.
    """
    return BillingService.remove_from_cart(cart_in.barcode)

@router.get("/cart", response_model=list[CartItemResponse], status_code=status.HTTP_200_OK)
def get_cart():
    """
    Retrieve items currently in the cart.
    """
    return BillingService.get_cart()

@router.post("/generate", status_code=status.HTTP_201_CREATED)
def generate_bill(
    request: GenerateBillRequest = None,
    db: Session = Depends(get_db)
):
    """
    Generates a bill from current cart items. Accepts optional customer details.
    Sends SMS + email receipt if contact info is provided.
    Awards loyalty points (1 per Rs.10 spent) when phone number is given.
    """
    customer_name = request.customer_name if request else None
    customer_phone = request.customer_phone if request else None
    payment_method = request.payment_method if request else "Cash"
    cash_received = request.cash_received if request else None
    change_returned = request.change_returned if request else None
    split_cash = request.split_cash if request else None
    split_upi = request.split_upi if request else None
    split_card = request.split_card if request else None

    return BillingService.generate_bill(
        db,
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_email=None,
        payment_method=payment_method,
        cash_received=cash_received,
        change_returned=change_returned,
        split_cash=split_cash,
        split_upi=split_upi,
        split_card=split_card
    )

@router.get("/history", response_model=list[BillHistoryResponse], status_code=status.HTTP_200_OK)
def get_history(db: Session = Depends(get_db)):
    """
    Retrieves bill history records (bill number, date, amount).
    """
    return BillingService.get_history(db)

