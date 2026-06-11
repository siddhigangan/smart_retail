
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product import ProductService

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product_in: ProductCreate, db: Session = Depends(get_db)):
    """
    Create a new product record.
    """
    return ProductService.create(db, product_in)

@router.get("", response_model=list[ProductResponse], status_code=status.HTTP_200_OK)
def get_products(db: Session = Depends(get_db)):
    """
    Retrieve all products.
    """
    return ProductService.get_all(db)

@router.get("/search", response_model=list[ProductResponse], status_code=status.HTTP_200_OK)
def search_products(q: str, db: Session = Depends(get_db)):
    """
    Search products case-insensitively by name, barcode, or category.
    """
    return ProductService.search(db, q)

@router.get("/low-stock", response_model=list[ProductResponse], status_code=status.HTTP_200_OK)
def get_low_stock_products(db: Session = Depends(get_db)):
    """
    Retrieve products that are low in stock (quantity <= reorder_level).
    """
    return ProductService.get_low_stock(db)

@router.get("/{id}", response_model=ProductResponse, status_code=status.HTTP_200_OK)
def get_product(id: int, db: Session = Depends(get_db)):
    """
    Retrieve a product by its database ID.
    """
    return ProductService.get_by_id(db, id)

@router.put("/{id}", response_model=ProductResponse, status_code=status.HTTP_200_OK)
def update_product(id: int, product_in: ProductUpdate, db: Session = Depends(get_db)):
    """
    Update details of a product by ID.
    """
    return ProductService.update(db, id, product_in)

@router.delete("/{id}", status_code=status.HTTP_200_OK)
def delete_product(id: int, db: Session = Depends(get_db)):
    """
    Delete a product by ID.
    """
    return ProductService.delete(db, id)

