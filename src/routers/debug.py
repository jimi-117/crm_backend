# src/routers/debug.py
from fastapi import APIRouter, Request
from pydantic import BaseModel
from src.config import settings
import sys
import os

# このルーターは開発環境でのみ有効にする
router = APIRouter(
    prefix="/debug",
    tags=["debug"],
    responses={404: {"description": "Not found"}},
)

class DebugInfo(BaseModel):
    python_version: str
    environment: str
    cors_origins: str
    database_url: str  # 機密情報をマスク
    api_host: str
    installed_packages: list

@router.get("/info", response_model=DebugInfo)
async def get_debug_info(request: Request):
    """システム情報を返す（開発環境のみ）"""
    if settings.ENV == "production":
        return {"message": "Debug endpoints are disabled in production"}
    
    # データベースURLのマスク処理
    db_url = settings.DATABASE_URL
    if db_url and "://" in db_url:
        # URLの認証情報部分をマスク
        parts = db_url.split("://")
        if len(parts) > 1 and "@" in parts[1]:
            auth_parts = parts[1].split("@")
            if len(auth_parts) > 1:
                db_url = f"{parts[0]}://***:***@{auth_parts[1]}"
    
    # パッケージ情報（簡易版）
    import pkg_resources
    packages = [f"{d.project_name}=={d.version}" for d in pkg_resources.working_set]
    
    return DebugInfo(
        python_version=sys.version,
        environment=settings.ENV,
        cors_origins=settings.FRONTEND_ORIGINS,
        database_url=db_url,
        api_host=str(request.base_url),
        installed_packages=packages
    )

@router.get("/echo")
async def echo_request(request: Request):
    """リクエストの詳細をエコーして返す"""
    if settings.ENV == "production":
        return {"message": "Debug endpoints are disabled in production"}
    
    # リクエストヘッダー
    headers = dict(request.headers)
    
    # クエリパラメータ
    query_params = dict(request.query_params)
    
    # 環境変数（機密情報は除外）
    safe_env_vars = {}
    for key, value in os.environ.items():
        # 機密情報を含む可能性のある環境変数をフィルタリング
        if not any(secret in key.lower() for secret in ["secret", "password", "token", "key", "auth"]):
            safe_env_vars[key] = value
    
    return {
        "method": request.method,
        "url": str(request.url),
        "headers": headers,
        "query_params": query_params,
        "client": {
            "host": request.client.host if request.client else None,
            "port": request.client.port if request.client else None,
        },
        "environment": settings.ENV,
        "safe_env_vars": safe_env_vars
    }