#!/bin/bash
# ============================================================
# Whisk Desktop — Build Windows .exe on remote VPS
# Uses Docker (tobix/pywine:3.11) + PyInstaller on remote server
#
# Usage: ./scripts/build_win_remote.sh
#
# Requirements (local):  sshpass, rsync
# Requirements (remote): Docker 26+
# ============================================================
set -e

# ---- Config ----
REMOTE_HOST="45.32.63.217"
REMOTE_USER="root"
REMOTE_PASS='m[Z3T(r%ghDWpk.q'
REMOTE_DIR="/root/whisk_build"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST_DIR="$PROJECT_DIR/dist"

SSH_OPTS="-o StrictHostKeyChecking=no -o ServerAliveInterval=15 -o ServerAliveCountMax=30"

echo "🔨 Building WhiskDesktop.exe on remote server ($REMOTE_HOST)..."
echo "================================================================="

# ---- Check sshpass ----
if ! command -v sshpass &>/dev/null; then
    echo "❌ sshpass chưa được cài! Chạy: brew install esolitos/ipa/sshpass"
    exit 1
fi

# Helper
run_ssh() {
    sshpass -p "$REMOTE_PASS" ssh $SSH_OPTS "$REMOTE_USER@$REMOTE_HOST" "$@"
}

run_rsync() {
    sshpass -p "$REMOTE_PASS" rsync -avz -e "ssh $SSH_OPTS" "$@"
}

# ---- Step 1: Upload project ----
echo ""
echo "📤 [1/4] Uploading project..."

run_rsync --delete \
    --exclude='.venv/' --exclude='venv/' --exclude='__pycache__/' \
    --exclude='.pytest_cache/' --exclude='dist/' --exclude='build/' \
    --exclude='.git/' --exclude='.gemini/' --exclude='.agent/' \
    --exclude='node_modules/' --exclude='.DS_Store' --exclude='*.pyc' \
    "$PROJECT_DIR/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

echo "✅ Upload hoàn tất"

# ---- Step 2: Ensure Docker is running ----
echo ""
echo "🐳 [2/4] Starting Docker..."
run_ssh "systemctl start docker 2>/dev/null; echo 3 > /proc/sys/vm/drop_caches; echo 'Docker OK'"

# ---- Step 3: Build with Docker ----
echo ""
echo "🔧 [3/4] Building .exe via Docker + PyInstaller..."
echo "   (Lần đầu sẽ mất 10-15 phút, các lần sau nhanh hơn)"
echo ""

run_ssh << 'REMOTE_BUILD'
set -e
cd /root/whisk_build
rm -rf dist/WhiskDesktop 2>/dev/null || true

DOCKER_BUILDKIT=0 docker compose -f scripts/docker-compose.pyinstaller.yml up --build --abort-on-container-exit 2>&1

echo ""
if [ -d "dist/WhiskDesktop" ] && [ -f "dist/WhiskDesktop/WhiskDesktop.exe" ]; then
    echo "✅ Build thành công!"
    echo "📦 Files: $(find dist/WhiskDesktop -type f | wc -l)"
    echo "📦 Size: $(du -sh dist/WhiskDesktop | cut -f1)"
else
    echo "❌ Build thất bại!"
    exit 1
fi
REMOTE_BUILD

# ---- Step 4: Download result ----
echo ""
echo "📥 [4/4] Downloading WhiskDesktop.exe..."

mkdir -p "$DIST_DIR"
run_rsync \
    "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/dist/WhiskDesktop/" \
    "$DIST_DIR/WhiskDesktop/"

echo ""
echo "================================================================="
echo "✅ Windows build hoàn tất!"
echo ""
if [ -f "$DIST_DIR/WhiskDesktop/WhiskDesktop.exe" ]; then
    echo "📍 EXE:   $DIST_DIR/WhiskDesktop/WhiskDesktop.exe"
    echo "📦 Total: $(du -sh "$DIST_DIR/WhiskDesktop" | cut -f1)"
    echo "📁 Files: $(find "$DIST_DIR/WhiskDesktop" -type f | wc -l) files"
else
    echo "⚠️  WhiskDesktop.exe không tìm thấy"
fi
echo ""
echo "Chạy trên Windows: dist\\WhiskDesktop\\WhiskDesktop.exe"
echo "================================================================="
