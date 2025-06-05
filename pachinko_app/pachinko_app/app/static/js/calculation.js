// 計算ロジック関連のJavaScript

// 入力値に基づいて期待値・収支を計算する関数
function calculateExpectedValue() {
    // 入力値を取得
    const nakiCount = parseFloat(document.getElementById('naki_count').value) || 0;
    const hiroiCount = parseFloat(document.getElementById('hiroi_count').value) || 0;
    const investment = parseFloat(document.getElementById('investment').value) || 0;
    
    // 選択された機種、確率、換金率の情報を取得
    const machineSelect = document.getElementById('machine_type_id');
    const probabilitySelect = document.getElementById('probability_id');
    const exchangeRateSelect = document.getElementById('exchange_rate_id');
    
    if (!machineSelect || !probabilitySelect || !exchangeRateSelect) {
        return; // 必要な要素がない場合は処理しない
    }
    
    const machineId = machineSelect.value;
    const probabilityId = probabilitySelect.value;
    const exchangeRateId = exchangeRateSelect.value;
    
    // データ属性から値を取得
    const averagePayout = parseFloat(machineSelect.options[machineSelect.selectedIndex].dataset.payout) || 0;
    const probabilityValue = parseFloat(probabilitySelect.options[probabilitySelect.selectedIndex].dataset.value) || 0;
    const exchangeRate = parseFloat(exchangeRateSelect.options[exchangeRateSelect.selectedIndex].dataset.rate) || 0;
    
    // 鳴き→拾い率を計算
    let nakiToHiroiRate = 0;
    if (nakiCount > 0) {
        nakiToHiroiRate = hiroiCount / nakiCount;
    }
    
    // 拾い→大当たり期待数を計算
    const expectedWins = hiroiCount * probabilityValue;
    
    // 予想出玉を計算
    const expectedPayout = Math.floor(expectedWins * averagePayout);
    
    // 差玉・差額を計算
    const payoutDifference = expectedPayout - investment;
    const amountDifference = Math.floor(payoutDifference * exchangeRate);
    
    // ボーダー率を計算
    let borderRate = 0;
    if (nakiCount > 0 && probabilityValue > 0 && averagePayout > 0) {
        borderRate = investment / (averagePayout * probabilityValue * nakiCount);
    }
    
    // 結果を表示
    document.getElementById('naki_to_hiroi_rate').textContent = (nakiToHiroiRate * 100).toFixed(2) + '%';
    document.getElementById('expected_wins').textContent = expectedWins.toFixed(2);
    document.getElementById('expected_payout').textContent = expectedPayout.toLocaleString() + '玉';
    
    const payoutDiffElement = document.getElementById('payout_difference');
    payoutDiffElement.textContent = payoutDifference.toLocaleString() + '玉';
    payoutDiffElement.className = payoutDifference >= 0 ? 'positive-value' : 'negative-value';
    
    const amountDiffElement = document.getElementById('amount_difference');
    amountDiffElement.textContent = amountDifference.toLocaleString() + '円';
    amountDiffElement.className = amountDifference >= 0 ? 'positive-value' : 'negative-value';
    
    document.getElementById('border_rate').textContent = (borderRate * 100).toFixed(2) + '%';
    
    // 回収アラートチェック
    checkRecoveryAlert(machineId, nakiToHiroiRate);
    
    // グラフを更新
    updateCharts(nakiToHiroiRate, expectedWins, payoutDifference, amountDifference);
}

// 回収アラートをチェックする関数
function checkRecoveryAlert(machineId, nakiToHiroiRate) {
    // APIにデータを送信
    fetch('/api/check_alert', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            machine_id: machineId,
            naki_to_hiroi_rate: nakiToHiroiRate
        })
    })
    .then(response => response.json())
    .then(data => {
        const alertElement = document.getElementById('recovery_alert');
        if (!alertElement) return;
        
        if (data.alert) {
            // アラート表示
            alertElement.style.display = 'block';
            alertElement.innerHTML = `
                <div class="alert alert-warning" role="alert">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>回収アラート:</strong> 現在の鳴き→拾い率(${(data.current_rate * 100).toFixed(2)}%)が
                    平均(${(data.avg_rate * 100).toFixed(2)}%)より${data.decrease_percent.toFixed(1)}%低下しています。
                    回収の可能性があります。
                </div>
            `;
        } else {
            // アラート非表示
            alertElement.style.display = 'none';
        }
    })
    .catch(error => {
        console.error('回収アラートチェックエラー:', error);
    });
}

