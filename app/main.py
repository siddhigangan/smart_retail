import os
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Import health & products routers
from app.api import health, products
from app.database.session import engine, Base, get_db
# Import models to register them on Base metadata
from app.models.product import Product

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
    return templates.TemplateResponse("index.html", {"request": request})

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
    if q:
        products = ProductService.search(db, q)
    else:
        products = ProductService.get_all(db)
        
    return templates.TemplateResponse("inventory.html", {
        "request": request,
        "stats": stats,
        "products": products,
        "search_query": q
    })

