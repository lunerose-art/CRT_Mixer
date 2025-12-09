# CRT Mixer - Build & Distribution Guide

This guide explains how to package CRT Mixer as a standalone desktop application for distribution.

## Prerequisites

- **macOS** (for building macOS apps)
- **Python 3.9+** with virtual environment
- All project dependencies installed

## Quick Start

### 1. Install Dependencies

```bash
# Activate your virtual environment
source venv/bin/activate

# Install all dependencies including PyInstaller
pip install -r requirements.txt
```

### 2. Build the macOS App

```bash
# Run the build script
./build.sh
```

This will:
- Install/update all dependencies
- Clean previous builds
- Create a standalone `.app` bundle in `dist/CRT Mixer.app`

### 3. Test the App

```bash
# Run the built app
open "dist/CRT Mixer.app"
```

### 4. Create DMG for Distribution

```bash
# Create a distributable DMG file
./create_dmg.sh
```

This creates `dist/CRT_Mixer_macOS.dmg` ready to share with users.

## Manual Build Process

If you prefer to build manually without the scripts:

```bash
# Activate virtual environment
source venv/bin/activate

# Install PyInstaller
pip install pyinstaller

# Build using the spec file
pyinstaller CRT_Mixer.spec

# The app will be in dist/CRT Mixer.app
```

## Build Configuration

### PyInstaller Spec File (`CRT_Mixer.spec`)

The spec file controls how the app is packaged:

- **Entry point**: `CRT_Mixer.py`
- **Hidden imports**: PyQt5, Pillow, NumPy, SciPy modules
- **Console**: Disabled (no terminal window)
- **Bundle**: macOS `.app` format
- **Bundle ID**: `com.lune.crtmixer`

### Customization Options

#### Add an App Icon

1. Create or obtain a `.icns` file (macOS icon format)
2. Place it in the project directory (e.g., `icon.icns`)
3. Edit `CRT_Mixer.spec` and change:
   ```python
   icon=None,  # Change to:
   icon='icon.icns',
   ```

#### Modify App Metadata

Edit the `info_plist` section in `CRT_Mixer.spec`:

```python
info_plist={
    'CFBundleName': 'CRT Mixer',
    'CFBundleDisplayName': 'CRT Mixer',
    'CFBundleVersion': '1.0.0',
    'CFBundleShortVersionString': '1.0.0',
    # ... other settings
}
```

## Distribution

### For macOS Users

**Option 1: DMG Installer (Recommended)**
- Run `./create_dmg.sh`
- Share `dist/CRT_Mixer_macOS.dmg`
- Users drag the app to Applications folder

**Option 2: Direct App Bundle**
- Share `dist/CRT Mixer.app` (compress as ZIP)
- Users extract and move to Applications

### Important Notes for Users

⚠️ **macOS Gatekeeper Warning**: Since the app is not signed with an Apple Developer Certificate, users will need to:

1. Right-click the app
2. Select "Open"
3. Click "Open" in the security dialog

This only needs to be done once.

### Code Signing (Optional but Recommended)

To avoid Gatekeeper warnings, sign the app with an Apple Developer certificate:

```bash
# Sign the app (requires Apple Developer account)
codesign --deep --force --sign "Developer ID Application: Your Name" "dist/CRT Mixer.app"

# Verify signature
codesign --verify --verbose "dist/CRT Mixer.app"

# Notarize with Apple (optional, for best user experience)
xcrun notarytool submit "dist/CRT_Mixer_macOS.dmg" \
    --apple-id "your@email.com" \
    --password "app-specific-password" \
    --team-id "TEAM_ID"
```

## Windows Distribution

To build for Windows, you'll need a Windows machine (or VM):

```bash
# On Windows with Python installed
pip install -r requirements.txt

# Build Windows executable
pyinstaller CRT_Mixer.spec

# Creates dist/CRT_Mixer.exe
```

**Note**: You may need to adjust the spec file for Windows-specific settings.

## Linux Distribution

On Linux:

```bash
# Install dependencies
pip install -r requirements.txt

# Build
pyinstaller CRT_Mixer.spec

# Creates dist/CRT_Mixer
```

Users may need to install system dependencies:
```bash
# Ubuntu/Debian
sudo apt-get install python3-pyqt5

# Fedora
sudo dnf install python3-qt5
```

## Troubleshooting

### Build Fails with Missing Modules

Add missing imports to the `hiddenimports` list in `CRT_Mixer.spec`:

```python
hiddenimports=[
    'your.missing.module',
    # ... other imports
],
```

### App Crashes on Launch

1. Test by running with console enabled:
   ```python
   # In CRT_Mixer.spec, change:
   console=True,  # Shows error messages
   ```

2. Rebuild and check error output

### Large App Size

The app bundle includes Python and all dependencies. Typical size: 150-300 MB.

To reduce size:
- Remove unused dependencies from `requirements.txt`
- Use UPX compression (already enabled in spec file)
- Exclude unnecessary files in the spec file

### Different Python Versions

The app is built with the Python version in your virtual environment. Ensure compatibility:

```bash
# Check Python version
python --version

# Use Python 3.9+ for best compatibility
```

## File Structure After Build

```
CRT/
├── build/              # Temporary build files (can be deleted)
├── dist/               # Distribution files
│   ├── CRT Mixer.app/  # macOS app bundle
│   └── CRT_Mixer_macOS.dmg  # DMG installer
├── CRT_Mixer.spec      # PyInstaller configuration
├── build.sh            # Build script
└── create_dmg.sh       # DMG creation script
```

## Best Practices

1. **Test thoroughly** before distribution
2. **Version your builds** - update version numbers in spec file
3. **Document requirements** - what macOS versions are supported
4. **Create release notes** - list features and known issues
5. **Consider code signing** - improves user trust

## Creating an Icon (macOS)

If you want a custom icon:

```bash
# 1. Create a 1024x1024 PNG image (icon.png)

# 2. Create iconset directory
mkdir icon.iconset

# 3. Generate all required sizes
sips -z 16 16     icon.png --out icon.iconset/icon_16x16.png
sips -z 32 32     icon.png --out icon.iconset/icon_16x16@2x.png
sips -z 32 32     icon.png --out icon.iconset/icon_32x32.png
sips -z 64 64     icon.png --out icon.iconset/icon_32x32@2x.png
sips -z 128 128   icon.png --out icon.iconset/icon_128x128.png
sips -z 256 256   icon.png --out icon.iconset/icon_128x128@2x.png
sips -z 256 256   icon.png --out icon.iconset/icon_256x256.png
sips -z 512 512   icon.png --out icon.iconset/icon_256x256@2x.png
sips -z 512 512   icon.png --out icon.iconset/icon_512x512.png
sips -z 1024 1024 icon.png --out icon.iconset/icon_512x512@2x.png

# 4. Convert to .icns
iconutil -c icns icon.iconset

# 5. Clean up
rm -rf icon.iconset

# Now you have icon.icns to use in the spec file
```

## Support & Resources

- **PyInstaller Docs**: https://pyinstaller.org/en/stable/
- **PyQt5 Deployment**: https://www.riverbankcomputing.com/static/Docs/PyQt5/
- **macOS App Bundle**: https://developer.apple.com/library/archive/documentation/CoreFoundation/Conceptual/CFBundles/

## Changelog

- **v1.0.0**: Initial build configuration
  - macOS app bundle support
  - DMG creation
  - Automated build scripts
