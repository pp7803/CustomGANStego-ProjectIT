#!/bin/bash
# ============================================
# Build script for CustomGANStego macOS App
# Includes: Environment Check → Build → Usage Guide
# ============================================

set -e  # Exit on error

echo "🚀 CustomGANStego macOS Application Builder"
echo "=============================================="
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PRJVENV_DIR="$PROJECT_DIR/prjvenv"

# ==================== STEP 1: Environment Check ====================
echo "📋 Step 1: Checking Environment"
echo "----------------------------------------"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python: $PYTHON_VERSION"

# Check virtual environment
if [ -d "$PRJVENV_DIR" ]; then
    echo "✅ Virtual environment found"
    source "$PRJVENV_DIR/bin/activate"
else
    echo "❌ Virtual environment not found at: $PRJVENV_DIR"
    echo ""
    read -p "Create virtual environment now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Creating virtual environment..."
        cd "$PROJECT_DIR"
        python3 -m venv prjvenv
        source prjvenv/bin/activate
        cd "$SCRIPT_DIR"
        echo "✅ Virtual environment created"
    else
        echo "Cannot continue without virtual environment"
        exit 1
    fi
fi

# Check and install dependencies
echo ""
echo "📦 Checking dependencies..."

# Test critical imports
python3 - <<EOF
import sys
errors = []

try:
    import tkinter
    print("✅ tkinter")
except ImportError:
    errors.append("tkinter")
    print("❌ tkinter - REQUIRED")

try:
    import torch
    print("✅ torch")
except ImportError:
    errors.append("torch")
    print("❌ torch - REQUIRED")

try:
    from PIL import Image
    print("✅ Pillow")
except ImportError:
    errors.append("Pillow")
    print("❌ Pillow - REQUIRED")

try:
    import numpy
    print("✅ numpy")
except ImportError:
    errors.append("numpy")
    print("❌ numpy - REQUIRED")

try:
    from skimage.metrics import peak_signal_noise_ratio
    print("✅ scikit-image")
except ImportError:
    errors.append("scikit-image")
    print("❌ scikit-image - REQUIRED")

try:
    import matplotlib
    print("✅ matplotlib")
except ImportError:
    errors.append("matplotlib")
    print("❌ matplotlib - REQUIRED")

try:
    from Crypto.PublicKey import RSA
    print("✅ pycryptodome")
except ImportError:
    print("⚠️  pycryptodome - OPTIONAL (encryption disabled)")

try:
    import imageio
    print("✅ imageio")
except ImportError:
    errors.append("imageio")
    print("❌ imageio - REQUIRED")

try:
    import reedsolo
    print("✅ reedsolo")
except ImportError:
    errors.append("reedsolo")
    print("❌ reedsolo - REQUIRED")

try:
    import PyInstaller
    print("✅ pyinstaller")
except ImportError:
    errors.append("pyinstaller")
    print("❌ pyinstaller - REQUIRED for build")

if errors:
    print(f"\n❌ Missing {len(errors)} required package(s)")
    sys.exit(1)
else:
    print("\n✅ All dependencies OK")
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo "Installing missing dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
    echo "✅ Dependencies installed"
fi

