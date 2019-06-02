from sqlalchemy import Column, Integer, String
from database import Base

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    distance = Column(Integer(), nullable=False)
    status = Column(String(20), nullable=False)

    def __init__(self, distance=None, status=None):
        self.distance = distance
        self.status = status
    def to_dict(self):
        cols = ["id", "distance", "status"]
        return dict((col, getattr(self, col)) for col in cols)
    def __repr__(self):
        return f"<Order(id={self.id}, distance={self.distance}, status={self.status})>"