# crm_backend

- FastAPI + postgreSQL + SQLAlchemy + Alembic + Render で構築した CRM システムのバックエンドデモです。
- ローカル開発用に、docker-compose.yml で PostgreSQL を立ち上げるようにしています。プロダクション環境では Render に本番用 postgres インスタンスをあらかじめ建てて、本番用の環境変数を render プロジェクトに設定しなければなりません。

# Point

- database.py でデータベース接続エンジンとセッションローカルを設定します。
- models.py で demo_shema.sql に基づいて SQLAlchemy の ORM モデル（クラス）を定義します。各カラムは SQLAlchemy の Column オブジェクトで表現され、データ型や制約（主キー、外部キー、NOT NULL など）を指定します。relationship を使うと、関連するモデル間でのデータの取得が容易になります（例: user.clients でそのユーザーのクライアントリストを取得）。
- database.py の get_db 関数は、FastAPI の依存性注入で使用するためのものです。これにより、各 API エンドポイントの関数シグネチャに db: Session = Depends(get_db) と記述するだけで、そのリクエストに対するデータベースセッションを取得し、リクエスト処理後に自動的にクローズできます。
- main.py では、get_db 依存関数を必要とするエンドポイントに追加します。db.query(models.User).filter(...) のように、db オブジェクトと ORM モデルを使ってデータベースからデータを取得したり操作したりします。
- database.py の DATABASE_URL は環境変数から読み込むようにします。Render にデプロイする際には、Render 側で設定したデータベースの内部接続 URL がこの環境変数に自動的にセットされるように構成します。
