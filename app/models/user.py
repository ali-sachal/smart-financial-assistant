from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class Users(Base):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, index=True) # From JWT
    auto_sub = Column(Boolean, default=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=True)
    customer_id = Column(String, nullable=True)
    provider = Column(String, nullable=True)
    total_general_credits = Column(Integer, default=0)
    general_credits_used = Column(Integer, default=0)
    general_credits_left = Column(Integer, default=0)

    plan = relationship("Plan")
