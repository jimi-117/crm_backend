import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from .config import settings

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
    try:
        # JWTをデコード・検証
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # ペイロードからユーザー情報を抽出
        user_id: int | None = payload.get("sub") # sub はユーザーIDとして使う慣例
        user_role: str | None = payload.get("role")
        user_city: str | None = payload.get("city")

        if user_id is None or user_role is None:
            raise credentials_exception

        # TokenData モデルに変換
        token_data = TokenData(id=user_id, role=user_role, city=user_city)

    except JWTError:
        raise credentials_exception

    # 必要であれば、ここで user_id を使ってデータベースからユーザーオブジェクトを
    # 取得し、is_active などの状態を確認することも可能。
    # 例: user = get_user_from_db(user_id)
    # if user is None or not user.is_active:
    #     raise credentials_exception
    # return user

    # 今回は簡単のため、JWTペイロードの情報のみを返す
    return token_data

# -- 認可関連のユーティリティ --
def get_admin_user(current_user: Annotated[TokenData, Depends(get_current_user)]):
    """adminロールを持つユーザーか確認する依存関数"""
    if current_user.role != "admin":
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return current_user