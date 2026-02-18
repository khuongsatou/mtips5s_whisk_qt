#!/usr/bin/env node
/**
 * Puppeteer Token Capture Sidecar (Persistent Mode)
 * Browser stays open, receives commands via stdin, outputs tokens to stdout
 * 
 * Commands (via stdin):
 *   GET_TOKENS <count>     - Get <count> tokens
 *   RESTART_BROWSER        - Force restart browser
 *   SHUTDOWN               - Close browser and exit
 */

const { connect } = require('puppeteer-real-browser');
const readline = require('readline');

// ============ CONFIG ============
const GRECAPTCHA_SITE_KEY = '6LdsFiUsAAAAAIjVDZcuLhaHiDn5nnHVXVRQGeMV';
const FLOW_URL = 'https://labs.google/fx';
const GRECAPTCHA_WAIT_TIMEOUT = 5000;
const GRECAPTCHA_CHECK_INTERVAL = 200;

// ============ PARSE ARGS ============
const args = process.argv.slice(2);
let proxyUrl = null;
let RECAPTCHA_ACTION = 'VIDEO_GENERATION';  // Default value

// Parse arguments
for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    if (arg === '--help' || arg === '-h') {
        console.error('Usage: node capture-sidecar.js [options] [proxy_url]');
        console.error('Options:');
        console.error('  --type <action>    reCAPTCHA action type (default: VIDEO_GENERATION)');
        console.error('                     Supported values: VIDEO_GENERATION, IMAGE_GENERATION');
        console.error('  proxy_url          Optional proxy URL (http://host:port or socks5://host:port)');
        console.error('');
        console.error('Examples:');
        console.error('  node capture-sidecar.js');
        console.error('  node capture-sidecar.js --type IMAGE_GENERATION');
        console.error('  node capture-sidecar.js http://proxy.example.com:8080');
        console.error('  node capture-sidecar.js --type IMAGE_GENERATION http://proxy.example.com:8080');
        process.exit(0);
    } else if (arg === '--type') {
        // Next argument is the type value
        if (i + 1 < args.length) {
            RECAPTCHA_ACTION = args[i + 1];
            i++; // Skip next argument
        } else {
            console.error('Error: --type requires a value');
            process.exit(1);
        }
    } else if (!arg.startsWith('--')) {
        // Assume it's the proxy URL
        proxyUrl = arg;
    }
}

if (proxyUrl) {
    console.error(`[PPT] 🔧 Proxy URL: ${proxyUrl}`);
}

// ============ GLOBAL STATE ============
let browser = null;
let page = null;
let isReady = false;
let isStarting = false;
let browserPid = null; // Track Chrome PID for safe cleanup on Windows
let proxyStatus = null; // Track proxy status for UI logging: { used: bool, proxy: string, error?: string }
let proxyDisabled = false; // When true, never use proxy again (due to ERR_CONNECTION_RESET)

// Retry counter - reset on success, max 3 retries for non-403 errors
let errorRetryCount = 0;
const MAX_ERROR_RETRIES = 3;

// PID file path for persistent tracking (handles crash recovery)
const os = require('os');
const path = require('path');
const fs = require('fs');
const PID_FILE = path.join(os.tmpdir(), 'superveo-browser-pid.txt');

// ============ PID FILE HELPERS ============

function saveBrowserPid(pid) {
    try {
        fs.writeFileSync(PID_FILE, pid.toString());
        console.error(`[PPT] 💾 Saved browser PID ${pid} to file`);
    } catch (e) { }
}

function loadAndKillOldBrowserPid() {
    try {
        if (fs.existsSync(PID_FILE)) {
            const oldPid = fs.readFileSync(PID_FILE, 'utf8').trim();
            if (oldPid && process.platform === 'win32') {
                try {
                    const { execSync } = require('child_process');
                    execSync(`taskkill /F /PID ${oldPid} /T`, { stdio: 'ignore' });
                    console.error(`[PPT] 🔪 Killed orphan browser PID ${oldPid}`);
                } catch (e) { }
            }
            fs.unlinkSync(PID_FILE);
        }
    } catch (e) { }
}

function clearBrowserPidFile() {
    try {
        if (fs.existsSync(PID_FILE)) {
            fs.unlinkSync(PID_FILE);
        }
    } catch (e) { }
}

/**
 * Parse proxy URL and return puppeteer-real-browser compatible proxy config.
 * For SOCKS5: needs to be passed via --proxy-server browser arg
 * For HTTP: can use { host, port, username, password } object
 * 
 * Supports formats:
 * - http://user:pass@host:port
 * - socks5://user:pass@host:port
 * - host:port:user:pass
 * - host:port
 */
