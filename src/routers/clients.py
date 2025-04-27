# src/routers/clients.py
from typing import Annotated, List
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
    limit: int = 100
):
    """クライアント一覧を取得する（ロールに応じてフィルタリング）"""
    if current_user.role == "admin":
        # adminの場合、全データを取得
        clients = db.query(models.Client).offset(skip).limit(limit).all()
    else:
        # 通常ユーザーの場合、自身の user_id に紐づくデータのみ取得
        clients = db.query(models.Client).filter(
            models.Client.user_id == current_user.id
        ).offset(skip).limit(limit).all()
    
    return clients

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

@router.put("/{client_id}", response_model=schemas.Client)
def update_client(
    current_user: Annotated[TokenData, Depends(get_current_user)],
    client_update: schemas.ClientCreate,
    db: Session = Depends(get_db),
    client_id: int = Path(..., title="The ID of the client to update")
):
    """クライアント情報を更新する"""
    # クライアントの存在確認
    db_client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if db_client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client non trouvé"
        )
    
    # 権限チェック: adminでなく、かつ自分のクライアントでない場合はアクセス不可
    if current_user.role != "admin" and db_client.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé à ce client"
        )
    
    try:
        # 更新データを適用
        client_data = client_update.model_dump(exclude_unset=True)
        for key, value in client_data.items():
            setattr(db_client, key, value)
        
        db.commit()
        db.refresh(db_client)
        return db_client
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}"
        )

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    current_user: Annotated[TokenData, Depends(get_current_user)],
    db: Session = Depends(get_db),
    client_id: int = Path(..., title="The ID of the client to delete")
):
    """クライアントを削除する"""
    # クライアントの存在確認
    db_client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if db_client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client non trouvé"
        )
    
    # 権限チェック: adminでなく、かつ自分のクライアントでない場合はアクセス不可
    if current_user.role != "admin" and db_client.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé à ce client"
        )
    
    try:
        # 実際に削除
        db.delete(db_client)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}"
        )