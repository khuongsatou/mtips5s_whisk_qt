#!/bin/bash
set -e

echo "🔨 Building WhiskDesktop.app for macOS..."
echo "==========================================="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_NAME="Whisk Desktop"
BUNDLE_ID="com.1nutnhanwhisk.desktop"
VERSION="1.0.0"

DIST_DIR="$PROJECT_DIR/dist"
APP_DIR="$DIST_DIR/$APP_NAME.app"
CONTENTS="$APP_DIR/Contents"
MACOS="$CONTENTS/MacOS"
RESOURCES="$CONTENTS/Resources"

# Check Python
PYTHON=$(which python3)
echo "Using Python: $PYTHON"
$PYTHON --version

# Run tests first
echo ""
echo "🧪 Running tests..."
$PYTHON -m pytest "$PROJECT_DIR/tests/" -v --tb=short

# Clean previous build
echo ""
echo "🧹 Cleaning previous build..."
rm -rf "$APP_DIR"

# Compile native launcher as universal binary (arm64 + x86_64)
echo ""
echo "🔧 Compiling universal native launcher (arm64 + x86_64)..."
cc -arch arm64 -arch x86_64 -o "$SCRIPT_DIR/launcher_bin" "$SCRIPT_DIR/launcher.c"
echo "   Compiled successfully"
file "$SCRIPT_DIR/launcher_bin"

# Create .app bundle structure
echo ""
echo "📦 Creating app bundle..."
mkdir -p "$MACOS" "$RESOURCES"

# --- Info.plist ---
cat > "$CONTENTS/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- Bundle Identity -->
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleDisplayName</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>$BUNDLE_ID</string>
    <key>CFBundleVersion</key>
    <string>$VERSION</string>
    <key>CFBundleShortVersionString</key>
    <string>$VERSION</string>
    <key>CFBundleExecutable</key>
    <string>WhiskDesktop</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleIconFile</key>
    <string>logo.png</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>

    <!-- Platform -->
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSArchitecturePriority</key>
    <array>
        <string>arm64</string>
        <string>x86_64</string>
    </array>

    <!-- File Access -->
    <key>NSDocumentsFolderUsageDescription</key>
    <string>Whisk Desktop cần truy cập thư mục Documents để lưu ảnh đã tạo.</string>
    <key>NSDownloadsFolderUsageDescription</key>
    <string>Whisk Desktop cần truy cập thư mục Downloads để lưu ảnh đã tạo.</string>
    <key>NSDesktopFolderUsageDescription</key>
    <string>Whisk Desktop cần truy cập Desktop để lưu ảnh xuất ra.</string>
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
    <key>com.apple.security.files.downloads.read-write</key>
    <true/>

    <!-- Photos -->
    <key>NSPhotoLibraryUsageDescription</key>
    <string>Whisk Desktop cần truy cập Thư viện Ảnh để nhập ảnh tham chiếu.</string>
    <key>NSPhotoLibraryAddUsageDescription</key>
    <string>Whisk Desktop cần quyền thêm ảnh đã tạo vào Thư viện Ảnh.</string>

    <!-- Camera & Microphone -->
    <key>NSCameraUsageDescription</key>
    <string>Whisk Desktop cần truy cập Camera để chụp ảnh tham chiếu.</string>
    <key>NSMicrophoneUsageDescription</key>
    <string>Whisk Desktop cần truy cập Microphone cho tính năng nhập giọng nói.</string>

    <!-- Network -->
    <key>NSLocalNetworkUsageDescription</key>
    <string>Whisk Desktop cần quyền mạng cục bộ để kết nối API server.</string>
    <key>com.apple.security.network.client</key>
    <true/>
    <key>com.apple.security.network.server</key>
    <true/>

    <!-- Accessibility -->
    <key>NSAccessibilityUsageDescription</key>
    <string>Whisk Desktop cần hỗ trợ trợ năng để cung cấp trải nghiệm tốt hơn.</string>

    <!-- Bluetooth -->
    <key>NSBluetoothAlwaysUsageDescription</key>
    <string>Whisk Desktop cần Bluetooth để kết nối thiết bị ngoại vi.</string>

    <!-- Contacts -->
    <key>NSContactsUsageDescription</key>
    <string>Whisk Desktop cần truy cập Danh bạ để chia sẻ ảnh.</string>

    <!-- Location -->
    <key>NSLocationUsageDescription</key>
    <string>Whisk Desktop cần vị trí để gắn thẻ metadata cho ảnh.</string>
    <key>NSLocationWhenInUseUsageDescription</key>
    <string>Whisk Desktop cần vị trí để gắn thẻ metadata cho ảnh.</string>

    <!-- Calendar & Reminders -->
    <key>NSCalendarsUsageDescription</key>
    <string>Whisk Desktop cần truy cập Lịch để lên lịch tạo ảnh tự động.</string>
    <key>NSRemindersUsageDescription</key>
    <string>Whisk Desktop cần truy cập Nhắc nhở để thông báo khi tạo ảnh xong.</string>

    <!-- Speech -->
    <key>NSSpeechRecognitionUsageDescription</key>
    <string>Whisk Desktop cần nhận dạng giọng nói để nhập prompt bằng giọng nói.</string>

    <!-- Apple Events (Automation) -->
    <key>NSAppleEventsUsageDescription</key>
    <string>Whisk Desktop cần điều khiển ứng dụng khác để tự động hóa workflow.</string>