function parseProxy(proxyUrl, defaultProtocol = 'http') {
    if (!proxyUrl) return null;

    proxyUrl = proxyUrl.trim();

    // Detect protocol
    let protocol = defaultProtocol;
    let cleanProxy = proxyUrl;

    if (proxyUrl.startsWith('socks5h://')) {
        protocol = 'socks5';
        cleanProxy = proxyUrl.substring(10);
    } else if (proxyUrl.startsWith('socks5://')) {
        protocol = 'socks5';
        cleanProxy = proxyUrl.substring(9);
    } else if (proxyUrl.startsWith('https://')) {
        protocol = 'http';
        cleanProxy = proxyUrl.substring(8);
    } else if (proxyUrl.startsWith('http://')) {
        protocol = 'http';
        cleanProxy = proxyUrl.substring(7);
    }

    // Parse auth and host
    let username = undefined;
    let password = undefined;
    let host = undefined;
    let port = undefined;

    if (cleanProxy.includes('@')) {
        // Format: user:pass@host:port
        const atIndex = cleanProxy.lastIndexOf('@');
        const authPart = cleanProxy.substring(0, atIndex);
        const hostPort = cleanProxy.substring(atIndex + 1);

        if (authPart.includes(':')) {
            const colonIndex = authPart.indexOf(':');
            username = authPart.substring(0, colonIndex);
            password = authPart.substring(colonIndex + 1);
        } else {
            username = authPart;
        }

        const hostParts = hostPort.split(':');
        host = hostParts[0];
        port = hostParts[1] || '80';
    } else {
        const parts = cleanProxy.split(':');
        if (parts.length >= 2) {
            host = parts[0];
            port = parts[1];
            if (parts[2] && parts[2].trim()) username = parts[2].trim();
            if (parts[3] && parts[3].trim()) password = parts[3].trim();
            if (parts.length > 4) {
                const passValue = parts.slice(3).join(':').trim();
                if (passValue) password = passValue;
            }
        }
    }

    if (!host || !port) {
        console.error(`[Proxy] ⚠️ Invalid proxy format: ${proxyUrl}`);
        return null;
    }

    // Build proxy config for puppeteer-real-browser
    // For SOCKS5: puppeteer-real-browser uses the proxy object differently
    const proxyConfig = {
        host,
        port,
        protocol,  // Keep track of protocol  
    };

    if (username) {
        proxyConfig.username = username;
    }
    if (password) {
        proxyConfig.password = password;
    }

    // Also build full URL for browser args (needed for SOCKS5)
    let fullUrl;
    if (username && password) {
        fullUrl = `${protocol}://${username}:${password}@${host}:${port}`;
    } else if (username) {
        fullUrl = `${protocol}://${username}@${host}:${port}`;
    } else {
        fullUrl = `${protocol}://${host}:${port}`;
    }
    proxyConfig.url = fullUrl;

    console.error(`[Proxy] Parsed: ${protocol}://${host}:${port} (auth: ${username ? 'yes' : 'no'})`);

    return proxyConfig;
}

/**
 * Test proxy by checking TCP connectivity
 * Works for both HTTP and SOCKS5 proxies on Windows and macOS
 * Returns: Promise<boolean> - true if proxy is reachable, false otherwise
 */
function testProxyConnection(proxyUrl, timeoutMs = 5000) {
    return new Promise((resolve) => {
        if (!proxyUrl) return resolve(false);

        const net = require('net');

        // Parse proxy URL to get host and port
        let host, port;

        try {
            // Remove protocol prefix
            let cleanUrl = proxyUrl;
            if (cleanUrl.startsWith('socks5h://')) cleanUrl = cleanUrl.substring(10);
            else if (cleanUrl.startsWith('socks5://')) cleanUrl = cleanUrl.substring(9);
            else if (cleanUrl.startsWith('http://')) cleanUrl = cleanUrl.substring(7);
            else if (cleanUrl.startsWith('https://')) cleanUrl = cleanUrl.substring(8);

            // Remove auth if present
            if (cleanUrl.includes('@')) {
                cleanUrl = cleanUrl.substring(cleanUrl.lastIndexOf('@') + 1);
            }

            // Parse host:port or host:port:user:pass format
            const parts = cleanUrl.split(':');
            host = parts[0];
            port = parseInt(parts[1]) || 80;
        } catch (e) {
            console.error(`[Proxy Test] Failed to parse proxy URL: ${proxyUrl}`);
            return resolve(false);
        }

        console.error(`[Proxy Test] Testing TCP connection to ${host}:${port}...`);

        const socket = new net.Socket();
        let resolved = false;

        const cleanup = () => {
            if (!resolved) {
                resolved = true;
                socket.destroy();
            }
        };

        socket.setTimeout(timeoutMs);

        socket.on('connect', () => {
            console.error(`[Proxy Test] ✅ Proxy reachable! ${host}:${port}`);
            cleanup();
            resolve(true);
        });

        socket.on('timeout', () => {
            console.error(`[Proxy Test] ❌ Connection timeout`);
            cleanup();
            resolve(false);
        });

        socket.on('error', (err) => {
            console.error(`[Proxy Test] ❌ Connection error: ${err.message}`);
            cleanup();
            resolve(false);
        });

        socket.connect(port, host);
    });
}

