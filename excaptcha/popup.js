/**
 * Whisk Captcha Bridge — Popup Script.
 *
 * Shows status, provides start/stop control, and Test button
 * to execute captcha and display the resulting token.
 */

const dot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const errorText = document.getElementById('errorText');
const tokenStat = document.getElementById('tokenStat');
const toggleBtn = document.getElementById('toggleBtn');
const testBtn = document.getElementById('testBtn');
const tokenResult = document.getElementById('tokenResult');
const projectNameEl = document.getElementById('projectName');

let currentStatus = 'disconnected';

/** Fetch project name from bridge /bridge/info */
async function fetchProjectName() {
    try {
        const resp = await fetch('http://localhost:18923/bridge/info', {
            signal: AbortSignal.timeout(2000),
        });
        const data = await resp.json();
        if (data.project_name) {
            projectNameEl.textContent = '📌 ' + data.project_name;
            projectNameEl.style.display = 'block';
        } else {
            projectNameEl.style.display = 'none';
        }
    } catch {
        projectNameEl.style.display = 'none';
    }
}

function updateUI(data) {
    currentStatus = data.status || 'disconnected';

    dot.className = 'dot';
    if (currentStatus === 'connected' || currentStatus === 'polling') {
        dot.classList.add('green');
        statusText.textContent = '🟢 Connected';
        toggleBtn.textContent = '⏹ Stop';
        toggleBtn.className = 'btn btn-stop';
    } else {
        dot.classList.add('red');
        statusText.textContent = '🔴 Disconnected';
        toggleBtn.textContent = '▶ Start';
        toggleBtn.className = 'btn btn-start';
    }

    if (data.lastError) {
        errorText.textContent = data.lastError;
        errorText.style.display = 'block';
    } else {
        errorText.style.display = 'none';
    }

    tokenStat.textContent = `Tokens sent: ${data.tokenCount || 0}`;
}

// Fetch current status
chrome.runtime.sendMessage({ type: 'GET_STATUS' }, (response) => {
    if (response) {
        updateUI(response);
        // Show last token if any
        if (response.lastToken) {
            tokenResult.value = response.lastToken;
            tokenResult.className = 'token-result success';
        }
    }
});
fetchProjectName();

// Toggle button (Start/Stop polling)
toggleBtn.addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (!tab || !tab.url?.includes('labs.google/fx')) {
        statusText.textContent = '⚠️ Open labs.google/fx first';
        dot.className = 'dot yellow';
        return;
    }

    const cmd = currentStatus === 'disconnected' ? 'START_POLLING' : 'STOP_POLLING';

    chrome.tabs.sendMessage(tab.id, { type: cmd }, (response) => {
        if (chrome.runtime.lastError) {
            statusText.textContent = '⚠️ Refresh labs.google/fx tab';
            dot.className = 'dot yellow';
            return;
        }
        setTimeout(() => {
            chrome.runtime.sendMessage({ type: 'GET_STATUS' }, (r) => {
                if (r) updateUI(r);
            });
        }, 500);
    });
});

// Test button — execute captcha and show token
testBtn.addEventListener('click', async () => {
    testBtn.disabled = true;
    testBtn.textContent = '⏳ Getting...';
    tokenResult.value = 'Executing grecaptcha.enterprise.execute()...';
    tokenResult.className = 'token-result';

    chrome.runtime.sendMessage(
        { type: 'EXECUTE_CAPTCHA', action: 'VIDEO_GENERATION' },
        (response) => {
            testBtn.disabled = false;
            testBtn.textContent = '🧪 Test';

            if (response?.success && response.token) {
                tokenResult.value = response.token;
                tokenResult.className = 'token-result success';
                // Also refresh status to update token count
                chrome.runtime.sendMessage({ type: 'GET_STATUS' }, (r) => {
                    if (r) updateUI(r);
                });
            } else {
                tokenResult.value = `❌ Error: ${response?.error || 'Unknown error'}`;
                tokenResult.className = 'token-result error';
            }
        }
    );
});

// Cookie button — one-time extract from browser
const cookieBtn = document.getElementById('cookieBtn');
const cookieResult = document.getElementById('cookieResult');
cookieBtn.addEventListener('click', () => {
    cookieBtn.disabled = true;
    cookieBtn.textContent = '⏳ Getting...';
    cookieResult.value = 'Extracting cookie from labs.google...';
    cookieResult.className = 'token-result';

    chrome.runtime.sendMessage(
        { type: 'GET_COOKIE' },
        (response) => {
            cookieBtn.disabled = false;
            cookieBtn.textContent = '🍪 Get Cookie';

            if (response?.success && response.cookie) {
                cookieResult.value = response.cookie;
                if (response.bridgeSaved) {
                    cookieResult.className = 'token-result success';
                } else {
                    cookieResult.className = 'token-result';
                    cookieResult.value += `\n\n⚠️ Bridge: ${response.bridgeError || 'not saved'}`;
                }
            } else {
                cookieResult.value = `❌ Error: ${response?.error || 'No cookies found'}`;
                cookieResult.className = 'token-result error';
            }
        }
    );
});

// Cookie Sync toggle — periodic extraction to bridge
const cookieSyncBtn = document.getElementById('cookieSyncBtn');
const cookieSyncStat = document.getElementById('cookieSyncStat');
let cookieSyncActive = false;

function updateCookieSyncUI(active, error) {
    cookieSyncActive = active;
    if (active) {
        cookieSyncBtn.textContent = '⏹ Stop Cookie';
        cookieSyncBtn.style.background = '#EF4444';
        cookieSyncStat.textContent = error
            ? `🍪 Sync: ⚠️ ${error}`
            : '🍪 Sync: ✅ Active (every 2h)';
    } else {
        cookieSyncBtn.textContent = '▶ Start Cookie';
        cookieSyncBtn.style.background = '#D97706';
        cookieSyncStat.textContent = '';
    }
}

// Check initial cookie sync state
chrome.runtime.sendMessage({ type: 'GET_COOKIE_STATUS' }, (r) => {
    if (r) updateCookieSyncUI(r.active, r.error);
});

cookieSyncBtn.addEventListener('click', () => {
    const cmd = cookieSyncActive ? 'STOP_COOKIE_SYNC' : 'START_COOKIE_SYNC';
    chrome.runtime.sendMessage({ type: cmd }, () => {
        setTimeout(() => {
            chrome.runtime.sendMessage({ type: 'GET_COOKIE_STATUS' }, (r) => {
                if (r) updateCookieSyncUI(r.active, r.error);
            });
        }, 500);
    });
});

// Auto-refresh status every 2 seconds
setInterval(() => {
    chrome.runtime.sendMessage({ type: 'GET_STATUS' }, (response) => {
        if (response) updateUI(response);
    });
    chrome.runtime.sendMessage({ type: 'GET_COOKIE_STATUS' }, (r) => {
        if (r) updateCookieSyncUI(r.active, r.error);
    });
    fetchProjectName();
}, 2000);
