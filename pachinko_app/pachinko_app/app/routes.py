from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
import os
import calendar
from werkzeug.utils import secure_filename
from app.models import db, MachineType, ProbabilitySetting, ExchangeRate, PlayRecord, UserSetting

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_for_pachinko_app')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///pachinko.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')
    
    db.init_app(app)
    
    # カスタムフィルター
    @app.template_filter('format_yen')
    def format_yen(value):
        if value is None:
            return '0円'
        return f"{value:,}円"
    
    # ルート
    @app.route('/')
    def index():
        # 最近の記録を取得
        recent_records = PlayRecord.query.order_by(PlayRecord.date.desc()).limit(5).all()
        
        # 月間統計データを取得
        today = date.today()
        start_of_month = date(today.year, today.month, 1)
        end_of_month = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
        
        monthly_records = PlayRecord.query.filter(
            PlayRecord.date >= start_of_month,
            PlayRecord.date <= end_of_month
        ).all()
        
        total_investment = sum(record.investment for record in monthly_records)
        total_profit = sum(record.amount_difference for record in monthly_records)
        
        monthly_stats = {
            'total_investment': total_investment,
            'total_profit': total_profit
        }
        
        # 月間チャートデータを準備
        days_in_month = (end_of_month - start_of_month).days + 1
        labels = []
        profits = []
        
        for i in range(days_in_month):
            current_date = start_of_month + timedelta(days=i)
            if current_date <= today:
                labels.append(current_date.strftime('%d'))
                
                # その日の収支を計算
                day_records = [r for r in monthly_records if r.date == current_date]
                day_profit = sum(r.amount_difference for r in day_records)
                profits.append(day_profit)
        
        monthly_chart_data = {
            'labels': labels,
            'profits': profits
        }
        
        # 機種別統計を取得
        machine_stats = []
        machines = MachineType.query.all()
        
        for machine in machines:
            machine_records = PlayRecord.query.filter_by(machine_type_id=machine.id).all()
            if machine_records:
                total_investment = sum(record.investment for record in machine_records)
                total_profit = sum(record.amount_difference for record in machine_records)
                avg_naki_to_hiroi_rate = sum(record.naki_to_hiroi_rate for record in machine_records) / len(machine_records)
                
                machine_stats.append({
                    'machine_type': machine,
                    'total_investment': total_investment,
                    'total_profit': total_profit,
                    'avg_naki_to_hiroi_rate': avg_naki_to_hiroi_rate
                })
        
        return render_template('index.html', 
                              recent_records=recent_records,
                              monthly_stats=monthly_stats,
                              monthly_chart_data=monthly_chart_data,
                              machine_stats=machine_stats)
    
    @app.route('/input', methods=['GET', 'POST'])
    def input():
        from flask_wtf import FlaskForm
        from wtforms import StringField, IntegerField, DateField, TextAreaField, SelectField, FileField
        from wtforms.validators import DataRequired, NumberRange
        
        class PlayRecordForm(FlaskForm):
            date = DateField('日付', validators=[DataRequired()])
            machine_type_id = SelectField('機種', validators=[DataRequired()], coerce=int)
            investment = IntegerField('投資額', validators=[DataRequired(), NumberRange(min=0)])
            naki_count = IntegerField('鳴き数', validators=[DataRequired(), NumberRange(min=0)])
            hiroi_count = IntegerField('拾い数', validators=[DataRequired(), NumberRange(min=0)])
            probability_id = SelectField('役物確率', validators=[DataRequired()], coerce=int)
            exchange_rate_id = SelectField('換金率', validators=[DataRequired()], coerce=int)
            memo = TextAreaField('メモ')
            photo = FileField('実機写真')
        
        form = PlayRecordForm()
        
        # 選択肢を設定
        form.machine_type_id.choices = [(m.id, m.name) for m in MachineType.query.all()]
        form.probability_id.choices = [(p.id, p.probability) for p in ProbabilitySetting.query.all()]
        form.exchange_rate_id.choices = [(r.id, f"{r.rate}円") for r in ExchangeRate.query.all()]
        
        if form.validate_on_submit():
            # ファイルアップロード処理
            photo_url = None
            if form.photo.data:
                filename = secure_filename(form.photo.data.filename)
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                form.photo.data.save(photo_path)
                photo_url = f"uploads/{filename}"
            
            # レコード作成
            record = PlayRecord(
                date=form.date.data,
                machine_type_id=form.machine_type_id.data,
                investment=form.investment.data,
                naki_count=form.naki_count.data,
                hiroi_count=form.hiroi_count.data,
                probability_id=form.probability_id.data,
                exchange_rate_id=form.exchange_rate_id.data,
                memo=form.memo.data,
                photo_url=photo_url
            )
            
            # 計算処理
            machine = MachineType.query.get(form.machine_type_id.data)
            probability = ProbabilitySetting.query.get(form.probability_id.data)
            exchange_rate = ExchangeRate.query.get(form.exchange_rate_id.data)
            
            # 鳴き→拾い率を計算
            if record.naki_count > 0:
                record.naki_to_hiroi_rate = record.hiroi_count / record.naki_count
            else:
                record.naki_to_hiroi_rate = 0
            
            # 拾い→大当たり期待数を計算
            record.expected_wins = record.hiroi_count * probability.probability_value
            
            # 予想出玉を計算
            record.expected_payout = int(record.expected_wins * machine.average_payout)
            
            # 差玉・差額を計算
            record.payout_difference = record.expected_payout - record.investment
            record.amount_difference = int(record.payout_difference * exchange_rate.rate)
            
            db.session.add(record)
            db.session.commit()
            
            flash('データを保存しました', 'success')
            return redirect(url_for('index'))
        
        # GETリクエストの場合
        machines = MachineType.query.all()
        probabilities = ProbabilitySetting.query.all()
        exchange_rates = ExchangeRate.query.all()
        
        return render_template('input.html', 
                              form=form, 
                              machines=machines,
                              probabilities=probabilities,
                              exchange_rates=exchange_rates)
    
    @app.route('/history')
    def history():
        # 月間カレンダーの準備
        year = int(request.args.get('year', date.today().year))
        month = int(request.args.get('month', date.today().month))
        
        # 前月と翌月
        if month == 1:
            prev_month = {'year': year - 1, 'month': 12}
        else:
            prev_month = {'year': year, 'month': month - 1}
            
        if month == 12:
            next_month = {'year': year + 1, 'month': 1}
        else:
            next_month = {'year': year, 'month': month + 1}
        
        # カレンダーデータの作成
        cal = calendar.monthcalendar(year, month)
        calendar_data = []
        
        # 月の最初の日と最後の日
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        
        # この月のすべての記録を取得
        month_records = PlayRecord.query.filter(
            PlayRecord.date >= first_day,
            PlayRecord.date <= last_day
        ).all()
        
        # 日付ごとの収支を計算
        daily_profits = {}
        for record in month_records:
            day = record.date.day
            if day not in daily_profits:
                daily_profits[day] = 0
            daily_profits[day] += record.amount_difference
        
        # カレンダーデータの作成
        for week in cal:
            week_data = []
            for day in week:
                if day == 0:
                    # 月に含まれない日
                    week_data.append({
                        'day': None,
                        'current_month': False
                    })
                else:
                    current_date = date(year, month, day)
                    has_records = day in daily_profits
                    profit = daily_profits.get(day, 0)
                    
                    week_data.append({
                        'day': day,
                        'date': current_date.strftime('%Y-%m-%d'),
                        'current_month': True,
                        'has_records': has_records,
                        'profit': profit
                    })
            calendar_data.append(week_data)
        
        # 月間統計データを取得
        monthly_records = PlayRecord.query.filter(
            PlayRecord.date >= first_day,
            PlayRecord.date <= last_day
        ).all()
        
        total_investment = sum(record.investment for record in monthly_records)
        total_profit = sum(record.amount_difference for record in monthly_records)
        
        if monthly_records:
            avg_naki_to_hiroi_rate = sum(record.naki_to_hiroi_rate for record in monthly_records) / len(monthly_records)
        else:
            avg_naki_to_hiroi_rate = 0
        
        monthly_stats = {
            'total_investment': total_investment,
            'total_profit': total_profit,
            'avg_naki_to_hiroi_rate': avg_naki_to_hiroi_rate
        }
        
        # 機種分布データの準備
        machine_counts = {}
        for record in monthly_records:
            machine_name = record.machine_type.name
            if machine_name not in machine_counts:
                machine_counts[machine_name] = 0
            machine_counts[machine_name] += 1
        
        machine_distribution = {
            'labels': list(machine_counts.keys()),
            'data': list(machine_counts.values())
        }
        
        # 機種別統計を取得
        machine_stats = []
        machines = MachineType.query.all()
        
        for machine in machines:
            machine_records = PlayRecord.query.filter_by(machine_type_id=machine.id).all()
            if machine_records:
                play_count = len(machine_records)
                total_investment = sum(record.investment for record in machine_records)
                total_profit = sum(record.amount_difference for record in machine_records)
                avg_naki_to_hiroi_rate = sum(record.naki_to_hiroi_rate for record in machine_records) / play_count
                
                machine_stats.append({
                    'machine_type': machine,
                    'play_count': play_count,
                    'total_investment': total_investment,
                    'total_profit': total_profit,
                    'avg_naki_to_hiroi_rate': avg_naki_to_hiroi_rate
                })
        
        # 全記録一覧（ページネーション）
        page = int(request.args.get('page', 1))
        per_page = 10
        
        search = request.args.get('search', '')
        if search:
            # 検索条件に一致する記録を取得
            records_query = PlayRecord.query.join(MachineType).filter(
                MachineType.name.ilike(f'%{search}%')
            )
        else:
            records_query = PlayRecord.query
        
        pagination = records_query.order_by(PlayRecord.date.desc()).paginate(page=page, per_page=per_page)
        records = pagination.items
        
        return render_template('history.html',
                              year=year,
                              month=month,
                              prev_month=prev_month,
                              next_month=next_month,
                              calendar_data=calendar_data,
                              monthly_stats=monthly_stats,
                              machine_distribution=machine_distribution,
                              machine_stats=machine_stats,
                              records=records,
                              pagination=pagination)
    
    @app.route('/settings', methods=['GET'])
    def settings():
        # 機種一覧を取得
        machines = MachineType.query.all()
        
        # 役物確率一覧を取得
        probabilities = ProbabilitySetting.query.all()
        
        # 換金率一覧を取得
        exchange_rates = ExchangeRate.query.all()
        
        # ユーザー設定を取得
        user_settings = UserSetting.query.first()
        if not user_settings:
            # デフォルト設定を作成
            user_settings = UserSetting()
            db.session.add(user_settings)
            db.session.commit()
        
        return render_template('settings.html',
                              machines=machines,
                              probabilities=probabilities,
                              exchange_rates=exchange_rates,
                              user_settings=user_settings)
    
    @app.route('/update_settings', methods=['POST'])
    def update_settings():
        # ユーザー設定を更新
        user_settings = UserSetting.query.first()
        if not user_settings:
            user_settings = UserSetting()
            db.session.add(user_settings)
        
        user_settings.alert_threshold = float(request.form.get('alert_threshold', 20)) / 100
        user_settings.theme = request.form.get('theme', 'light')
        user_settings.display_mode = request.form.get('display_mode', 'standard')
        
        db.session.commit()
        
        flash('設定を保存しました', 'success')
        return redirect(url_for('settings'))
    
    # 機種管理API
    @app.route('/add_machine', methods=['POST'])
    def add_machine():
        name = request.form.get('name')
        average_payout = int(request.form.get('average_payout'))
        notes = request.form.get('notes', '')
        
        machine = MachineType(name=name, average_payout=average_payout, notes=notes)
        db.session.add(machine)
        db.session.commit()
        
        flash('機種を追加しました', 'success')
        return redirect(url_for('settings'))
    
    @app.route('/edit_machine', methods=['POST'])
    def edit_machine():
        machine_id = int(request.form.get('id'))
        name = request.form.get('name')
        average_payout = int(request.form.get('average_payout'))
        notes = request.form.get('notes', '')
        
        machine = MachineType.query.get(machine_id)
        if machine:
            machine.name = name
            machine.average_payout = average_payout
            machine.notes = notes
            db.session.commit()
            
            flash('機種を更新しました', 'success')
        else:
            flash('機種が見つかりません', 'danger')
        
        return redirect(url_for('settings'))
    
    # 役物確率管理API
    @app.route('/add_probability', methods=['POST'])
    def add_probability():
        machine_id = int(request.form.get('machine_id'))
        probability = request.form.get('probability')
        probability_value = float(request.form.get('probability_value'))
        is_default = 'is_default' in request.form
        
        # 同じ機種の他の確率のデフォルト設定を解除
        if is_default:
            ProbabilitySetting.query.filter_by(
                machine_type_id=machine_id, 
                is_default=True
            ).update({'is_default': False})
        
        prob = ProbabilitySetting(
            machine_type_id=machine_id,
            probability=probability,
            probability_value=probability_value,
            is_default=is_default
        )
        db.session.add(prob)
        db.session.commit()
        
        flash('役物確率を追加しました', 'success')
        return redirect(url_for('settings'))
    
    # 換金率管理API
    @app.route('/add_exchange_rate', methods=['POST'])
    def add_exchange_rate():
        rate = float(request.form.get('rate'))
        name = request.form.get('name', '')
        is_default = 'is_default' in request.form
        
        # 他の換金率のデフォルト設定を解除
        if is_default:
            ExchangeRate.query.filter_by(is_default=True).update({'is_default': False})
        
        exchange_rate = ExchangeRate(
            rate=rate,
            name=name,
            is_default=is_default
        )
        db.session.add(exchange_rate)
        db.session.commit()
        
        flash('換金率を追加しました', 'success')
        return redirect(url_for('settings'))
    
    # 記録詳細・編集・削除API
    @app.route('/record/<int:record_id>')
    def record_detail(record_id):
        record = PlayRecord.query.get_or_404(record_id)
        return render_template('record_detail.html', record=record)
    
    @app.route('/record/<int:record_id>/edit', methods=['GET', 'POST'])
    def edit_record(record_id):
        record = PlayRecord.query.get_or_404(record_id)
        
        # 編集フォームの処理（省略）
        
        return render_template('edit_record.html', record=record)
    
    @app.route('/record/<int:record_id>/delete', methods=['POST'])
    def delete_record(record_id):
        record = PlayRecord.query.get_or_404(record_id)
        db.session.delete(record)
        db.session.commit()
        
        flash('記録を削除しました', 'success')
        return redirect(url_for('history'))
    
    # 機種詳細API
    @app.route('/machine/<int:machine_id>')
    def machine_detail(machine_id):
        machine = MachineType.query.get_or_404(machine_id)
        records = PlayRecord.query.filter_by(machine_type_id=machine_id).order_by(PlayRecord.date.desc()).all()
        
        # 統計データの計算
        total_investment = sum(record.investment for record in records)
        total_profit = sum(record.amount_difference for record in records)
        
        if records:
            avg_naki_to_hiroi_rate = sum(record.naki_to_hiroi_rate for record in records) / len(records)
        else:
            avg_naki_to_hiroi_rate = 0
        
        stats = {
            'total_investment': total_investment,
            'total_profit': total_profit,
            'avg_naki_to_hiroi_rate': avg_naki_to_hiroi_rate,
            'play_count': len(records)
        }
        
        return render_template('machine_detail.html', 
                              machine=machine, 
                              records=records, 
                              stats=stats)
    
    # 計算API
    @app.route('/api/calculate', methods=['POST'])
    def calculate():
        data = request.json
        
        naki_count = float(data.get('naki_count', 0))
        hiroi_count = float(data.get('hiroi_count', 0))
        investment = float(data.get('investment', 0))
        probability_value = float(data.get('probability_value', 0))
        exchange_rate = float(data.get('exchange_rate', 0))
        average_payout = float(data.get('average_payout', 0))
        
        # 鳴き→拾い率を計算
        naki_to_hiroi_rate = 0
        if naki_count > 0:
            naki_to_hiroi_rate = hiroi_count / naki_count
        
        # 拾い→大当たり期待数を計算
        expected_wins = hiroi_count * probability_value
        
        # 予想出玉を計算
        expected_payout = int(expected_wins * average_payout)
        
        # 差玉・差額を計算
        payout_difference = expected_payout - investment
        amount_difference = int(payout_difference * exchange_rate)
        
        # ボーダー率を計算
        border_rate = 0
        if naki_count > 0 and probability_value > 0 and average_payout > 0:
            border_rate = investment / (average_payout * probability_value * naki_count)
        
        return jsonify({
            'naki_to_hiroi_rate': naki_to_hiroi_rate,
            'expected_wins': expected_wins,
            'expected_payout': expected_payout,
            'payout_difference': payout_difference,
            'amount_difference': amount_difference,
            'border_rate': border_rate
        })
    
    # 日別記録API
    @app.route('/api/day_records/<date_str>')
    def day_records(date_str):
        try:
            record_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            records = PlayRecord.query.filter_by(date=record_date).all()
            
            result = []
            for record in records:
                result.append({
                    'id': record.id,
                    'machine_name': record.machine_type.name,
                    'investment': record.investment,
                    'naki_count': record.naki_count,
                    'hiroi_count': record.hiroi_count,
                    'naki_to_hiroi_rate': record.naki_to_hiroi_rate,
                    'amount_difference': record.amount_difference
                })
            
            return jsonify(result)
        except:
            return jsonify([])
    
    # 回収アラートAPI
    @app.route('/api/check_alert', methods=['POST'])
    def check_alert():
        data = request.json
        
        machine_id = data.get('machine_id')
        naki_to_hiroi_rate = float(data.get('naki_to_hiroi_rate', 0))
        
        # ユーザー設定のアラートしきい値を取得
        user_settings = UserSetting.query.first()
        if not user_settings:
            user_settings = UserSetting()
        
        alert_threshold = user_settings.alert_threshold
        
        # 機種の過去の平均鳴き→拾い率を取得
        records = PlayRecord.query.filter_by(machine_type_id=machine_id).all()
        
        if not records:
            return jsonify({'alert': False})
        
        avg_naki_to_hiroi_rate = sum(record.naki_to_hiroi_rate for record in records) / len(records)
        
        # 現在の鳴き→拾い率が平均より一定割合以上低下しているかチェック
        rate_decrease = (avg_naki_to_hiroi_rate - naki_to_hiroi_rate) / avg_naki_to_hiroi_rate
        
        return jsonify({
            'alert': rate_decrease >= alert_threshold,
            'avg_rate': avg_naki_to_hiroi_rate,
            'current_rate': naki_to_hiroi_rate,
            'decrease_percent': rate_decrease * 100
        })
    
    return app
