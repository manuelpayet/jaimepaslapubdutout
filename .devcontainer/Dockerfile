FROM python:3.11-slim

# Installation de FFmpeg et dépendances système
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    libffi-dev \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Création d'un utilisateur non-root avec droits sudo
RUN useradd -m -s /bin/bash vscode && \
    echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Création de tous les répertoires cache et locaux avec les bonnes permissions
RUN mkdir -p /home/vscode/.cache/pip \
             /home/vscode/.cache/whisper \
             /home/vscode/.local/bin \
             /home/vscode/.local/lib \
             /home/vscode/.local/share && \
    chown -R vscode:vscode /home/vscode/.cache /home/vscode/.local

# Répertoire de travail
WORKDIR /workspace

USER vscode
