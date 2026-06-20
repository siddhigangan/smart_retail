from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.billing import CartAdd, CartRemove, CartItemResponse, BillResponse, BillHistoryResponse
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

@router.post("/generate", response_model=BillResponse, status_code=status.HTTP_201_CREATED)
def generate_bill(db: Session = Depends(get_db)):
    """
    Generates a bill from current cart items, registers the bill,
    and decrements the product stock quantities.
    """
    return BillingService.generate_bill(db)

@router.get("/history", response_model=list[BillHistoryResponse], status_code=status.HTTP_200_OK)
def get_history(db: Session = Depends(get_db)):
    """
    Retrieves bill history records (bill number, date, amount).
    """
    return BillingService.get_history(db)
