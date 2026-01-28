# Radio Transcription & Classification

Système de retranscription audio en temps réel d'un flux RTSP de radio avec classification des segments.

## Architecture

Le projet est composé de deux modules principaux :

1. **Radio Listener** : Écoute et retranscription en temps réel
   - Capture audio via flux RTSP
   - Retranscription avec Whisper
   - Enregistrement par blocs de N secondes

2. **Classifier** : Classification des sessions enregistrées
   - Conversion des sessions brutes en format structuré
   - Interface d'annotation console
   - Catégories : À classifier, Publicité, Radio, Impossible à classifier

## Stack Technique

- **Python 3.11**
- **Whisper** pour la retranscription
- **FFmpeg** pour l'acquisition audio
- **Devcontainer** pour l'environnement de développement

## Installation

1. Ouvrir le projet dans VS Code
2. Accepter l'ouverture dans le devcontainer
3. Les dépendances seront installées automatiquement

**Note :** Le projet utilise des volumes Docker pour mettre en cache :
- Les packages Python (pip cache) - accélère les rebuilds
- Les modèles Whisper - évite les re-téléchargements

Voir `.devcontainer/CACHE.md` pour plus de détails.

## Utilisation

### Module Radio Listener
```bash
python -m src.radio_listener.main --rtsp-url <URL> --block-duration <seconds>
```

### Module Classifier
```bash
python -m src.classifier.main --session-dir <path>
```

## Tests

```bash
pytest
```

## Développement

- Architecture modulaire avec classes
- Tests unitaires pour toutes les fonctionnalités
- Code formaté avec Black