// Kill Chrome/Chromium processes spawned by puppeteer
// IMPORTANT: On Windows, only kill specific browserPid to avoid killing user's Chrome
function killAllBrowsers() {
    const { execSync } = require('child_process');

    try {
        if (process.platform === 'darwin') {
            // macOS - Use pattern matching for puppeteer's temp profile
            try { execSync('pkill -9 -f "Google Chrome.*puppeteer_dev_profile"', { stdio: 'ignore' }); } catch (e) { }
            try { execSync('pkill -9 -f "Google Chrome.*--user-data-dir=/var/folders"', { stdio: 'ignore' }); } catch (e) { }
            try { execSync('pkill -9 -f "Google Chrome.*--user-data-dir=/tmp"', { stdio: 'ignore' }); } catch (e) { }
            try { execSync('pkill -9 -f "Chromium.*puppeteer"', { stdio: 'ignore' }); } catch (e) { }
        } else if (process.platform === 'win32') {
            // Windows - First kill any orphan browser from previous crash
            loadAndKillOldBrowserPid();

            // Then kill our current browser PID if we have one
            if (browserPid) {
                try {
                    execSync(`taskkill /F /PID ${browserPid} /T`, { stdio: 'ignore' });
                    console.error(`[PPT] 🔪 Killed browser PID ${browserPid}`);
                } catch (e) { }
                browserPid = null;
            }
            clearBrowserPidFile();
            // DO NOT use: taskkill /F /IM chrome.exe - this kills ALL Chrome instances!
        } else {
            // Linux - Use pattern matching for puppeteer's temp profile
            try { execSync('pkill -9 -f "chrome.*puppeteer"', { stdio: 'ignore' }); } catch (e) { }
            try { execSync('pkill -9 -f "chrome.*--user-data-dir=/tmp"', { stdio: 'ignore' }); } catch (e) { }
            try { execSync('pkill -9 -f "chromium.*puppeteer"', { stdio: 'ignore' }); } catch (e) { }
        }
        console.error('[PPT] 🔪 Killed existing browser processes');
    } catch (e) {
        // Ignore errors - no browsers to kill
    }
}

