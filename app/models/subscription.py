import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class Plan(Base):
    __tablename__ = "plans"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_title = Column(String, nullable=False, unique=True)
    pricing = Column(Numeric(10, 2), nullable=False)
    duration = Column(Integer, nullable=False)
    status = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    credits = Column(Integer, default=0)
    
    details = relationship("PlanDetail", back_populates="plan", cascade="all, delete-orphan")
    subscriptions = relationship("UserSubscription", back_populates="plan")

class Module(Base):
    __tablename__ = "modules"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    module_name = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True)
    status = Column(Boolean, default=True)
    type = Column(String, nullable=True, comment="credit, quantity")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    credits_required = Column(Numeric(10, 2), nullable=False, server_default="1.00")

    plan_details = relationship("PlanDetail", back_populates="module")

class PlanDetail(Base):
    __tablename__ = "plan_details"
    __table_args__ = (UniqueConstraint("plan_id", "module_id", name="uq_plan_module"),)
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    module_limit = Column(Integer)
    
    plan = relationship("Plan", back_populates="details")
    module = relationship("Module", back_populates="plan_details")

class UserSubscription(Base):
    __tablename__ = "user_subscription"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    plan_title = Column(String, default="freemium")
    purchase_at = Column(DateTime, default=datetime.utcnow)
    purchased_id = Column(String, nullable=True, unique=True)
    payment_status = Column(String, default="pending")
    amount_paid = Column(Numeric(10, 2), nullable=False)
    expiry_at = Column(DateTime, nullable=False)

    total_credits = Column(Integer, default=0)
    credits_used = Column(Integer, default=0)
    credits_left = Column(Integer, default=0)
    
    plan = relationship("Plan", back_populates="subscriptions")
