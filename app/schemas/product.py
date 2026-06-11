from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict

class ProductBase(BaseModel):
    barcode: str = Field(..., min_length=1, description="Unique barcode identifier")
    name: str = Field(..., min_length=1, description="Name of the product")
    category: str = Field(..., min_length=1, description="Category of the product")
    price: Decimal = Field(..., description="Price of the product")
    quantity: int = Field(..., description="Available stock quantity")
    reorder_level: int = Field(0, description="Stock level threshold for reorder warnings")

    @field_validator('barcode', 'name', 'category')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """
        Strip whitespace from string fields to prevent blank/empty inputs.
        """
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or blank spaces.")
        return stripped

class ProductCreate(ProductBase):
    @field_validator('price')
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Price must be greater than 0.")
        return v

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Quantity cannot be negative.")
        return v

    @field_validator('reorder_level')
    @classmethod
    def validate_reorder_level(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Reorder level cannot be negative.")
        return v

class ProductResponse(ProductBase):
    id: int
    created_at: datetime

    # Config for SQLAlchemy ORM compatibility
    model_config = ConfigDict(from_attributes=True)

class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, description="Name of the product")
    category: str | None = Field(None, min_length=1, description="Category of the product")
    price: Decimal | None = Field(None, description="Price of the product")
    quantity: int | None = Field(None, description="Available stock quantity")
    reorder_level: int | None = Field(None, description="Stock level threshold for reorder warnings")

    @field_validator('name', 'category')
    @classmethod
    def strip_whitespace(cls, v: str | None) -> str | None:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Field cannot be empty or blank spaces.")
            return stripped
        return v

    @field_validator('price')
    @classmethod
    def validate_price(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("Price must be greater than 0.")
        return v

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("Quantity cannot be negative.")
        return v

    @field_validator('reorder_level')
    @classmethod
    def validate_reorder_level(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("Reorder level cannot be negative.")
        return v

