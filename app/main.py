import os
from fastapi import FastAPI, Request, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Import health, products & billing routers
from app.api import health, products, billing, shelf, products_management
from app.database.session import engine, Base, get_db
# Import models to register them on Base metadata
from app.models.product import Product
from app.models.customer import Customer
from app.models.bill import Bill, BillItem
from app.models.shelf import Shelf
from app.models.inventory_mapping import InventoryMapping
from app.models.refill_log import RefillLog

# Import services for dashboard data rendering
from app.services.inventory import InventoryService
from app.services.product import ProductService


# Load .env configurations
load_dotenv()

# Create database tables automatically
Base.metadata.create_all(bind=engine)

# Initialize FastAPI application
app = FastAPI(
    title="Smart Retail System",
    description="Backend foundation for the Smart Retail System.",
    version="1.0.0"
)

# Mount static files (CSS, JS, etc.)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configure Jinja2 templates directory
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(health.router, prefix="/api")
app.include_router(products.router)
app.include_router(billing.router)
app.include_router(shelf.router)
app.include_router(products_management.router, prefix="/api")


@app.get("/", response_class=JSONResponse)
def get_root():
    """
    Root endpoint for Smart Retail health status.
    """
    return {"message": "Smart Retail Running"}

@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard(request: Request):
    """
    Renders the HTML Dashboard.
    """
    return templates.TemplateResponse(request, "index.html")

@app.get("/inventory-dashboard", response_class=HTMLResponse)
def get_inventory_dashboard(
    request: Request,
    q: str | None = None,
    db: Session = Depends(get_db)
):
    """
    Renders the visual Inventory Dashboard.
    """
    stats = InventoryService.get_dashboard_stats(db)
    
    # Fetch initial counts for quick buttons
    filter_data = InventoryService.get_filtered_inventory(db, "all")
    counts = filter_data["counts"]
    
    if q:
        products = ProductService.search(db, q)
    else:
        products = ProductService.get_all(db)
        
    return templates.TemplateResponse(request, "inventory.html", {
        "stats": stats,
        "counts": counts,
        "products": products,
        "search_query": q
    })

@app.get("/inventory/filter", response_class=JSONResponse)
def filter_inventory(
    type: str = Query("all"),
    db: Session = Depends(get_db)
):
    """
    API endpoint to retrieve filtered inventory products and counts dynamically.
    """
    data = InventoryService.get_filtered_inventory(db, type)
    return JSONResponse(content=data)

@app.get("/billing", response_class=HTMLResponse)
def get_billing(request: Request):
    """
    Renders the cashier billing screen.
    """
    return templates.TemplateResponse(request, "billing.html")

@app.get("/shelf-management", response_class=HTMLResponse)
def get_shelf_management(
    request: Request,
    floor_number: int | None = None,
    category: str | None = None,
    low_stock_only: bool = False,
    q: str | None = None,
    db: Session = Depends(get_db)
):
    """
    Renders the visual Shelf Management & Replenishment Dashboard.
    """
    # Fetch distinct categories and floors from shelves
    from app.models.shelf import Shelf
    categories = [r[0] for r in db.query(Shelf.category).distinct().all()]
    floors = [r[0] for r in db.query(Shelf.floor_number).distinct().order_by(Shelf.floor_number.asc()).all()]
    
    # Fetch shelves list
    from app.services.shelf import ShelfService
    shelves_list = ShelfService.get_shelves(
        db,
        floor_number=floor_number,
        category=category,
        low_stock_only=low_stock_only,
        search_query=q
    )
    
    # Fetch analytics
    analytics = ShelfService.get_analytics(db)
    
    # Fetch history
    history = ShelfService.get_refill_history(db, limit=10)
    
    return templates.TemplateResponse(request, "shelf_management.html", {
        "shelves": shelves_list,
        "categories": categories,
        "floors": floors,
        "selected_floor": floor_number,
        "selected_category": category,
        "low_stock_only": low_stock_only,
        "search_query": q,
        "analytics": analytics,
        "history": history
    })

