# src/routers/content_items.py
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.database import get_db
import src.models as models
import src.schemas as schemas
from src.auth import get_current_user, TokenData, get_admin_user

router = APIRouter(
    prefix="/content-items",
    tags=["content items"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[schemas.ContentItem])
def read_content_items(
    current_user: Annotated[TokenData, Depends(get_current_user)],
    db: Session = Depends(get_db),
    client_id: int = None,
    skip: int = 0,
    limit: int = 100
):
    """コンテンツアイテム一覧を取得する"""
    query = db.query(models.ContentItem)
    
    # client_idによるフィルタリングがある場合
    if client_id is not None:
        query = query.filter(models.ContentItem.client_id == client_id)
    
    # 権限によるフィルタリング
    if current_user.role != "admin":
        # 通常ユーザーの場合、自分が担当するクライアントのコンテンツアイテムのみを取得
        query = query.join(models.Client).filter(models.Client.user_id == current_user.id)
    
    return query.offset(skip).limit(limit).all()

@router.post("/", response_model=schemas.ContentItem, status_code=status.HTTP_201_CREATED)
def create_content_item(
    content_item: schemas.ContentItemCreate,
    client_id: int = Query(..., title="The ID of the client to associate with this content item"),
    current_user: Annotated[TokenData, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """新しいコンテンツアイテムを作成する"""
    # クライアントの存在確認
    client = db.query(models.Client).filter(models.Client.id == client_id).first()
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
    
    try:
        # ORMモデルに変換
        db_content_item = models.ContentItem(
            **content_item.model_dump(),
            client_id=client_id
        )
        
        # データベースに追加して保存
        db.add(db_content_item)
        db.commit()
        db.refresh(db_content_item)
        return db_content_item
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Une erreur est survenue lors de la création du contenu"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}"
        )

@router.get("/{content_item_id}", response_model=schemas.ContentItem)
def read_content_item(
    content_item_id: int = Path(..., title="The ID of the content item to get"),
    current_user: Annotated[TokenData, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """指定したIDのコンテンツアイテム情報を取得する"""
    content_item = db.query(models.ContentItem).filter(models.ContentItem.id == content_item_id).first()
    
    # コンテンツアイテムが存在しない場合は404エラー
    if content_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contenu non trouvé"
        )
    
    # 権限チェック: クライアントの情報を取得
    client = db.query(models.Client).filter(models.Client.id == content_item.client_id).first()
    
    # adminでなく、かつ自分のクライアントでない場合はアクセス不可
    if current_user.role != "admin" and client.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé à ce contenu"
        )
    
    return content_item

@router.put("/{content_item_id}", response_model=schemas.ContentItem)
def update_content_item(
    content_item_update: schemas.ContentItemCreate,
    content_item_id: int = Path(..., title="The ID of the content item to update"),
    current_user: Annotated[TokenData, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """コンテンツアイテム情報を更新する"""
    # コンテンツアイテムの存在確認
    db_content_item = db.query(models.ContentItem).filter(models.ContentItem.id == content_item_id).first()
    if db_content_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contenu non trouvé"
        )
    
    # 権限チェック: クライアントの情報を取得
    client = db.query(models.Client).filter(models.Client.id == db_content_item.client_id).first()
    
    # adminでなく、かつ自分のクライアントでない場合はアクセス不可
    if current_user.role != "admin" and client.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé à ce contenu"
        )
    
    try:
        # 更新データを適用
        content_item_data = content_item_update.model_dump(exclude_unset=True)
        for key, value in content_item_data.items():
            setattr(db_content_item, key, value)
        
        db.commit()
        db.refresh(db_content_item)
        return db_content_item
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}"
        )

@router.delete("/{content_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_content_item(
    content_item_id: int = Path(..., title="The ID of the content item to delete"),
    current_user: Annotated[TokenData, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """コンテンツアイテムを削除する"""
    # コンテンツアイテムの存在確認
    db_content_item = db.query(models.ContentItem).filter(models.ContentItem.id == content_item_id).first()
    if db_content_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contenu non trouvé"
        )
    
    # 権限チェック: クライアントの情報を取得
    client = db.query(models.Client).filter(models.Client.id == db_content_item.client_id).first()
    
    # adminでなく、かつ自分のクライアントでない場合はアクセス不可
    if current_user.role != "admin" and client.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé à ce contenu"
        )
    
    try:
        # 実際に削除
        db.delete(db_content_item)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}"
        )