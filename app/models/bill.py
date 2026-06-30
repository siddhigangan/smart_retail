from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database.session import Base

class Bill(Base):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Customer link (nullable — walk-in customers have no record)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    # Denormalized snapshot at time of sale (so history is preserved even if customer record changes)
    customer_name = Column(String(100), nullable=True)
    customer_phone = Column(String(15), nullable=True)
    customer_email = Column(String(255), nullable=True)

    # Payment details
    payment_method = Column(String(50), nullable=True, default="Cash")
    cash_received = Column(Numeric(10, 2), nullable=True)
    change_returned = Column(Numeric(10, 2), nullable=True)
    split_cash = Column(Numeric(10, 2), nullable=True)
    split_upi = Column(Numeric(10, 2), nullable=True)
    split_card = Column(Numeric(10, 2), nullable=True)

    items = relationship("BillItem", back_populates="bill", cascade="all, delete-orphan")
    customer = relationship("Customer", back_populates="bills")

    def __repr__(self):
        return f"<Bill(id={self.id}, total_amount={self.total_amount})>"

class BillItem(Base):
    __tablename__ = "bill_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    bill_id = Column(Integer, ForeignKey("bills.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    bill = relationship("Bill", back_populates="items")
    product = relationship("Product")

    def __repr__(self):
        return f"<BillItem(id={self.id}, bill_id={self.bill_id}, product_id={self.product_id}, subtotal={self.subtotal})>"

