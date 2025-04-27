# schemas.py
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from datetime import date, datetime
from typing import Optional, List, Literal

# ユーザー作成用のリクエストボディモデル
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str = "user"  # デフォルトは通常ユーザー
    name: str
    city: str

# ユーザー更新用のリクエストボディモデル
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[str] = None
    name: Optional[str] = None
    city: Optional[str] = None
    is_active: Optional[bool] = None

# クライアントステータス - 新しいリテラル型
ClientStatusType = Literal["to_do", "in_progress", "done"]

# クライアント作成時のリクエストボディ用モデル
class ClientCreate(BaseModel):
    name: str
    company_name: Optional[str] = None
    business_category: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    status: Optional[ClientStatusType] = "to_do"  # デフォルト値を設定
    signed_date: Optional[date] = None
    estimated_monthly_revenue: Optional[float] = None  # decimal は float で扱う

# クライアント情報のレスポンス用モデル
class Client(BaseModel):
    id: int
    user_id: int
    name: str
    company_name: Optional[str] = None
    business_category: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    status: Optional[str] = None
    signed_date: Optional[date] = None
    estimated_monthly_revenue: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# プロスペクトステータス - 新しいリテラル型
ProspectStatusType = Literal[
    "new_inquiry", 
    "contact_attempted_phone", 
    "contact_attempted_email", 
    "contacted_no_response", 
    "meeting_scheduled", 
    "waiting_for_feedback", 
    "follow_up_needed", 
    "qualified", 
    "converted", 
    "disqualified"
]

# プロスペクト作成時のリクエストボディ用モデル
class ProspectCreate(BaseModel):
    name: str
    company_name: Optional[str] = None
    business_category: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    interest_level: Optional[str] = None
    status: ProspectStatusType = "new_inquiry"  # デフォルト値を設定
    next_follow_up_date: Optional[date] = None
    notes: Optional[str] = None

# プロスペクト情報のレスポンス用モデル
class Prospect(BaseModel):
    id: int
    user_id: int
    name: str
    company_name: Optional[str] = None
    business_category: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    interest_level: Optional[str] = None
    status: str
    next_follow_up_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# コンテンツアイテム作成時のリクエストボディ用モデル
class ContentItemCreate(BaseModel):
    content_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    instagram_post_url: str

# コンテンツアイテム情報のレスポンス用モデル
class ContentItem(BaseModel):
    id: int
    client_id: int
    content_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    instagram_post_url: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# ユーザー情報のレスポンス用モデル (パスワードなどは含めない)
class User(BaseModel):
    id: int
    email: str
    role: str
    name: str
    city: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)