</dict>
</plist>
PLIST

# --- Native launcher binary ---
cp "$SCRIPT_DIR/launcher_bin" "$MACOS/WhiskDesktop"
chmod +x "$MACOS/WhiskDesktop"

# --- Shell launcher script (called by native binary) ---
cat > "$MACOS/launcher.sh" << 'LAUNCHER'
#!/bin/bash

# macOS GUI apps don't inherit terminal PATH — source shell profile
if [ -f "$HOME/.zprofile" ]; then source "$HOME/.zprofile" 2>/dev/null; fi
if [ -f "$HOME/.zshrc" ]; then source "$HOME/.zshrc" 2>/dev/null; fi
if [ -f "$HOME/.bash_profile" ]; then source "$HOME/.bash_profile" 2>/dev/null; fi

# Ensure common Python locations are in PATH
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:$PATH"

# Find python3
PYTHON=""
for p in /usr/local/bin/python3 /opt/homebrew/bin/python3 /usr/bin/python3 python3; do
    if command -v "$p" &>/dev/null; then
        PYTHON="$p"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    osascript -e 'display alert "Python 3 không tìm thấy" message "Vui lòng cài đặt Python 3 từ python.org hoặc Homebrew." as critical'
    exit 1
fi

# Set up environment
DIR="$(cd "$(dirname "$0")/../Resources" && pwd)"
export PYTHONPATH="$DIR/app_bundle"
export WHISK_RESOURCE_DIR="$DIR"

# Launch app
cd "$DIR/app_bundle"
exec "$PYTHON" main.py "$@"
LAUNCHER
chmod +x "$MACOS/launcher.sh"

# --- Copy app code ---
APP_BUNDLE="$RESOURCES/app_bundle"
mkdir -p "$APP_BUNDLE"

# Copy Python source files
cp "$PROJECT_DIR/main.py" "$APP_BUNDLE/"
cp -R "$PROJECT_DIR/app" "$APP_BUNDLE/"

# Remove __pycache__ directories
find "$APP_BUNDLE" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# --- Copy resources ---
cp "$PROJECT_DIR/app/assets/logo.png" "$RESOURCES/logo.png"

# Copy theme files
mkdir -p "$RESOURCES/app/theme/icons" "$RESOURCES/app/i18n" "$RESOURCES/app/assets"
cp "$PROJECT_DIR/app/theme/"*.qss "$RESOURCES/app/theme/"
cp "$PROJECT_DIR/app/theme/icons/"*.svg "$RESOURCES/app/theme/icons/"
cp "$PROJECT_DIR/app/i18n/"*.json "$RESOURCES/app/i18n/"
cp "$PROJECT_DIR/app/assets/"* "$RESOURCES/app/assets/" 2>/dev/null || true

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
echo "✅ Build complete!"
echo "📍 App:  $APP_DIR ($(du -sh "$APP_DIR" | cut -f1))"
echo "💿 DMG:  $DIST_DIR/WhiskDesktop.dmg ($(du -sh "$DIST_DIR/WhiskDesktop.dmg" | cut -f1))"
echo ""
echo "To install: open dist/WhiskDesktop.dmg → drag to Applications"
echo "To run:     open 'dist/$APP_NAME.app'"
