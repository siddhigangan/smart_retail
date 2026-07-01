from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.inventory_mapping import InventoryMapping
from app.models.bill import BillItem

class InventoryService:
    @staticmethod
    def get_dynamic_movement_groups(db: Session) -> dict:
        """
        Classifies product IDs dynamically based on bill_items checkout counts.
        """
        # Check if there are any sales
        has_sales = db.query(func.count(BillItem.id)).scalar() > 0
        if not has_sales:
            return {
                "has_sales": False,
                "fast_ids": set(),
                "slow_ids": set(),
                "dead_ids": set()
            }
            
        # Get total units sold per product
        sales = db.query(
            BillItem.product_id,
            func.sum(BillItem.quantity)
        ).group_by(BillItem.product_id).all()
        
        sales_map = {row[0]: row[1] for row in sales}
        
        # Sort product IDs with sales by quantity sold descending
        sorted_sales = sorted(sales_map.items(), key=lambda x: x[1], reverse=True)
        sold_product_ids = [x[0] for x in sorted_sales]
        
        # Define Fast (top 20%) and Slow (bottom 20%) of the sold items
        fast_limit = max(1, len(sold_product_ids) // 5)
        fast_ids = set(sold_product_ids[:fast_limit])
        slow_ids = set(sold_product_ids[-fast_limit:])
        
        # Dead stock: registered products with 0 sales
        all_product_ids = [r[0] for r in db.query(Product.id).all()]
        dead_ids = set(all_product_ids) - set(sales_map.keys())
        
        return {
            "has_sales": True,
            "fast_ids": fast_ids,
            "slow_ids": slow_ids,
            "dead_ids": dead_ids
        }

    @staticmethod
    def get_dashboard_stats(db: Session) -> dict:
        """
        Compute dashboard metrics:
        - total_products: Count of all unique products
        - total_quantity: Sum of stock quantities of all products
        - low_stock_count: Count of products where quantity <= reorder_level
        - out_of_stock_count: Count of products where quantity = 0
        - shelf_refill_count: Count of products where current_shelf_quantity <= minimum_shelf_quantity
        - wh_empty_count: Count of products where warehouse_quantity = 0
        """
        total_products = db.query(func.count(Product.id)).scalar() or 0
        total_quantity = db.query(func.sum(Product.quantity)).scalar() or 0
        low_stock_count = db.query(func.count(Product.id)).filter(Product.quantity <= Product.reorder_level).scalar() or 0
        
        out_of_stock_count = db.query(func.count(Product.id)).filter(Product.quantity == 0).scalar() or 0
        
        shelf_refill_count = db.query(func.count(Product.id)).\
            join(InventoryMapping, Product.id == InventoryMapping.product_id).\
            filter(InventoryMapping.current_shelf_quantity <= InventoryMapping.minimum_shelf_quantity).scalar() or 0
            
        wh_empty_count = db.query(func.count(Product.id)).\
            join(InventoryMapping, Product.id == InventoryMapping.product_id).\
            filter(InventoryMapping.warehouse_quantity == 0).scalar() or 0

        return {
            "total_products": total_products,
            "total_quantity": total_quantity,
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
            "shelf_refill_count": shelf_refill_count,
            "wh_empty_count": wh_empty_count
        }

    @staticmethod
    def get_filtered_inventory(db: Session, filter_type: str) -> dict:
        """
        Get filtered products list and current count badges.
        """
        # Determine existence of expiry date in db
        has_expiry_date = db.query(func.count(Product.id)).filter(Product.expiry_date.isnot(None)).scalar() > 0

        # Query products
        products_query = db.query(Product)
        placeholder_message = None

        # Fetch dynamic movement classes based on bill_items checkout counts
        groups = InventoryService.get_dynamic_movement_groups(db)

        if filter_type == "low_stock":
            products_query = products_query.filter(Product.quantity <= Product.reorder_level)
        elif filter_type == "out_of_stock":
            products_query = products_query.filter(Product.quantity == 0)
        elif filter_type == "overstocked":
            products_query = products_query.filter(Product.quantity > Product.reorder_level * 5)
        elif filter_type == "fast_moving":
            if not groups["has_sales"]:
                placeholder_message = "Fast moving analytics will be available after sales history is generated."
                products_query = products_query.filter(Product.id == -1)
            else:
                products_query = products_query.filter(Product.id.in_(list(groups["fast_ids"])))
        elif filter_type == "slow_moving":
            if not groups["has_sales"]:
                placeholder_message = "Slow moving analytics will be available after sales history is generated."
                products_query = products_query.filter(Product.id == -1)
            else:
                products_query = products_query.filter(Product.id.in_(list(groups["slow_ids"])))
        elif filter_type == "expiring_soon":
            if not has_expiry_date:
                placeholder_message = "Expiry tracking will be available after expiry data is added."
                products_query = products_query.filter(Product.id == -1)
            else:
                products_query = products_query.filter(Product.expiry_date <= func.current_date() + 30)
        elif filter_type == "warehouse_empty":
            products_query = products_query.join(InventoryMapping, Product.id == InventoryMapping.product_id).\
                filter(InventoryMapping.warehouse_quantity == 0)
        elif filter_type == "shelf_refill_needed":
            products_query = products_query.join(InventoryMapping, Product.id == InventoryMapping.product_id).\
                filter(InventoryMapping.current_shelf_quantity <= InventoryMapping.minimum_shelf_quantity)
        
        products = products_query.all()

        # Compute badges count
        all_count = db.query(func.count(Product.id)).scalar() or 0
        low_stock_count = db.query(func.count(Product.id)).filter(Product.quantity <= Product.reorder_level).scalar() or 0
        out_of_stock_count = db.query(func.count(Product.id)).filter(Product.quantity == 0).scalar() or 0
        overstocked_count = db.query(func.count(Product.id)).filter(Product.quantity > Product.reorder_level * 5).scalar() or 0
        
        fast_count = len(groups["fast_ids"])
        slow_count = len(groups["slow_ids"])
            
        expiring_count = 0
        if has_expiry_date:
            expiring_count = db.query(func.count(Product.id)).filter(Product.expiry_date <= func.current_date() + 30).scalar() or 0

        wh_empty_count = db.query(func.count(Product.id)).\
            join(InventoryMapping, Product.id == InventoryMapping.product_id).\
            filter(InventoryMapping.warehouse_quantity == 0).scalar() or 0

        shelf_refill_count = db.query(func.count(Product.id)).\
            join(InventoryMapping, Product.id == InventoryMapping.product_id).\
            filter(InventoryMapping.current_shelf_quantity <= InventoryMapping.minimum_shelf_quantity).scalar() or 0

        # Form response product structures
        serialized_products = []
        for p in products:
            serialized_products.append({
                "id": p.id,
                "barcode": p.barcode,
                "name": p.name,
                "category": p.category,
                "price": float(p.price),
                "quantity": p.quantity,
                "reorder_level": p.reorder_level,
                "status": "Low Stock" if p.quantity <= p.reorder_level else "Healthy"
            })

        return {
            "products": serialized_products,
            "placeholder_message": placeholder_message,
            "counts": {
                "all": all_count,
                "low_stock": low_stock_count,
                "out_of_stock": out_of_stock_count,
                "overstocked": overstocked_count,
                "fast_moving": fast_count,
                "slow_moving": slow_count,
                "expiring_soon": expiring_count,
                "warehouse_empty": wh_empty_count,
                "shelf_refill_needed": shelf_refill_count
            }
        }
