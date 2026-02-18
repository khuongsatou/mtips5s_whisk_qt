#!/bin/bash
# ============================================================
# Quick build: Windows .exe via Docker + Nuitka (native compilation)
# Usage: ./scripts/build_win_nuitka.sh
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🔨 Building Veo3DeskTop.exe (Nuitka native) for Windows via Docker..."
echo "======================================================================="
echo "🛡️  Nuitka compiles Python → C → native code (anti-decompile)"
echo ""

# Check Docker
if ! docker info &>/dev/null; then
    echo "❌ Docker không chạy! Hãy mở Docker Desktop trước."
    exit 1
fi

echo "✅ Docker đang chạy"
echo ""

# Clean dist
rm -rf "$PROJECT_DIR/dist/Veo3DeskTop.exe" 2>/dev/null

# Build using docker compose
cd "$PROJECT_DIR"
docker compose -f scripts/docker-compose.nuitka.yml up --build --abort-on-container-exit

echo ""
if [ -f "dist/Veo3DeskTop.exe" ]; then
    echo "✅ Nuitka build thành công!"
    echo "📍 Output: dist/Veo3DeskTop.exe"
    echo "📦 Size: $(du -sh dist/Veo3DeskTop.exe | cut -f1)"
    echo "🛡️  Code compiled to native C — cannot be decompiled!"
else
    echo "❌ Build thất bại — không tìm thấy Veo3DeskTop.exe"
    exit 1
fi