# Check model files
echo ""
echo "🤖 Checking model files..."
MODEL_DIR="$PROJECT_DIR/results/model"
if [ -d "$MODEL_DIR" ]; then
    MODEL_COUNT=$(ls -1 "$MODEL_DIR"/*.dat 2>/dev/null | wc -l)
    if [ $MODEL_COUNT -gt 0 ]; then
        echo "✅ Found $MODEL_COUNT model file(s)"
        # Find best model
        BEST_MODEL=$(ls -1 "$MODEL_DIR"/*.dat | sort | tail -n 1 | xargs basename)
        echo "   Best: $BEST_MODEL"
    else
        echo "⚠️  No .dat model files found in $MODEL_DIR"
        echo "   App will work but may have reduced quality"
    fi
else
    echo "⚠️  Model directory not found: $MODEL_DIR"
    echo "   Run 'python train.py' to train models first"
fi

# Check project modules
echo ""
echo "📚 Checking project modules..."
python3 - <<EOF
import sys
sys.path.insert(0, "$PROJECT_DIR")
try:
    from enhancedstegan import encode_message, decode_message, reverse_hiding
    print("✅ enhancedstegan module OK")
except ImportError as e:
    print(f"❌ enhancedstegan module FAILED: {e}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo "❌ Project modules check failed"
    exit 1
fi

echo ""
echo "✅ Environment check complete!"
echo ""

# ==================== STEP 2: Build ====================
echo "📋 Step 2: Building Application"
echo "----------------------------------------"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
cd "$SCRIPT_DIR"
rm -rf build dist __pycache__ *.spec.bak

# Build with PyInstaller
echo "🔨 Building with PyInstaller..."
pyinstaller steganography_app.spec

# Check if build succeeded
if [ -d "dist/CustomGANStego.app" ]; then
    echo ""
    echo "=============================================="
    echo "✅ BUILD SUCCESSFUL!"
    echo "=============================================="
    
    # Get app size
    APP_SIZE=$(du -sh "dist/CustomGANStego.app" | awk '{print $1}')
    echo ""
    echo "📦 Application Details:"
    echo "   Location: $SCRIPT_DIR/dist/CustomGANStego.app"
    echo "   Size: $APP_SIZE"
    echo ""
    
    # ==================== STEP 3: Create Distribution Package ====================
    echo "📋 Step 3: Creating Distribution Package"
    echo "----------------------------------------"
    
    # Ask user if they want DMG or ZIP
    echo "Choose distribution format:"
    echo "  1) ZIP archive (recommended - smaller, faster)"
    echo "  2) DMG disk image (traditional macOS installer)"
    echo "  3) Skip packaging (just use .app directly)"
    read -p "Enter choice [1-3] (default: 1): " PACKAGE_CHOICE
    PACKAGE_CHOICE=${PACKAGE_CHOICE:-1}
    
    if [ "$PACKAGE_CHOICE" = "1" ]; then
        # Create ZIP
        ZIP_NAME="CustomGANStego-macOS.zip"
        ZIP_PATH="$SCRIPT_DIR/dist/$ZIP_NAME"
        rm -f "$ZIP_PATH"
        
        echo "📦 Creating ZIP archive..."
        cd "$SCRIPT_DIR/dist"
        zip -r -q "$ZIP_NAME" CustomGANStego.app
        cd "$SCRIPT_DIR"
        
        if [ -f "$ZIP_PATH" ]; then
            ZIP_SIZE=$(du -sh "$ZIP_PATH" | awk '{print $1}')
            echo "✅ ZIP created successfully!"
            echo "   Location: $ZIP_PATH"
            echo "   Size: $ZIP_SIZE"
        else
            echo "⚠️  ZIP creation failed"
        fi
        
    elif [ "$PACKAGE_CHOICE" = "2" ]; then
        # Create DMG
        DMG_NAME="CustomGANStego-macOS.dmg"
        DMG_PATH="$SCRIPT_DIR/dist/$DMG_NAME"
        TEMP_DMG="$SCRIPT_DIR/dist/temp.dmg"
        VOLUME_NAME="CustomGANStego"
        
        # Remove old DMG if exists
        rm -f "$DMG_PATH" "$TEMP_DMG"
        
        echo "📦 Creating disk image (this may take a while)..."
        
        # Create a temporary DMG (3GB for large PyTorch app with overhead)
        hdiutil create -size 3000m -fs HFS+ -volname "$VOLUME_NAME" "$TEMP_DMG" > /dev/null 2>&1
        
        # Mount the DMG
        MOUNT_DIR=$(hdiutil attach "$TEMP_DMG" | grep "/Volumes/$VOLUME_NAME" | awk '{print $3}')
        
        if [ -z "$MOUNT_DIR" ]; then
            echo "⚠️  Failed to mount temporary DMG"
            echo "   Skipping DMG creation"
        else
            # Copy app to DMG
            echo "📋 Copying app to DMG..."
            cp -R "dist/CustomGANStego.app" "$MOUNT_DIR/"
            
            # Create Applications symlink
            ln -s /Applications "$MOUNT_DIR/Applications"
            
            # Copy README
            cp README.md "$MOUNT_DIR/README.txt"
            
            # Create a simple instruction file
            cat > "$MOUNT_DIR/INSTALL.txt" << 'EOL'
CustomGANStego - Installation Instructions
==========================================

1. Drag "CustomGANStego.app" to the "Applications" folder
2. Open from Launchpad or Applications folder
3. If macOS blocks the app, run in Terminal:
   xattr -cr /Applications/CustomGANStego.app

Features:
- Encode: Hide messages in images
- Decode: Extract hidden messages
- Reverse: Recover original images
- GenRSA: Generate encryption keys
- Compare: Calculate image metrics

For more information, see README.txt

Enjoy! 🎉
EOL
            
            # Unmount
            echo "💾 Finalizing DMG..."
            hdiutil detach "$MOUNT_DIR" > /dev/null 2>&1
            
            # Convert to compressed DMG
            hdiutil convert "$TEMP_DMG" -format UDZO -o "$DMG_PATH" > /dev/null 2>&1
            rm -f "$TEMP_DMG"
            
            if [ -f "$DMG_PATH" ]; then
                DMG_SIZE=$(du -sh "$DMG_PATH" | awk '{print $1}')
                echo "✅ DMG created successfully!"
                echo "   Location: $DMG_PATH"
                echo "   Size: $DMG_SIZE"
            else
                echo "⚠️  DMG creation failed"
            fi
        fi
    else
        echo "⏭️  Skipping package creation"
        echo "   Use dist/CustomGANStego.app directly"
    fi
    
    echo ""
    
    # ==================== STEP 4: Usage Guide ====================
    echo "📋 Step 4: Distribution & Usage"
    echo "=============================================="
    echo ""
    echo "🎯 Files Created:"
    echo ""
    echo "1️⃣  App Bundle:"
    echo "   dist/CustomGANStego.app"
    echo ""
    echo "2️⃣  DMG Installer:"
    echo "   dist/$DMG_NAME"
    echo ""
    echo "=============================================="
    echo "📱 How to Use:"
    echo "=============================================="
    echo ""
    echo "Option A - Install from DMG (Recommended):"
    echo "   1. Open dist/$DMG_NAME"
    echo "   2. Drag app to Applications folder"
    echo "   3. Eject disk image"
    echo "   4. Open from Launchpad"
    echo ""
    echo "Option B - Run directly:"
    echo "   open dist/CustomGANStego.app"
    echo ""
    echo "Option C - Manual install:"
    echo "   cp -r dist/CustomGANStego.app /Applications/"
    echo ""
    echo "If macOS blocks the app:"
    echo "   xattr -cr dist/CustomGANStego.app"
    echo "   (or for installed: xattr -cr /Applications/CustomGANStego.app)"
    echo ""
    echo "=============================================="
    echo "📤 Distribution:"
    echo "=============================================="
    echo ""
    echo "Share the DMG file with users:"
    echo "   • File: dist/$DMG_NAME"
    echo "   • Double-click to open"
    echo "   • Drag to Applications"
    echo "   • Done!"
    echo ""
    echo "=============================================="
    echo "🎨 Features:"
    echo "=============================================="
    echo ""
    echo "📝 Encode:  Hide messages in images"
    echo "🔍 Decode:  Extract messages from images"
    echo "⏮️  Reverse: Recover original cover image"
    echo "🔑 GenRSA:  Generate RSA key pairs"
    echo "📊 Compare: Calculate PSNR/SSIM metrics"
    echo ""
    echo "=============================================="
    echo "💡 Tips:"
    echo "=============================================="
    echo ""
    echo "• Use PNG images for best quality"
    echo "• Enable encryption for sensitive data"
    echo "• Keep private keys safe!"
    echo "• Check metrics: PSNR > 40 dB is excellent"
    echo ""
    echo "=============================================="
    echo ""
    
    # Ask to open app
    read -p "Open the app now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Opening CustomGANStego..."
        open dist/CustomGANStego.app
    else
        read -p "Open DMG file? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Opening DMG..."
            open "dist/$DMG_NAME"
        fi
    fi
    
    echo ""
    echo "✅ All done! Enjoy CustomGANStego! 🎉"
    echo ""
    echo "📦 Distribute: dist/$DMG_NAME"
    echo ""
    
else
    echo ""
    echo "=============================================="
    echo "❌ BUILD FAILED!"
    echo "=============================================="
    echo ""
    echo "Common issues:"
    echo "• Check error messages above"
    echo "• Ensure all dependencies installed"
    echo "• Try: pip install -r requirements.txt"
    echo "• Check PyInstaller version"
    echo ""
    exit 1
fi
