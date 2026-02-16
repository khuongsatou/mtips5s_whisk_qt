#!/bin/bash
# ============================================================
# Quick build: Windows .exe via Docker
# Usage: ./scripts/build_win_docker.sh
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🔨 Building WhiskDesktop.exe for Windows via Docker..."
echo "======================================================="
echo ""

# Check Docker
if ! docker info &>/dev/null; then
    echo "❌ Docker không chạy! Hãy mở Docker Desktop trước."
    exit 1
fi

echo "✅ Docker đang chạy"
echo ""

# Clean dist
rm -rf "$PROJECT_DIR/dist/WhiskDesktop" 2>/dev/null

# Build
cd "$PROJECT_DIR"
docker compose -f scripts/docker-compose.build.yml up --build --abort-on-container-exit

echo ""
if [ -f "dist/WhiskDesktop/WhiskDesktop.exe" ]; then
    echo "✅ Build thành công!"
    echo "📍 Output: dist/WhiskDesktop/WhiskDesktop.exe"
    echo "📦 Size: $(du -sh dist/WhiskDesktop/ | cut -f1)"
else
    echo "❌ Build thất bại — không tìm thấy WhiskDesktop.exe"
    exit 1
fi
