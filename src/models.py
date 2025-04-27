# models.py
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, Text, DECIMAL, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database import Base # database.py から Base をインポート

# demo_shema.sql の users テーブルに対応
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True) # serial は Integer で表現される
    email = Column(String, unique=True, index=True, nullable=False) # varchar255 は String で、UNIQUE, INDEX を追加
    role = Column(String, nullable=False) # varchar50 は String
    hashed_password = Column(String, nullable=False) # varchar255 は String。名前を password から hashed_password に変更（コードに合わせて）
    name = Column(String, nullable=False) # varchar255 は String
    city = Column(String, nullable=False) # varchar100 は String
    is_active = Column(Boolean, default=True, nullable=False) # bool は Boolean
    created_at = Column(DateTime, server_default=func.now()) # timestamp は DateTime, func.now()でデフォルト値を現在時刻に
    updated_at = Column(DateTime, onupdate=func.now()) # timestamp は DateTime, onupdateで更新時に現在時刻に

    # リレーションシップ: このユーザーが担当するクライアントとプロスペクト
    clients = relationship("Client", back_populates="owner")
    prospects = relationship("Prospect", back_populates="owner")


# demo_shema.sql の clients テーブルに対応
class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True) # serial は Integer で表現される
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # int は Integer, ForeignKey で users.id を参照
    name = Column(String, nullable=False) # varchar255 は String
    company_name = Column(String) # varchar255 は String
    business_category = Column(String, nullable=False) # varchar50 は String
    contact_email = Column(String) # varchar50 は String
    contact_phone = Column(String) # varchar50 は String
    status = Column(String) # varchar50 は String
    signed_date = Column(Date) # date は Date
    estimated_monthly_revenue = Column(DECIMAL(10, 2)) # decimal(10,2) は DECIMAL(10,2)
    created_at = Column(DateTime, server_default=func.now()) # timestamp は DateTime
    updated_at = Column(DateTime, onupdate=func.now()) # timestamp は DateTime

    # リレーションシップ: このクライアントを担当するユーザー
    owner = relationship("User", back_populates="clients")
    # リレーションシップ: このクライアントに紐づくコンテンツアイテム
    content_items = relationship("ContentItem", back_populates="client")


# demo_shema.sql の prospects テーブルに対応
class Prospect(Base):
    __tablename__ = "prospects"

    id = Column(Integer, primary_key=True, index=True) # serial は Integer で表現される
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # int は Integer, ForeignKey で users.id を参照
    name = Column(String, nullable=False) # varchar255 は String
    company_name = Column(String) # varchar255 は String
    business_category = Column(String, nullable=False) # varchar50 は String
    contact_email = Column(String) # varchar50 は String
    contact_phone = Column(String) # varchar50 は String
    interest_level = Column(String) # varchar50 は String
    status = Column(String, nullable=False) # varchar50 は String
    next_follow_up_date = Column(Date) # date は Date
    notes = Column(Text) # text は Text
    created_at = Column(DateTime, server_default=func.now()) # timestamp は DateTime
    updated_at = Column(DateTime, onupdate=func.now()) # timestamp は DateTime

    # リレーションシップ: このプロスペクトを担当するユーザー
    owner = relationship("User", back_populates="prospects")


# demo_shema.sql の content_items テーブルに対応
class ContentItem(Base):
    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, index=True) # serial は Integer で表現される
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False) # int は Integer, ForeignKey で clients.id を参照
    content_type = Column(String, nullable=False) # varchar50 は String
    title = Column(String) # varchar255 は String
    description = Column(Text) # text は Text
    instagram_post_url = Column(String, nullable=False) # varchar255 は String
    created_at = Column(DateTime, server_default=func.now()) # timestamp は DateTime
    updated_at = Column(DateTime, onupdate=func.now()) # timestamp は DateTime

    # リレーションシップ: このコンテンツアイテムが紐づくクライアント
    client = relationship("Client", back_populates="content_items")