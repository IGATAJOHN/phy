document.addEventListener('DOMContentLoaded', function() {
  // Service Worker Registration
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js').then(function(registration) {
      console.log('Service Worker registered with scope:', registration.scope);
    }).catch(function(error) {
      console.log('Service Worker registration failed:', error);
    });
  }

  // PWA Install Prompt
  let deferredPrompt;
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    document.getElementById('installBtn').style.display = 'block';

    document.getElementById('installBtn').addEventListener('click', () => {
      deferredPrompt.prompt();
      deferredPrompt.userChoice.then((choiceResult) => {
        if (choiceResult.outcome === 'accepted') {
          console.log('User accepted the install prompt');
        } else {
          console.log('User dismissed the install prompt');
        }
      });
    });
  });

  // File Upload Handling
  document.getElementById('fileInput').addEventListener('change', function() {
    const fileInput = this;
    const selectedFileName = document.getElementById('selectedFileName');

    if (fileInput.files.length > 0) {
      selectedFileName.textContent = `Selected file: ${fileInput.files[0].name}`;
      selectedFileName.classList.remove('hidden');
    } else {
      selectedFileName.classList.add('hidden');
    }
  });

  // Modal Controls
  document.getElementById('closeModal').addEventListener('click', function() {
    const modal = document.getElementById('conceptsModal');
    modal.classList.add('hidden');
  });

  document.getElementById('upgradeBtn').addEventListener('click', function() {
    const modal = document.getElementById('upgradeModal');
    modal.classList.remove('hidden');
  });

  document.getElementById('closeUpgradeModal').addEventListener('click', function() {
    const modal = document.getElementById('upgradeModal');
    modal.classList.add('hidden');
  });
});
