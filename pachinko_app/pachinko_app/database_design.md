# パチンコ羽根モノ期待値・収支予測アプリ データベース設計

## テーブル構造

### 1. MachineTypes（機種マスター）
```
id: Integer, Primary Key
name: String(100) - 機種名（おだてブタ2、Pファミスタなど）
average_payout: Integer - 平均出玉数
image_url: String(255) - 機種画像URL（オプション）
notes: Text - 機種に関する備考
created_at: DateTime - 作成日時
updated_at: DateTime - 更新日時
```

### 2. ProbabilitySettings（役物確率マスター）
```
id: Integer, Primary Key
machine_type_id: Integer, Foreign Key (MachineTypes.id)
probability: String(10) - 確率表記（例：1/11, 1/12, 1/13）
probability_value: Float - 確率の数値（例：1/11 → 0.0909）
is_default: Boolean - デフォルト設定かどうか
created_at: DateTime - 作成日時
updated_at: DateTime - 更新日時
```

### 3. ExchangeRates（換金率マスター）
```
id: Integer, Primary Key
rate: Float - 換金率（例：4.0, 3.57, 3.3, 3.03）
name: String(50) - 換金率の名称（オプション）
is_default: Boolean - デフォルト設定かどうか
created_at: DateTime - 作成日時
updated_at: DateTime - 更新日時
```

### 4. PlayRecords（プレイ記録）
```
id: Integer, Primary Key
date: Date - プレイ日
machine_type_id: Integer, Foreign Key (MachineTypes.id) - 機種ID
investment: Integer - 投資額（円）
naki_count: Integer - 鳴き数
hiroi_count: Integer - 拾い数
probability_id: Integer, Foreign Key (ProbabilitySettings.id) - 役物確率ID
exchange_rate_id: Integer, Foreign Key (ExchangeRates.id) - 換金率ID
naki_to_hiroi_rate: Float - 鳴き→拾い率（計算値）
expected_wins: Float - 期待大当たり数（計算値）
expected_payout: Integer - 予想出玉数（計算値）
payout_difference: Integer - 差玉（計算値）
amount_difference: Integer - 差額（円）（計算値）
photo_url: String(255) - 実機写真URL（オプション）
memo: Text - メモ
created_at: DateTime - 作成日時
updated_at: DateTime - 更新日時
```

### 5. UserSettings（ユーザー設定）
```
id: Integer, Primary Key
alert_threshold: Float - 回収アラートのしきい値（鳴き率・拾い率の低下率）
theme: String(20) - アプリテーマ設定
display_mode: String(20) - 表示モード設定
created_at: DateTime - 作成日時
updated_at: DateTime - 更新日時
```

## リレーションシップ

1. MachineTypes ⟷ ProbabilitySettings: 1対多
   - 1つの機種に対して複数の役物確率設定が可能

2. MachineTypes ⟷ PlayRecords: 1対多
   - 1つの機種に対して複数のプレイ記録が存在

3. ProbabilitySettings ⟷ PlayRecords: 1対多
   - 1つの役物確率設定に対して複数のプレイ記録が存在

4. ExchangeRates ⟷ PlayRecords: 1対多
   - 1つの換金率設定に対して複数のプレイ記録が存在

## 初期データ

### MachineTypes
1. おだてブタ2
2. Pファミスタ
3. ニュートキオ
4. ニュートキオグリーン

### ProbabilitySettings
- おだてブタ2: 1/11, 1/12, 1/13
- Pファミスタ: 1/11, 1/12, 1/13
- ニュートキオ: 1/11, 1/12, 1/13
- ニュートキオグリーン: 1/11, 1/12, 1/13

### ExchangeRates
1. 4.0円
2. 3.57円
3. 3.3円
4. 3.03円

### UserSettings
- alert_threshold: 0.2 (20%低下でアラート)
- theme: "light"
- display_mode: "standard"

## 計算ロジック（モデルメソッド）

1. 鳴き→拾い率計算:
   ```
   naki_to_hiroi_rate = hiroi_count / naki_count if naki_count > 0 else 0
   ```

2. 拾い→大当たり期待数計算:
   ```
   expected_wins = hiroi_count * probability_value
   ```

3. 予想出玉計算:
   ```
   expected_payout = expected_wins * machine_type.average_payout
   ```

4. 差玉・差額計算:
   ```
   payout_difference = expected_payout - investment
   amount_difference = payout_difference * exchange_rate.rate
   ```

5. ボーダー自動算出:
   ```
   border_rate = investment / (machine_type.average_payout * probability_value * naki_count) if naki_count > 0 else 0
   ```
