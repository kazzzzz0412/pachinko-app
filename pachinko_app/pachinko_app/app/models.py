from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class MachineType(db.Model):
    """機種マスターテーブル"""
    __tablename__ = 'machine_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    average_payout = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(255))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ
    probability_settings = db.relationship('ProbabilitySetting', backref='machine_type', lazy=True)
    play_records = db.relationship('PlayRecord', backref='machine_type', lazy=True)
    
    def __repr__(self):
        return f'<MachineType {self.name}>'


class ProbabilitySetting(db.Model):
    """役物確率マスターテーブル"""
    __tablename__ = 'probability_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    machine_type_id = db.Column(db.Integer, db.ForeignKey('machine_types.id'), nullable=False)
    probability = db.Column(db.String(10), nullable=False)
    probability_value = db.Column(db.Float, nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ
    play_records = db.relationship('PlayRecord', backref='probability_setting', lazy=True)
    
    def __repr__(self):
        return f'<ProbabilitySetting {self.probability}>'


class ExchangeRate(db.Model):
    """換金率マスターテーブル"""
    __tablename__ = 'exchange_rates'
    
    id = db.Column(db.Integer, primary_key=True)
    rate = db.Column(db.Float, nullable=False)
    name = db.Column(db.String(50))
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # リレーションシップ
    play_records = db.relationship('PlayRecord', backref='exchange_rate', lazy=True)
    
    def __repr__(self):
        return f'<ExchangeRate {self.rate}>'


class PlayRecord(db.Model):
    """プレイ記録テーブル"""
    __tablename__ = 'play_records'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    machine_type_id = db.Column(db.Integer, db.ForeignKey('machine_types.id'), nullable=False)
    investment = db.Column(db.Integer, nullable=False)
    naki_count = db.Column(db.Integer, nullable=False)
    hiroi_count = db.Column(db.Integer, nullable=False)
    probability_id = db.Column(db.Integer, db.ForeignKey('probability_settings.id'), nullable=False)
    exchange_rate_id = db.Column(db.Integer, db.ForeignKey('exchange_rates.id'), nullable=False)
    naki_to_hiroi_rate = db.Column(db.Float)
    expected_wins = db.Column(db.Float)
    expected_payout = db.Column(db.Integer)
    payout_difference = db.Column(db.Integer)
    amount_difference = db.Column(db.Integer)
    photo_url = db.Column(db.String(255))
    memo = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PlayRecord {self.date} - {self.machine_type_id}>'
    
    def calculate_rates(self):
        """鳴き→拾い率を計算"""
        if self.naki_count > 0:
            self.naki_to_hiroi_rate = self.hiroi_count / self.naki_count
        else:
            self.naki_to_hiroi_rate = 0
        return self.naki_to_hiroi_rate
    
    def calculate_expected_wins(self):
        """拾い→大当たり期待数を計算"""
        self.expected_wins = self.hiroi_count * self.probability_setting.probability_value
        return self.expected_wins
    
    def calculate_expected_payout(self):
        """予想出玉を計算"""
        self.expected_payout = int(self.expected_wins * self.machine_type.average_payout)
        return self.expected_payout
    
    def calculate_differences(self):
        """差玉・差額を計算"""
        self.payout_difference = self.expected_payout - self.investment
        self.amount_difference = int(self.payout_difference * self.exchange_rate.rate)
        return self.payout_difference, self.amount_difference
    
    def calculate_border_rate(self):
        """ボーダー率を計算（収支±0になる拾い率）"""
        if self.naki_count > 0 and self.probability_setting.probability_value > 0:
            return self.investment / (self.machine_type.average_payout * self.probability_setting.probability_value * self.naki_count)
        return 0


class UserSetting(db.Model):
    """ユーザー設定テーブル"""
    __tablename__ = 'user_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_threshold = db.Column(db.Float, default=0.2)  # 20%低下でアラート
    theme = db.Column(db.String(20), default='light')
    display_mode = db.Column(db.String(20), default='standard')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserSetting {self.id}>'
