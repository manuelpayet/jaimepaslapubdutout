# Changelog

## [Unreleased] - 2026-01-28

### Changed
- Renommé la catégorie "Impossible" en "Impossible à classifier" pour plus de clarté
  - Mis à jour dans `src/classifier/annotator.py`
  - Mis à jour dans `instructions.md`
  - Mis à jour dans `README.md`

### Added
- Module radio_listener complet (audio_capture, transcriber, block_recorder, console_display)
- Module classifier complet (session_reader, session_converter, annotator)
- Module common (config, storage, models)
- 51 tests unitaires (100% de réussite)
- Documentation complète
- Scripts utilitaires (run_tests.sh)

## Architecture

### Module Radio Listener
- Capture audio depuis flux RTSP via FFmpeg
- Retranscription en temps réel avec Whisper
- Enregistrement par blocs de 10 secondes (configurable)
- Affichage console optimisé (faible CPU)

### Module Classifier
- Lecture des sessions brutes
- Conversion en format SQLite optimisé
- Interface d'annotation console interactive
- 4 catégories : À classifier, Publicité, Radio, Impossible à classifier

### Stack Technique
- Python 3.11
- OpenAI Whisper pour la transcription
- FFmpeg pour la capture audio
- SQLite pour le stockage structuré
- DevContainer pour l'environnement de développement
