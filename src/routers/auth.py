# auth.py

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import logging

from src.database import get_db
import src.models as models
from src.auth import create_access_token, verify_password, Token, get_current_user, TokenData

router = APIRouter(tags=["authentication"])

# ロガーの設定
logger = logging.getLogger("auth_router")
logger.setLevel(logging.INFO)

# get user from DB
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

@router.post("/token", response_model=Token)
async def login_for_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    db: Session = Depends(get_db)
):
    """ユーザー認証を行い、JWTアクセストークンを発行するエンドポイント"""
    # リクエスト情報をログに記録
    client_host = request.client.host if request.client else "unknown"
    logger.info(f"Login attempt from {client_host} for user: {form_data.username}")
    
    # データベースからユーザーを取得
    user = get_user_by_email(db, form_data.username)
    
    # ユーザーが見つからない場合のログ
    if not user:
        logger.warning(f"Login failed: User {form_data.username} not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # パスワード検証のログ
    password_verified = verify_password(form_data.password, user.hashed_password)
    if not password_verified:
        logger.warning(f"Login failed: Invalid password for user {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # アクティブでないユーザーの確認
    if not user.is_active:
        logger.warning(f"Login failed: Inactive user {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Compte utilisateur inactif",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # JWTペイロードに含める情報
    access_token_data = {
        "sub": str(user.id), 
        "role": user.role, 
        "city": user.city
    }
    
    # アクセストークン生成
    access_token = create_access_token(data=access_token_data)
    logger.info(f"Login successful for user {form_data.username}")

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=TokenData)
async def read_users_me(
    current_user: Annotated[TokenData, Depends(get_current_user)]
):
    """認証された現在のユーザー情報を返すエンドポイント"""
    logger.info(f"Profile request for user ID: {current_user.id}")
    return current_user

# デバッグ用エンドポイント - 開発環境でのみ使用
@router.post("/debug-token")
async def debug_token_creation(
    user_data: dict,
    request: Request
):
    """開発環境でのデバッグ用: 指定したユーザーデータでトークンを生成"""
    from src.config import settings
    
    # 本番環境では無効化
    if settings.ENV == "production":
        raise HTTPException(status_code=404, detail="Not found")
    
    required_fields = ["id", "role", "city"]
    for field in required_fields:
        if field not in user_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required field: {field}"
            )
    
    # トークンデータを準備
    token_data = {
        "sub": str(user_data["id"]),
        "role": user_data["role"],
        "city": user_data["city"]
    }
    
    # トークン生成
    access_token = create_access_token(data=token_data)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "debug_info": {
            "token_data": token_data,
            "client_ip": request.client.host if request.client else None
        }
    }