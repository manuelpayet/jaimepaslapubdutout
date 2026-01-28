# Cache DevContainer

Ce projet utilise des volumes Docker pour mettre en cache les dépendances Python et les modèles Whisper.

## 📦 Volumes de cache

### 1. `radio-pip-cache`
- **Cible** : `/home/vscode/.cache/pip`
- **Contenu** : Packages Python téléchargés par pip
- **Taille** : ~500 MB - 1 GB (dépend des dépendances)
- **Bénéfice** : Accélère `pip install` lors des rebuilds

### 2. `radio-whisper-cache`
- **Cible** : `/home/vscode/.cache/whisper`
- **Contenu** : Modèles Whisper pré-entraînés
- **Taille** : 140 MB - 2.9 GB (dépend du modèle)
  - `tiny` : 75 MB
  - `base` : 142 MB
  - `small` : 466 MB
  - `medium` : 1.5 GB
  - `large` : 2.9 GB
- **Bénéfice** : Évite de re-télécharger les modèles Whisper

## 🚀 Comment ça fonctionne

### Premier lancement
1. Le devcontainer démarre
2. `pip install` télécharge tous les packages
3. Les packages sont stockés dans `radio-pip-cache`
4. Au premier usage de Whisper, le modèle est téléchargé
5. Le modèle est stocké dans `radio-whisper-cache`

### Lancements suivants / Rebuilds
1. Le devcontainer démarre
2. `pip install` utilise le cache → **Beaucoup plus rapide !**
3. Whisper utilise le modèle en cache → **Pas de re-téléchargement !**

## 📊 Vérifier les caches

### Lister les volumes
```bash
docker volume ls | grep radio
```

Résultat attendu :
```
local     radio-pip-cache
local     radio-whisper-cache
```

### Voir la taille des caches
```bash
# Taille du cache pip
docker run --rm -v radio-pip-cache:/cache alpine du -sh /cache

# Taille du cache whisper
docker run --rm -v radio-whisper-cache:/cache alpine du -sh /cache
```

### Inspecter le contenu
```bash
# Contenu du cache pip
docker run --rm -v radio-pip-cache:/cache alpine ls -lh /cache

# Contenu du cache whisper
docker run --rm -v radio-whisper-cache:/cache alpine ls -lh /cache
```

## 🧹 Gestion des caches

### Nettoyer le cache pip
```bash
# Supprimer complètement
docker volume rm radio-pip-cache

# Recréé automatiquement au prochain lancement
```

### Nettoyer le cache whisper
```bash
# Supprimer complètement
docker volume rm radio-whisper-cache

# Le modèle sera re-téléchargé au prochain usage
```

### Nettoyer tous les caches du projet
```bash
docker volume rm radio-pip-cache radio-whisper-cache
```

### Nettoyer tous les volumes Docker non utilisés
```bash
# ATTENTION : Supprime TOUS les volumes non utilisés
docker volume prune
```

## ⚠️ Attention

### Les caches sont liés à Docker
- Si vous changez de machine, les caches ne suivent pas
- Si vous supprimez Docker Desktop, les caches sont perdus
- Les caches sont stockés dans le système Docker local

### Rebuild complet
Si vous voulez un rebuild vraiment "propre" :
```bash
# 1. Supprimer les caches
docker volume rm radio-pip-cache radio-whisper-cache

# 2. Rebuild le devcontainer
# Dans VS Code : Ctrl+Shift+P > "Dev Containers: Rebuild Container"
```

## 💡 Astuces

### Pré-charger les modèles Whisper
Si vous savez quel modèle vous utiliserez, vous pouvez le télécharger à l'avance :

Dans le devcontainer :
```python
import whisper
whisper.load_model("base")  # ou "tiny", "small", "medium", "large"
```

### Partager le cache entre projets
Si vous avez plusieurs projets utilisant Whisper, vous pouvez partager le cache whisper :

Dans `.devcontainer/devcontainer.json` :
```json
"mounts": [
  "source=radio-pip-cache,target=/home/vscode/.cache/pip,type=volume",
  "source=shared-whisper-cache,target=/home/vscode/.cache/whisper,type=volume"
]
```

## 📈 Gains de performance estimés

### Sans cache
- Premier `pip install` : 5-10 minutes
- Premier téléchargement modèle Whisper `base` : 1-2 minutes
- Rebuild complet : 5-12 minutes

### Avec cache
- `pip install` (rebuild) : 30-60 secondes ✅
- Modèle Whisper : 0 seconde (déjà en cache) ✅
- Rebuild : 1-2 minutes ✅

**Gain : ~80-90% de temps sur les rebuilds !**

## 🔍 Troubleshooting

### Le cache ne semble pas fonctionner
1. Vérifiez que les volumes existent :
   ```bash
   docker volume ls | grep radio
   ```

2. Vérifiez les permissions :
   ```bash
   docker run --rm -v radio-pip-cache:/cache alpine ls -la /cache
   ```

3. Recréez les volumes :
   ```bash
   docker volume rm radio-pip-cache radio-whisper-cache
   # Puis rebuilder le devcontainer
   ```

### Erreur "volume not found"
Les volumes sont créés automatiquement au premier lancement. Si vous avez cette erreur, rebuilder le devcontainer résoudra le problème.

### Cache corrompu
Si vous suspectez un cache corrompu :
```bash
# Supprimer et laisser recréer
docker volume rm radio-pip-cache
# Rebuild le devcontainer
```

## 📚 Références

- [Docker Volumes](https://docs.docker.com/storage/volumes/)
- [Dev Container Mounts](https://containers.dev/implementors/json_reference/#mount-point)
- [Whisper Models](https://github.com/openai/whisper#available-models-and-languages)
