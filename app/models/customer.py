from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from app.database.session import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=True)
    phone = Column(String(15), unique=True, index=True, nullable=False)
    email = Column(String(255), nullable=True)
    total_points = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    bills = relationship("Bill", back_populates="customer")

    def __repr__(self):
        return f"<Customer(id={self.id}, phone='{self.phone}', points={self.total_points})>"
