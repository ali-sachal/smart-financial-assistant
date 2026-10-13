from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import UUID4
from decimal import Decimal

class PlanBase(BaseModel):
    plan_title: str
    pricing: Decimal
    duration: int
    status: bool = True
    credits : int 

class PlanModuleLimit(BaseModel):
    module_slug: str
    module_limit: int

class PlanCreate(PlanBase):
    modules: List[PlanModuleLimit] = Field(default_factory=list)

class SubscriptionPurchaseRequest(BaseModel):
    plan_id: int
    module_slug: Optional[str] = None
    uuid: Optional[UUID4] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    user_source: Optional[str] = None
    category_id: Optional[str] = None

class PlanUpdate(PlanBase):
    plan_title: Optional[str] = None
    pricing: Optional[Decimal] = None
    duration: Optional[int] = None
    status: Optional[bool] = None

class PlanInDBBase(PlanBase):
    id: int
    created_at: datetime
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)

class Plan(PlanInDBBase):
    pass

class ModuleBase(BaseModel):
    module_name: str
    slug: str
    status: bool = True
    type: str = "credit"
    credits_required: Decimal = Decimal("1.00")

    model_config = ConfigDict(from_attributes=True)

class ModuleCreate(ModuleBase):
    pass

class ModuleUpdate(ModuleBase):
    module_name: Optional[str] = None
    slug: Optional[str] = None
    status: Optional[bool] = None
    type: Optional[str] = None
    credits_required: Optional[Decimal] = None

class ModuleInDBBase(ModuleBase):
    id: int
    created_at: datetime
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)

class Module(ModuleInDBBase):
    pass

class PlanModuleDetail(BaseModel):
    module_id:  Optional[int] = None
    module_slug: str
    module_name: str
    module_limit: Optional[int] = None
    module_type: Optional[str] = None # "credit" or "quantity"

class PlanWithModules(PlanInDBBase):
    modules: List[PlanModuleDetail]
    subscribed: bool = False

class PlanDetailBase(BaseModel):
    plan_id: int
    module_slug: str
    module_limit: int

class PlanDetailCreate(PlanDetailBase):
    pass

class PlanDetailUpdate(BaseModel):
    module_limit: Optional[int] = None

class PlanDetailInDBBase(PlanDetailBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)

class PlanDetail(PlanDetailInDBBase):
    pass

class UserSubscriptionBase(BaseModel):
    user_id: str
    plan_id: int
    plan_title: str = "freemium"
    purchased_id: Optional[str] = None
    payment_status: str = "pending"
    amount_paid: Decimal
    expiry_at: datetime

class CreditDetail(BaseModel):
    total_credits: int
    credits_used: int
    credits_left: int

class UserSubscriptionCreate(UserSubscriptionBase):
    pass

class UserSubscriptionUpdate(BaseModel):
    expiry_at: Optional[datetime] = None

class UserSubscriptionInDBBase(UserSubscriptionBase):
    id: UUID
    purchase_at: datetime
    total_credits: int
    credits_used: int = 0
    credits_left: int

    model_config = ConfigDict(from_attributes=True)

class UserSubscription(UserSubscriptionInDBBase):
    pass

class UserCreditBase(BaseModel):
    user_id: str
    plan_id: Optional[int] = None
    user_subscription_id: Optional[UUID] = None
    module_slug: str
    total_credits: int
    credits_used: int = 0
    credits_left: int

class UserCreditCreate(UserCreditBase):
    pass

class UserCreditUpdate(BaseModel):
    credits_used: Optional[int] = None
    credits_left: Optional[int] = None

class UserCreditInDBBase(UserCreditBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)

class UserCredit(UserCreditInDBBase):
    pass


class ModuleOut(BaseModel):
    id: int
    module_name: str
    slug: Optional[str]
    status: Optional[bool] = None
    type: Optional[str] = None
    credits_required: Decimal = Decimal("1.00")

    model_config = ConfigDict(from_attributes=True)

class PlanDetailOut(BaseModel):
    id: UUID
    module_limit: int
    module: ModuleOut  # nested module

    model_config = ConfigDict(from_attributes=True)

