// メインアプリケーションJavaScript

// DOMが読み込まれたら実行
document.addEventListener('DOMContentLoaded', function() {
    // フォーム送信時の処理
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="loading-spinner me-2"></span>処理中...';
            }
        });
    });

    // 数値入力フィールドの処理
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(input => {
        // 入力値が変更されたときに計算を実行
        input.addEventListener('change', function() {
            const calculationForm = document.getElementById('calculation-form');
            if (calculationForm && calculationForm.dataset.autoCalculate === 'true') {
                calculateValues();
            }
        });
    });

    // セレクトフィールドの処理
    const selectFields = document.querySelectorAll('select');
    selectFields.forEach(select => {
        // 選択値が変更されたときに計算を実行
        select.addEventListener('change', function() {
            const calculationForm = document.getElementById('calculation-form');
            if (calculationForm && calculationForm.dataset.autoCalculate === 'true') {
                calculateValues();
            }
        });
    });

    // 計算ボタンの処理
    const calculateButton = document.getElementById('calculate-button');
    if (calculateButton) {
        calculateButton.addEventListener('click', calculateValues);
    }

    // 画像アップロードプレビュー
    const photoInput = document.getElementById('photo');
    const photoPreview = document.getElementById('photo-preview');
    if (photoInput && photoPreview) {
        photoInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    photoPreview.src = e.target.result;
                    photoPreview.style.display = 'block';
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    }
});

// 計算ロジック
function calculateValues() {
    // 入力値の取得
    const nakiCount = parseFloat(document.getElementById('naki_count').value) || 0;
    const hiroiCount = parseFloat(document.getElementById('hiroi_count').value) || 0;
    const investment = parseFloat(document.getElementById('investment').value) || 0;
    
    // 選択値の取得
    const probabilitySelect = document.getElementById('probability_id');
    const exchangeRateSelect = document.getElementById('exchange_rate_id');
    const machineTypeSelect = document.getElementById('machine_type_id');
    
    if (!probabilitySelect || !exchangeRateSelect || !machineTypeSelect) {
        return;
    }
    
    // 選択されたオプションからデータ属性を取得
    const probabilityValue = parseFloat(probabilitySelect.options[probabilitySelect.selectedIndex].dataset.value) || 0;
    const exchangeRate = parseFloat(exchangeRateSelect.options[exchangeRateSelect.selectedIndex].dataset.rate) || 0;
    const averagePayout = parseFloat(machineTypeSelect.options[machineTypeSelect.selectedIndex].dataset.payout) || 0;
    
    // 計算処理
    let nakiToHiroiRate = 0;
    if (nakiCount > 0) {
        nakiToHiroiRate = hiroiCount / nakiCount;
    }
    
    const expectedWins = hiroiCount * probabilityValue;
    const expectedPayout = Math.round(expectedWins * averagePayout);
    const payoutDifference = expectedPayout - investment;
    const amountDifference = Math.round(payoutDifference * exchangeRate);
    
    // ボーダー計算
    let borderRate = 0;
    if (nakiCount > 0 && probabilityValue > 0 && averagePayout > 0) {
        borderRate = investment / (averagePayout * probabilityValue * nakiCount);
    }
    
    // 結果の表示
    updateResultDisplay('naki-to-hiroi-rate', (nakiToHiroiRate * 100).toFixed(2) + '%');
    updateResultDisplay('expected-wins', expectedWins.toFixed(2));
    updateResultDisplay('expected-payout', expectedPayout.toLocaleString());
    updateResultDisplay('payout-difference', payoutDifference.toLocaleString(), payoutDifference >= 0);
    updateResultDisplay('amount-difference', amountDifference.toLocaleString() + '円', amountDifference >= 0);
    updateResultDisplay('border-rate', (borderRate * 100).toFixed(2) + '%');
    
    // グラフの更新（存在する場合）
    updateCharts(nakiToHiroiRate, expectedWins, payoutDifference);
}

// 結果表示の更新
function updateResultDisplay(elementId, value, isPositive) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
        
        // 正負の値によるスタイル変更
        if (isPositive !== undefined) {
            element.classList.remove('positive-value', 'negative-value');
            if (isPositive) {
                element.classList.add('positive-value');
            } else {
                element.classList.add('negative-value');
            }
        }
    }
}

// グラフの更新
function updateCharts(nakiToHiroiRate, expectedWins, payoutDifference) {
    // 結果グラフ（存在する場合）
    const resultChartCanvas = document.getElementById('result-chart');
    if (resultChartCanvas && window.resultChart) {
        window.resultChart.data.datasets[0].data = [nakiToHiroiRate * 100, expectedWins, payoutDifference > 0 ? payoutDifference : 0];
        window.resultChart.data.datasets[1].data = [0, 0, payoutDifference < 0 ? Math.abs(payoutDifference) : 0];
        window.resultChart.update();
    }
}

// PWA インストールプロンプト
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
    // インストールプロンプトを表示せずに保存
    e.preventDefault();
    deferredPrompt = e;
    
    // インストールボタンを表示（存在する場合）
    const installButton = document.getElementById('install-button');
    if (installButton) {
        installButton.style.display = 'block';
        
        installButton.addEventListener('click', () => {
            // インストールプロンプトを表示
            deferredPrompt.prompt();
            
            // ユーザーの選択を待つ
            deferredPrompt.userChoice.then((choiceResult) => {
                if (choiceResult.outcome === 'accepted') {
                    console.log('ユーザーがアプリをインストールしました');
                } else {
                    console.log('ユーザーがインストールを拒否しました');
                }
                deferredPrompt = null;
                installButton.style.display = 'none';
            });
        });
    }
});
