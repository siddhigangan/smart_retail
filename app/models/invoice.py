from sqlalchemy import Column, Integer, String, Numeric, DateTime, func
from app.database.session import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    invoice_number = Column(String(50), unique=True, index=True, nullable=False)
    invoice_url = Column(String(255), nullable=False)
    pdf_path = Column(String(555), nullable=False)
    customer_name = Column(String(100), nullable=False)
    customer_phone = Column(String(15), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    whatsapp_status = Column(String(50), nullable=False, default="PENDING")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Invoice(number='{self.invoice_number}', customer='{self.customer_name}', amount={self.total_amount})>"
