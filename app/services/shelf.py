from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from decimal import Decimal
from fastapi import HTTPException, status
from app.models.shelf import Shelf
from app.models.inventory_mapping import InventoryMapping
from app.models.refill_log import RefillLog
from app.models.product import Product

class ShelfService:
    @staticmethod
    def get_shelves(
        db: Session,
        floor_number: int | None = None,
        category: str | None = None,
        low_stock_only: bool = False,
        search_query: str | None = None
    ) -> list[InventoryMapping]:
        query = db.query(InventoryMapping).join(Product).join(Shelf)
        
        if floor_number is not None:
            query = query.filter(Shelf.floor_number == floor_number)
            
        if category:
            query = query.filter(Shelf.category == category)
            
        if low_stock_only:
            query = query.filter(InventoryMapping.current_shelf_quantity <= InventoryMapping.minimum_shelf_quantity)
            
        if search_query:
            search_query_clean = f"%{search_query.strip()}%"
            query = query.filter(
                (Product.name.ilike(search_query_clean)) |
                (Product.barcode.ilike(search_query_clean))
            )
            
        return query.order_by(Shelf.floor_number.asc(), Shelf.aisle.asc(), Shelf.rack.asc()).all()

    @staticmethod
    def get_low_stock_shelves(db: Session) -> list[InventoryMapping]:
        return db.query(InventoryMapping).join(Product).join(Shelf).filter(
            InventoryMapping.current_shelf_quantity <= InventoryMapping.minimum_shelf_quantity
        ).order_by(Shelf.floor_number.asc(), Shelf.aisle.asc()).all()

    @staticmethod
    def refill_shelf(db: Session, product_id: int) -> InventoryMapping:
        mapping = db.query(InventoryMapping).filter(InventoryMapping.product_id == product_id).with_for_update().first()
        if not mapping:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Inventory mapping for product ID {product_id} not found"
            )
            
        product = db.query(Product).filter(Product.id == product_id).with_for_update().first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found"
            )
            
        if mapping.warehouse_quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Warehouse stock is empty, cannot refill shelf"
            )
            
        refill_needed = mapping.shelf_capacity - mapping.current_shelf_quantity
        if refill_needed <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shelf is already full"
            )
            
        actual_moved = min(refill_needed, mapping.warehouse_quantity)
        
        before_quantity = mapping.current_shelf_quantity
        warehouse_before = mapping.warehouse_quantity
        
        # Perform updates
        mapping.current_shelf_quantity += actual_moved
        mapping.warehouse_quantity -= actual_moved
        mapping.last_refilled_at = datetime.now()
        
        # Verify alignment of products.quantity
        product.quantity = mapping.current_shelf_quantity + mapping.warehouse_quantity
        
        # Create refill log
        log = RefillLog(
            product_id=product_id,
            quantity_moved=actual_moved,
            before_quantity=before_quantity,
            after_quantity=mapping.current_shelf_quantity,
            warehouse_before=warehouse_before,
            warehouse_after=mapping.warehouse_quantity,
            refilled_at=datetime.now()
        )
        db.add(log)
        db.commit()
        db.refresh(mapping)
        db.refresh(product)
        
        return mapping

    @staticmethod
    def get_refill_history(db: Session, limit: int = 50) -> list[RefillLog]:
        return db.query(RefillLog).join(Product).order_by(RefillLog.refilled_at.desc()).limit(limit).all()

    @staticmethod
    def get_analytics(db: Session) -> dict:
        # 1. Products needing refill
        needing_refill_count = db.query(func.count(InventoryMapping.id)).filter(
            InventoryMapping.current_shelf_quantity <= InventoryMapping.minimum_shelf_quantity
        ).scalar() or 0
        
        # 2. Most frequently refilled products
        freq_results = db.query(
            Product.name,
            func.count(RefillLog.id)
        ).join(RefillLog, RefillLog.product_id == Product.id).group_by(Product.name).order_by(
            func.count(RefillLog.id).desc()
        ).limit(5).all()
        most_frequent = [{"name": r[0], "count": r[1]} for r in freq_results]
        
        # 3. Warehouse stock value
        value_results = db.query(
            func.sum(InventoryMapping.warehouse_quantity * Product.price)
        ).join(Product, InventoryMapping.product_id == Product.id).scalar() or Decimal("0.00")
        warehouse_value = float(value_results)
        
        # 4. Shelf utilization %
        capacity_sum = db.query(func.sum(InventoryMapping.shelf_capacity)).scalar() or 1
        current_sum = db.query(func.sum(InventoryMapping.current_shelf_quantity)).scalar() or 0
        utilization = round((current_sum / capacity_sum) * 100, 2)
        
        # Summary counts
        total_shelves = db.query(func.count(Shelf.id)).scalar() or 0
        products_on_shelf = db.query(func.sum(InventoryMapping.current_shelf_quantity)).scalar() or 0
        warehouse_stock = db.query(func.sum(InventoryMapping.warehouse_quantity)).scalar() or 0
        
        return {
            "products_needing_refill": needing_refill_count,
            "most_frequently_refilled": most_frequent,
            "warehouse_stock_value": warehouse_value,
            "shelf_utilization_percent": utilization,
            "total_shelves": total_shelves,
            "products_on_shelf": products_on_shelf,
            "warehouse_stock": warehouse_stock,
            "pending_refills": needing_refill_count
        }
