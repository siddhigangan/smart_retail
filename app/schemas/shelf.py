from datetime import datetime
from pydantic import BaseModel, ConfigDict
from decimal import Decimal

class ShelfBase(BaseModel):
    floor_number: int
    aisle: str
    rack: str
    shelf_number: str
    category: str

class ShelfResponse(ShelfBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class ProductBriefResponse(BaseModel):
    id: int
    barcode: str
    name: str
    category: str
    price: Decimal

    model_config = ConfigDict(from_attributes=True)

class InventoryMappingResponse(BaseModel):
    id: int
    product_id: int
    shelf_id: int
    shelf_capacity: int
    current_shelf_quantity: int
    warehouse_quantity: int
    minimum_shelf_quantity: int
    last_refilled_at: datetime | None = None
    
    product: ProductBriefResponse
    shelf: ShelfResponse

    model_config = ConfigDict(from_attributes=True)

class RefillLogResponse(BaseModel):
    id: int
    product_id: int
    quantity_moved: int
    before_quantity: int
    after_quantity: int
    warehouse_before: int
    warehouse_after: int
    refilled_at: datetime
    
    product: ProductBriefResponse

    model_config = ConfigDict(from_attributes=True)
