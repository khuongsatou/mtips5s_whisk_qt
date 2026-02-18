/**
 * Whisk Captcha Bridge — Background Service Worker.
 *
 * Uses chrome.scripting.executeScript with world: "MAIN" to access
 * grecaptcha.enterprise.execute() in the page's real context.
 */

const SITE_KEY = '6LdsFiUsAAAAAIjVDZcuLhaHiDn5nnHVXVRQGeMV';
const DEFAULT_ACTION = 'VIDEO_GENERATION';

let connectionStatus = 'disconnected';
let tokenCount = 0;
let lastError = null;
let lastToken = null;

/**
 * Execute grecaptcha in MAIN world of a target tab.
 */
async function executeCaptcha(tabId, action = DEFAULT_ACTION) {
    console.log(`🔐 [Captcha] Executing in tab ${tabId}, action: ${action}`);

    try {
        const results = await chrome.scripting.executeScript({
            target: { tabId },
            world: 'MAIN',
            func: async (siteKey, action) => {
                try {
                    if (!window.grecaptcha?.enterprise?.execute) {
                        return { error: 'grecaptcha.enterprise.execute not found on page' };
                    }
                    const token = await window.grecaptcha.enterprise.execute(siteKey, { action });
                    return { token };
                } catch (e) {
                    return { error: e.message || String(e) };
                }
            },
            args: [SITE_KEY, action],
        });

        const result = results?.[0]?.result;

        if (!result || result.error) {
            throw new Error(result?.error || 'MAIN world captcha execution failed');
        }

        lastToken = result.token;
        tokenCount++;
        lastError = null;
        connectionStatus = 'connected';
        updateBadge();

        console.log(`🔐 [Captcha] ✅ Token captured: ${result.token.substring(0, 50)}...`);
        return result.token;

    } catch (error) {
        console.error(`🔐 [Captcha] ❌ Failed:`, error.message);
        lastError = error.message;
        throw error;
    }
}

/**
 * Find a tab on labs.google/fx
 */
async function findLabsTab() {
    const tabs = await chrome.tabs.query({ url: 'https://labs.google/fx/*' });
    return tabs.length > 0 ? tabs[0] : null;
}

