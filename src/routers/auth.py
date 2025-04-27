# auth.py

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.database import get_db
import src.models as models
from src.auth import create_access_token, verify_password, Token, get_current_user, TokenData

router = APIRouter(tags=["authentication"])

# get user from DB
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    db: Session = Depends(get_db)
):
    """ユーザー認証を行い、JWTアクセストークンを発行するエンドポイント"""
    # データベースからユーザーを取得
    user = get_user_by_email(db, form_data.username)
    # username は email にマッピング
    # パスワード検証
    # user が存在し、かつパスワードが一致するかを確認
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # アクティブでないユーザーの確認
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Compte utilisateur inactif",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        # JWTペイロードに含める情報
    access_token_data = {"sub": str(user.id), "role": user.role, "city": user.city}

    # アクセストークン生成
    access_token = create_access_token(data=access_token_data)

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me/", response_model=TokenData)
async def read_users_me(current_user: Annotated[TokenData, Depends(get_current_user)]):
    """認証された現在のユーザー情報を返すエンドポイント"""
    return current_user