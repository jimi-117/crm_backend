# src/routers/users.py
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.database import get_db
import src.models as models
import src.schemas as schemas
from src.auth import get_current_user, TokenData, get_admin_user, hash_password

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[schemas.User])
async def read_users(
    current_user: Annotated[TokenData, Depends(get_admin_user)],
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """すべてのユーザー情報を返すエンドポイント (admin ロール必須)"""
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: schemas.UserCreate,
    current_user: Annotated[TokenData, Depends(get_admin_user)],
    db: Session = Depends(get_db)
):
    """新しいユーザーを作成する (adminロール必須)"""
    # メールアドレスの重複チェック
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà enregistré"
        )
    
    try:
        # パスワードのハッシュ化
        hashed_password = hash_password(user.password)
        
        # ユーザーのDB登録
        db_user = models.User(
            email=user.email,
            role=user.role,
            hashed_password=hashed_password,
            name=user.name,
            city=user.city,
            is_active=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: