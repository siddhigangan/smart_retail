from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.session import Base

class AdjustmentLog(Base):
    __tablename__ = "adjustment_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    barcode = Column(String(50), nullable=False)
    quantity_changed = Column(Integer, nullable=False)
    before_quantity = Column(Integer, nullable=False)
    after_quantity = Column(Integer, nullable=False)
    reason = Column(String(100), nullable=False)
    adjusted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    product = relationship("Product")

    def __repr__(self):
        return f"<AdjustmentLog(id={self.id}, barcode='{self.barcode}', changed={self.quantity_changed}, reason='{self.reason}')>"