// Listen for messages from content script and popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'STATUS_UPDATE') {
        connectionStatus = message.status;
        lastError = message.error || null;
        updateBadge();
        sendResponse({ ok: true });

    } else if (message.type === 'GET_STATUS') {
        sendResponse({
            status: connectionStatus,
            tokenCount,
            lastError,
            lastToken,
        });

    } else if (message.type === 'EXECUTE_CAPTCHA') {
        // Called from popup Test button or content_script polling
        const action = message.action || DEFAULT_ACTION;
        const tabId = message.tabId;

        (async () => {
            try {
                let targetTabId = tabId;
                if (!targetTabId) {
                    const tab = await findLabsTab();
                    if (!tab) {
                        sendResponse({ success: false, error: 'No labs.google/fx tab found. Open one first.' });
                        return;
                    }
                    targetTabId = tab.id;
                }

                const token = await executeCaptcha(targetTabId, action);
                sendResponse({ success: true, token });
            } catch (error) {
                sendResponse({ success: false, error: error.message });
            }
        })();
        return true; // Keep channel open for async response

    } else if (message.type === 'CAPTCHA_REQUEST_FROM_APP') {
        // Content script forwarding a request from localhost
        // Use sender.tab.id since content_script is already on labs.google
        const { action, count } = message;
        const senderTabId = sender?.tab?.id;

        console.log(`🔐 [Background] CAPTCHA_REQUEST_FROM_APP: action=${action}, count=${count}, senderTab=${senderTabId}`);

        (async () => {
            try {
                let targetTabId = senderTabId;
                if (!targetTabId) {
                    console.log(`🔐 [Background] No sender tab, searching for labs tab...`);
                    const tab = await findLabsTab();
                    if (!tab) {
                        console.error(`🔐 [Background] No labs.google tab found!`);
                        sendResponse({ success: false, error: 'No labs.google/fx tab found' });
                        return;
                    }
                    targetTabId = tab.id;
                }

                console.log(`🔐 [Background] Executing captcha in tab ${targetTabId}...`);
                const tokens = [];
                for (let i = 0; i < (count || 1); i++) {
                    try {
                        const token = await executeCaptcha(targetTabId, action || DEFAULT_ACTION);
                        tokens.push(token);
                    } catch (e) {
                        console.error(`🔐 [Background] Token ${i + 1} failed:`, e.message);
                    }
                }
                console.log(`🔐 [Background] Got ${tokens.length} token(s)`);
                sendResponse({ success: tokens.length > 0, tokens });
            } catch (e) {
                console.error(`🔐 [Background] CAPTCHA_REQUEST_FROM_APP error:`, e.message);
                sendResponse({ success: false, error: e.message });
            }
        })();
        return true;
    } else if (message.type === 'GET_COOKIE') {
        // Extract __Secure-next-auth.session-token from labs.google
        (async () => {
            try {
                const cookie = await chrome.cookies.get({
                    url: 'https://labs.google',
                    name: '__Secure-next-auth.session-token',
                });

                const cookieVal = cookie?.value || '';

                if (!cookieVal) {
                    sendResponse({ success: false, error: 'Cookie __Secure-next-auth.session-token not found on labs.google' });
                    return;
                }

                console.log(`🍪 [Cookie] Extracted session-token (${cookieVal.length} chars)`);

                // Send to bridge server and track result
                let bridgeSaved = false;
                let bridgeError = null;
                try {
                    const resp = await fetch('http://localhost:18923/bridge/cookie', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ cookie: cookieVal }),
                    });
                    const result = await resp.json();
                    bridgeSaved = result?.ok === true;
                    if (!bridgeSaved) bridgeError = result?.error || 'Unknown';
                    console.log(`🍪 [Cookie] Bridge POST: ${bridgeSaved ? '✅ saved' : '❌ failed: ' + bridgeError}`);
                } catch (e) {
                    bridgeError = e.message;
                    console.warn('🍪 [Cookie] Bridge POST failed:', e.message);
                }

                sendResponse({
                    success: true,
                    cookie: cookieVal,
                    count: 1,
                    bridgeSaved,
                    bridgeError,
                });
            } catch (error) {
                console.error('🍪 [Cookie] Error:', error.message);
                sendResponse({ success: false, error: error.message });
            }
        })();
        return true;
    } else if (message.type === 'START_COOKIE_SYNC') {
        // Start periodic cookie extraction → bridge
        if (cookieSyncTimer) clearInterval(cookieSyncTimer);
        cookieSyncActive = true;
        cookieSyncLastOk = null;
        cookieSyncError = null;

        const doSync = async () => {
            try {
                const cookie = await chrome.cookies.get({
                    url: 'https://labs.google',
                    name: '__Secure-next-auth.session-token',
                });
                const val = cookie?.value || '';
                if (!val) {
                    cookieSyncError = 'session-token not found';
                    return;
                }
                const resp = await fetch('http://localhost:18923/bridge/cookie', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ cookie: val }),
                });
                const result = await resp.json();
                cookieSyncLastOk = result?.ok === true;
                cookieSyncError = cookieSyncLastOk ? null : (result?.error || 'save failed');
                console.log(`🍪 [Sync] ${cookieSyncLastOk ? '✅' : '❌'} (${val.length} chars)`);
            } catch (e) {
                cookieSyncError = e.message;
                console.warn('🍪 [Sync] Error:', e.message);
            }
        };

        doSync(); // Run immediately
        cookieSyncTimer = setInterval(doSync, 7200000); // Every 2 hours
        sendResponse({ ok: true });

    } else if (message.type === 'STOP_COOKIE_SYNC') {
        if (cookieSyncTimer) { clearInterval(cookieSyncTimer); cookieSyncTimer = null; }
        cookieSyncActive = false;
        cookieSyncLastOk = null;
        cookieSyncError = null;
        sendResponse({ ok: true });

    } else if (message.type === 'GET_COOKIE_STATUS') {
        sendResponse({
            active: cookieSyncActive,
            lastOk: cookieSyncLastOk,
            error: cookieSyncError,
        });
    }

    return false;
});

// Cookie sync state
let cookieSyncActive = false;
let cookieSyncTimer = null;
let cookieSyncLastOk = null;
let cookieSyncError = null;

function updateBadge() {
    if (connectionStatus === 'connected' || connectionStatus === 'polling') {
        chrome.action.setBadgeText({ text: '✓' });
        chrome.action.setBadgeBackgroundColor({ color: '#22C55E' });
    } else {
        chrome.action.setBadgeText({ text: '✗' });
        chrome.action.setBadgeBackgroundColor({ color: '#EF4444' });
    }
}
