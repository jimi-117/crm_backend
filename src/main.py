# main.py
from typing import Annotated, List
from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

import src.models as models, src.database as database, src.schemas as schemas
from src.database import get_db, engine # get_db 依存関数と engine をインポート
# 認証モジュール (auth.py) から必要なものをインポート
from src.auth import create_access_token, verify_password, Token, TokenData, get_current_user, get_admin_user, hash_password
# アプリケーション起動時にテーブルを作成する (開発・検証用)
models.Base.metadata.create_all(bind=engine) # 既に実行していればコメントアウト可


app = FastAPI()


from fastapi.middleware.cors import CORSMiddleware
import os

allowed_origins_str = os.getenv("FRONTEND_ORIGINS")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 認証エンドポイント (token 発行) ---
from fastapi.security import OAuth2PasswordRequestForm

# 仮のDBからユーザーを取得する関数を SQLAlchemy を使って再実装
# ここで models.User を使います
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    """ユーザー認証を行い、JWTアクセストークンを発行するエンドポイント"""
    # データベースからユーザーを取得
    user = get_user_by_email(db, form_data.username) # username は email にマッピング

    # パスワード検証
    # user が存在し、かつパスワードが一致するかを確認
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password", # username を email に変更
            headers={"WWW-Authenticate": "Bearer"},
        )

    # JWTペイロードに含める情報
    access_token_data = {"sub": str(user.id), "role": user.role, "city": user.city}

    # アクセストークン生成
    access_token = create_access_token(data=access_token_data)

    return {"access_token": access_token, "token_type": "bearer"}


# --- 保護されたエンドポイントの例 ---

@app.get("/users/me/", response_model=TokenData) # 認証ユーザー自身の情報を返す例
async def read_users_me(current_user: Annotated[TokenData, Depends(get_current_user)]):
    """認証された現在のユーザー情報を返すエンドポイント"""
    # current_user は JWT から抽出された TokenData オブジェクト
    return current_user

@app.get("/admin/users/", ) # adminユーザーのみアクセス可能な例
async def read_admin_users(current_user: Annotated[TokenData, Depends(get_admin_user)], db: Session = Depends(get_db)):
    """すべてのユーザー情報を返すエンドポイント (admin ロール必須)"""
    # データベースからすべてのユーザー情報を取得
    users = db.query(models.User).all()
    return users # 例：ユーザーリストを返す

# TODO: clients, prospects, content_items の CRUD エンドポイントを実装
# 例: クライアント一覧取得エンドポイント (フランチャイズ向けフィルタリングを含む)

@app.get("/clients/")
def list_clients(current_user: Annotated[TokenData, Depends(get_current_user)], db: Session = Depends(get_db)):
    """クライアント一覧を取得する（ロールに応じてフィルタリング）"""
    if current_user.role == "admin":
        # adminの場合、全データを取得
        clients = db.query(models.Client).all()
    elif current_user.role == "franchise":
        # フランチャイズの場合、自身の user_id に紐づくデータのみ取得
        clients = db.query(models.Client).filter(models.Client.user_id == current_user.id).all()
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return clients

# 他のクライアント、プロスペクト、コンテンツアイテム関連のエンドポイントも同様に実装...