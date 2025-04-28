# src/routers/clients.py
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.database import get_db
import src.models as models
import src.schemas as schemas
from src.auth import get_current_user, TokenData, get_admin_user

router = APIRouter(
    prefix="/clients",
    tags=["clients"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[schemas.Client])
def read_clients(
    current_user: Annotated[TokenData, Depends(get_current_user)],
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    city: Optional[str] = None  # 都市によるフィルタリングを追加
):
    """クライアント一覧を取得する（ロールと都市に応じてフィルタリング）"""
    query = db.query(models.Client)
    
    if current_user.role == "admin":
        # adminの場合、全データを取得するが、都市フィルターがあれば適用
        if city:
            # clientsテーブルにはcity情報がないので、usersテーブルと結合
            query = query.join(models.User).filter(models.User.city == city)
    else:
        # 通常ユーザーの場合、自身の user_id に紐づくデータのみ取得
        query = query.filter(models.Client.user_id == current_user.id)
        
        # さらに都市でフィルタリング（ユーザー自身の都市）
        if not city and current_user.city:
            # 都市が指定されていない場合は、ユーザー自身の都市でフィルター
            city = current_user.city
        
        if city:
            # 担当しているクライアントの中で、特定の都市のもののみ表示
            query = query.join(models.User).filter(models.User.city == city)
    
    clients = query.offset(skip).limit(limit).all()
    return clients

# 以下は既存のコードを残します
@router.post("/", response_model=schemas.Client, status_code=status.HTTP_201_CREATED)
def create_client(
    client: schemas.ClientCreate,
    current_user: Annotated[TokenData, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """新しいクライアントを作成する"""
    try:
        # ORMモデルに変換
        db_client = models.Client(
            **client.model_dump(),
            user_id=current_user.id  # 現在のユーザーIDを設定
        )
        
        # データベースに追加して保存
        db.add(db_client)
        db.commit()
        db.refresh(db_client)
        return db_client
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Une erreur est survenue lors de la création du client"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}"
        )

@router.get("/{client_id}", response_model=schemas.Client)
def read_client(
    current_user: Annotated[TokenData, Depends(get_current_user)],
    db: Session = Depends(get_db),
    client_id: int = Path(..., title="The ID of the client to get")
):
    """指定したIDのクライアント情報を取得する"""
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
    
    # クライアントが存在しない場合は404エラー
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client non trouvé"
        )
    
    # 権限チェック: adminでなく、かつ自分のクライアントでない場合はアクセス不可
    if current_user.role != "admin" and client.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé à ce client"
        )
    
    return client