#!/bin/bash
# Build script for CRT Mixer desktop app

set -e  # Exit on error

echo "🎨 CRT Mixer Build Script"
echo "=========================="
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated!"
    echo "Please run: source venv/bin/activate"
    exit 1
fi

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist
rm -rf "dist/CRT Mixer.app"

# Build the app
echo "🔨 Building macOS app bundle..."
pyinstaller CRT_Mixer.spec

# Check if build succeeded
if [ -d "dist/CRT Mixer.app" ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    echo "📍 Your app is located at: dist/CRT Mixer.app"
    echo ""
    echo "To run the app:"
    echo "  open \"dist/CRT Mixer.app\""
    echo ""
    echo "To create a DMG for distribution:"
    echo "  ./create_dmg.sh"
else
    echo ""
    echo "❌ Build failed!"
    exit 1
fi
