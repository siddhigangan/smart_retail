from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict

class CartAdd(BaseModel):
    barcode: str = Field(..., min_length=1, description="Product barcode to add")
    quantity: int = Field(..., description="Quantity of product to buy")

    @field_validator('barcode')
    @classmethod
    def strip_barcode(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Barcode cannot be empty or blank.")
        return stripped

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantity must be greater than 0.")
        return v

class CartRemove(BaseModel):
    barcode: str = Field(..., min_length=1, description="Product barcode to remove")

    @field_validator('barcode')
    @classmethod
    def strip_barcode(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Barcode cannot be empty or blank.")
        return stripped

class CartItemResponse(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal

class BillItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    subtotal: Decimal

    model_config = ConfigDict(from_attributes=True)

class BillResponse(BaseModel):
    id: int
    total_amount: Decimal
    created_at: datetime
    items: list[BillItemResponse]

    model_config = ConfigDict(from_attributes=True)

class BillHistoryResponse(BaseModel):
    bill_number: int = Field(..., validation_alias="id", description="The generated bill ID")
    date: datetime = Field(..., validation_alias="created_at", description="The date the bill was generated")
    amount: Decimal = Field(..., validation_alias="total_amount", description="The total amount of the bill")

    model_config = ConfigDict(from_attributes=True)
