from fastapi import APIRouter, Depends, status, UploadFile, File, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.product_management import ProductManagementService
from app.models.product import Product
from app.models.inventory_mapping import InventoryMapping
from decimal import Decimal
import io
import json

router = APIRouter(
    prefix="/products-management",
    tags=["Product Management"]
)

@router.get("/recommend-shelves")
def recommend_shelves(category: str = Query(None), db: Session = Depends(get_db)):
    """
    Query shelves table and display recommended shelves for product category.
    """
    return ProductManagementService.get_shelf_recommendations(db, category)

@router.get("/template")
def download_template():
    """
    Generates and downloads the bulk import CSV template.
    """
    template_content = ProductManagementService.get_download_template()
    stream = io.StringIO(template_content)
    response = StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv"
    )
    response.headers["Content-Disposition"] = "attachment; filename=products_import_template.csv"
    return response

@router.post("/manual-add", status_code=status.HTTP_201_CREATED)
def manual_add(data: dict, db: Session = Depends(get_db)):
    """
    Endpoint for manual product entry.
    """
    # Quick inline validation check
    errors = ProductManagementService.validate_product_data(
        db=db,
        barcode=data.get("barcode"),
        name=data.get("name"),
        category=data.get("category"),
        price=data.get("selling_price", 0),
        cost_price=data.get("cost_price"),
        quantity=data.get("quantity", 0),
        reorder_level=data.get("reorder_level", 0)
    )
    if errors:
        raise HTTPException(status_code=400, detail=", ".join(errors))
        
    try:
        prod = ProductManagementService.manual_add_product(db, data)
        return {
            "status": "success",
            "message": "Product created successfully.",
            "product_id": prod.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import/validate")
async def import_validate(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Step 2/3 of Bulk Import: parse, validate, and separate records.
    """
    content = await file.read()
    try:
        rows = ProductManagementService.parse_import_file(content, file.filename)
        preview_data = ProductManagementService.validate_and_preview_import(db, rows)
        return {
            "status": "success",
            "total_records": len(rows),
            "preview": preview_data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

@router.post("/import/commit")
def import_commit(data: dict, db: Session = Depends(get_db)):
    """
    Step 4 of Bulk Import: executes the database writes for valid rows.
    """
    valid_records = data.get("valid_records", [])
    if not valid_records:
        raise HTTPException(status_code=400, detail="No valid records provided for import.")
        
    summary = ProductManagementService.execute_import(db, valid_records)
    return {
        "status": "success",
        "message": "Bulk import completed successfully.",
        "summary": summary
    }

@router.post("/bulk-update")
def bulk_update(data: dict, db: Session = Depends(get_db)):
    """
    Endpoint for Bulk Stock Update.
    """
    updates_list = data.get("updates", [])
    if not updates_list:
        raise HTTPException(status_code=400, detail="No updates list provided.")
        
    result = ProductManagementService.bulk_stock_update(db, updates_list)
    return {
        "status": "success",
        "message": f"Successfully updated {result['updated']} items. Failed: {result['failed']}",
        "summary": result
    }

@router.post("/adjust")
def adjust_inventory(data: dict, db: Session = Depends(get_db)):
    """
    Endpoint for Inventory Adjustment (Damaged, Expired, Lost, etc.).
    """
    barcode = data.get("barcode")
    quantity_changed = data.get("quantity_changed")
    reason = data.get("reason")
    
    if not barcode or quantity_changed is None or not reason:
        raise HTTPException(status_code=400, detail="Barcode, quantity_changed, and reason are required.")
        
    try:
        res = ProductManagementService.adjust_inventory(db, barcode, int(quantity_changed), reason)
        return {
            "status": "success",
            "message": "Inventory adjustment registered successfully.",
            "data": res
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile/{product_id}")
def get_profile(product_id: int, db: Session = Depends(get_db)):
    """
    Fetches the comprehensive Product Profile details.
    """
    profile = ProductManagementService.get_product_profile(db, product_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Product profile not found.")
    return profile

@router.put("/edit/{product_id}")
def edit_product(product_id: int, data: dict, db: Session = Depends(get_db)):
    """
    Updates basic product attributes and stock mappings.
    """
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found.")
        
    try:
        prod.name = data["name"].strip()
        prod.brand = data.get("brand")
        prod.category = data["category"].strip()
        prod.sub_category = data.get("sub_category")
        prod.supplier = data.get("supplier")
        prod.price = Decimal(str(data["selling_price"]))
        prod.cost_price = Decimal(str(data["cost_price"])) if data.get("cost_price") else None
        prod.mrp = Decimal(str(data["mrp"])) if data.get("mrp") else None
        prod.gst = Decimal(str(data["gst"])) if data.get("gst") else None
        prod.hsn_code = data.get("hsn_code")
        prod.reorder_level = int(data.get("reorder_level", 0))
        
        # Keep total quantity aligned with mapping sum
        mapping = db.query(InventoryMapping).filter(InventoryMapping.product_id == prod.id).first()
        if mapping:
            mapping.shelf_capacity = int(data.get("shelf_capacity", mapping.shelf_capacity))
            mapping.current_shelf_quantity = int(data.get("current_shelf_quantity", mapping.current_shelf_quantity))
            mapping.warehouse_quantity = int(data.get("warehouse_quantity", mapping.warehouse_quantity))
            prod.quantity = mapping.current_shelf_quantity + mapping.warehouse_quantity
            
            # Update shelf allocation if shelf_id is passed
            if data.get("shelf_id"):
                mapping.shelf_id = int(data["shelf_id"])

        db.commit()
        return {
            "status": "success",
            "message": "Product details updated successfully."
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """
    Removes product and mappings records.
    """
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found.")
        
    try:
        db.delete(prod)
        db.commit()
        return {
            "status": "success",
            "message": "Product deleted successfully."
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
