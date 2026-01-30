#!/bin/bash
set -e

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

CHECKSUM_FILE="/home/vscode/.cache/checksum-cache/.requirements-checksum"
REQUIREMENTS_FILES="requirements.txt requirements-dev.txt"

echo "🔧 Configuration de l'environnement..."

# Corriger les permissions de tous les répertoires cache et locaux
echo "🔑 Correction des permissions..."
sudo chown -R vscode:vscode /home/vscode/.cache /home/vscode/.local 2>/dev/null || true

# S'assurer que tous les répertoires existent
mkdir -p /home/vscode/.cache/pip \
         /home/vscode/.cache/whisper \
         /home/vscode/.local/bin \
         /home/vscode/.local/lib \
         /home/vscode/.local/share

echo "🔍 Vérification des dépendances Python..."

# Calculer le checksum actuel des fichiers requirements
current_checksum=$(cat $REQUIREMENTS_FILES 2>/dev/null | md5sum | cut -d' ' -f1)

# Lire le checksum précédent s'il existe
previous_checksum=""
if [ -f "$CHECKSUM_FILE" ]; then
    previous_checksum=$(cat "$CHECKSUM_FILE")
fi

# Comparer les checksums
if [ "$current_checksum" = "$previous_checksum" ] && [ -n "$previous_checksum" ]; then
    echo -e "${GREEN}✓ Les dépendances sont déjà à jour (pas de changement détecté)${NC}"
    echo "  Checksum: $current_checksum"
else
    if [ -z "$previous_checksum" ]; then
        echo -e "${YELLOW}→ Première installation des dépendances...${NC}"
    else
        echo -e "${YELLOW}→ Changements détectés dans requirements.txt, réinstallation...${NC}"
        echo "  Ancien checksum: $previous_checksum"
        echo "  Nouveau checksum: $current_checksum"
    fi
    
    # Installer les dépendances
    pip install -r requirements.txt -r requirements-dev.txt
    
    # Sauvegarder le nouveau checksum
    echo "$current_checksum" > "$CHECKSUM_FILE"
    echo -e "${GREEN}✓ Installation terminée avec succès${NC}"
fi

echo -e "${GREEN}✓ Configuration terminée${NC}"
