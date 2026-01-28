#!/bin/bash
# Script de gestion des caches DevContainer

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Noms des volumes
PIP_CACHE="radio-pip-cache"
WHISPER_CACHE="radio-whisper-cache"

# Fonctions d'affichage
info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

# Fonction pour vérifier si un volume existe
volume_exists() {
    docker volume ls -q | grep -q "^$1$"
}

# Fonction pour obtenir la taille d'un volume
get_volume_size() {
    if volume_exists "$1"; then
        docker run --rm -v "$1:/cache" alpine du -sh /cache 2>/dev/null | awk '{print $1}' || echo "N/A"
    else
        echo "N/A"
    fi
}

# Commande: status
cmd_status() {
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  Status des caches DevContainer"
    echo "═══════════════════════════════════════════════════════════"
    echo ""

    # Cache pip
    if volume_exists "$PIP_CACHE"; then
        SIZE=$(get_volume_size "$PIP_CACHE")
        success "Cache pip: $PIP_CACHE ($SIZE)"
    else
        warning "Cache pip: $PIP_CACHE (non créé)"
    fi

    # Cache whisper
    if volume_exists "$WHISPER_CACHE"; then
        SIZE=$(get_volume_size "$WHISPER_CACHE")
        success "Cache Whisper: $WHISPER_CACHE ($SIZE)"
    else
        warning "Cache Whisper: $WHISPER_CACHE (non créé)"
    fi

    echo ""
    echo "Pour plus d'informations : ./manage-cache.sh help"
    echo ""
}

# Commande: list
cmd_list() {
    echo ""
    info "Contenu du cache pip:"
    if volume_exists "$PIP_CACHE"; then
        docker run --rm -v "$PIP_CACHE:/cache" alpine ls -lh /cache 2>/dev/null || warning "Impossible de lister le contenu"
    else
        warning "Cache non créé"
    fi

    echo ""
    info "Contenu du cache Whisper:"
    if volume_exists "$WHISPER_CACHE"; then
        docker run --rm -v "$WHISPER_CACHE:/cache" alpine ls -lh /cache 2>/dev/null || warning "Impossible de lister le contenu"
    else
        warning "Cache non créé"
    fi
    echo ""
}

# Commande: clean
cmd_clean() {
    local WHAT="$1"
    
    case "$WHAT" in
        pip)
            if volume_exists "$PIP_CACHE"; then
                info "Suppression du cache pip..."
                docker volume rm "$PIP_CACHE"
                success "Cache pip supprimé"
            else
                warning "Cache pip n'existe pas"
            fi
            ;;
        whisper)
            if volume_exists "$WHISPER_CACHE"; then
                info "Suppression du cache Whisper..."
                docker volume rm "$WHISPER_CACHE"
                success "Cache Whisper supprimé"
            else
                warning "Cache Whisper n'existe pas"
            fi
            ;;
        all)
            info "Suppression de tous les caches..."
            
            if volume_exists "$PIP_CACHE"; then
                docker volume rm "$PIP_CACHE"
                success "Cache pip supprimé"
            fi
            
            if volume_exists "$WHISPER_CACHE"; then
                docker volume rm "$WHISPER_CACHE"
                success "Cache Whisper supprimé"
            fi
            
            if ! volume_exists "$PIP_CACHE" && ! volume_exists "$WHISPER_CACHE"; then
                warning "Aucun cache à supprimer"
            fi
            ;;
        *)
            error "Argument invalide. Utilisez: pip, whisper, ou all"
            exit 1
            ;;
    esac
    
    echo ""
    info "Les caches seront recréés automatiquement au prochain lancement du devcontainer"
    echo ""
}

# Commande: help
cmd_help() {
    cat << EOF

Usage: ./manage-cache.sh <commande> [arguments]

Commandes disponibles:

  status              Affiche le status des caches
  list                Liste le contenu des caches
  clean <type>        Supprime les caches
                      Types: pip, whisper, all
  help                Affiche cette aide

Exemples:

  ./manage-cache.sh status
  ./manage-cache.sh list
  ./manage-cache.sh clean pip
  ./manage-cache.sh clean whisper
  ./manage-cache.sh clean all

Volumes Docker utilisés:
  - $PIP_CACHE       (cache pip)
  - $WHISPER_CACHE   (cache Whisper)

Pour plus d'informations, voir .devcontainer/CACHE.md

EOF
}

# Main
main() {
    local CMD="${1:-status}"
    
    case "$CMD" in
        status)
            cmd_status
            ;;
        list)
            cmd_list
            ;;
        clean)
            if [ -z "$2" ]; then
                error "Argument manquant. Utilisez: pip, whisper, ou all"
                echo ""
                cmd_help
                exit 1
            fi
            cmd_clean "$2"
            ;;
        help|--help|-h)
            cmd_help
            ;;
        *)
            error "Commande inconnue: $CMD"
            echo ""
            cmd_help
            exit 1
            ;;
    esac
}

main "$@"
