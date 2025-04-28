# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# データベースセットアップをインポート
import src.models as models
from src.database import engine

# ルーターをインポート
from src.routers import auth, clients, prospects, content_items, users
from src.config import settings

# アプリケーション起動時にテーブルを作成する (開発・検証用)
# 本番環境では Alembic などのマイグレーションツールを使うべき
models.Base.metadata.create_all(bind=engine)

# FastAPIアプリケーションを初期化
app = FastAPI(
    title="CRM API",
    description="CRM application API for managing clients, prospects, and content",
    version="0.1.0"
)

# CORS設定
# カンマ区切りの文字列を配列に変換
allowed_origins_str = settings.FRONTEND_ORIGINS
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(',')]

# デバッグ用に許可されたオリジンを表示
print(f"Allowed CORS origins: {allowed_origins}")

# すべてのオリジンを許可するフォールバック（開発環境用）
if settings.ENV != "production" and (not allowed_origins or len(allowed_origins) == 0):
    allowed_origins = ["*"]
    print("Warning: Using wildcard CORS origin in non-production environment")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターをアプリケーションに追加
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(clients.router)
app.include_router(prospects.router)
app.include_router(content_items.router)

# 開発環境の場合のみデバッグルーターを追加
if settings.ENV != "production":
    from src.routers import debug
    app.include_router(debug.router)

@app.get("/")
async def root():
    return {"message": "Bienvenue sur l'API du CRM"}

@app.get("/health")
async def health():
    """ヘルスチェックエンドポイント"""
    return {"status": "ok", "environment": settings.ENV, "cors_origins": allowed_origins}