async function startBrowser() {
    if (isStarting) return false;
    isStarting = true;

    try {
        // Close existing browser instance if any
        if (browser) {
            console.error('[PPT] 🔄 Closing existing browser instance...');
            try { await browser.close(); } catch (e) { }
            browser = null;
            page = null;
        }

        // Force kill any orphan Chrome processes
        killAllBrowsers();

        // Wait a moment for processes to terminate
        await new Promise(r => setTimeout(r, 500));

        // Find system Chrome (like nodehelper.py)
        const findSystemChrome = () => {
            const fs = require('fs');
            const os = require('os');
            const path = require('path');

            let chromePaths = [];

            if (process.platform === 'darwin') {
                // macOS
                chromePaths = [
                    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                    path.join(os.homedir(), 'Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
                    '/Applications/Chromium.app/Contents/MacOS/Chromium',
                ];
            } else if (process.platform === 'win32') {
                // Windows
                chromePaths = [
                    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
                    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
                    path.join(os.homedir(), 'AppData\\Local\\Google\\Chrome\\Application\\chrome.exe'),
                ];
            } else {
                // Linux
                chromePaths = [
                    '/usr/bin/google-chrome',
                    '/usr/bin/google-chrome-stable',
                    '/usr/bin/chromium',
                    '/usr/bin/chromium-browser',
                    '/snap/bin/chromium',
                ];
            }

            for (const chromePath of chromePaths) {
                if (fs.existsSync(chromePath)) {
                    console.error(`[PPT] ✅ Found Chrome at: ${chromePath}`);
                    return chromePath;
                }
            }

            console.error('[PPT] ⚠️ Chrome not found in default paths, puppeteer will try to find it');
            return null;
        };

        const executablePath = findSystemChrome();

        const options = {
            headless: false,
            turnstile: true,
            args: [
                // Anti-detection flags
                '--incognito',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--no-first-run',
                '--no-default-browser-check',
                '--no-zygote',
                '--window-size=800,600',
                '--app=https://labs.google/fx/vi/tools/flow',
                '--window-position=-32000,-32000',
                '--ignore-certificate-errors',  // Help with SOCKS5 proxy SSL
            ],
            customConfig: {},
            connectOption: { defaultViewport: { width: 800, height: 600 } },
            disableXvfb: false,
            ignoreAllFlags: false,
        };

        // Use system Chrome if found
        if (executablePath) {
            options.executablePath = executablePath;
        }

        // Handle proxy configuration
        let useProxy = false;
        if (proxyUrl && !proxyDisabled) {
            const proxy = parseProxy(proxyUrl);
            if (proxy) {
                // Test proxy connectivity first
                console.error(`[PPT] 🔍 Testing proxy: ${proxy.host}:${proxy.port}...`);
                const proxyWorks = await testProxyConnection(proxyUrl, 5000);

                if (proxyWorks) {
                    // Proxy works - add to browser args
                    options.args.push(`--proxy-server=${proxy.url}`);
                    useProxy = true;
                    console.error(`[PPT] ✅ Proxy OK, using: ${proxy.url.replace(/:[^:@]+@/, ':***@')}`);
                } else {
                    // Proxy test failed - continue WITHOUT proxy
                    console.error(`[PPT] ❌ Proxy unreachable: ${proxy.host}:${proxy.port}`);
                    console.error(`[PPT] ⚠️ Continuing without proxy (direct connection)`);
                    proxyStatus = { used: false, proxy: proxyUrl, error: 'PROXY_UNREACHABLE', fallback: true };
                }
            } else {
                console.error(`[PPT] ⚠️ Invalid proxy URL, using direct connection`);
                proxyStatus = { used: false, proxy: proxyUrl, error: 'PROXY_INVALID', fallback: true };
            }
        } else if (proxyDisabled) {
            console.error('[PPT] 🚫 Proxy đã bị disable do lỗi trước đó, dùng kết nối trực tiếp');
            proxyStatus = { used: false, proxy: proxyUrl, error: 'PROXY_DISABLED', disabled: true };
        } else {
            console.error('[PPT] 🔗 No proxy configured, using direct connection');
        }

        // Connect to browser
        let result;
        try {
            result = await connect(options);
            if (useProxy) {
                proxyStatus = { used: true, proxy: proxyUrl, success: true };
                console.error(`[PPT] ✅ Connected with proxy`);
            } else if (!proxyStatus) {
                proxyStatus = { used: false, proxy: null, direct: true };
                console.error(`[PPT] ✅ Connected (direct)`);
            } else {
                console.error(`[PPT] ✅ Connected (direct - proxy skipped)`);
            }
        } catch (connectError) {
            // If proxy was used and failed, retry without proxy
            if (useProxy) {
                console.error(`[PPT] ❌ Connect with proxy failed: ${connectError.message}`);
                console.error(`[PPT] 🔄 Retrying without proxy...`);
                options.args = options.args.filter(arg => !arg.startsWith('--proxy-server='));
                proxyStatus = { used: false, proxy: proxyUrl, error: connectError.message, fallback: true };
                result = await connect(options);
                console.error(`[PPT] ✅ Connected (fallback direct)`);
            } else {
                throw connectError;
            }
        }

        browser = result.browser;
        page = result.page;

        // Store browser PID for safe cleanup on Windows
        try {
            const browserProcess = browser.process();
            if (browserProcess && browserProcess.pid) {
                browserPid = browserProcess.pid;
                console.error(`[PPT] 📝 Browser PID: ${browserPid}`);
                // Save to file for crash recovery on Windows
                if (process.platform === 'win32') {
                    saveBrowserPid(browserPid);
                }
            }
        } catch (e) {
            // Some puppeteer versions don't expose browser.process()
        }

        // Enable request interception to block unnecessary resources
        await page.setRequestInterception(true);
        page.on('request', (request) => {
            const resourceType = request.resourceType();
            const url = request.url();

            // Block fonts, images, media, stylesheets
            const blockedTypes = ['font', 'image', 'media', 'stylesheet'];

            // Block specific URL patterns that are not needed for grecaptcha
            const blockedPatterns = [
                'fonts.googleapis.com',
                'fonts.gstatic.com',
                '.woff',
                '.woff2',
                '.ttf',
                '.otf',
                '.eot',
                '.png',
                '.jpg',
                '.jpeg',
                '.gif',
                '.webp',
                '.svg',
                '.ico',
                '.mp4',
                '.webm',
                '.mp3',
                '.wav',
                'analytics',
                'tracking',
                'gtag',
                'facebook.com',
                'twitter.com',
                'doubleclick.net',
            ];

            // Allow grecaptcha and essential scripts
            const allowedPatterns = [
                'recaptcha',
                'grecaptcha',
                'gstatic.com/recaptcha',
                'google.com/recaptcha',
            ];

            // Check if URL matches allowed patterns (always allow these)
            const isAllowed = allowedPatterns.some(pattern => url.includes(pattern));
            if (isAllowed) {
                request.continue();
                return;
            }

            // Block by resource type
            if (blockedTypes.includes(resourceType)) {
                request.abort();
                return;
            }

            // Block by URL pattern
            const isBlocked = blockedPatterns.some(pattern => url.includes(pattern));
            if (isBlocked) {
                request.abort();
                return;
            }

            // Allow everything else
            request.continue();
        });

        // Inject protection script BEFORE navigation so it applies immediately
        await page.evaluateOnNewDocument(() => {
            // Block F12 and other dev tools shortcuts
            document.addEventListener('keydown', function (e) {
                if (e.key === 'F12' || e.keyCode === 123) {
                    e.preventDefault();
                    return false;
                }
                if (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'J' || e.key === 'C')) {
                    e.preventDefault();
                    return false;
                }
                if (e.ctrlKey && e.key === 'u') {
                    e.preventDefault();
                    return false;
                }
            });

            // Disable right-click context menu
            document.addEventListener('contextmenu', function (e) {
                e.preventDefault();
                return false;
            });

            // Inject style immediately when DOM is ready
            const injectStyle = () => {
                if (document.head) {
                    const style = document.createElement('style');
                    style.textContent = `
                        * {
                            -webkit-user-select: none !important;
                            -moz-user-select: none !important;
                            -ms-user-select: none !important;
                            user-select: none !important;
                        }
                        html, body {
                            background: #ffffff !important;
                            background-color: #ffffff !important;
                            margin: 0 !important;
                            padding: 0 !important;
                        }
                        body > *:not(#bypass-overlay) {
                            visibility: hidden !important;
                            opacity: 0 !important;
                        }
                        #bypass-overlay {
                            position: fixed !important;
                            top: 0 !important;
                            left: 0 !important;
                            width: 100vw !important;
                            height: 100vh !important;
                            background: #ffffff !important;
                            display: flex !important;
                            align-items: center !important;
                            justify-content: center !important;
                            z-index: 999999 !important;
                            visibility: visible !important;
                            opacity: 1 !important;
                        }
                        #bypass-overlay span {
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
                            font-size: 24px !important;
                            color: #666666 !important;
                            font-weight: 500 !important;
                        }
                    `;
                    document.head.appendChild(style);
                }
            };

            // Create overlay when body is ready
            const createOverlay = () => {
                if (document.body && !document.getElementById('bypass-overlay')) {
                    const overlay = document.createElement('div');
                    overlay.id = 'bypass-overlay';
                    overlay.innerHTML = '<span>🔐 Bypass Captcha...</span>';
                    document.body.insertBefore(overlay, document.body.firstChild);
                }
            };

            // Apply immediately if DOM ready, otherwise wait
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => {
                    injectStyle();
                    createOverlay();
                });
            } else {
                injectStyle();
                createOverlay();
            }

            // Also apply on mutation for dynamic content
            const observer = new MutationObserver(() => {
                injectStyle();
                createOverlay();
            });
            if (document.documentElement) {
                observer.observe(document.documentElement, { childList: true, subtree: true });
            }
        });

        // Navigate to Flow URL directly - with retry for connection issues
        try {
            await page.goto(FLOW_URL, { waitUntil: 'domcontentloaded' });
        } catch (navError) {
            const errMsg = navError.message || String(navError);
            // Check for ERR_CONNECTION_RESET - proxy issue
            if (errMsg.includes('ERR_CONNECTION_RESET') || errMsg.includes('net::ERR_CONNECTION_RESET')) {
                console.error(`[PPT] ❌ net::ERR_CONNECTION_RESET - Proxy lỗi!`);

                // If using proxy, disable it and retry with direct connection
                if (useProxy && !proxyDisabled) {
                    console.error(`[PPT] 🚫 Disabling proxy vĩnh viễn và thử lại với kết nối trực tiếp...`);
                    proxyDisabled = true; // Never use proxy again in this session
                    proxyStatus = {
                        used: false,
                        proxy: proxyUrl,
                        error: 'ERR_CONNECTION_RESET',
                        disabled: true,
                        message: 'Proxy lỗi - Đã chuyển sang kết nối trực tiếp'
                    };

                    // Close current browser and retry without proxy
                    if (browser) {
                        try { await browser.close(); } catch (e) { }
                        browser = null;
                        page = null;
                    }
                    killAllBrowsers();
                    await new Promise(r => setTimeout(r, 500));

                    // Retry startBrowser (will now skip proxy due to proxyDisabled flag)
                    isStarting = false; // Reset flag to allow retry
                    return await startBrowser();
                }

                // If not using proxy or proxy already disabled, rethrow the error
                throw new Error(`net::ERR_CONNECTION_RESET - Lỗi kết nối`);
            }
            // Other navigation errors - rethrow
            throw navError;
        }

        // No need to set cookies or reload - access directly

        // Wait for grecaptcha
        for (let i = 0; i < GRECAPTCHA_WAIT_TIMEOUT / GRECAPTCHA_CHECK_INTERVAL; i++) {
            const ready = await page.evaluate(() =>
                typeof window.grecaptcha?.enterprise?.execute === 'function'
            ).catch(() => false);
            if (ready) break;
            await new Promise(r => setTimeout(r, GRECAPTCHA_CHECK_INTERVAL));
        }

        const hasExecute = await page.evaluate(() =>
            !!(window.grecaptcha?.enterprise?.execute)
        ).catch(() => false);

        if (!hasExecute) {
            throw new Error('grecaptcha not ready');
        }

        isReady = true;
        isStarting = false;
        return { success: true };

    } catch (error) {
        console.error(`[PPT] ❌ startBrowser error: ${error.message}`);
        console.error(`[PPT] ❌ Stack: ${error.stack}`);
        isReady = false;
        isStarting = false;

        // Return detailed error for UI display
        let errorType = 'UNKNOWN';
        let errorHint = '';
        let isFatal = false;  // Fatal errors should not retry

        if (error.message.includes('Chrome') || error.message.includes('chrome') ||
            error.message.includes('executable') || error.message.includes('Failed to find browser') ||
            error.message.includes('No Chrome installations') || error.message.includes('browser not found')) {
            errorType = 'CHROME_NOT_FOUND';
            errorHint = 'Cài đặt Google Chrome hoặc kiểm tra đường dẫn Chrome';
            isFatal = true;  // Chrome not found - no point in retrying
        } else if (error.message.includes('ERR_CONNECTION_RESET')) {
            errorType = 'PROXY_CONNECTION_RESET';
            errorHint = 'Proxy lỗi - Đã chuyển sang kết nối trực tiếp';
            // Mark proxy as disabled so next retry won't use it
            if (!proxyDisabled && proxyUrl) {
                proxyDisabled = true;
                proxyStatus = {
                    used: false,
                    proxy: proxyUrl,
                    error: 'ERR_CONNECTION_RESET',
                    disabled: true,
                    message: 'Proxy lỗi - Đã chuyển sang kết nối trực tiếp'
                };
            }
        } else if (error.message.includes('proxy') || error.message.includes('PROXY')) {
            errorType = 'PROXY_ERROR';
            errorHint = 'Kiểm tra cài đặt proxy hoặc tắt proxy';
        } else if (error.message.includes('timeout') || error.message.includes('Timeout')) {
            errorType = 'TIMEOUT';
            errorHint = 'Kết nối chậm, thử lại sau';
        } else if (error.message.includes('navigation') || error.message.includes('Navigate')) {
            errorType = 'NAVIGATION_ERROR';
            errorHint = 'Không thể tải trang, kiểm tra kết nối mạng';
        }

        return {
            success: false,
            error: error.message,
            errorType,
            errorHint,
            isFatal  // If true, caller should NOT retry
        };
    }
}

