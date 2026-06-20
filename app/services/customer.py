from sqlalchemy.orm import Session
from app.models.customer import Customer
import math


class CustomerService:

    @classmethod
    def get_or_create(cls, db: Session, phone: str, name: str = None, email: str = None) -> Customer:
        """
        Find an existing customer by phone number or create a new one.
        Updates name/email if they've changed.
        """
        customer = db.query(Customer).filter(Customer.phone == phone).first()

        if customer:
            # Update fields if new data provided
            if name and name != customer.name:
                customer.name = name
            if email and email != customer.email:
                customer.email = email
            db.flush()
        else:
            customer = Customer(
                phone=phone,
                name=name,
                email=email,
                total_points=0
            )
            db.add(customer)
            db.flush()

        return customer

    @classmethod
    def add_points(cls, db: Session, customer_id: int, bill_total: float) -> int:
        """
        Add loyalty points to a customer: 1 point per Rs.10 spent.
        Returns the number of points earned this transaction.
        """
        points_earned = math.floor(float(bill_total) / 10)
        if points_earned > 0:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if customer:
                customer.total_points += points_earned
                db.flush()
        return points_earned

    @classmethod
    def get_by_phone(cls, db: Session, phone: str) -> Customer | None:
        return db.query(Customer).filter(Customer.phone == phone).first()
