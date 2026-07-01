from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date, Boolean, func
from app.database.session import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    barcode = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    price = Column(Numeric(10, 2), nullable=False) # Represents selling price
    quantity = Column(Integer, nullable=False) # Total quantity = shelf + warehouse
    reorder_level = Column(Integer, nullable=False, default=0)
    
    # Analytics fields
    movement_class = Column(String(50), nullable=True)
    expiry_date = Column(Date, nullable=True)
    cost_price = Column(Numeric(10, 2), nullable=True)
    max_stock_capacity = Column(Integer, nullable=True)

    # Extended Product Management fields
    brand = Column(String(100), nullable=True)
    sub_category = Column(String(100), nullable=True)
    description = Column(String, nullable=True)
    unit = Column(String(50), nullable=True)
    pack_size = Column(String(100), nullable=True)
    supplier = Column(String(100), nullable=True)
    mrp = Column(Numeric(10, 2), nullable=True)
    gst = Column(Numeric(10, 2), nullable=True) # GST percentage
    hsn_code = Column(String(50), nullable=True)
    expiry_required = Column(Boolean, default=False, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', barcode='{self.barcode}')>"
