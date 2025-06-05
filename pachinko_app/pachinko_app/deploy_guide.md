# パチンコ羽根モノ期待値・収支予測アプリ デプロイ手順

## Herokuへのデプロイ手順

### 1. 前提条件
- Herokuアカウントが必要です
- Heroku CLIがインストールされていること
- Gitがインストールされていること

### 2. Herokuアプリの作成
```bash
# Herokuにログイン
heroku login

# アプリケーションの作成
heroku create pachinko-hanemono-app

# Gitリポジトリの初期化（まだ行っていない場合）
git init
git add .
git commit -m "Initial commit"

# Herokuリモートの追加
heroku git:remote -a pachinko-hanemono-app
```

### 3. 必要なファイルの確認
- `requirements.txt`：依存パッケージのリスト
- `Procfile`：Herokuの起動コマンド
- `runtime.txt`：Pythonバージョンの指定

#### Procfileの作成
```
web: gunicorn app.main:app
```

#### runtime.txtの作成
```
python-3.11.0
```

### 4. デプロイ
```bash
# Herokuにプッシュ
git push heroku main

# データベースの初期化
heroku run python -c "
from app.models import db, MachineType, ProbabilitySetting, ExchangeRate, UserSetting
from app.routes import create_app
import os

# アプリケーションの作成
app = create_app()

# アプリケーションコンテキストの開始
with app.app_context():
    # データベースの作成
    db.create_all()
    
    # 初期データの投入
    # 機種データ
    machines = [
        MachineType(name='おだてブタ2', average_payout=1500, notes='人気の羽根モノ機種'),
        MachineType(name='Pファミスタ', average_payout=1600, notes='スポーツテーマの羽根モノ'),
        MachineType(name='ニュートキオ', average_payout=1700, notes='定番の羽根モノ機種'),
        MachineType(name='ニュートキオグリーン', average_payout=1800, notes='ニュートキオの派生機種')
    ]
    db.session.add_all(machines)
    
    # 役物確率データ
    probabilities = [
        ProbabilitySetting(machine_type_id=1, probability='1/11', probability_value=1/11, is_default=True),
        ProbabilitySetting(machine_type_id=1, probability='1/12', probability_value=1/12, is_default=False),
        ProbabilitySetting(machine_type_id=2, probability='1/11', probability_value=1/11, is_default=True),
        ProbabilitySetting(machine_type_id=3, probability='1/12', probability_value=1/12, is_default=True),
        ProbabilitySetting(machine_type_id=4, probability='1/13', probability_value=1/13, is_default=True)
    ]
    db.session.add_all(probabilities)
    
    # 換金率データ
    exchange_rates = [
        ExchangeRate(rate=4.0, name='等価', is_default=True),
        ExchangeRate(rate=3.57, name='5.6枚', is_default=False),
        ExchangeRate(rate=3.3, name='6枚', is_default=False),
        ExchangeRate(rate=3.03, name='6.5枚', is_default=False)
    ]
    db.session.add_all(exchange_rates)
    
    # ユーザー設定
    user_settings = UserSetting(
        alert_threshold=0.2,
        theme='light',
        display_mode='standard'
    )
    db.session.add(user_settings)
    
    # コミット
    db.session.commit()
    
    print('本番用データベースの初期化が完了しました')
"
```

### 5. アプリの起動確認
```bash
heroku open
```

## 代替デプロイ方法：Render.comへのデプロイ

Herokuの無料プランが終了した場合、Render.comを代替として使用できます。

### 1. Render.comでのセットアップ
- Render.comにアカウント登録
- 「New Web Service」を選択
- GitHubリポジトリと連携

### 2. 設定
- Name: pachinko-hanemono-app
- Environment: Python
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app.main:app`
- 環境変数の設定（必要に応じて）

### 3. デプロイ
- 「Create Web Service」ボタンをクリック
- デプロイが完了するまで待機（数分かかる場合があります）

## ローカルでの実行方法（参考）

```bash
# 仮想環境のアクティベート
source venv/bin/activate

# 依存パッケージのインストール
pip install -r requirements.txt

# アプリケーションの起動
python app/main.py
```

## デプロイ後の確認事項

1. PWA機能が正常に動作するか
2. データベースが正しく初期化されているか
3. 計算ロジックが正常に動作するか
4. レスポンシブデザインが適切に表示されるか
5. オフライン機能が動作するか

## トラブルシューティング

### Herokuログの確認
```bash
heroku logs --tail
```

### データベースのリセット
```bash
heroku pg:reset DATABASE
```

### 手動でのデータベース操作
```bash
heroku pg:psql
```
