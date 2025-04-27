# database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 環境変数からデータベースURLを読み込む
# RenderのManaged PostgreSQLを使う場合、接続URLは環境変数として提供されます。
# 例: "postgresql://user:password@host:port/dbname"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/mydatabase") # TODO: デフォルト値はローカル環境に合わせて変更してください

# データベースエンジンを作成
# connect_args={"check_same_thread": False} は SQLite で必要になる設定ですが、
# PostgreSQLの場合は通常不要です。ただし、環境によっては考慮が必要かもしれません。
engine = create_engine(DATABASE_URL)

# 各データベースセッション用の SessionLocal クラスを作成
# autocommit=False: トランザクションは手動でコミットします
# autoflush=False: クエリ実行前に自動的にセッションをフラッシュしません
# bind=engine: 作成したエンジンにバインドします
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ORMモデルを定義するためのベースクラス
# これを継承して各テーブルに対応するクラスを作成します
Base = declarative_base()

# データベースセッションを取得するための依存関数
def get_db():
    """リクエストごとにDBセッションを作成し、終了時にクローズする"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# (オプション) テーブルをまだ作成していない場合に作成する関数
def create_database_tables():
    """Base に登録されている全てのモデルに対応するテーブルをデータベースに作成する"""
    # from . import models # models モジュールをインポート (循環参照に注意)
    Base.metadata.create_all(bind=engine)