/**
 * Check auth status before generating tokens
 * @returns {Promise<boolean>} - Returns true if should use FAKE mode
 */
async function checkAuth() {
    try {
        const rawDeviceId = process.env.VEO3_RAW_DEVICE_ID;
        const encryptedDeviceId = process.env.VEO3_DEVICE_ID;
        if (!rawDeviceId || !encryptedDeviceId) return false;

        const method = 'GET', url = 'https://imagenfx.art/api/v2/veo3/get-token';
        const timestamp = Math.floor(Date.now() / 1000).toString();
        const payload = `${method}|${url}|${timestamp}|${rawDeviceId}|`;
        const signature = require('crypto').createHmac('sha256', 'took_veo3').update(payload).digest('hex');

        const response = await fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json',
                'X-Device-ID': encryptedDeviceId,
                'X-App-Version': process.env.VEO3_APP_VERSION || '1.0.0',
                'X-Signature': signature,
                'X-Timestamp': timestamp,
                'Authorization': `Bearer ${process.env.VEO3_AUTH_TOKEN || ''}`
            },
            signal: AbortSignal.timeout(5000)
        });

        if (response.status === 401 || response.status === 403) {
            console.error(`[PPT] 🛑 Auth check failed (${response.status})`);
            return true;
        }
        return false;
    } catch (e) {
        return false; // Network error - allow normal flow
    }
}

