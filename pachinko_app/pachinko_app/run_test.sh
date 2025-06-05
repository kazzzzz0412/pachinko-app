#!/bin/bash

# パチンコ羽根モノ期待値・収支予測アプリのテスト・デプロイスクリプト

# 作業ディレクトリに移動
cd /home/ubuntu/pachinko_app

# 仮想環境の作成（存在しない場合）
if [ ! -d "venv" ]; then
    echo "仮想環境を作成しています..."
    python3 -m venv venv
fi

# 仮想環境のアクティベート
source venv/bin/activate

# 依存パッケージのインストール
echo "依存パッケージをインストールしています..."
pip install -r requirements.txt

# データベースディレクトリの作成（存在しない場合）
if [ ! -d "instance" ]; then
    mkdir -p instance
fi

# テスト用データベースの初期化
echo "テスト用データベースを初期化しています..."
python -c "
from app.models import db, MachineType, ProbabilitySetting, ExchangeRate, UserSetting
from app.routes import create_app
import os

# テスト用アプリケーションの作成
app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/pachinko_test.db'

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
    
    print('テスト用データベースの初期化が完了しました')
"

# アプリケーションの起動
echo "アプリケーションを起動しています..."
echo "テスト用URL: http://localhost:5000"
echo "Ctrl+Cで終了できます"
python app/main.py
