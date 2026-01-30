#!/bin/bash
# Build script for creating standalone binaries

set -e  # Exit on error

echo "========================================"
echo "Building Radio Transcription Binaries"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo -e "${RED}Error: PyInstaller is not installed${NC}"
    echo "Install it with: pip install pyinstaller"
    exit 1
fi

# Clean previous builds
echo -e "${BLUE}Cleaning previous builds...${NC}"
rm -rf build dist
mkdir -p dist

# Build radio-listener
echo ""
echo -e "${BLUE}Building radio-listener...${NC}"
pyinstaller radio_listener.spec --clean --noconfirm

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ radio-listener built successfully${NC}"
else
    echo -e "${RED}✗ Failed to build radio-listener${NC}"
    exit 1
fi

# Build classifier
echo ""
echo -e "${BLUE}Building classifier...${NC}"
pyinstaller classifier.spec --clean --noconfirm

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ classifier built successfully${NC}"
else
    echo -e "${RED}✗ Failed to build classifier${NC}"
    exit 1
fi

# Create distribution package
echo ""
echo -e "${BLUE}Creating distribution package...${NC}"
mkdir -p dist/radio-transcription-linux
cp dist/radio-listener dist/radio-transcription-linux/
cp dist/classifier dist/radio-transcription-linux/
cp README.md dist/radio-transcription-linux/
cat > dist/radio-transcription-linux/USAGE.txt << 'EOF'
Radio Transcription - Standalone Binaries
==========================================

Cette distribution contient deux binaires standalone :

1. radio-listener : Capture et transcription en temps réel
   Usage: ./radio-listener --stream-url <URL> [options]
   
   Options:
     --stream-url URL          URL du flux audio (obligatoire)
     --block-duration N        Durée des blocs en secondes (défaut: 10)
     --whisper-model MODEL     Modèle Whisper: tiny/base/small/medium/large (défaut: base)
     --language LANG           Code langue (défaut: fr)
     --output-dir DIR          Répertoire de sortie (défaut: data/raw)
     --session-id ID           ID de session personnalisé
   
   Exemple:
     ./radio-listener --stream-url http://audio.bfmtv.com/rmcradio_128.mp3 --block-duration 10

2. classifier : Annotation des sessions enregistrées
   Usage: ./classifier [session_id] [options]
   
   Options:
     --list                    Lister toutes les sessions
     --convert-all             Convertir toutes les sessions
     --force-convert           Forcer la conversion
     --input-dir DIR           Répertoire des sessions brutes (défaut: data/raw)
     --output-dir DIR          Répertoire des sessions traitées (défaut: data/processed)
   
   Exemples:
     ./classifier --list
     ./classifier session_2026-01-28_14-30-00
     ./classifier --convert-all

Dépendances système requises :
- FFmpeg (pour radio-listener)
- PulseAudio ou ALSA (pour le playback audio dans classifier)

Installation FFmpeg sur Ubuntu/Debian:
  sudo apt-get install ffmpeg

Note: Ces binaires incluent Python et toutes les dépendances Python.
      Aucune installation Python n'est nécessaire.
EOF

# Create tarball
echo ""
echo -e "${BLUE}Creating tarball...${NC}"
cd dist
tar -czf radio-transcription-linux-x86_64.tar.gz radio-transcription-linux/
cd ..

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Binaries location:"
echo "  - dist/radio-listener"
echo "  - dist/classifier"
echo ""
echo "Distribution package:"
echo "  - dist/radio-transcription-linux-x86_64.tar.gz"
echo ""
echo "File sizes:"
ls -lh dist/radio-listener dist/classifier dist/radio-transcription-linux-x86_64.tar.gz
echo ""
echo -e "${BLUE}To test the binaries:${NC}"
echo "  ./dist/radio-listener --help"
echo "  ./dist/classifier --help"