async function fetchTokens(count) {
    if (!isReady || !page) {
        return { success: false, error: 'Browser not ready' };
    }

    try {
        // Check auth BEFORE generating tokens
        const shouldUseFake = await checkAuth();
        const action = shouldUseFake ? 'FAKE' : RECAPTCHA_ACTION;


        const results = await page.evaluate(async (siteKey, action, n) => {
            const promises = [];
            for (let i = 0; i < n; i++) {
                promises.push(
                    window.grecaptcha.enterprise.execute(siteKey, { action: action })
                        .then(token => ({ ok: true, token }))
                        .catch(e => ({ ok: false, error: e.message }))
                );
            }
            return Promise.all(promises);
        }, GRECAPTCHA_SITE_KEY, action, count);

        const tokens = results.filter(r => r.ok).map(r => r.token);

        if (tokens.length === 0) {
            // Check if we got 403 or rate limited
            const has403 = results.some(r => r.error && r.error.includes('403'));
            if (has403) {
                // 403 always requires restart (cookie/IP blocked)
                return { success: false, error: '403 Forbidden', restart: true, is403: true, proxyStatus };
            }
            return { success: false, error: 'No tokens received', proxyStatus };
        }

        // SUCCESS - reset error counter
        errorRetryCount = 0;
        return { success: true, tokens, proxyStatus };

    } catch (error) {
        const errorMsg = error.message || String(error);
        const is403 = errorMsg.includes('403');

        // Only 403 triggers immediate restart
        // Other errors: check retry counter
        if (is403) {
            return { success: false, error: errorMsg, restart: true, is403: true, proxyStatus };
        }

        // For other errors, don't request restart here - let handleCommand manage retries
        return { success: false, error: errorMsg, restart: false, proxyStatus };
    }
}

