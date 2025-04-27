# schemas.py
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

# クライアント作成時のリクエストボディ用モデル
class ClientCreate(BaseModel):
    name: str
    company_name: Optional[str] = None
    business_category: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    status: Optional[str] = None
    # signed_date, estimated_monthly_revenue は契約後に設定される可能性があるので、作成時は含めない設計も考えられます
    
    signed_date: Optional[date] = None
    estimated_monthly_revenue: Optional[float] = None # decimal は float で扱う

# クライアント情報のレスポンス用モデル
# データベースから取得したORMオブジェクトをこのモデルに変換して返します
class Client(ClientCreate):
    id: int
    user_id: int
    signed_date: Optional[date] = None
    estimated_monthly_revenue: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    # ORM モデルを Pydantic モデルにマッピングするために必要
    class Config:
        orm_mode = True # Deprecated: from FastAPI 0.110 onwards, use `model_config = ConfigDict(from_attributes=True)`
        # 新しいPydanticの書き方 (Pydantic v2以降)
        # from pydantic import ConfigDict
        # model_config = ConfigDict(from_attributes=True)


# プロスペクト作成時のリクエストボディ用モデル
class ProspectCreate(BaseModel):
    name: str
    company_name: Optional[str] = None
    business_category: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    interest_level: Optional[str] = None
    status: str
    next_follow_up_date: Optional[date] = None
    notes: Optional[str] = None

# プロスペクト情報のレスポンス用モデル
class Prospect(ProspectCreate):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        # 新しいPydanticの書き方
        # from pydantic import ConfigDict
        # model_config = ConfigDict(from_attributes=True)


# コンテンツアイテム作成時のリクエストボディ用モデル
class ContentItemCreate(BaseModel):
    # client_id はパスパラメータなどで受け取る可能性もある
    content_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    instagram_post_url: str

# コンテンツアイテム情報のレスポンス用モデル
class ContentItem(ContentItemCreate):
    id: int
    client_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        # 新しいPydanticの書き方
        # from pydantic import ConfigDict
        # model_config = ConfigDict(from_attributes=True)


# ユーザー情報のレスポンス用モデル (パスワードなどは含めない)
class User(BaseModel):
    id: int
    email: str
    role: str
    name: str
    city: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        # 新しいPydanticの書き方
        # from pydantic import ConfigDict
        # model_config = ConfigDict(from_attributes=True)

# 認証ユーザー情報 (auth.py で定義したものと同じにするか、こちらを正規とする)
# from auth import TokenData # もし auth.py に既に定義があればそちらを使う
# class TokenData(BaseModel):
#     id: int | None = None
#     role: str
#     city: str | None = None