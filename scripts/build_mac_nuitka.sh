#!/bin/bash
set -e

echo "🔨 Building WhiskDesktop.app with Nuitka (native compilation)..."
echo "================================================================="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_NAME="Whisk Desktop"
BUNDLE_ID="com.1nutnhanwhisk.desktop"
VERSION="1.0.0"

DIST_DIR="$PROJECT_DIR/dist"
APP_DIR="$DIST_DIR/$APP_NAME.app"

# Check Python
PYTHON=$(which python3)
echo "Using Python: $PYTHON"
$PYTHON --version

# Check Nuitka
echo ""
echo "🔍 Checking Nuitka..."
$PYTHON -m nuitka --version

# Run tests first
echo ""
echo "🧪 Running tests..."
$PYTHON -m pytest "$PROJECT_DIR/tests/" -q --tb=short

# Clean previous build
echo ""
echo "🧹 Cleaning previous build..."
rm -rf "$DIST_DIR/main.dist" "$DIST_DIR/main.build" "$APP_DIR"

# Build with Nuitka
echo ""
echo "🔧 Compiling with Nuitka (this may take several minutes)..."
cd "$PROJECT_DIR"

$PYTHON -m nuitka \
    --standalone \
    --macos-create-app-bundle \
    --macos-app-name="$APP_NAME" \
    --macos-app-icon="$PROJECT_DIR/app/assets/logo.png" \
    --macos-app-version="$VERSION" \
    --enable-plugin=pyside6 \
    --include-data-dir="$PROJECT_DIR/app/i18n=app/i18n" \
    --include-data-dir="$PROJECT_DIR/app/theme=app/theme" \
    --include-data-dir="$PROJECT_DIR/app/assets=app/assets" \
    --include-package=app \
    --output-dir="$DIST_DIR" \
    --output-filename="WhiskDesktop" \
    --remove-output \
    --assume-yes-for-downloads \
    "$PROJECT_DIR/main.py"

echo ""
echo "📦 Nuitka compilation complete!"

# Move .app to expected location if needed
if [ -d "$DIST_DIR/main.app" ]; then
    rm -rf "$APP_DIR"
    mv "$DIST_DIR/main.app" "$APP_DIR"
fi

# Update Info.plist with our bundle identifier
if [ -f "$APP_DIR/Contents/Info.plist" ]; then
    /usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier $BUNDLE_ID" "$APP_DIR/Contents/Info.plist" 2>/dev/null || true
    /usr/libexec/PlistBuddy -c "Set :NSHighResolutionCapable true" "$APP_DIR/Contents/Info.plist" 2>/dev/null || true
    echo "✅ Updated Info.plist"
fi

# --- Create DMG ---
echo ""
echo "💿 Creating DMG installer..."
DMG_STAGING="$DIST_DIR/dmg_staging"
rm -rf "$DMG_STAGING"
mkdir -p "$DMG_STAGING"
cp -R "$APP_DIR" "$DMG_STAGING/"
ln -sf /Applications "$DMG_STAGING/Applications"
hdiutil create -volname "$APP_NAME" -srcfolder "$DMG_STAGING" -ov -format UDZO "$DIST_DIR/WhiskDesktop.dmg"
rm -rf "$DMG_STAGING"

echo ""
echo "✅ Nuitka build complete!"
echo "📍 App:  $APP_DIR ($(du -sh "$APP_DIR" | cut -f1))"
echo "💿 DMG:  $DIST_DIR/WhiskDesktop.dmg ($(du -sh "$DIST_DIR/WhiskDesktop.dmg" | cut -f1))"
echo ""
echo "🛡️  All Python code compiled to native C — cannot be decompiled!"
echo ""
echo "To install: open dist/WhiskDesktop.dmg → drag to Applications"
echo "To run:     open 'dist/$APP_NAME.app'"