async function handleCommand(command) {
    const parts = command.trim().split(' ');
    const cmd = parts[0].toUpperCase();

    if (cmd === 'GET_TOKENS') {
        const count = parseInt(parts[1]) || 1;

        // Ensure browser is ready
        if (!isReady && !isStarting) {
            const startResult = await startBrowser();
            if (!startResult.success) {
                // Send detailed error to Rust for UI display
                const errorMsg = startResult.errorHint
                    ? `${startResult.error} - ${startResult.errorHint}`
                    : startResult.error || 'Failed to start browser';
                console.log(JSON.stringify({
                    success: false,
                    error: errorMsg,
                    errorType: startResult.errorType || 'UNKNOWN',
                    errorHint: startResult.errorHint || '',
                    isFatal: startResult.isFatal || false,  // Signal to stop completely
                    stopGeneration: startResult.isFatal || false  // Tell frontend to stop
                }));

                // If fatal error (e.g. Chrome not found), exit process
                if (startResult.isFatal) {
                    console.error(`[PPT] ❌ Fatal error: ${errorMsg} - Exiting`);
                    process.exit(1);
                }
                return;
            }
        }

        const result = await fetchTokens(count);

        // SUCCESS - already reset counter in fetchTokens, just return
        if (result.success) {
            console.log(JSON.stringify(result));
            return;
        }

        // ERROR HANDLING

        // 403 error - always restart immediately (cookie/IP blocked)
        if (result.is403) {
            console.error(`[PPT] 🔄 403 error - restarting browser...`);
            isReady = false;
            browser = null;
            page = null;
            errorRetryCount = 0; // Reset counter for 403 since we're doing a full restart

            const restartResult = await startBrowser();
            if (restartResult.success) {
                const retryResult = await fetchTokens(count);
                console.log(JSON.stringify(retryResult));
            } else {
                const errorMsg = restartResult.errorHint
                    ? `${restartResult.error} - ${restartResult.errorHint}`
                    : restartResult.error || 'Browser restart failed after 403';
                console.log(JSON.stringify({ success: false, error: errorMsg }));
            }
            return;
        }

        // Other errors - use retry counter
        errorRetryCount++;
        console.error(`[PPT] ⚠️ Error (attempt ${errorRetryCount}/${MAX_ERROR_RETRIES}): ${result.error}`);

        if (errorRetryCount >= MAX_ERROR_RETRIES) {
            // Max retries reached - stop retrying to avoid spam
            console.error(`[PPT] ❌ Max retries (${MAX_ERROR_RETRIES}) reached. Stopping retries.`);
            console.log(JSON.stringify({
                success: false,
                error: `${result.error} (max retries reached)`,
                maxRetriesReached: true,
                proxyStatus: result.proxyStatus
            }));
            return;
        }

        // Retry by restarting browser
        console.error(`[PPT] 🔄 Retrying... (${errorRetryCount}/${MAX_ERROR_RETRIES})`);
        isReady = false;
        browser = null;
        page = null;

        const restartResult = await startBrowser();
        if (restartResult.success) {
            const retryResult = await fetchTokens(count);
            if (retryResult.success) {
                // Success after retry - reset counter
                errorRetryCount = 0;
            }
            console.log(JSON.stringify(retryResult));
        } else {
            const errorMsg = restartResult.errorHint
                ? `${restartResult.error} - ${restartResult.errorHint}`
                : restartResult.error || 'Browser restart failed';
            console.log(JSON.stringify({ success: false, error: errorMsg }));
        }

    } else if (cmd === 'RESTART_BROWSER') {
        console.error('[PPT] 🔄 Manual restart requested...');
        isReady = false;
        browser = null;
        page = null;
        // Reset proxyDisabled on restart - new proxy rotation may work
        if (proxyDisabled) {
            console.error('[PPT] 🔄 Reset proxy flag - sẽ thử dùng proxy lại');
            proxyDisabled = false;
            proxyStatus = null;
        }
        const restartResult = await startBrowser();
        console.log(JSON.stringify({
            success: restartResult.success,
            message: restartResult.success ? 'Browser restarted' : (restartResult.error || 'Restart failed')
        }));

    } else if (cmd === 'RESET_PROXY') {
        // Reset proxy flag - called when proxy is rotated to try new proxy
        console.error('[PPT] 🔄 Reset proxy flag - sẽ thử dùng proxy mới');
        proxyDisabled = false;
        proxyStatus = null;
        console.log(JSON.stringify({ success: true, message: 'Proxy flag reset, will try proxy on next request' }));

    } else if (cmd === 'PING') {
        console.log(JSON.stringify({ success: true, ready: isReady, message: 'pong' }));

    } else if (cmd === 'SHUTDOWN') {
        console.error('[PPT] 🛑 Shutdown requested...');
        if (browser) {
            try { await browser.close(); } catch (e) { }
        }
        // Force kill any remaining Chrome processes
        killAllBrowsers();
        console.log(JSON.stringify({ success: true, message: 'Shutting down' }));
        process.exit(0);

    } else {
        console.log(JSON.stringify({ success: false, error: `Unknown command: ${cmd}` }));
    }
}

