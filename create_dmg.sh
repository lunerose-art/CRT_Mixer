#!/bin/bash
# Create DMG installer for CRT Mixer

set -e

echo "📦 Creating DMG Installer"
echo "========================="
echo ""

# Check if app exists
if [ ! -d "dist/CRT Mixer.app" ]; then
    echo "❌ Error: dist/CRT Mixer.app not found!"
    echo "Please run ./build.sh first"
    exit 1
fi

# Create temporary DMG directory
DMG_DIR="dmg_temp"
DMG_NAME="CRT_Mixer_macOS"
APP_NAME="CRT Mixer.app"

echo "🗂️  Preparing DMG contents..."
rm -rf "$DMG_DIR"
mkdir -p "$DMG_DIR"

# Copy app to DMG directory
cp -R "dist/$APP_NAME" "$DMG_DIR/"

# Create Applications symlink
ln -s /Applications "$DMG_DIR/Applications"

# Create README
cat > "$DMG_DIR/README.txt" << 'EOF'
CRT Mixer - Glitch Art & CRT Effects Tool
==========================================

INSTALLATION:
1. Drag "CRT Mixer.app" to the Applications folder
2. Right-click the app and select "Open" on first launch
   (macOS Gatekeeper may block unsigned apps)

USAGE:
1. Launch CRT Mixer
2. Click "Select Input File" to load an image
3. Adjust effect parameters using the sliders
4. Click "Preview" to see the result
5. Click "Save As..." to export your creation

EFFECTS:
- Pixel Sorting (brightness, color channels, hue)
- CRT Monitor Effects (scanlines, phosphor glow, curvature)
- RGB Distortion (channel shifting, chromatic aberration)
- Signal Distortion (VHS effects)

For issues and updates, visit: github.com/[your-username]/CRT

Enjoy creating glitch art! 🎨
EOF

echo "💿 Creating DMG file..."
# Remove old DMG if exists
rm -f "dist/$DMG_NAME.dmg"

# Create DMG using hdiutil (built into macOS)
hdiutil create -volname "CRT Mixer" \
    -srcfolder "$DMG_DIR" \
    -ov -format UDZO \
    "dist/$DMG_NAME.dmg"

# Clean up
rm -rf "$DMG_DIR"

if [ -f "dist/$DMG_NAME.dmg" ]; then
    echo ""
    echo "✅ DMG created successfully!"
    echo ""
    echo "📍 Location: dist/$DMG_NAME.dmg"

    # Get file size
    SIZE=$(du -h "dist/$DMG_NAME.dmg" | cut -f1)
    echo "📊 Size: $SIZE"
    echo ""
    echo "You can now distribute this DMG file to users!"
else
    echo "❌ DMG creation failed!"
    exit 1
fi
