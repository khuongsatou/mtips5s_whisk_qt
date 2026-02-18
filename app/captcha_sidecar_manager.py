"""
Whisk Desktop — Captcha Sidecar Manager (Puppeteer Mode).

Manages the Node.js capture-sidecar subprocess.
Communicates via stdin (commands) / stdout (JSON responses).

Commands sent to sidecar:
  GET_TOKENS <count>  — Request captcha tokens
  RESTART_BROWSER     — Force browser restart
  PING                — Check if sidecar is alive
  SHUTDOWN            — Graceful stop
"""
import json
import logging
import os
import shutil
import subprocess
import sys
import threading

from PySide6.QtCore import QThread, Signal

logger = logging.getLogger("whisk.captcha_sidecar")


def _find_node():
    """Find the Node.js binary path."""
    # 1. Check PATH
    node = shutil.which("node")
    if node:
        return node

    # 2. Common locations
    candidates = []
    if sys.platform == "darwin":
        candidates = [
            "/usr/local/bin/node",
            "/opt/homebrew/bin/node",
            os.path.expanduser("~/.nvm/versions/node/*/bin/node"),
        ]
    elif sys.platform == "win32":
        candidates = [
            r"C:\Program Files\nodejs\node.exe",
            r"C:\Program Files (x86)\nodejs\node.exe",
        ]
    else:
        candidates = ["/usr/bin/node", "/usr/local/bin/node"]

    for path in candidates:
        if "*" in path:
            import glob
            matches = sorted(glob.glob(path), reverse=True)
            if matches:
                return matches[0]
        elif os.path.isfile(path):
            return path

    return None


