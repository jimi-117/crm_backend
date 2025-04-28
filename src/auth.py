import os
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
import logging
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt, ExpiredSignatureError
from passlib.context import CryptContext
from pydantic import BaseModel
from .config import settings

logger = logging.getLogger("auth_module")
logger.setLevel(logging.INFO)

# 環境変数から秘密鍵などを読み込む (本番では環境変数として設定)
SECRET_KEY = settings.JWT_SECRET_KEY # デフォルト値は開発用、本番では必ず変更！
ALGORITHM = settings.JWT_ALGORITHM # 使用するJWTアルゴリズム
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES # アクセストークンの有効期限

# パスワードハッシュ化の設定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 スキームの定義
# tokenUrl はフロントエンドがトークンを取得するためにPOSTするURL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    """JWTトークンのレスポンスモデル"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """JWTペイロードのデータモデル"""
    id: int | None = None
    role: str
    city: str | None = None

# -- パスワード関連のユーティリティ --
def hash_password(password: str) -> str:
    """パスワードをハッシュ化する"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """入力されたパスワードとハッシュ化されたパスワードを検証する"""
    return pwd_context.verify(plain_password, hashed_password)

# -- JWT 関連のユーティリティ --
def create_access_token(data: dict):
    """JWTアクセストークンを生成する"""
    to_encode = data.copy()
    # 有効期限を設定
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """リクエストヘッダーのJWTを検証し、現在のユーザー情報を取得する依存関数"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 短いログ出力のためのトークンプレビュー
    token_preview = token[:10] + "..." if token and len(token) > 10 else "None"
    logger.info(f"Validating token: {token_preview}")
    
    try:
        # JWTをデコード・検証
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # ペイロードからユーザー情報を抽出
        user_id_str: str = payload.get("sub")
        user_role: str = payload.get("role")
        user_city: str = payload.get("city")

        if user_id_str is None or user_role is None:
            logger.warning("Token validation failed: Missing user_id or role in payload")
            raise credentials_exception
        
        # IDを整数に変換
        try:
            user_id = int(user_id_str)
        except ValueError:
            logger.warning(f"Token validation failed: Invalid user_id format: {user_id_str}")
            raise credentials_exception

        # TokenData モデルに変換
        token_data = TokenData(id=user_id, role=user_role, city=user_city)
        logger.info(f"Token validation successful for user ID: {user_id}")
        return token_data

    except ExpiredSignatureError:
        logger.warning("Token validation failed: Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        logger.warning(f"Token validation failed: JWTError - {str(e)}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Unexpected error in token validation: {str(e)}")
        raise credentials_exception

# -- 認可関連のユーティリティ --
def get_admin_user(current_user: Annotated[TokenData, Depends(get_current_user)]):
    """adminロールを持つユーザーか確認する依存関数"""
    if current_user.role != "admin":
        logger.warning(f"Admin access attempt by non-admin user: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not enough permissions"
        )
    logger.info(f"Admin access granted for user ID: {current_user.id}")
    return current_user