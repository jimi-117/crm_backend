# src/routers/prospects.py
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from src.database import get_db
import src.models as models
import src.schemas as schemas
from src.auth import get_current_user, TokenData, get_admin_user

router = APIRouter(
    prefix="/prospects",
    tags=["prospects"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[schemas.Prospect])
def read_prospects(
    current_user: Annotated[TokenData, Depends(get_current_user)],
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """プロスペクト一覧を取得する（ロールに応じてフィルタリング）"""
    if current_user.role == "admin":
        # adminの場合、全データを取得
        prospects = db.query(models.Prospect).offset(skip).limit(limit).all()
    else:
        # 通常ユーザーの場合、自身の user_id に紐づくデータのみ取得
        prospects = db.query(models.Prospect).filter(
            models.Prospect.user_id == current_user.id
        ).offset(skip).limit(limit).all()
    
    return prospects

@router.post("/", response_model=schemas.Prospect, status_code=status.HTTP_201_CREATED)
def create_prospect(
    prospect: schemas.ProspectCreate,
    current_user: Annotated[TokenData, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """新しいプロスペクトを作成する"""
    try:
        # ORMモデルに変換
        db_prospect = models.Prospect(
            **prospect.model_dump(),
            user_id=current_user.id  # 現在のユーザーIDを設定
        )
        
        # データベースに追加して保存
        db.add(db_prospect)
        db.commit()
        db.refresh(db_prospect)
        return db_prospect
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Une erreur est survenue lors de la création du prospect"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}"
        )

@router.get("/{prospect_id}", response_model=schemas.Prospect)
def read_prospect(
    current_user: Annotated[TokenData, Depends(get_current_user)],
    prospect_id: int = Path(..., title="The ID of the prospect to get"),
    db: Session = Depends(get_db)
):
    """指定したIDのプロスペクト情報を取得する"""
    prospect = db.query(models.Prospect).filter(models.Prospect.id == prospect_id).first()
    
    # プロスペクトが存在しない場合は404エラー
    if prospect is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prospect non trouvé"
        )
    
    # 権限チェック: adminでなく、かつ自分のプロスペクトでない場合はアクセス不可
    if current_user.role != "admin" and prospect.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé à ce prospect"
        )
    
    return prospect

@router.put("/{prospect_id}", response_model=schemas.Prospect)
def update_prospect(
    prospect_update: schemas.ProspectCreate,
    current_user: Annotated[TokenData, Depends(get_current_user)],
    prospect_id: int = Path(..., title="The ID of the prospect to update"),
    db: Session = Depends(get_db)
):
    """プロスペクト情報を更新する"""
    # プロスペクトの存在確認
    db_prospect = db.query(models.Prospect).filter(models.Prospect.id == prospect_id).first()
    if db_prospect is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prospect non trouvé"
        )
    
    # 権限チェック: adminでなく、かつ自分のプロスペクトでない場合はアクセス不可
    if current_user.role != "admin" and db_prospect.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé à ce prospect"
        )
    
    try:
        # 更新データを適用
        prospect_data = prospect_update.model_dump(exclude_unset=True)
        for key, value in prospect_data.items():
            setattr(db_prospect, key, value)
        
        db.commit()
        db.refresh(db_prospect)
        return db_prospect
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}"
        )

@router.delete("/{prospect_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prospect(
    current_user: Annotated[TokenData, Depends(get_current_user)],
    prospect_id: int = Path(..., title="The ID of the prospect to delete"),
    db: Session = Depends(get_db)
):
    """プロスペクトを削除する"""
    # プロスペクトの存在確認
    db_prospect = db.query(models.Prospect).filter(models.Prospect.id == prospect_id).first()
    if db_prospect is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prospect non trouvé"
        )
    
    # 権限チェック: adminでなく、かつ自分のプロスペクトでない場合はアクセス不可
    if current_user.role != "admin" and db_prospect.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès non autorisé à ce prospect"
        )
    
    try:
        # 実際に削除
        db.delete(db_prospect)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur serveur: {str(e)}"
        )
        
        
@router.get("/recommended", response_model=List[schemas.Prospect])
def get_recommended_prospects(
    current_user: Annotated[TokenData, Depends(get_current_user)],
    db: Session = Depends(get_db),
    limit: int = 3
):
    """ユーザーにおすすめのプロスペクトを取得する（高関心度や直近のフォローアップ日などに基づく）"""
    # 基本クエリの作成
    query = db.query(models.Prospect)
    
    # ユーザーの権限に基づくフィルタリング
    if current_user.role != "admin":
        query = query.filter(models.Prospect.user_id == current_user.id)
    
    # ステータスが「新規」または「コンタクト済み」でフィルタリング
    query = query.filter(models.Prospect.status.in_(["new", "contacted"]))
    
    # 関心度が「高」のプロスペクトを優先
    high_interest_prospects = query.filter(
        models.Prospect.interest_level == "high"
    ).order_by(models.Prospect.created_at.desc()).limit(limit).all()
    
    # 高関心度のプロスペクトが少ない場合、フォローアップ日が近いものも追加
    if len(high_interest_prospects) < limit:
        # 既に取得したプロスペクトのIDリスト
        existing_ids = [p.id for p in high_interest_prospects]
        
        # 次のフォローアップ日が近いプロスペクトを追加
        remaining_needed = limit - len(high_interest_prospects)
        upcoming_followup_prospects = query.filter(
            ~models.Prospect.id.in_(existing_ids)
        ).order_by(models.Prospect.next_follow_up_date).limit(remaining_needed).all()
        
        # 結果を結合
        recommended_prospects = high_interest_prospects + upcoming_followup_prospects
    else:
        recommended_prospects = high_interest_prospects
    
    return recommended_prospects