class PlanOut(BaseModel):
    id: int
    plan_title: str
    pricing: float
    duration: int
    status: bool
    subscription: Optional[UserSubscriptionBase] = None
    details: List[PlanDetailOut] = []  # list of PlanDetail

    model_config = ConfigDict(from_attributes=True)
        
class UserOut(BaseModel):
    auto_sub: bool
    plan: Optional[PlanOut]
    model_config = ConfigDict(from_attributes=True)

class UserSettingsOut(BaseModel):
    active_plan_expiry_date: datetime
    plan_detail: Optional[UserOut]

    model_config = ConfigDict(from_attributes=True)

class subscrptionCancelPayload(BaseModel):
    auto_sub: Optional[bool]  = None

# New Schemas for Paginated Response with Module Stats

class ModuleStats(BaseModel):
    total_credits: int
    credits_used: int
    credits_left: int

class UserAutoSubSettingsOut(BaseModel):
    auto_sub: bool
    active_plan: Optional[Dict] = None

class PaginatedUserSubscriptions(BaseModel):
    data: List[UserSubscription]
    per_page: int
    total: int
    current_page: int
    next_page_url: Optional[str] = None
    prev_page_url: Optional[str] = None
    path: str

class AdminPurchaseItem(BaseModel):
    id: str
    type: str # "plan" or "one time payment"
    user_id: str
    title: str # plan_title or module_name
    amount_paid: Optional[float]
    payment_status: str
    purchase_at: Optional[datetime]
    payment_id: Optional[str]
    expiry_at: Optional[datetime] = None
    plan_id: Optional[int] = None
    module_id: Optional[int] = None
    modules_stats: Optional[Dict[str, CreditDetail]] = {}
    modules_name: Optional[str]

class PaginatedAdminPurchases(BaseModel):
    data: List[AdminPurchaseItem]
    per_page: int
    total: int
    current_page: int
    next_page_url: Optional[str] = None
    prev_page_url: Optional[str] = None
    path: str

# DataTables request schemas
class SearchModel(BaseModel):
    value: str = Field(default="", description="Global search value")
    regex: bool = Field(default=False, description="Whether to use regex for search")

class ColumnSearchModel(BaseModel):
    value: str = Field(default="", description="Column specific search value")
    regex: bool = Field(default=False, description="Whether to use regex for column search")

class ColumnModel(BaseModel):
    data: str = Field(..., description="Column's data source")
    name: Optional[str] = Field(default="", description="Column's name")
    searchable: bool = Field(default=True, description="Whether column is searchable")
    orderable: bool = Field(default=True, description="Whether column is orderable")
    search: ColumnSearchModel = Field(default_factory=ColumnSearchModel, description="Column search parameters")

class OrderModel(BaseModel):
    column: int = Field(..., description="Column index to order by")
    dir: str = Field(..., description="Ordering direction: asc or desc")

class DataTablesRequest(BaseModel):
    draw: int = Field(..., description="Draw counter for DataTables")
    start: int = Field(default=0, description="Paging first record indicator (offset)")
    length: int = Field(default=10, description="Number of records per page")
    search: SearchModel = Field(default_factory=SearchModel, description="Global search parameters")
    order: List[OrderModel] = Field(default_factory=list, description="Order/sort parameters")
    columns: List[ColumnModel] = Field(default_factory=list, description="Column definitions")

    class Config:
        json_schema_extra = {
            "example": {
                "draw": 1,
                "start": 0,
                "length": 1,
                "search": {
                    "value": "",
                    "regex": False
                },
                "order": [
                    {
                        "column": 0,
                        "dir": "asc"
                    }
                ],
                "columns": [
                    {
                        "data": "plan_title",
                        "name": "",
                        "searchable": True,
                        "orderable": True,
                        "search": {
                            "value": "",
                            "regex": False
                        }
                    },
                    {
                        "data": "payment_status",
                        "name": "",
                        "searchable": True,
                        "orderable": True,
                        "search": {
                            "value": "",
                            "regex": False
                        }
                    }
                ]
            }
        }
