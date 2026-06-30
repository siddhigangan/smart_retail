from sqlalchemy import Column, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.session import Base

class RefillLog(Base):
    __tablename__ = "refill_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity_moved = Column(Integer, nullable=False)
    before_quantity = Column(Integer, nullable=False)
    after_quantity = Column(Integer, nullable=False)
    warehouse_before = Column(Integer, nullable=False)
    warehouse_after = Column(Integer, nullable=False)
    refilled_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    product = relationship("Product")

    def __repr__(self):
        return f"<RefillLog(id={self.id}, product_id={self.product_id}, moved={self.quantity_moved})>"
