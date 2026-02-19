/**
 * Whisk Captcha Bridge — Content Script.
 *
 * Injected into labs.google/fx pages.
 * Polls local Whisk Desktop app for captcha requests,
 * then asks the background service worker to execute grecaptcha
 * in MAIN world (since content scripts can't access page JS).
 *
 * Supports multi-channel routing (1..5).
 */

const APP_BASE = 'http://localhost:18923';
const POLL_INTERVAL = 2000;

let isPolling = false;
let pollTimer = null;
let currentChannel = 1; // Default channel

/**
 * Poll the desktop app for captcha requests on the current channel.
 */
async function pollForRequests() {
    if (!isPolling) return;

    try {
        const response = await fetch(`${APP_BASE}/captcha/request?channel=${currentChannel}`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' },
            signal: AbortSignal.timeout(3000),
        });

        if (response.status === 200) {
            const data = await response.json();
            if (data.need_token) {
                const action = data.action || 'VIDEO_GENERATION';
                const count = data.count || 1;
                const ch = data.channel || currentChannel;

                console.log(`[Whisk Captcha] 📥 Got request: ch=${ch}, action=${action}, count=${count}`);

                // Ask background to execute captcha in MAIN world
                try {
                    const result = await new Promise((resolve, reject) => {
                        chrome.runtime.sendMessage(
                            {
                                type: 'CAPTCHA_REQUEST_FROM_APP',
                                action,
                                count,
                                channel: ch,
                            },
                            (response) => {
                                if (chrome.runtime.lastError) {
                                    reject(new Error(chrome.runtime.lastError.message));
                                    return;
                                }
                                resolve(response);
                            }
                        );
                    });

                    console.log(`[Whisk Captcha] 🔐 Background response:`, result);

                    if (result?.success && result.tokens?.length > 0) {
                        // Send tokens back to desktop app with channel
                        try {
                            const postResp = await fetch(`${APP_BASE}/captcha/token`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                    tokens: result.tokens,
                                    action,
                                    channel: ch,
                                }),
                                signal: AbortSignal.timeout(3000),
                            });
                            console.log(`[Whisk Captcha] ✅ Sent ${result.tokens.length} token(s) on ch ${ch}, status=${postResp.status}`);
                        } catch (e) {
                            console.error(`[Whisk Captcha] ❌ Failed to POST tokens:`, e.message);
                        }
                    } else {
                        console.warn(`[Whisk Captcha] ⚠️ No tokens received from background:`, result?.error || 'unknown');
                    }
                } catch (e) {
                    console.error(`[Whisk Captcha] ❌ sendMessage error:`, e.message);
                }
            }
        }

        chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', status: 'polling', channel: currentChannel });

    } catch (error) {
        if (error.name === 'AbortError' || error.message?.includes('Failed to fetch')) {
            chrome.runtime.sendMessage({
                type: 'STATUS_UPDATE',
                status: 'disconnected',
                error: 'App not running',
            });
        } else {
            console.error(`[Whisk Captcha] Poll error:`, error.message);
            chrome.runtime.sendMessage({
                type: 'STATUS_UPDATE',
                status: 'disconnected',
                error: error.message,
            });
        }
    }

    if (isPolling) {
        pollTimer = setTimeout(pollForRequests, POLL_INTERVAL);
    }
}

/**
 * Start polling.
 */
function start() {
    console.log(`[Whisk Captcha] 🔌 Starting captcha bridge on channel ${currentChannel}...`);
    chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', status: 'connected', channel: currentChannel });
    isPolling = true;
    pollForRequests();
}

// Listen for start/stop commands from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'START_POLLING') {
        currentChannel = message.channel || 1;
        if (!isPolling) start();
        sendResponse({ ok: true });
    } else if (message.type === 'STOP_POLLING') {
        isPolling = false;
        if (pollTimer) clearTimeout(pollTimer);
        chrome.runtime.sendMessage({ type: 'STATUS_UPDATE', status: 'disconnected' });
        sendResponse({ ok: true });
    } else if (message.type === 'SET_CHANNEL') {
        currentChannel = message.channel || 1;
        console.log(`[Whisk Captcha] 📡 Channel switched to ${currentChannel}`);
        sendResponse({ ok: true });
    }
    return true;
});

// Load saved channel and auto-start
chrome.storage.local.get(['captchaChannel'], (result) => {
    currentChannel = result.captchaChannel || 1;
    start();
});
