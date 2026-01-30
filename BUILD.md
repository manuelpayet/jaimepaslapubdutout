# Guide de Build - Binaires Standalone

Ce guide explique comment créer des binaires Linux standalone pour les applications `radio-listener` et `classifier`.

## 📦 Prérequis

### Dépendances système (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install -y \
    python3.11 \
    python3-pip \
    python3-venv \
    ffmpeg \
    upx-ucl
```

**Note:** `upx-ucl` est optionnel mais recommandé pour compresser les binaires.

### Dépendances Python
```bash
# Installer les dépendances du projet
pip install -r requirements.txt

# Installer PyInstaller
pip install -r requirements-build.txt
```

## 🚀 Build des binaires

### Build automatique (Recommandé)
```bash
./build.sh
```

Le script va :
1. Nettoyer les builds précédents
2. Construire `radio-listener`
3. Construire `classifier`
4. Créer un package de distribution
5. Créer une archive `.tar.gz`

### Build manuel

#### Radio Listener
```bash
pyinstaller radio_listener.spec --clean --noconfirm
```

#### Classifier
```bash
pyinstaller classifier.spec --clean --noconfirm
```

## 📂 Structure après le build

```
dist/
├── radio-listener                              # Binaire standalone
├── classifier                                  # Binaire standalone
├── radio-transcription-linux/                  # Package complet
│   ├── radio-listener
│   ├── classifier
│   ├── README.md
│   └── USAGE.txt
└── radio-transcription-linux-x86_64.tar.gz    # Archive de distribution
```

## 🧪 Test des binaires

### Test radio-listener
```bash
./dist/radio-listener --help
./dist/radio-listener --stream-url http://audio.bfmtv.com/rmcradio_128.mp3
```

### Test classifier
```bash
./dist/classifier --help
./dist/classifier --list
```

## 📦 Distribution

L'archive `radio-transcription-linux-x86_64.tar.gz` contient tout le nécessaire :

```bash
# Extraire l'archive
tar -xzf dist/radio-transcription-linux-x86_64.tar.gz

# Utiliser les binaires
cd radio-transcription-linux
./radio-listener --help
./classifier --help
```

## ⚙️ Configuration des fichiers spec

### radio_listener.spec
- **Mode:** One-file (tout en un seul exécutable)
- **Inclusions:** Whisper + modèles, source code
- **Hidden imports:** Whisper, sklearn, tiktoken
- **Compression UPX:** Activée

### classifier.spec
- **Mode:** One-file (tout en un seul exécutable)
- **Inclusions:** Rich library, pygame, source code
- **Hidden imports:** pygame, rich, sqlite3
- **Compression UPX:** Activée

## 🔧 Personnalisation

### Modifier les inclusions
Éditez les fichiers `.spec` pour ajouter/retirer des modules :

```python
hiddenimports = [
    'votre_module',
    # ...
]
```

### Mode multi-fichiers
Pour un build plus rapide mais avec plusieurs fichiers, changez dans les `.spec` :

```python
exe = EXE(
    pyz,
    a.scripts,
    # Commentez les lignes suivantes :
    # a.binaries,
    # a.zipfiles,
    # a.datas,
    [],
    name='app-name',
    # ...
)

# Ajoutez :
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='app-name',
)
```

## 📊 Taille des binaires

Tailles approximatives :
- **radio-listener:** ~500-800 MB (inclut Whisper + modèles)
- **classifier:** ~100-200 MB (inclut pygame + rich)

### Réduire la taille

1. **Sans UPX:**
   - Désactiver dans les `.spec`: `upx=False`
   
2. **Exclure les modèles Whisper du binaire:**
   ```python
   # Dans radio_listener.spec
   whisper_datas = []  # Ne pas inclure les données
   ```
   Les modèles seront téléchargés au premier lancement.

3. **Mode multi-fichiers:**
   - Voir section "Personnalisation" ci-dessus
   - Réduit le temps de démarrage mais crée plusieurs fichiers

## 🐛 Dépannage

### Erreur: "Module not found"
Ajoutez le module manquant dans `hiddenimports` du fichier `.spec`.

### Erreur: "Failed to execute script"
Testez avec le mode debug :
```python
exe = EXE(
    # ...
    debug=True,
    # ...
)
```

### Binaire trop volumineux
- Utilisez le mode multi-fichiers
- Excluez les modèles Whisper pré-inclus
- Désactivez UPX si problèmes

### Erreur FFmpeg au runtime
FFmpeg doit être installé sur le système cible :
```bash
sudo apt-get install ffmpeg
```

## 🖥️ Compatibilité

Les binaires générés sont compatibles avec :
- **Architecture:** x86_64 (64-bit)
- **OS:** Linux (testé sur Ubuntu 20.04+)
- **Dépendances système requises:**
  - FFmpeg (pour radio-listener)
  - PulseAudio/ALSA (pour classifier avec audio)
  - libc6 2.31+ (généralement présent)

**Important:** Le binaire doit être compilé sur un système similaire au système cible. Pour une compatibilité maximale, buildez sur une distribution ancienne (ex: Ubuntu 20.04).

## 🐳 Build dans le devcontainer

Le build peut être effectué dans le devcontainer :

```bash
# Dans le devcontainer
pip install -r requirements-build.txt
./build.sh
```

Les binaires seront dans `dist/` et peuvent être copiés sur l'hôte.

## 📝 Notes

- Les binaires incluent **tout Python** et les dépendances
- **Aucune installation Python** n'est nécessaire sur le système cible
- Les logs sont écrits dans le répertoire courant
- Les données (sessions) sont stockées dans `data/`

## 🔗 Liens utiles

- [PyInstaller Documentation](https://pyinstaller.org/)
- [PyInstaller Spec Files](https://pyinstaller.org/en/stable/spec-files.html)
- [UPX Compressor](https://upx.github.io/)