// グラフを更新する関数
function updateCharts(nakiToHiroiRate, expectedWins, payoutDifference, amountDifference) {
    // 鳴き→拾い率グラフ
    const rateChartCanvas = document.getElementById('rate-chart');
    if (rateChartCanvas && window.rateChart) {
        window.rateChart.data.datasets[0].data = [nakiToHiroiRate * 100, 100 - (nakiToHiroiRate * 100)];
        window.rateChart.update();
    }
    
    // 収支グラフ
    const profitChartCanvas = document.getElementById('profit-chart');
    if (profitChartCanvas && window.profitChart) {
        window.profitChart.data.datasets[0].data = [
            amountDifference >= 0 ? amountDifference : 0,
            amountDifference < 0 ? -amountDifference : 0
        ];
        window.profitChart.update();
    }
}

// グラフを初期化する関数
function initCharts() {
    // 鳴き→拾い率グラフ
    const rateChartCanvas = document.getElementById('rate-chart');
    if (rateChartCanvas) {
        window.rateChart = new Chart(rateChartCanvas, {
            type: 'doughnut',
            data: {
                labels: ['鳴き→拾い率', ''],
                datasets: [{
                    data: [0, 100],
                    backgroundColor: [
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(200, 200, 200, 0.2)'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.raw.toFixed(2) + '%';
                            }
                        }
                    }
                }
            }
        });
    }
    
    // 収支グラフ
    const profitChartCanvas = document.getElementById('profit-chart');
    if (profitChartCanvas) {
        window.profitChart = new Chart(profitChartCanvas, {
            type: 'bar',
            data: {
                labels: ['収支'],
                datasets: [{
                    label: '収支',
                    data: [0],
                    backgroundColor: [
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(255, 99, 132, 0.8)'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString() + '円';
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.raw.toLocaleString() + '円';
                            }
                        }
                    }
                }
            }
        });
    }
}

// 機種選択時に役物確率を更新する関数
function updateProbabilities() {
    const machineSelect = document.getElementById('machine_type_id');
    const probabilitySelect = document.getElementById('probability_id');
    
    if (!machineSelect || !probabilitySelect) {
        return;
    }
    
    const machineId = machineSelect.value;
    
    // APIから機種に対応する役物確率を取得
    fetch(`/api/probabilities/${machineId}`)
        .then(response => response.json())
        .then(data => {
            // 選択肢をクリア
            probabilitySelect.innerHTML = '';
            
            // 新しい選択肢を追加
            data.forEach(prob => {
                const option = document.createElement('option');
                option.value = prob.id;
                option.textContent = prob.probability;
                option.dataset.value = prob.probability_value;
                
                // デフォルト値を選択
                if (prob.is_default) {
                    option.selected = true;
                }
                
                probabilitySelect.appendChild(option);
            });
            
            // 計算を更新
            calculateExpectedValue();
        })
        .catch(error => {
            console.error('役物確率取得エラー:', error);
        });
}

// ページ読み込み時の処理
document.addEventListener('DOMContentLoaded', function() {
    // 入力フォームのイベントリスナー設定
    const inputForm = document.getElementById('input-form');
    if (inputForm) {
        // 入力値が変更されたら計算を実行
        const inputElements = inputForm.querySelectorAll('input, select');
        inputElements.forEach(element => {
            element.addEventListener('change', calculateExpectedValue);
            element.addEventListener('input', calculateExpectedValue);
        });
        
        // 機種選択時に役物確率を更新
        const machineSelect = document.getElementById('machine_type_id');
        if (machineSelect) {
            machineSelect.addEventListener('change', updateProbabilities);
        }
        
        // 初期計算
        calculateExpectedValue();
    }
    
    // グラフの初期化
    initCharts();
    
    // 月間収支グラフの初期化
    const monthlyChartCanvas = document.getElementById('monthly-chart');
    if (monthlyChartCanvas && monthlyChartData) {
        new Chart(monthlyChartCanvas, {
            type: 'line',
            data: {
                labels: monthlyChartData.labels,
                datasets: [{
                    label: '日別収支',
                    data: monthlyChartData.profits,
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: function(context) {
                        const value = context.dataset.data[context.dataIndex];
                        return value >= 0 ? 'rgba(75, 192, 192, 1)' : 'rgba(255, 99, 132, 1)';
                    },
                    pointRadius: 5,
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString() + '円';
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + context.raw.toLocaleString() + '円';
                            }
                        }
                    }
                }
            }
        });
    }
    
    // 機種分布グラフの初期化
    const distributionChartCanvas = document.getElementById('machine-distribution-chart');
    if (distributionChartCanvas && machineDistribution) {
        new Chart(distributionChartCanvas, {
            type: 'pie',
            data: {
                labels: machineDistribution.labels,
                datasets: [{
                    data: machineDistribution.data,
                    backgroundColor: [
                        'rgba(54, 162, 235, 0.7)',
                        'rgba(75, 192, 192, 0.7)',
                        'rgba(255, 206, 86, 0.7)',
                        'rgba(255, 99, 132, 0.7)',
                        'rgba(153, 102, 255, 0.7)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
});