@app.get("/inventory-analytics", response_class=HTMLResponse)
def inventory_analytics(
    request: Request,
    category: str = Query(None),
    floor: int = Query(None),
    movement_class: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Renders the visual Inventory Analytics Dashboard.
    """
    from app.services.analytics import AnalyticsService
    data = AnalyticsService.get_dashboard_data(
        db,
        category=category,
        floor=floor,
        movement_class=movement_class
    )
    return templates.TemplateResponse(request, "inventory_analytics.html", {
        "cards": data["cards"],
        "charts": data["charts"],
        "tables": data["tables"],
        "filters_options": data["filters_options"],
        "selected_category": category,
        "selected_floor": floor,
        "selected_movement_class": movement_class
    })

@app.get("/invoice/{invoice_number}", response_class=HTMLResponse)
def get_invoice_page(
    request: Request,
    invoice_number: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves invoice details and renders the HTML printable receipt view.
    """
    import math
    from fastapi import HTTPException
    from app.models.invoice import Invoice
    from app.models.bill import Bill
    from app.models.product import Product

    invoice = db.query(Invoice).filter(Invoice.invoice_number == invoice_number).first()
    if not invoice:
        raise HTTPException(status_code=404, detail=f"Invoice {invoice_number} not found.")

    # Find corresponding Bill
    db_bill = db.query(Bill).filter(
        Bill.customer_phone == invoice.customer_phone,
        Bill.total_amount == invoice.total_amount
    ).order_by(Bill.created_at.desc()).first()

    items = []
    total_quantity = 0
    if db_bill:
        for bi in db_bill.items:
            product = db.query(Product).filter(Product.id == bi.product_id).first()
            items.append({
                "barcode": product.barcode if product else "N/A",
                "product_name": product.name if product else f"Product #{bi.product_id}",
                "quantity": bi.quantity,
                "price": float(bi.unit_price),
                "subtotal": float(bi.subtotal)
            })
            total_quantity += bi.quantity

    # Calculate loyalty points earned: 1 point per Rs.10 spent
    loyalty_points = math.floor(float(invoice.total_amount) / 10)

    return templates.TemplateResponse(request, "invoice_view.html", {
        "invoice": invoice,
        "items": items,
        "total_quantity": total_quantity,
        "loyalty_points": loyalty_points
    })

@app.post("/admin/reset-transactions")
def reset_transactions(db: Session = Depends(get_db)):
    """
    Clears all bills, bill items, invoices, local PDF receipts,
    and resets customer loyalty points.
    """
    import os
    import shutil
    from fastapi import HTTPException
    from app.models.bill import Bill, BillItem
    from app.models.invoice import Invoice
    from app.models.customer import Customer

    try:
        # Delete transactional data records
        db.query(BillItem).delete()
        db.query(Bill).delete()
        db.query(Invoice).delete()

        # Reset customer loyalty points
        db.query(Customer).update({
            Customer.total_points: 0
        })

        # Clear local static PDF invoice files
        invoices_dir = "app/static/invoices"
        if os.path.exists(invoices_dir):
            for filename in os.listdir(invoices_dir):
                file_path = os.path.join(invoices_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    pass

        db.commit()
        return {
            "status": "success",
            "message": "All transactional data cleared successfully."
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset transactional data: {str(e)}"
        )

@app.get("/products-management", response_class=HTMLResponse)
def get_products_management_page(
    request: Request,
    q: str | None = Query(None),
    category: str | None = Query(None),
    supplier: str | None = Query(None),
    shelf_id: int | None = Query(None),
    filter_status: str | None = Query(None),
    db: Session = Depends(get_db)
):
    """
    Renders the central Products Management ERP dashboard.
    """
    from datetime import date, timedelta
    from app.models.product import Product
    from app.models.inventory_mapping import InventoryMapping
    from app.models.shelf import Shelf

    query = db.query(Product, InventoryMapping, Shelf).\
        outerjoin(InventoryMapping, Product.id == InventoryMapping.product_id).\
        outerjoin(Shelf, InventoryMapping.shelf_id == Shelf.id)

    if q:
        q_str = f"%{q.strip()}%"
        query = query.filter(
            (Product.name.ilike(q_str)) |
            (Product.barcode.ilike(q_str)) |
            (Product.category.ilike(q_str)) |
            (Product.brand.ilike(q_str)) |
            (Product.supplier.ilike(q_str)) |
            (Shelf.shelf_number.ilike(q_str))
        )

    if category:
        query = query.filter(Product.category == category)
    if supplier:
        query = query.filter(Product.supplier == supplier)
    if shelf_id:
        query = query.filter(Shelf.id == shelf_id)

    if filter_status == "low_stock":
        query = query.filter(Product.quantity <= Product.reorder_level)
    elif filter_status == "out_of_stock":
        query = query.filter(Product.quantity == 0)
    elif filter_status == "expiring":
        query = query.filter(Product.expiry_date.between(date.today(), date.today() + timedelta(days=30)))

    records = query.all()

    # Form products structures
    products_list = []
    for p, m, s in records:
        products_list.append({
            "id": p.id,
            "barcode": p.barcode,
            "name": p.name,
            "category": p.category,
            "brand": p.brand or "N/A",
            "shelf_number": s.shelf_number if s else "Unassigned",
            "shelf_quantity": m.current_shelf_quantity if m else 0,
            "warehouse_quantity": m.warehouse_quantity if m else 0,
            "selling_price": float(p.price),
            "mrp": float(p.mrp) if p.mrp else float(p.price),
            "gst": float(p.gst) if p.gst else 0.0,
            "supplier": p.supplier or "N/A",
            "status": "Low Stock" if p.quantity <= p.reorder_level else "Healthy"
        })

    # Dropdown selections helper lists
    all_categories = [r[0] for r in db.query(Product.category).distinct().all() if r[0]]
    all_suppliers = [r[0] for r in db.query(Product.supplier).distinct().all() if r[0]]
    all_shelves = db.query(Shelf).all()

    return templates.TemplateResponse(request, "products_management.html", {
        "products": products_list,
        "categories": sorted(all_categories),
        "suppliers": sorted(all_suppliers),
        "shelves": all_shelves,
        "q": q or "",
        "selected_category": category or "",
        "selected_supplier": supplier or "",
        "selected_shelf_id": shelf_id or "",
        "selected_status": filter_status or ""
    })






