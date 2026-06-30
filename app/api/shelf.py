from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.shelf import InventoryMappingResponse, RefillLogResponse
from app.services.shelf import ShelfService

router = APIRouter(
    tags=["Shelf Management"]
)

@router.get("/shelf", response_model=list[InventoryMappingResponse], status_code=status.HTTP_200_OK)
def get_shelves(
    floor_number: int | None = None,
    category: str | None = None,
    low_stock_only: bool = False,
    search_query: str | None = None,
    db: Session = Depends(get_db)
):
    """
    Get all store shelf mappings with optional filters.
    """
    return ShelfService.get_shelves(
        db,
        floor_number=floor_number,
        category=category,
        low_stock_only=low_stock_only,
        search_query=search_query
    )

@router.get("/shelf/low", response_model=list[InventoryMappingResponse], status_code=status.HTTP_200_OK)
def get_low_stock_shelves(db: Session = Depends(get_db)):
    """
    Get all shelves that are low in stock (shelf quantity <= minimum shelf quantity).
    """
    return ShelfService.get_low_stock_shelves(db)

@router.post("/shelf/refill/{product_id}", response_model=InventoryMappingResponse, status_code=status.HTTP_200_OK)
def refill_shelf(product_id: int, db: Session = Depends(get_db)):
    """
    Refill the shelf from the warehouse for a specific product.
    """
    return ShelfService.refill_shelf(db, product_id)

@router.get("/refill/history", response_model=list[RefillLogResponse], status_code=status.HTTP_200_OK)
def get_refill_history(limit: int = 50, db: Session = Depends(get_db)):
    """
    Get historical log of shelf refill operations.
    """
    return ShelfService.get_refill_history(db, limit=limit)
