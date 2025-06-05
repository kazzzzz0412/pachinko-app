// PWA登録スクリプト
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function() {
    navigator.serviceWorker.register('/static/js/service-worker.js')
      .then(function(registration) {
        console.log('ServiceWorker登録成功:', registration.scope);
        
        // インストールボタンの処理
        let deferredPrompt;
        const installButton = document.getElementById('install-button');
        const installInstructions = document.getElementById('install-instructions');
        
        window.addEventListener('beforeinstallprompt', (e) => {
          // インストールプロンプトを表示せず、イベントを保存
          e.preventDefault();
          deferredPrompt = e;
          
          // インストールボタンを表示
          if (installButton) {
            installButton.style.display = 'block';
            
            installButton.addEventListener('click', () => {
              // インストールボタンを非表示
              installButton.style.display = 'none';
              
              // インストールプロンプトを表示
              deferredPrompt.prompt();
              
              // ユーザーの選択を待機
              deferredPrompt.userChoice.then((choiceResult) => {
                if (choiceResult.outcome === 'accepted') {
                  console.log('ユーザーがインストールを承認しました');
                  // インストール手順を非表示
                  if (installInstructions) {
                    installInstructions.style.display = 'none';
                  }
                } else {
                  console.log('ユーザーがインストールを拒否しました');
                  // インストールボタンを再表示
                  installButton.style.display = 'block';
                }
                deferredPrompt = null;
              });
            });
          }
        });
        
        // アプリがインストール済みの場合
        window.addEventListener('appinstalled', (evt) => {
          console.log('アプリがインストールされました');
          if (installButton) {
            installButton.style.display = 'none';
          }
          if (installInstructions) {
            installInstructions.style.display = 'none';
          }
        });
      })
      .catch(function(error) {
        console.log('ServiceWorker登録失敗:', error);
      });
  });
}

// オフライン検出
window.addEventListener('online', updateOnlineStatus);
window.addEventListener('offline', updateOnlineStatus);

function updateOnlineStatus() {
  const statusElement = document.getElementById('connection-status');
  if (!statusElement) return;
  
  if (navigator.onLine) {
    statusElement.textContent = 'オンライン';
    statusElement.className = 'badge bg-success';
    
    // オフライン中に保存されたデータがあれば同期
    syncOfflineData();
  } else {
    statusElement.textContent = 'オフライン';
    statusElement.className = 'badge bg-danger';
    
    // オフライン通知
    showOfflineNotification();
  }
}

// オフライン通知
function showOfflineNotification() {
  const notificationContainer = document.getElementById('notification-container');
  if (!notificationContainer) return;
  
  const notification = document.createElement('div');
  notification.className = 'alert alert-warning alert-dismissible fade show';
  notification.innerHTML = `
    <i class="fas fa-wifi-slash me-2"></i>
    <strong>オフラインモード:</strong> インターネット接続がありません。一部の機能が制限されます。
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;
  
  notificationContainer.appendChild(notification);
  
  // 5秒後に自動的に消える
  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => {
      notificationContainer.removeChild(notification);
    }, 150);
  }, 5000);
}

// オフラインデータの同期
function syncOfflineData() {
  // IndexedDBに保存されたオフラインデータを取得して同期
  // 実装は省略
}

// 初期状態の確認
document.addEventListener('DOMContentLoaded', function() {
  updateOnlineStatus();
});
