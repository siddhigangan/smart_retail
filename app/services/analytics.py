from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, Float
from app.models.product import Product
from app.models.inventory_mapping import InventoryMapping
from app.models.shelf import Shelf
from decimal import Decimal
from datetime import date
from app.services.inventory import InventoryService

class AnalyticsService:
    @classmethod
    def get_dashboard_data(
        cls,
        db: Session,
        category: str = None,
        floor: int = None,
        movement_class: str = None
    ) -> dict:
        # Fetch dynamic movement classes based on checkout stats
        groups = InventoryService.get_dynamic_movement_groups(db)

        # Base query joining Product, InventoryMapping, and Shelf
        query = db.query(Product, InventoryMapping, Shelf).\
            join(InventoryMapping, Product.id == InventoryMapping.product_id).\
            join(Shelf, InventoryMapping.shelf_id == Shelf.id)

        # Apply filters
        if category and category.strip():
            query = query.filter(Product.category == category.strip())
        if floor is not None:
            query = query.filter(Shelf.floor_number == floor)
            
        # Filter by dynamic movement class if requested
        if movement_class and movement_class.strip():
            if movement_class == "Fast":
                query = query.filter(Product.id.in_(list(groups["fast_ids"])))
            elif movement_class == "Slow":
                query = query.filter(Product.id.in_(list(groups["slow_ids"])))
            elif movement_class == "Dead":
                query = query.filter(Product.id.in_(list(groups["dead_ids"])))
            elif movement_class == "Medium":
                # Medium items are items with sales that are not Fast or Slow
                # i.e., sold items not in fast_ids or slow_ids
                sold_non_fast_slow = groups["has_sales"] and (groups["fast_ids"] | groups["slow_ids"])
                if sold_non_fast_slow:
                    query = query.filter(Product.id.notin_(list(sold_non_fast_slow))).filter(Product.id.notin_(list(groups["dead_ids"])))
                else:
                    query = query.filter(Product.id.notin_(list(groups["dead_ids"])))

        filtered_records = query.all()

        # 1. KPI Cards Calculations
        total_products = len(filtered_records)
        inventory_value = Decimal("0.00")
        low_stock_count = 0
        out_of_stock_count = 0
        dead_stock_count = 0
        overstocked_count = 0

        total_shelf_qty = 0
        total_shelf_cap = 0
        total_wh_qty = 0
        total_wh_cap = 0

        for prod, mapping, shelf in filtered_records:
            total_qty = prod.quantity
            cost = prod.cost_price if prod.cost_price is not None else Decimal("0.00")
            
            # Value = total quantity * cost_price
            inventory_value += Decimal(str(total_qty)) * cost

            # Low stock criteria
            if total_qty <= prod.reorder_level or mapping.current_shelf_quantity <= mapping.minimum_shelf_quantity:
                low_stock_count += 1

            # Out of stock
            if total_qty <= 0:
                out_of_stock_count += 1

            # Dead stock (dynamic check)
            if prod.id in groups["dead_ids"]:
                dead_stock_count += 1

            # Overstocked
            max_cap = prod.max_stock_capacity if prod.max_stock_capacity is not None else 0
            if max_cap > 0 and total_qty > max_cap:
                overstocked_count += 1

            # Shelf stats
            total_shelf_qty += mapping.current_shelf_quantity
            total_shelf_cap += mapping.shelf_capacity

            # Warehouse stats
            total_wh_qty += mapping.warehouse_quantity
            wh_cap = max_cap - mapping.shelf_capacity
            if wh_cap > 0:
                total_wh_cap += wh_cap

        shelf_utilization = 0.0
        if total_shelf_cap > 0:
            shelf_utilization = round((total_shelf_qty / total_shelf_cap) * 100, 1)

        wh_utilization = 0.0
        if total_wh_cap > 0:
            wh_utilization = round((total_wh_qty / total_wh_cap) * 100, 1)

        # 2. Charts Data (grouped by category)
        cat_data = {}
        for prod, mapping, shelf in filtered_records:
            cat = prod.category
            cost = prod.cost_price if prod.cost_price is not None else Decimal("0.00")
            val = Decimal(str(prod.quantity)) * cost

            if cat not in cat_data:
                cat_data[cat] = {
                    "count": 0,
                    "stock": 0,
                    "value": Decimal("0.00")
                }
            cat_data[cat]["count"] += 1
            cat_data[cat]["stock"] += prod.quantity
            cat_data[cat]["value"] += val

        categories_labels = list(cat_data.keys())
        cat_counts = [cat_data[c]["count"] for c in categories_labels]
        cat_stocks = [cat_data[c]["stock"] for c in categories_labels]
        cat_values = [float(cat_data[c]["value"]) for c in categories_labels]

        # Top 5 Categories by Value
        top_cats = sorted(cat_data.items(), key=lambda x: x[1]["value"], reverse=True)[:5]
        top_cat_labels = [x[0] for x in top_cats]
        top_cat_values = [float(x[1]["value"]) for x in top_cats]

        charts = {
            "category_distribution": {
                "labels": categories_labels,
                "data": cat_counts
            },
            "stock_distribution": {
                "labels": categories_labels,
                "data": cat_stocks
            },
            "value_distribution": {
                "labels": categories_labels,
                "data": cat_values
            },
            "top_categories": {
                "labels": top_cat_labels,
                "data": top_cat_values
            }
        }

        # 3. Tabular Lists (limited to top 15 records each)
        fast_moving = []
        slow_moving = []
        dead_stock = []
        expiring_soon = []
        wh_empty = []

        for prod, mapping, shelf in filtered_records:
            item_info = {
                "id": prod.id,
                "name": prod.name,
                "barcode": prod.barcode,
                "category": prod.category,
                "price": float(prod.price),
                "cost_price": float(prod.cost_price) if prod.cost_price else 0.0,
                "quantity": prod.quantity,
                "shelf_quantity": mapping.current_shelf_quantity,
                "warehouse_quantity": mapping.warehouse_quantity,
                "movement_class": "Fast" if prod.id in groups["fast_ids"] else ("Slow" if prod.id in groups["slow_ids"] else ("Dead" if prod.id in groups["dead_ids"] else "Medium")),
                "expiry_date": prod.expiry_date.strftime("%Y-%m-%d") if prod.expiry_date else "N/A"
            }

            if prod.id in groups["fast_ids"]:
                fast_moving.append(item_info)
            elif prod.id in groups["slow_ids"]:
                slow_moving.append(item_info)
            elif prod.id in groups["dead_ids"]:
                dead_stock.append(item_info)

            if prod.expiry_date:
                expiring_soon.append((prod.expiry_date, item_info))

            if mapping.warehouse_quantity == 0:
                wh_empty.append(item_info)

        # Sort and limit lists
        fast_moving = sorted(fast_moving, key=lambda x: x["quantity"], reverse=True)[:15]
        slow_moving = sorted(slow_moving, key=lambda x: x["quantity"])[:15]
        dead_stock = sorted(dead_stock, key=lambda x: x["quantity"])[:15]
        
        # Sort expiring soon by date ascending
        expiring_soon = [x[1] for x in sorted(expiring_soon, key=lambda x: x[0])][:15]
        wh_empty = sorted(wh_empty, key=lambda x: x["shelf_quantity"])[:15]

        # Get list of unique categories and movement classes in DB
        all_categories = [r[0] for r in db.query(Product.category).distinct().all()]
        all_movement_classes = ["Fast", "Medium", "Slow", "Dead"] if groups["has_sales"] else []

        return {
            "cards": {
                "inventory_value": float(inventory_value),
                "total_products": total_products,
                "low_stock": low_stock_count,
                "out_of_stock": out_of_stock_count,
                "dead_stock": dead_stock_count,
                "overstocked": overstocked_count,
                "shelf_utilization": shelf_utilization,
                "warehouse_utilization": wh_utilization
            },
            "charts": charts,
            "tables": {
                "fast_moving": fast_moving,
                "slow_moving": slow_moving,
                "dead_stock": dead_stock,
                "expiring_soon": expiring_soon,
                "warehouse_empty": wh_empty
            },
            "filters_options": {
                "categories": sorted(all_categories),
                "movement_classes": all_movement_classes,
                "floors": [0, 1, 2]
            }
        }
