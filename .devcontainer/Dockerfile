FROM python:3.11-slim

# Installation de FFmpeg et dépendances système
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Création d'un utilisateur non-root
RUN useradd -m -s /bin/bash vscode

# Répertoire de travail
WORKDIR /workspace

USER vscode
