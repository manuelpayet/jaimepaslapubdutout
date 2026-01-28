# Guide de Tests

Ce document explique comment exécuter les tests du projet.

## Prérequis

Les tests doivent être exécutés dans le devcontainer VS Code, où toutes les dépendances sont installées automatiquement.

## Exécuter tous les tests

```bash
# Méthode 1 : Utiliser le script
./run_tests.sh

# Méthode 2 : Utiliser pytest directement
python -m pytest tests/

# Méthode 3 : Avec coverage détaillé
python -m pytest tests/ --cov=src --cov-report=html --cov-report=term
```

## Exécuter des tests spécifiques

### Tests d'un module spécifique

```bash
# Tests du module common
python -m pytest tests/test_common/

# Tests du module radio_listener
python -m pytest tests/test_radio_listener/

# Tests du module classifier
python -m pytest tests/test_classifier/
```

### Tests d'un fichier spécifique

```bash
python -m pytest tests/test_common/test_config.py
```

### Tests d'une classe spécifique

```bash
python -m pytest tests/test_common/test_config.py::TestRadioListenerConfig
```

### Test d'une fonction spécifique

```bash
python -m pytest tests/test_common/test_config.py::TestRadioListenerConfig::test_default_values
```

## Options utiles

```bash
# Mode verbose (plus de détails)
python -m pytest tests/ -v

# Afficher les print statements
python -m pytest tests/ -s

# Arrêter au premier échec
python -m pytest tests/ -x

# Exécuter seulement les tests qui ont échoué la dernière fois
python -m pytest tests/ --lf

# Voir la couverture de code
python -m pytest tests/ --cov=src --cov-report=term-missing
```

## Rapport de couverture

Après avoir exécuté les tests avec `--cov-report=html`, ouvrez le rapport :

```bash
# Le rapport HTML est généré dans htmlcov/
# Ouvrir htmlcov/index.html dans un navigateur
```

## Structure des tests

```
tests/
├── test_common/
│   ├── test_config.py      # Tests de configuration
│   └── test_storage.py     # Tests de stockage
├── test_radio_listener/
│   ├── test_audio_capture.py    # Tests de capture audio
│   ├── test_transcriber.py      # Tests de transcription
│   ├── test_block_recorder.py   # Tests d'enregistrement
│   └── test_console_display.py  # Tests d'affichage
└── test_classifier/
    └── (à venir)
```

## Conventions de tests

- Chaque module a son propre répertoire de tests
- Les fichiers de test commencent par `test_`
- Les classes de test commencent par `Test`
- Les fonctions de test commencent par `test_`
- Utiliser des fixtures pytest pour les dépendances communes
- Mocker les dépendances externes (FFmpeg, Whisper, etc.)

## Tests d'intégration

Pour tester avec un vrai flux RTSP :

```bash
# Définir l'URL RTSP
export RTSP_URL="rtsp://your-stream-url"

# Lancer le listener (pas un test unitaire)
python -m src.radio_listener.main --rtsp-url $RTSP_URL --block-duration 10
```
