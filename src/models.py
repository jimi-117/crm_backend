# models.py
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, Text, DECIMAL, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base # database.py から Base をインポート

# demo_shema.sql の users テーブルに対応
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False) # UNIQUE, INDEX を追加
    role = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False) # 名前を password から hashed_password に変更（コードに合わせて）
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now()) # func.now()でデフォルト値を現在時刻に
    updated_at = Column(DateTime, onupdate=func.now()) # onupdateで更新時に現在時刻に

    # リレーションシップ: このユーザーが担当するクライアントとプロスペクト
    clients = relationship("Client", back_populates="owner")
    prospects = relationship("Prospect", back_populates="owner")


# demo_shema.sql の clients テーブルに対応
class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) #ForeignKey で users.id を参照
    name = Column(String, nullable=False)
    company_name = Column(String)
    business_category = Column(String, nullable=False)
    contact_email = Column(String)
    contact_phone = Column(String)
    status = Column(String)
    signed_date = Column(Date)
    estimated_monthly_revenue = Column(DECIMAL(10, 2))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # リレーションシップ: このクライアントを担当するユーザー
    owner = relationship("User", back_populates="clients")
    # リレーションシップ: このクライアントに紐づくコンテンツアイテム
    content_items = relationship("ContentItem", back_populates="client")


# demo_shema.sql の prospects テーブルに対応
class Prospect(Base):
    __tablename__ = "prospects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # ForeignKey で users.id を参照
    name = Column(String, nullable=False)
    company_name = Column(String)
    business_category = Column(String, nullable=False)
    contact_email = Column(String)
    contact_phone = Column(String)
    interest_level = Column(String)
    status = Column(String, nullable=False)
    next_follow_up_date = Column(Date)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # リレーションシップ: このプロスペクトを担当するユーザー
    owner = relationship("User", back_populates="prospects")


# demo_shema.sql の content_items テーブルに対応
class ContentItem(Base):
    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False) #ForeignKey で clients.id を参照
    content_type = Column(String, nullable=False)
    title = Column(String)
    description = Column(Text)
    instagram_post_url = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # リレーションシップ: このコンテンツアイテムが紐づくクライアント
    client = relationship("Client", back_populates="content_items")