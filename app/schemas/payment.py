from uuid import UUID
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, UUID4

class PaymentRequest(BaseModel):
    uuid: UUID

class PaymentResponse(BaseModel):
    uuid: Optional[str] = None
    user_id:Optional[str] = None
    payment_id: Optional[str] = None
    payment_link: Optional[str] = None
    success_url: Optional[str] = None
    failure_url: Optional[str] = None
    plan_name: Optional[str] = None
    
class PaymentStatusResponse(BaseModel):
    uuid: UUID4
    user_id: Optional[str] = None
    payment_status: Optional[str] = None
    payment_id: Optional[str] = None
    paid_at: Optional[datetime] = None

    class Config:
        from_attributes = True
