
// --- Manual Control Features ---

let isPaused = false;

// Poll control status every 1s
function startControlPolling() {
    setInterval(pollControlStatus, 1000);
    pollControlStatus(); // Initial check
}

async function pollControlStatus() {
    try {
        const response = await fetch('/api/control/status');
        if (!response.ok) return; // API might not be ready
        const data = await response.json();

        isPaused = data.paused;
        updateControlUI();
    } catch (e) {
        // console.debug("Control status poll failed:", e);
    }
}

function updateControlUI() {
    const group = document.getElementById('sim-control-group');
    const btnPause = document.getElementById('btn-play-pause');
    const btnStep = document.getElementById('btn-step');

    // Always show if API works (backend supports it)
    if (group) group.style.display = 'flex';

    if (btnPause) {
        btnPause.textContent = isPaused ? "RESUME" : "PAUSE";
        btnPause.className = isPaused ? "btn-outline" : "btn-accent";
    }

    if (btnStep) {
        btnStep.disabled = !isPaused;
        btnStep.style.opacity = isPaused ? 1 : 0.5;
    }
}

async function togglePause() {
    const action = isPaused ? 'resume' : 'pause';
    try {
        const response = await fetch(`/api/control/${action}`, { method: 'POST' });
        const data = await response.json();
        if (data.status === 'success') {
            isPaused = (action === 'pause');
            updateControlUI();
        }
    } catch (e) {
        console.error(`Failed to ${action}:`, e);
    }
}

async function triggerStep() {
    try {
        await fetch('/api/control/step', { method: 'POST' });
        // UI will update naturally via stream or next poll
    } catch (e) {
        console.error("Step trigger failed:", e);
    }
}

// Hook into Init
document.addEventListener('DOMContentLoaded', () => {
    // ... existing init ...
    startControlPolling();
});
