from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base

class InventoryMapping(Base):
    __tablename__ = "inventory_mappings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, unique=True)
    shelf_id = Column(Integer, ForeignKey("shelves.id", ondelete="CASCADE"), nullable=False)
    shelf_capacity = Column(Integer, nullable=False)
    current_shelf_quantity = Column(Integer, nullable=False)
    warehouse_quantity = Column(Integer, nullable=False)
    minimum_shelf_quantity = Column(Integer, nullable=False)
    last_refilled_at = Column(DateTime(timezone=True), nullable=True)

    product = relationship("Product")
    shelf = relationship("Shelf")

    def __repr__(self):
        return f"<InventoryMapping(id={self.id}, product_id={self.product_id}, shelf_id={self.shelf_id})>"
