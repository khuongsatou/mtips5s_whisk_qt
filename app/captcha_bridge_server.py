"""
Whisk Desktop — Captcha Bridge HTTP Server.

Runs a lightweight HTTP server on localhost:18923 in a QThread.
The Chrome extension polls this server for captcha requests
and posts back tokens.

Endpoints:
  GET  /captcha/request  — Check if the app needs a captcha token
  POST /captcha/token    — Receive tokens from the extension
  GET  /captcha/status   — Get current bridge status
"""
import json
import queue
import urllib.request
import urllib.error
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from PySide6.QtCore import QThread, Signal

logger = logging.getLogger("whisk.captcha_bridge")

BRIDGE_PORT = 18923


class CaptchaBridgeHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the captcha bridge."""

    def log_message(self, format, *args):
        """Redirect HTTP logs to our logger (suppress noisy polling)."""
        msg = format % args
        # Suppress repetitive polling when idle
        if "/captcha/request" in msg or "/bridge/cookie" in msg or "/bridge/info" in msg:
            return
        logger.debug(f"[HTTP] {msg}")

    def _send_json(self, status_code, data):
        """Send a JSON response."""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _send_html(self, html):
        """Send an HTML response."""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self._send_json(200, {"ok": True})

    def do_GET(self):
        if self.path == "/" or self.path == "" or self.path == "/index.html":
            bridge = self.server.bridge
            self._send_html(self._build_login_page(bridge))

        elif self.path == "/dashboard":
            bridge = self.server.bridge
            self._send_html(self._build_landing_page(bridge))

        elif self.path == "/captcha/request":
            bridge = self.server.bridge
            if bridge.pending_request:
                self._send_json(200, {
                    "need_token": True,
                    "action": bridge.pending_request.get("action", "VIDEO_GENERATION"),
                    "count": bridge.pending_request.get("count", 1),
                })
            else:
                self._send_json(200, {"need_token": False})

        elif self.path == "/captcha/status":
            bridge = self.server.bridge
            self._send_json(200, {
                "running": True,
                "has_pending": bridge.pending_request is not None,
                "tokens_received": bridge.total_tokens_received,
                "project_name": bridge.project_name,
            })

        elif self.path == "/bridge/info":
            bridge = self.server.bridge
            self._send_json(200, {
                "project_name": bridge.project_name,
                "port": bridge.port,
                "running": True,
            })

        elif self.path == "/bridge/cookie":
            bridge = self.server.bridge
            self._send_json(200, {
                "cookie": bridge._stored_cookie,
                "has_cookie": bool(bridge._stored_cookie),
            })

        else:
            self._send_json(404, {"error": "Not found"})

    @staticmethod
    def _build_login_page(bridge):
        """Build the login gate page HTML."""
        return f'''<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🔐 Whisk Captcha Bridge — Login</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
  :root {{
    --bg-primary: #0B0F19;
    --bg-card: rgba(22, 33, 62, 0.7);
    --border: rgba(51, 65, 85, 0.5);
    --border-glow: rgba(124, 58, 237, 0.3);
    --text-primary: #F1F5F9;
    --text-secondary: #94A3B8;
    --text-muted: #64748B;
    --accent-purple: #8B5CF6;
    --accent-red: #EF4444;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Inter', -apple-system, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    min-height: 100vh;
    display: flex; align-items: center; justify-content: center;
  }}
  body::before {{
    content: '';
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background:
      radial-gradient(ellipse at 20% 50%, rgba(124,58,237,0.08) 0%, transparent 50%),
      radial-gradient(ellipse at 80% 20%, rgba(59,130,246,0.06) 0%, transparent 50%),
      radial-gradient(ellipse at 50% 80%, rgba(6,182,212,0.05) 0%, transparent 50%);
    pointer-events: none; z-index: 0;
    animation: bgPulse 8s ease-in-out infinite alternate;
  }}
  @keyframes bgPulse {{ 0% {{ opacity: 0.5; }} 100% {{ opacity: 1; }} }}
  .login-container {{
    position: relative; z-index: 1;
    width: 100%; max-width: 420px; padding: 0 24px;
  }}
  .login-card {{
    background: var(--bg-card);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--border); border-radius: 20px;
    padding: 48px 36px 40px;
    box-shadow: 0 0 0 1px rgba(124,58,237,0.1), 0 20px 60px rgba(0,0,0,0.4);
    transition: border-color 0.3s, box-shadow 0.3s;
  }}
  .login-card:hover {{
    border-color: var(--border-glow);
    box-shadow: 0 0 0 1px rgba(124,58,237,0.2), 0 20px 60px rgba(0,0,0,0.5), 0 0 60px rgba(124,58,237,0.08);
  }}
  .login-header {{ text-align: center; margin-bottom: 36px; }}
  .login-icon {{
    font-size: 48px; display: block; margin-bottom: 16px;
    filter: drop-shadow(0 0 20px rgba(124,58,237,0.4));
  }}
  .login-header h1 {{
    font-size: 24px; font-weight: 700;
    background: linear-gradient(135deg, #C4B5FD, #818CF8, #60A5FA);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin-bottom: 6px;
  }}
  .login-header p {{ color: var(--text-muted); font-size: 13px; }}
  .form-group {{ margin-bottom: 20px; }}
  .form-group label {{
    display: block; font-size: 12px; font-weight: 600;
    color: var(--text-secondary); margin-bottom: 8px;
    text-transform: uppercase; letter-spacing: 0.5px;
  }}
  .form-group input {{
    width: 100%; padding: 12px 16px;
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid var(--border); border-radius: 10px;
    color: var(--text-primary); font-family: inherit; font-size: 14px;
    transition: border-color 0.2s, box-shadow 0.2s; outline: none;
  }}
  .form-group input:focus {{
    border-color: var(--accent-purple);
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
  }}
  .form-group input::placeholder {{ color: var(--text-muted); }}
  .login-btn {{
    width: 100%; padding: 13px 24px;
    background: linear-gradient(135deg, #7C3AED, #6366F1);
    color: white; border: none; border-radius: 10px;
    font-family: inherit; font-size: 15px; font-weight: 600;
    cursor: pointer; transition: all 0.2s; margin-top: 8px;
  }}
  .login-btn:hover {{ transform: translateY(-1px); box-shadow: 0 8px 24px rgba(124,58,237,0.35); }}
  .login-btn:active {{ transform: translateY(0); }}
  .login-btn:disabled {{ opacity: 0.6; cursor: not-allowed; transform: none; }}
  .login-btn .spinner {{
    display: none; width: 18px; height: 18px;
    border: 2px solid rgba(255,255,255,0.3); border-top-color: white;
    border-radius: 50%; animation: spin 0.6s linear infinite;
    margin-right: 8px; vertical-align: middle;
  }}
  .login-btn.loading .spinner {{ display: inline-block; }}
  @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
  .error-msg {{
    background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3);
    border-radius: 8px; padding: 10px 14px; color: #FCA5A5;
    font-size: 13px; margin-bottom: 16px; display: none;
    animation: shake 0.3s ease;
  }}
  .error-msg.visible {{ display: block; }}
  @keyframes shake {{
    0%,100% {{ transform: translateX(0); }}
    25% {{ transform: translateX(-4px); }}
    75% {{ transform: translateX(4px); }}
  }}
  .footer {{ text-align: center; margin-top: 24px; color: var(--text-muted); font-size: 11px; }}
</style>
</head>
<body>
<div class="login-container">
  <div class="login-card">
    <div class="login-header">
      <span class="login-icon">🔐</span>
      <h1>Whisk Captcha Bridge</h1>
      {'<p style="color: #06B6D4; font-size: 13px; margin-top: 4px;">📌 ' + bridge.project_name + '</p>' if bridge.project_name else ''}
      <p>Đăng nhập để truy cập bảng điều khiển</p>
    </div>
    <div id="errorMsg" class="error-msg"></div>
    <form id="loginForm" onsubmit="handleLogin(event)">
      <div class="form-group">
        <label for="email">Email</label>
        <input type="email" id="email" placeholder="your@email.com" required autocomplete="email">
      </div>
      <div class="form-group">
        <label for="password">Mật khẩu</label>
        <input type="password" id="password" placeholder="••••••••" required autocomplete="current-password">
      </div>
      <button type="submit" class="login-btn" id="loginBtn">
        <span class="spinner"></span>
        <span class="btn-text">🔑 Đăng nhập</span>
      </button>
    </form>
  </div>
  <div class="footer">Whisk Captcha Bridge v1.0 · Port {bridge.port}</div>
</div>
<script>
  if (sessionStorage.getItem('bridge_auth')) {{
    window.location.href = '/dashboard';
  }}
  async function handleLogin(e) {{
    e.preventDefault();
    const btn = document.getElementById('loginBtn');
    const errEl = document.getElementById('errorMsg');
    const mail = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    errEl.classList.remove('visible');
    btn.classList.add('loading');
    btn.disabled = true;
    try {{
      const resp = await fetch('/bridge/login', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ mail, password }}),
      }});
      const data = await resp.json();
      if (resp.ok && data.ok) {{
        sessionStorage.setItem('bridge_auth', JSON.stringify(data));
        window.location.href = '/dashboard';
      }} else {{
        errEl.textContent = data.error || 'Đăng nhập thất bại';
        errEl.classList.add('visible');
      }}
    }} catch (err) {{
      errEl.textContent = 'Không thể kết nối server: ' + err.message;
      errEl.classList.add('visible');
    }} finally {{
      btn.classList.remove('loading');
      btn.disabled = false;
    }}
  }}
</script>
</body>
</html>'''

    @staticmethod
    def _build_landing_page(bridge):
        """Build the HTML landing page with API docs and live status."""
        tokens_received = bridge.total_tokens_received
        has_pending = bridge.pending_request is not None
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🔐 Whisk Captcha Bridge</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  :root {{
    --bg-primary: #0B0F19;
    --bg-card: rgba(22, 33, 62, 0.6);
    --bg-card-hover: rgba(30, 41, 75, 0.8);
    --bg-code: #0F172A;
    --border: rgba(51, 65, 85, 0.5);
    --border-glow: rgba(124, 58, 237, 0.3);
    --text-primary: #F1F5F9;
    --text-secondary: #94A3B8;
    --text-muted: #64748B;
    --accent-purple: #8B5CF6;
    --accent-blue: #3B82F6;
    --accent-cyan: #06B6D4;
    --accent-green: #10B981;
    --accent-amber: #F59E0B;
    --accent-red: #EF4444;
    --gradient-hero: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }}

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    min-height: 100vh;
  }}

  /* Animated background */
  body::before {{
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background:
      radial-gradient(ellipse at 20% 50%, rgba(124,58,237,0.08) 0%, transparent 50%),
      radial-gradient(ellipse at 80% 20%, rgba(59,130,246,0.06) 0%, transparent 50%),
      radial-gradient(ellipse at 50% 80%, rgba(6,182,212,0.05) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
  }}

  .container {{
    max-width: 860px;
    margin: 0 auto;
    padding: 40px 24px 60px;
    position: relative;
    z-index: 1;
  }}

  /* Hero */
  .hero {{
    text-align: center;
    margin-bottom: 48px;
  }}

  .hero-icon {{
    font-size: 48px;
    display: block;
    margin-bottom: 16px;
    filter: drop-shadow(0 0 20px rgba(124,58,237,0.4));
  }}

  .hero h1 {{
    font-size: 32px;
    font-weight: 700;
    background: linear-gradient(135deg, #C4B5FD, #818CF8, #60A5FA);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 8px;
    letter-spacing: -0.5px;
  }}

  .hero p {{
    color: var(--text-secondary);
    font-size: 15px;
    max-width: 500px;
    margin: 0 auto;
  }}

  /* Status bar */
  .status-bar {{
    display: flex;
    gap: 12px;
    justify-content: center;
    margin: 24px 0 40px;
    flex-wrap: wrap;
  }}

  .status-chip {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
    border: 1px solid var(--border);
    background: var(--bg-card);
    backdrop-filter: blur(10px);
  }}

  .status-dot {{
    width: 8px; height: 8px;
    border-radius: 50%;
    animation: pulse 2s infinite;
  }}

  .status-dot.green {{ background: var(--accent-green); box-shadow: 0 0 8px rgba(16,185,129,0.5); }}
  .status-dot.amber {{ background: var(--accent-amber); box-shadow: 0 0 8px rgba(245,158,11,0.5); }}

  @keyframes pulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.5; }}
  }}

  /* Section headers */
  .section-title {{
    font-size: 18px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 36px 0 16px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}

  .section-title::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, var(--border) 0%, transparent 100%);
  }}

  /* Endpoint cards */
  .endpoint {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 14px;
    backdrop-filter: blur(12px);
    transition: all 0.3s ease;
  }}

  .endpoint:hover {{
    background: var(--bg-card-hover);
    border-color: var(--border-glow);
    transform: translateY(-1px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.3);
  }}

  .endpoint-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
    flex-wrap: wrap;
  }}

  .method {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
  }}

  .method.get {{ background: rgba(16,185,129,0.15); color: var(--accent-green); border: 1px solid rgba(16,185,129,0.3); }}
  .method.post {{ background: rgba(59,130,246,0.15); color: var(--accent-blue); border: 1px solid rgba(59,130,246,0.3); }}

  .endpoint-path {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    color: var(--text-primary);
    font-weight: 500;
  }}

  .endpoint-desc {{
    color: var(--text-secondary);
    font-size: 13px;
    margin-bottom: 12px;
  }}

  /* Code blocks */
  .code-block {{
    background: var(--bg-code);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
    margin: 10px 0;
  }}

  .code-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 14px;
    background: rgba(30,41,59,0.5);
    border-bottom: 1px solid var(--border);
  }}

  .code-label {{
    font-size: 11px;
    color: var(--text-muted);
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}

  .try-btn {{
    padding: 4px 12px;
    border-radius: 6px;
    border: 1px solid var(--accent-purple);
    background: rgba(124,58,237,0.15);
    color: var(--accent-purple);
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }}

  .try-btn:hover {{
    background: var(--accent-purple);
    color: white;
  }}

  .try-btn:disabled {{
    opacity: 0.5;
    cursor: not-allowed;
  }}

  pre {{
    padding: 14px;
    overflow-x: auto;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    line-height: 1.7;
    color: #CBD5E1;
  }}

  pre .key {{ color: #7DD3FC; }}
  pre .str {{ color: #86EFAC; }}
  pre .num {{ color: #FCD34D; }}
  pre .bool {{ color: #C4B5FD; }}
  pre .comment {{ color: var(--text-muted); font-style: italic; }}

  /* Response area */
  .response-area {{
    margin-top: 8px;
    display: none;
  }}

  .response-area.visible {{
    display: block;
  }}

  .response-content {{
    background: var(--bg-code);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: var(--accent-green);
    min-height: 40px;
    white-space: pre-wrap;
    word-break: break-all;
  }}

  .response-content.error {{
    color: var(--accent-red);
  }}

  /* Steps guide */
  .steps {{
    display: grid;
    gap: 12px;
    margin-top: 16px;
  }}

  .step {{
    display: flex;
    gap: 14px;
    padding: 16px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    backdrop-filter: blur(12px);
    transition: all 0.3s;
  }}

  .step:hover {{
    border-color: var(--border-glow);
    background: var(--bg-card-hover);
  }}

  .step-num {{
    width: 32px; height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--accent-purple), var(--accent-blue));
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 14px;
    flex-shrink: 0;
  }}

  .step-content h3 {{
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 4px;
  }}

  .step-content p {{
    font-size: 13px;
    color: var(--text-secondary);
  }}

  .step-content code {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    background: var(--bg-code);
    padding: 2px 6px;
    border-radius: 4px;
    border: 1px solid var(--border);
    color: var(--accent-cyan);
  }}

  /* Architecture diagram */
  .arch-diagram {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 24px;
    margin-top: 16px;
    text-align: center;
    backdrop-filter: blur(12px);
  }}

  .arch-flow {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    flex-wrap: wrap;
    font-size: 13px;
  }}

  .arch-node {{
    padding: 10px 16px;
    border-radius: 10px;
    font-weight: 500;
    white-space: nowrap;
  }}

  .arch-node.app {{ background: rgba(124,58,237,0.2); border: 1px solid rgba(124,58,237,0.4); color: #C4B5FD; }}
  .arch-node.bridge {{ background: rgba(6,182,212,0.2); border: 1px solid rgba(6,182,212,0.4); color: #67E8F9; }}
  .arch-node.ext {{ background: rgba(59,130,246,0.2); border: 1px solid rgba(59,130,246,0.4); color: #93C5FD; }}
  .arch-node.google {{ background: rgba(16,185,129,0.2); border: 1px solid rgba(16,185,129,0.4); color: #6EE7B7; }}

  .arch-arrow {{
    color: var(--text-muted);
    font-size: 18px;
  }}

  /* Footer */
  .footer {{
    text-align: center;
    color: var(--text-muted);
    font-size: 11px;
    margin-top: 48px;
    padding-top: 24px;
    border-top: 1px solid var(--border);
  }}
</style>
</head>
<body>

<div class="container">
  <div class="hero">
    <span class="hero-icon">🔐</span>
    <h1>Whisk Captcha Bridge</h1>
    {'<p style="color: var(--accent-cyan); font-size: 14px; font-weight: 600; margin-bottom: 6px;">📌 ' + bridge.project_name + '</p>' if bridge.project_name else ''}
    <p>Local HTTP server giúp Chrome Extension giao tiếp với Whisk Desktop để lấy reCAPTCHA token</p>
  </div>

  <!-- Live status -->
  <div class="status-bar">
    <div class="status-chip">
      <div class="status-dot green"></div>
      Server: Running on port {bridge.port}
    </div>
    <div class="status-chip">
      <div class="status-dot {"amber" if has_pending else "green"}"></div>
      Pending: {"Yes" if has_pending else "None"}
    </div>
    <div class="status-chip">
      🎫 Tokens received: {tokens_received}
    </div>
  </div>

  <!-- Cookie Manager -->
  <h2 class="section-title">🍪 Cookie Manager</h2>
  <div class="endpoint" style="padding: 24px;">
    <div style="display: flex; gap: 10px; margin-bottom: 14px; flex-wrap: wrap;">
      <button class="try-btn" id="getCookieBtn" onclick="getCookie()" style="padding: 8px 16px; font-size: 13px;">
        📥 Get Cookie
      </button>
      <button class="try-btn" id="saveCookieBtn" onclick="saveCookie()" style="padding: 8px 16px; font-size: 13px;">
        💾 Save Cookie
      </button>
      <button class="try-btn" id="copyCookieBtn" onclick="copyCookie()" style="padding: 8px 16px; font-size: 13px;">
        📋 Copy
      </button>
      <button class="try-btn" id="clearCookieBtn" onclick="clearCookie()" style="padding: 8px 16px; font-size: 13px; border-color: var(--accent-red); color: var(--accent-red); background: rgba(239,68,68,0.1);">
        🗑️ Clear
      </button>
    </div>
    <textarea id="cookieArea" rows="4" placeholder="Paste cookie here or click Get Cookie..." style="
      width: 100%; padding: 12px 14px;
      background: var(--bg-code); border: 1px solid var(--border); border-radius: 10px;
      color: var(--text-primary); font-family: 'JetBrains Mono', monospace; font-size: 12px;
      resize: vertical; outline: none; transition: border-color 0.2s;
      line-height: 1.6;
    " onfocus="this.style.borderColor='var(--accent-purple)'" onblur="this.style.borderColor='var(--border)'"></textarea>
    <div id="cookieStatus" style="margin-top: 8px; font-size: 12px; color: var(--text-muted); min-height: 18px;"></div>
  </div>

  <!-- Architecture -->
  <h2 class="section-title">🏗️ Architecture</h2>
  <div class="arch-diagram">
    <div class="arch-flow">
      <span class="arch-node app">🖥️ Whisk Desktop</span>
      <span class="arch-arrow">→</span>
      <span class="arch-node bridge">🌐 Bridge :18923</span>
      <span class="arch-arrow">←</span>
      <span class="arch-node ext">🔌 Extension</span>
      <span class="arch-arrow">→</span>
      <span class="arch-node google">🔒 grecaptcha</span>
    </div>
    <p style="color: var(--text-muted); font-size: 12px; margin-top: 14px;">
      Extension poll bridge mỗi 2s → khi có request → gọi grecaptcha trên labs.google/fx → trả token về bridge → app nhận token
    </p>
  </div>

  <!-- API Endpoints -->
  <h2 class="section-title">📡 API Endpoints</h2>

  <!-- GET /captcha/request -->
  <div class="endpoint">
    <div class="endpoint-header">
      <span class="method get">GET</span>
      <span class="endpoint-path">/captcha/request</span>
    </div>
    <p class="endpoint-desc">Extension gọi endpoint này để kiểm tra app có đang cần captcha token không.</p>
    <div class="code-block">
      <div class="code-header">
        <span class="code-label">Response</span>
        <button class="try-btn" onclick="tryEndpoint('GET', '/captcha/request', 'resp1')">▶ Try it</button>
      </div>
      <pre>{{
  <span class="key">"need_token"</span>: <span class="bool">false</span>,       <span class="comment">// true nếu cần token</span>
  <span class="key">"action"</span>: <span class="str">"VIDEO_GENERATION"</span>, <span class="comment">// reCAPTCHA action</span>
  <span class="key">"count"</span>: <span class="num">1</span>                    <span class="comment">// số token cần lấy</span>
}}</pre>
    </div>
    <div class="response-area" id="resp1">
      <div class="response-content" id="resp1-content"></div>
    </div>
  </div>

  <!-- POST /captcha/token -->
  <div class="endpoint">
    <div class="endpoint-header">
      <span class="method post">POST</span>
      <span class="endpoint-path">/captcha/token</span>
    </div>
    <p class="endpoint-desc">Extension gửi captcha token đã lấy được về cho app qua endpoint này.</p>
    <div class="code-block">
      <div class="code-header">
        <span class="code-label">Request Body</span>
        <button class="try-btn" onclick="tryPost('/captcha/token', 'resp2')">▶ Try it</button>
      </div>
      <pre>{{
  <span class="key">"tokens"</span>: [<span class="str">"03AFcWeA..."</span>],  <span class="comment">// mảng token</span>
  <span class="key">"action"</span>: <span class="str">"VIDEO_GENERATION"</span>  <span class="comment">// action đã dùng</span>
}}</pre>
    </div>
    <div class="code-block">
      <div class="code-header"><span class="code-label">Response</span></div>
      <pre>{{
  <span class="key">"ok"</span>: <span class="bool">true</span>,
  <span class="key">"received"</span>: <span class="num">1</span>
}}</pre>
    </div>
    <div class="response-area" id="resp2">
      <div class="response-content" id="resp2-content"></div>
    </div>
  </div>

  <!-- GET /captcha/status -->
  <div class="endpoint">
    <div class="endpoint-header">
      <span class="method get">GET</span>
      <span class="endpoint-path">/captcha/status</span>
    </div>
    <p class="endpoint-desc">Kiểm tra trạng thái hoạt động của bridge server.</p>
    <div class="code-block">
      <div class="code-header">
        <span class="code-label">Response</span>
        <button class="try-btn" onclick="tryEndpoint('GET', '/captcha/status', 'resp3')">▶ Try it</button>
      </div>
      <pre>{{
  <span class="key">"running"</span>: <span class="bool">true</span>,
  <span class="key">"has_pending"</span>: <span class="bool">false</span>,
  <span class="key">"tokens_received"</span>: <span class="num">0</span>
}}</pre>
    </div>
    <div class="response-area" id="resp3">
      <div class="response-content" id="resp3-content"></div>
    </div>
  </div>

  <!-- GET /bridge/cookie -->
  <div class="endpoint">
    <div class="endpoint-header">
      <span class="method get">GET</span>
      <span class="endpoint-path">/bridge/cookie</span>
    </div>
    <p class="endpoint-desc">Lấy cookie đã lưu từ extension (session-token).</p>
    <div class="code-block">
      <div class="code-header">
        <span class="code-label">Response</span>
        <button class="try-btn" onclick="tryEndpoint('GET', '/bridge/cookie', 'resp4')">▶ Try it</button>
      </div>
      <pre>{{
  <span class="key">"cookie"</span>: <span class="str">"eyJhbGci..."</span>,    <span class="comment">// session token value</span>
  <span class="key">"has_cookie"</span>: <span class="bool">true</span>           <span class="comment">// có cookie hay không</span>
}}</pre>
    </div>
    <div class="response-area" id="resp4">
      <div class="response-content" id="resp4-content"></div>
    </div>
  </div>

  <!-- POST /bridge/cookie -->
  <div class="endpoint">
    <div class="endpoint-header">
      <span class="method post">POST</span>
      <span class="endpoint-path">/bridge/cookie</span>
    </div>
    <p class="endpoint-desc">Lưu cookie vào bridge (gọi bởi extension hoặc dashboard).</p>
    <div class="code-block">
      <div class="code-header">
        <span class="code-label">Request Body</span>
      </div>
      <pre>{{
  <span class="key">"cookie"</span>: <span class="str">"__Secure-next-auth.session-token value"</span>
}}</pre>
    </div>
    <div class="code-block">
      <div class="code-header"><span class="code-label">Response</span></div>
      <pre>{{
  <span class="key">"ok"</span>: <span class="bool">true</span>,
  <span class="key">"saved"</span>: <span class="num">1079</span>   <span class="comment">// số ký tự đã lưu</span>
}}</pre>
    </div>
  </div>

  <!-- Setup Guide -->
  <h2 class="section-title">🚀 Hướng dẫn cài đặt</h2>
  <div class="steps">
    <div class="step">
      <div class="step-num">1</div>
      <div class="step-content">
        <h3>Bật Extension Mode</h3>
        <p>Trong Whisk Desktop, click nút <strong>🔐</strong> trên header → chọn <strong>🔌 Extension</strong>. Server này sẽ tự động chạy.</p>
      </div>
    </div>
    <div class="step">
      <div class="step-num">2</div>
      <div class="step-content">
        <h3>Cài Chrome Extension</h3>
        <p>Mở <code>chrome://extensions</code> → bật <strong>Developer mode</strong> → click <strong>Load unpacked</strong> → chọn thư mục <code>excaptcha/</code></p>
      </div>
    </div>
    <div class="step">
      <div class="step-num">3</div>
      <div class="step-content">
        <h3>Mở trang Google Flow</h3>
        <p>Mở tab <code>labs.google/fx</code> trong Chrome. Extension sẽ tự kích hoạt và bắt đầu poll server này.</p>
      </div>
    </div>
    <div class="step">
      <div class="step-num">4</div>
      <div class="step-content">
        <h3>Kiểm tra kết nối</h3>
        <p>Click icon extension trên toolbar → nếu thấy <strong>🟢 Connected</strong> là OK. Bấm <strong>🧪 Test</strong> để thử lấy token.</p>
      </div>
    </div>
  </div>

  <div class="footer">
    Whisk Captcha Bridge v1.0 · Port {bridge.port} · Python {__import__('sys').version.split()[0]}
  </div>
</div>

<script>
  async function tryEndpoint(method, path, areaId) {{
    const area = document.getElementById(areaId);
    const content = document.getElementById(areaId + '-content');
    area.classList.add('visible');
    content.className = 'response-content';
    content.textContent = 'Loading...';
    try {{
      const resp = await fetch(path);
      const data = await resp.json();
      content.textContent = JSON.stringify(data, null, 2);
      content.className = 'response-content';
    }} catch (e) {{
      content.textContent = 'Error: ' + e.message;
      content.className = 'response-content error';
    }}
  }}

  async function tryPost(path, areaId) {{
    const area = document.getElementById(areaId);
    const content = document.getElementById(areaId + '-content');
    area.classList.add('visible');
    content.className = 'response-content';
    content.textContent = 'Sending test token...';
    try {{
      const resp = await fetch(path, {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{
          tokens: ['TEST_TOKEN_' + Date.now()],
          action: 'VIDEO_GENERATION'
        }})
      }});
      const data = await resp.json();
      content.textContent = JSON.stringify(data, null, 2);
      content.className = 'response-content';
    }} catch (e) {{
      content.textContent = 'Error: ' + e.message;
      content.className = 'response-content error';
    }}
  }}

  // ── Cookie Manager ──
  async function getCookie() {{
    const area = document.getElementById('cookieArea');
    const status = document.getElementById('cookieStatus');
    try {{
      const resp = await fetch('/bridge/cookie');
      const data = await resp.json();
      if (data.cookie) {{
        area.value = data.cookie;
        showStatus(status, '✅ Cookie loaded (' + data.cookie.length + ' chars)', 'var(--accent-green)');
      }} else {{
        showStatus(status, '⚠️ No cookie stored', 'var(--accent-amber)');
      }}
    }} catch (e) {{
      showStatus(status, '❌ Error: ' + e.message, 'var(--accent-red)');
    }}
  }}

  async function saveCookie() {{
    const area = document.getElementById('cookieArea');
    const status = document.getElementById('cookieStatus');
    const cookie = area.value.trim();
    if (!cookie) {{
      showStatus(status, '⚠️ Textarea is empty', 'var(--accent-amber)');
      return;
    }}
    try {{
      const resp = await fetch('/bridge/cookie', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ cookie }}),
      }});
      const data = await resp.json();
      if (data.ok) {{
        showStatus(status, '✅ Cookie saved (' + data.saved + ' chars)', 'var(--accent-green)');
      }} else {{
        showStatus(status, '❌ ' + (data.error || 'Save failed'), 'var(--accent-red)');
      }}
    }} catch (e) {{
      showStatus(status, '❌ Error: ' + e.message, 'var(--accent-red)');
    }}
  }}

  async function copyCookie() {{
    const area = document.getElementById('cookieArea');
    const status = document.getElementById('cookieStatus');
    if (!area.value) {{
      showStatus(status, '⚠️ Nothing to copy', 'var(--accent-amber)');
      return;
    }}
    try {{
      await navigator.clipboard.writeText(area.value);
      showStatus(status, '📋 Copied to clipboard!', 'var(--accent-green)');
    }} catch (e) {{
      area.select();
      document.execCommand('copy');
      showStatus(status, '📋 Copied!', 'var(--accent-green)');
    }}
  }}

  async function clearCookie() {{
    const area = document.getElementById('cookieArea');
    const status = document.getElementById('cookieStatus');
    area.value = '';
    try {{
      await fetch('/bridge/cookie', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ cookie: '' }}),
      }});
      showStatus(status, '🗑️ Cookie cleared', 'var(--accent-amber)');
    }} catch (e) {{
      showStatus(status, '❌ Error: ' + e.message, 'var(--accent-red)');
    }}
  }}

  function showStatus(el, msg, color) {{
    el.textContent = msg;
    el.style.color = color;
    clearTimeout(el._timer);
    el._timer = setTimeout(() => {{ el.textContent = ''; }}, 4000);
  }}
</script>

</body>
</html>'''

    def do_POST(self):
        if self.path == "/captcha/token":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                data = json.loads(body.decode("utf-8"))

                tokens = data.get("tokens", [])
                action = data.get("action", "VIDEO_GENERATION")

                if tokens:
                    bridge = self.server.bridge
                    bridge.total_tokens_received += len(tokens)
                    bridge._last_token = tokens[0]  # Display only
                    for t in tokens:
                        bridge._token_queue.put(t)  # Each worker gets unique token
                    bridge.pending_request = None  # Clear request
                    bridge.token_received.emit(tokens, action)
                    logger.info(f"🔐 Received {len(tokens)} captcha token(s) from extension")
                    self._send_json(200, {
                        "ok": True,
                        "received": len(tokens),
                    })
                else:
                    self._send_json(400, {"error": "No tokens provided"})

            except (json.JSONDecodeError, ValueError) as e:
                self._send_json(400, {"error": f"Invalid JSON: {e}"})

        elif self.path == "/bridge/login":
            self._handle_bridge_login()

        elif self.path == "/bridge/cookie":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                raw_body = self.rfile.read(content_length)
                data = json.loads(raw_body.decode("utf-8"))
                cookie_val = data.get("cookie", "")
                bridge = self.server.bridge
                bridge._stored_cookie = cookie_val
                logger.debug(f"🍪 Cookie {'saved' if cookie_val else 'cleared'} ({len(cookie_val)} chars)")
                self._send_json(200, {"ok": True, "saved": len(cookie_val)})
            except Exception as e:
                self._send_json(400, {"error": str(e)})

        else:
            self._send_json(404, {"error": "Not found"})

    def _handle_bridge_login(self):
        """Proxy login to tools.1nutnhan.com/auth/login and check admin role."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length)
            creds = json.loads(raw_body.decode("utf-8"))

            mail = creds.get("mail", "")
            password = creds.get("password", "")
            if not mail or not password:
                self._send_json(400, {"error": "Email and password are required"})
                return

            # Forward to auth API
            login_url = "https://tools.1nutnhan.com/auth/login"
            payload = json.dumps({"mail": mail, "password": password}).encode("utf-8")
            req = urllib.request.Request(
                login_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))

            user_data = resp_data.get("data", {})
            roles = user_data.get("roles", "")
            tools_access = user_data.get("tools_access", {})

            if roles != "admin" and not tools_access.get("WHISK", False):
                logger.warning(f"🔐 Login denied: {mail} (roles={roles})")
                self._send_json(403, {
                    "error": "Bạn không có quyền truy cập. Chỉ admin được phép.",
                    "roles": roles,
                })
                return

            logger.info(f"🔐 Bridge login OK: {mail} (roles={roles})")
            self._send_json(200, {
                "ok": True,
                "access_token": resp_data.get("access_token", ""),
                "user": {
                    "name": user_data.get("name", ""),
                    "mail": user_data.get("mail", ""),
                    "roles": roles,
                    "username": user_data.get("username", ""),
                },
            })

        except urllib.error.HTTPError as e:
            try:
                err_body = json.loads(e.read().decode("utf-8"))
                msg = err_body.get("message", f"HTTP {e.code}")
            except Exception:
                msg = f"HTTP {e.code}"
            self._send_json(e.code, {"error": msg})
        except urllib.error.URLError as e:
            self._send_json(502, {"error": f"Cannot connect to auth server: {e.reason}"})
        except Exception as e:
            self._send_json(500, {"error": str(e)})


