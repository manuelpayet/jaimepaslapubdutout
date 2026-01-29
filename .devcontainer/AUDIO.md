# Configuration Audio pour l'Annotateur

## 🔊 Problème

Dans un devcontainer (environnement Docker), l'audio ne fonctionne pas par défaut car :
1. Pas de serveur audio (PulseAudio/ALSA)
2. Pas d'accès au matériel audio de l'hôte

## ✅ Solutions

### **Option 1 : Mode Dummy (Recommandé pour annotation)**

Le code utilise automatiquement un driver "dummy" qui :
- ✅ Permet de continuer sans erreur
- ❌ N'émet pas de son
- ✅ Parfait si vous voulez juste voir les transcriptions

**Aucune action requise** - fonctionne automatiquement.

---

### **Option 2 : Activer l'audio réel (si besoin)**

#### A. Installer PulseAudio dans le container

Le Dockerfile inclut déjà PulseAudio. Après rebuild :

```bash
# Rebuild du devcontainer
Ctrl+Shift+P → "Dev Containers: Rebuild Container"
```

#### B. Partager l'audio de l'hôte (Linux uniquement)

Ajoutez dans `.devcontainer/devcontainer.json` :

```json
{
  "runArgs": [
    "--device=/dev/snd",
    "-e", "PULSE_SERVER=unix:/run/user/1000/pulse/native",
    "-v", "/run/user/1000/pulse:/run/user/1000/pulse"
  ]
}
```

**Note** : Nécessite PulseAudio sur l'hôte Linux.

---

### **Option 3 : Utiliser un lecteur externe**

Si vous voulez vraiment écouter l'audio :

1. Ouvrez le fichier WAV depuis VS Code
2. Ou copiez-le vers l'hôte :

```bash
# Dans le terminal du devcontainer
cp data/raw/session_XXX/blocks/block_0042.wav /tmp/
```

3. Lisez-le sur votre machine hôte avec n'importe quel lecteur

---

## 🎯 Recommandation

Pour l'annotation, le **mode dummy est suffisant** car :
- L'objectif est de lire la transcription, pas l'audio
- Évite les complications de configuration
- Fonctionne sur tous les systèmes (Linux/Mac/Windows)

Si vous avez vraiment besoin d'écouter l'audio :
- Utilisez l'**Option 3** (copier + lire sur hôte)
- C'est plus simple et fiable que configurer l'audio dans Docker
