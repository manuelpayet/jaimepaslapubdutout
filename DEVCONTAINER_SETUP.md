# Configuration DevContainer

Ce document explique la configuration du DevContainer pour le projet Radio Transcription.

## 📦 Composants

### 1. Dockerfile (`.devcontainer/Dockerfile`)
- **Base** : Python 3.11-slim
- **Outils** : FFmpeg, Git
- **Utilisateur** : vscode (non-root)

### 2. Configuration DevContainer (`.devcontainer/devcontainer.json`)
- **Extensions VS Code** : Python, Pylance, Black
- **Volumes de cache** : pip, whisper
- **Post-create** : Installation automatique des dépendances

### 3. Cache persistant
Deux volumes Docker pour accélérer les rebuilds :
- `radio-pip-cache` : Cache des packages Python
- `radio-whisper-cache` : Cache des modèles Whisper

## 🚀 Premier lancement

### Prérequis
- Docker Desktop installé
- VS Code avec l'extension "Dev Containers"

### Démarrage
1. Ouvrir le projet dans VS Code
2. Accepter la notification "Reopen in Container"
3. Attendre la construction du container (5-10 min la première fois)
4. Les dépendances s'installent automatiquement

### Ce qui se passe
```
1. Construction de l'image Docker (Python + FFmpeg)
   └─> ~1-2 minutes

2. Démarrage du container avec les volumes montés
   └─> ~10 secondes

3. Installation des dépendances (postCreateCommand)
   pip install -r requirements.txt -r requirements-dev.txt
   └─> ~5-8 minutes (première fois)
   └─> ~30-60 secondes (fois suivantes grâce au cache)

4. VS Code se connecte au container
   └─> Prêt à coder !
```

## ♻️ Rebuilds suivants

### Rebuild normal
**Commande** : Ctrl+Shift+P > "Dev Containers: Rebuild Container"

**Durée** : ~1-2 minutes (grâce aux caches)

**Ce qui est préservé** :
- ✅ Cache pip (packages déjà téléchargés)
- ✅ Cache Whisper (modèles déjà téléchargés)
- ✅ Workspace (vos fichiers)

**Ce qui est reconstruit** :
- 🔄 Image Docker (si Dockerfile modifié)
- 🔄 Installation des dépendances (utilise le cache)

### Rebuild complet (sans cache)
**Commandes** :
```bash
# Supprimer les caches
./manage-cache.sh clean all

# Rebuild
Ctrl+Shift+P > "Dev Containers: Rebuild Container"
```

**Durée** : ~5-12 minutes (comme le premier lancement)

## 📊 Gains de performance

| Opération | Sans cache | Avec cache | Gain |
|-----------|------------|------------|------|
| Premier lancement | 5-10 min | 5-10 min | - |
| Rebuild | 5-10 min | 1-2 min | 80% |
| pip install | 5-8 min | 30-60 sec | 90% |
| Modèle Whisper | 1-2 min | 0 sec | 100% |

## 🛠️ Gestion des caches

### Script helper
Un script bash est fourni pour gérer facilement les caches :

```bash
# Voir le status des caches
./manage-cache.sh status

# Lister le contenu des caches
./manage-cache.sh list

# Nettoyer un cache spécifique
./manage-cache.sh clean pip
./manage-cache.sh clean whisper

# Nettoyer tous les caches
./manage-cache.sh clean all

# Aide
./manage-cache.sh help
```

### Commandes Docker manuelles

```bash
# Lister les volumes
docker volume ls | grep radio

# Voir la taille
docker run --rm -v radio-pip-cache:/cache alpine du -sh /cache
docker run --rm -v radio-whisper-cache:/cache alpine du -sh /cache

# Supprimer un volume
docker volume rm radio-pip-cache
docker volume rm radio-whisper-cache
```

## 🔍 Troubleshooting

### Le container ne démarre pas
1. Vérifier que Docker Desktop est lancé
2. Vérifier les logs : Ctrl+Shift+P > "Dev Containers: Show Container Log"
3. Essayer un rebuild : Ctrl+Shift+P > "Dev Containers: Rebuild Container"

### Les dépendances ne s'installent pas
1. Vérifier le `postCreateCommand` dans `.devcontainer/devcontainer.json`
2. Vérifier que les fichiers `requirements.txt` existent
3. Essayer manuellement dans le container :
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```

### Le cache ne semble pas fonctionner
1. Vérifier que les volumes existent :
   ```bash
   ./manage-cache.sh status
   ```
2. Vérifier les mounts dans `devcontainer.json`
3. Recréer les volumes :
   ```bash
   ./manage-cache.sh clean all
   # Puis rebuild
   ```

### Performance lente dans le container
1. Vérifier les ressources Docker Desktop (CPU, RAM)
2. Augmenter les ressources dans Docker Desktop > Settings > Resources
3. Minimum recommandé : 4 CPU, 8GB RAM

### Erreur de permissions
Si vous avez des erreurs de permissions sur les caches :
```bash
# Supprimer et recréer
./manage-cache.sh clean all
# Rebuild le container
```

## 📝 Modification de la configuration

### Ajouter une extension VS Code
Éditez `.devcontainer/devcontainer.json` :
```json
"extensions": [
  "ms-python.python",
  "ms-python.vscode-pylance",
  "ms-python.black-formatter",
  "votre-extension-ici"  // ← Ajoutez ici
]
```

### Ajouter des outils système
Éditez `.devcontainer/Dockerfile` :
```dockerfile
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    votre-outil-ici \  # ← Ajoutez ici
    && rm -rf /var/lib/apt/lists/*
```

### Changer la commande post-create
Éditez `.devcontainer/devcontainer.json` :
```json
"postCreateCommand": "pip install -r requirements.txt && votre-commande"
```

### Ajouter un volume de cache
Éditez `.devcontainer/devcontainer.json` :
```json
"mounts": [
  "source=radio-pip-cache,target=/home/vscode/.cache/pip,type=volume",
  "source=radio-whisper-cache,target=/home/vscode/.cache/whisper,type=volume",
  "source=mon-cache,target=/chemin/cible,type=volume"  // ← Ajoutez ici
]
```

## 🔗 Ressources

- [Dev Containers Documentation](https://code.visualstudio.com/docs/devcontainers/containers)
- [Dev Container Specification](https://containers.dev/)
- [Docker Volumes](https://docs.docker.com/storage/volumes/)
- Documentation du cache : `.devcontainer/CACHE.md`

## ✅ Checklist post-installation

Après le premier lancement, vérifiez que tout fonctionne :

- [ ] Le container a démarré sans erreur
- [ ] Python est accessible (`python --version`)
- [ ] Les dépendances sont installées (`pip list`)
- [ ] Les tests passent (`./run_tests.sh`)
- [ ] Les caches existent (`./manage-cache.sh status`)
- [ ] VS Code est connecté (indicateur "Dev Container" en bas à gauche)

Si tous les points sont cochés, vous êtes prêt à développer ! 🎉