class CaptchaBridgeServer(QThread):
    """
    Runs the captcha bridge HTTP server in a background thread.

    Signals:
        token_received(list, str) — emitted when tokens arrive from extension
        server_started(int)       — emitted with port when server starts
        server_error(str)         — emitted if server fails to start
    """

    token_received = Signal(list, str)   # (tokens, action)
    server_started = Signal(int)          # port
    server_error = Signal(str)            # error message

    def __init__(self, port=BRIDGE_PORT, parent=None):
        super().__init__(parent)
        self.port = port
        self.project_name = ''       # Active project name
        self.pending_request = None
        self.total_tokens_received = 0
        self._last_token = ''  # Last received token (display only)
        self._token_queue = queue.Queue()  # Thread-safe token queue
        self._stored_cookie = ''  # Cookie stored via dashboard
        self._httpd = None
        self._stop_event = threading.Event()

    def set_project_name(self, name: str):
        """Update the active project name shown in dashboard and extension."""
        self.project_name = name or ''
        logger.debug(f"📌 Bridge project: {self.project_name or '(none)'}")

    def request_token(self, action="VIDEO_GENERATION", count=1):
        """
        Set a pending captcha request for the extension to pick up.

        Args:
            action: reCAPTCHA action string
            count: number of tokens to request
        """
        self.pending_request = {
            "action": action,
            "count": count,
        }
        logger.info(f"🔐 Captcha request queued: action={action}, count={count}")

    def clear_request(self):
        """Clear any pending captcha request."""
        self.pending_request = None

    def run(self):
        """Start the HTTP server."""
        try:
            self._httpd = HTTPServer(("127.0.0.1", self.port), CaptchaBridgeHandler)
            self._httpd.bridge = self   # Give handler access to bridge state
            self._httpd.timeout = 1.0   # Check stop_event every 1s

            logger.info(f"🔐 Captcha bridge server started on http://localhost:{self.port}")
            self.server_started.emit(self.port)

            while not self._stop_event.is_set():
                self._httpd.handle_request()

        except OSError as e:
            error_msg = f"Failed to start captcha bridge: {e}"
            logger.error(f"🔐 ❌ {error_msg}")
            self.server_error.emit(error_msg)

        finally:
            if self._httpd:
                self._httpd.server_close()
            logger.info("🔐 Captcha bridge server stopped")

    def stop(self):
        """Stop the HTTP server gracefully."""
        self._stop_event.set()
        self.quit()
        self.wait(3000)  # Wait up to 3s for cleanup
