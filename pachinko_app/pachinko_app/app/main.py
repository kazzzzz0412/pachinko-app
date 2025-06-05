from app.routes import create_app
import os

# アプリケーションの作成
app = create_app()

# 本番環境用の設定
if __name__ == '__main__':
    # デバッグモードを無効化
    app.debug = False
    
    # ポート設定（環境変数から取得、デフォルトは5000）
    port = int(os.environ.get('PORT', 5000))
    
    # ホスト設定（0.0.0.0で全てのIPからのアクセスを許可）
    app.run(host='0.0.0.0', port=port)
