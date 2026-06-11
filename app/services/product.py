from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate

class ProductService:
    @staticmethod
    def get_by_barcode(db: Session, barcode: str) -> Product:
        """
        Retrieve a product by its unique barcode.
        """
        return db.query(Product).filter(Product.barcode == barcode).first()

    @staticmethod
    def get_by_id(db: Session, product_id: int) -> Product:
        """
        Retrieve a single product by its database ID.
        Raises 404 error if not found.
        """
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found"
            )
        return product

    @staticmethod
    def get_all(db: Session) -> list[Product]:
        """
        Retrieve all products in the database.
        """
        return db.query(Product).all()

    @staticmethod
    def create(db: Session, product_in: ProductCreate) -> Product:
        """
        Create a new product in the database.
        Validates uniqueness of the barcode.
        """
        # Check for duplicate barcode
        existing_product = ProductService.get_by_barcode(db, product_in.barcode)
        if existing_product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with barcode '{product_in.barcode}' already exists"
            )
        
        # Convert schema to DB model
        db_product = Product(
            barcode=product_in.barcode,
            name=product_in.name,
            category=product_in.category,
            price=product_in.price,
            quantity=product_in.quantity,
            reorder_level=product_in.reorder_level
        )
        
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product

    @staticmethod
    def update(db: Session, product_id: int, product_in: ProductUpdate) -> Product:
        """
        Update an existing product record.
        """
        db_product = ProductService.get_by_id(db, product_id)
        
        # Extract fields provided in the update request
        update_data = product_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_product, field, value)
            
        db.commit()
        db.refresh(db_product)
        return db_product

    @staticmethod
    def delete(db: Session, product_id: int) -> dict:
        """
        Delete a product record from the database.
        """
        db_product = ProductService.get_by_id(db, product_id)
        db.delete(db_product)
        db.commit()
        return {"message": "Product deleted successfully"}

    @staticmethod
    def search(db: Session, query_str: str) -> list[Product]:
        """
        Search products case-insensitively by name, barcode, or category.
        """
        search_pattern = f"%{query_str}%"
        return db.query(Product).filter(
            or_(
                Product.barcode.ilike(search_pattern),
                Product.name.ilike(search_pattern),
                Product.category.ilike(search_pattern)
            )
        ).all()

    @staticmethod
    def get_low_stock(db: Session) -> list[Product]:
        """
        Retrieve all products whose quantity is less than or equal to their reorder_level.
        """
        return db.query(Product).filter(Product.quantity <= Product.reorder_level).all()

