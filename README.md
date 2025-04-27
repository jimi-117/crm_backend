# crm_backend

# Point
- database.py でデータベース接続エンジンとセッションローカルを設定します。
- models.py で demo_shema.sql に基づいてSQLAlchemyのORMモデル（クラス）を定義します。各カラムはSQLAlchemyの Column オブジェクトで表現され、データ型や制約（主キー、外部キー、NOT NULLなど）を指定します。relationship を使うと、関連するモデル間でのデータの取得が容易になります（例: user.clients でそのユーザーのクライアントリストを取得）。
- database.py の get_db 関数は、FastAPIの依存性注入で使用するためのものです。これにより、各APIエンドポイントの関数シグネチャに db: Session = Depends(get_db) と記述するだけで、そのリクエストに対するデータベースセッションを取得し、リクエスト処理後に自動的にクローズできます。
- main.py では、get_db 依存関数を必要とするエンドポイントに追加します。db.query(models.User).filter(...) のように、db オブジェクトとORMモデルを使ってデータベースからデータを取得したり操作したりします。
- database.py の DATABASE_URL は環境変数から読み込むようにします。Renderにデプロイする際には、Render側で設定したデータベースの内部接続URLがこの環境変数に自動的にセットされるように構成します。