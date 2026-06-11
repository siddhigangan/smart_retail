from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.product import Product

class InventoryService:
    @staticmethod
    def get_dashboard_stats(db: Session) -> dict:
        """
        Compute dashboard metrics:
        - total_products: Count of all unique products
        - total_quantity: Sum of stock quantities of all products
        - low_stock_count: Count of products where quantity <= reorder_level
        """
        total_products = db.query(func.count(Product.id)).scalar() or 0
        total_quantity = db.query(func.sum(Product.quantity)).scalar() or 0
        low_stock_count = db.query(func.count(Product.id)).filter(Product.quantity <= Product.reorder_level).scalar() or 0

        return {
            "total_products": total_products,
            "total_quantity": total_quantity,
            "low_stock_count": low_stock_count
        }