def _find_sidecar_script():
    """Find the capture-sidecar.js script."""
    # Try relative to project root
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join(base_dir, "pucaptcha", "capture-sidecar.js"),
        os.path.join(base_dir, "captcha", "capture-sidecar.js"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


class CaptchaSidecarManager(QThread):
    """
    Manages the Puppeteer captcha sidecar subprocess.

    Signals:
        token_received(list, str) — tokens and action
        sidecar_ready()           — sidecar is initialized and ready
        sidecar_error(str)        — error message from sidecar
        sidecar_stopped()         — sidecar process has ended
    """

    token_received = Signal(list, str)
    sidecar_ready = Signal()
    sidecar_error = Signal(str)
    sidecar_stopped = Signal()

    def __init__(self, proxy_url=None, action="VIDEO_GENERATION", parent=None):
        super().__init__(parent)
        self.proxy_url = proxy_url
        self.action = action
        self._process = None
        self._stop_event = threading.Event()
        self._stdin_lock = threading.Lock()
        self._pending_action = "VIDEO_GENERATION"

    def run(self):
        """Start the sidecar subprocess and read its stdout."""
        node_path = _find_node()
        if not node_path:
            self.sidecar_error.emit(
                "Node.js not found. Install Node.js to use Puppeteer mode."
            )
            self.sidecar_stopped.emit()
            return

        script_path = _find_sidecar_script()
        if not script_path:
            self.sidecar_error.emit(
                "capture-sidecar.js not found in pucaptcha/ or captcha/"
            )
            self.sidecar_stopped.emit()
            return

        # Build command
        cmd = [node_path, script_path]
        if self.action and self.action != "VIDEO_GENERATION":
            cmd.extend(["--type", self.action])
        if self.proxy_url:
            cmd.append(self.proxy_url)

        logger.info(f"🔐 Starting sidecar: {' '.join(cmd)}")

        try:
            self._process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line-buffered
                cwd=os.path.dirname(script_path),
            )

            # Start stderr reader thread (for debug logs)
            stderr_thread = threading.Thread(
                target=self._read_stderr, daemon=True
            )
            stderr_thread.start()

            # Read stdout line by line (JSON responses)
            while not self._stop_event.is_set():
                if self._process.poll() is not None:
                    logger.warning("🔐 Sidecar process exited unexpectedly")
                    break

                line = self._process.stdout.readline()
                if not line:
                    break

                line = line.strip()
                if not line:
                    continue

                self._handle_stdout_line(line)

        except FileNotFoundError as e:
            self.sidecar_error.emit(f"Failed to start sidecar: {e}")
        except Exception as e:
            self.sidecar_error.emit(f"Sidecar error: {e}")
        finally:
            self._cleanup()
            self.sidecar_stopped.emit()
            logger.info("🔐 Sidecar manager stopped")

    def _read_stderr(self):
        """Read stderr from sidecar (debug/info logs)."""
        if not self._process or not self._process.stderr:
            return
        try:
            for line in self._process.stderr:
                line = line.strip()
                if line:
                    logger.debug(f"[PPT] {line}")
        except (ValueError, OSError):
            pass  # Process closed

    def _handle_stdout_line(self, line: str):
        """Parse a JSON line from sidecar stdout."""
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            logger.warning(f"🔐 Non-JSON from sidecar: {line}")
            return

        success = data.get("success", False)
        message = data.get("message", "")
        tokens = data.get("tokens", [])
        error = data.get("error", "")

        # READY signal
        if success and message == "READY":
            logger.info("🔐 Sidecar is READY")
            self.sidecar_ready.emit()
            return

        # INIT_FAILED
        if message == "INIT_FAILED":
            error_msg = error or "Sidecar initialization failed"
            hint = data.get("errorHint", "")
            if hint:
                error_msg = f"{error_msg} — {hint}"
            logger.error(f"🔐 Sidecar INIT_FAILED: {error_msg}")
            self.sidecar_error.emit(error_msg)
            return

        # Tokens received
        if success and tokens:
            logger.info(f"🔐 Got {len(tokens)} token(s) from sidecar")
            self.token_received.emit(tokens, self._pending_action)
            return

        # Error response
        if not success and error:
            error_type = data.get("errorType", "")
            hint = data.get("errorHint", "")
            is_fatal = data.get("isFatal", False)
            full_msg = error
            if hint:
                full_msg = f"{error} — {hint}"
            logger.error(f"🔐 Sidecar error [{error_type}]: {full_msg}")
            self.sidecar_error.emit(full_msg)
            if is_fatal:
                logger.error("🔐 Fatal sidecar error, stopping")
                self._stop_event.set()
            return

        # Other messages (PING response, restart confirmation, etc.)
        if message:
            logger.info(f"🔐 Sidecar: {message}")

    def _send_command(self, command: str):
        """Send a command to the sidecar via stdin."""
        if not self._process or self._process.poll() is not None:
            logger.warning("🔐 Cannot send command: sidecar not running")
            return False

        with self._stdin_lock:
            try:
                self._process.stdin.write(command + "\n")
                self._process.stdin.flush()
                logger.debug(f"🔐 Sent command: {command}")
                return True
            except (BrokenPipeError, OSError) as e:
                logger.error(f"🔐 Failed to send command: {e}")
                return False

    def request_tokens(self, count=1, action="VIDEO_GENERATION"):
        """Request captcha tokens from the sidecar."""
        self._pending_action = action
        return self._send_command(f"GET_TOKENS {count}")

    def restart_browser(self):
        """Request the sidecar to restart its browser."""
        return self._send_command("RESTART_BROWSER")

    def ping(self):
        """Ping the sidecar to check if it's alive."""
        return self._send_command("PING")

    def _cleanup(self):
        """Clean up the subprocess."""
        if self._process:
            try:
                # Try graceful shutdown first
                with self._stdin_lock:
                    try:
                        self._process.stdin.write("SHUTDOWN\n")
                        self._process.stdin.flush()
                    except (BrokenPipeError, OSError):
                        pass

                # Wait up to 5 seconds for graceful exit
                try:
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("🔐 Sidecar didn't exit gracefully, killing")
                    self._process.kill()
                    self._process.wait(timeout=3)

            except Exception as e:
                logger.error(f"🔐 Cleanup error: {e}")
                try:
                    self._process.kill()
                except Exception:
                    pass
            finally:
                self._process = None

    def stop(self):
        """Stop the sidecar gracefully."""
        logger.info("🔐 Stopping sidecar...")
        self._stop_event.set()
        self._cleanup()
        self.quit()
        self.wait(5000)

    @property
    def is_running(self):
        """Check if the sidecar process is running."""
        return self._process is not None and self._process.poll() is None
