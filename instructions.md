# Objectif du projet
Ce projet a pour objectif de retranscrire la voix d'une flux rtsp d'une radio, enregistré par bloc de N secondes.
Ces blocs de N secondes seront ensuite classifié avec un outil dédié pour classifier chaque bloc. 

# Comportement de l'assistance au code
Avant d'appliquer quelconque modification, me les montrer, me les expliquer pour demander validation

# Stack technologique
L'application sera faite en Python, et doit pouvoir s'exécuter sans installer python directement sur la machine (je veux utiliser devcontainer dans vscode).
La retranscription audio se fera avec whisper.
L'acquisition audio utiliser ffmpeg (en mode librairie ou en execution du binaire, peu importe)

Le frontend sera un affichage console, qui doit limiter au plus possible la consommation CPU, pour ne pas prendre le pas sur les performances du backend

# Architecture
Le projet est découpé en différentes applications autonomes

## Principe commun des applications
Les applications sont modulaires et utilise des classes pour découper la logique métier
Le code doit être couvert par des tests unitaires afin de s'assurer que les nouvelles fonctionnalités appliquées ne cassent pas les anciennes

## Ecoute de la radio et retranscription en temps réel 
    Avec fonctionnalité d'enregistrement du texte et de l'audio associés en bloc de N secondes
    L'enregistrement doit consommer le moins de CPU et RAM possible

## Outil de classification d'une session d'enregistrement:
    Permet de classifier les sessions d'enregistrement du module de retranscription. Il commencera par convertir les sessions qui ont été enregistrés avec comme objectif d'écrire le plus vite possible, en quelque chose de structuré pour pouvoir lire et annoter les sessions de manière performante
    - A classifier (la catégorie par défaut)
    - Publicité
    - Radio
    - Impossible à déterminer