// ============ MAIN ============

async function main() {
    // Start browser initially
    const startResult = await startBrowser();

    if (startResult.success) {
        console.log(JSON.stringify({ success: true, message: 'READY' }));
    } else {
        // Send detailed error for UI display
        const errorMsg = startResult.errorHint
            ? `${startResult.error} - ${startResult.errorHint}`
            : startResult.error || 'INIT_FAILED';
        console.log(JSON.stringify({
            success: false,
            error: errorMsg,
            errorType: startResult.errorType || 'UNKNOWN',
            errorHint: startResult.errorHint || '',
            message: 'INIT_FAILED'
        }));
        process.exit(1);
    }

    // Listen for commands from stdin
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout,
        terminal: false
    });

    rl.on('line', async (line) => {
        await handleCommand(line);
    });

    rl.on('close', async () => {
        console.error('[PPT] 🛑 stdin closed, cleaning up...');
        if (browser) {
            try { await browser.close(); } catch (e) { }
        }
        killAllBrowsers();
        process.exit(0);
    });

    // Keep process alive
    process.on('SIGINT', async () => {
        console.error('[PPT] 🛑 SIGINT received, cleaning up...');
        if (browser) {
            try { await browser.close(); } catch (e) { }
        }
        killAllBrowsers();
        process.exit(0);
    });

    process.on('SIGTERM', async () => {
        console.error('[PPT] 🛑 SIGTERM received, cleaning up...');
        if (browser) {
            try { await browser.close(); } catch (e) { }
        }
        killAllBrowsers();
        process.exit(0);
    });
}

main().catch(err => {
    console.error('[PPT] ❌ Fatal error:', err.message);
    killAllBrowsers();
    process.exit(1);
});
