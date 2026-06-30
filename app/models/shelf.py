from sqlalchemy import Column, Integer, String
from app.database.session import Base

class Shelf(Base):
    __tablename__ = "shelves"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    floor_number = Column(Integer, nullable=False)
    aisle = Column(String(100), nullable=False)
    rack = Column(String(50), nullable=False)
    shelf_number = Column(String(100), unique=True, index=True, nullable=False)
    category = Column(String(100), nullable=False)

    def __repr__(self):
        return f"<Shelf(id={self.id}, shelf_number='{self.shelf_number}', floor={self.floor_number})>"
