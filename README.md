# 🏭 Factory de vérification QC — Wenov

Page web + worker de vérification qualité pour les livrables clients (design, vidéo, motion design).
L'utilisateur colle un lien Frame.io → le système télécharge, transcrit, contrôle la technique,
puis **publie automatiquement les corrections en commentaires Frame.io**.

## Fonctionnalités

- Écran d'accès par code (vérifié **côté serveur**, session signée)
- Sélection du client (liste) ou « Autre (nouveau client) »
- Lien Frame.io + type de livrable (Design / Vidéo / Motion design)
- Jauge de progression par job (temps écoulé / estimé / restant)
- États animés par phase : résolution du lien → téléchargement → transcription → analyse → publication → rapport
- Section « Terminées » : lien Frame.io, rapport, nombre de commentaires
- Ordonnanceur intelligent : vidéos/motion = 1 à la fois (CPU), designs = jusqu'à 2 en parallèle
- Résolution des liens Frame.io limitée aux assets **réellement partagés** (jamais le dossier parent)
- Contrôle technique vidéo : codec, résolution, fps, audio (crêtes dB, silences > 3 s, écrêtage)
- Publication réelle des commentaires via l'API Frame.io v4

## Démarrage local

```bash
cp .env.example .env
# Renseigner FRAMEIO_TOKEN (token développeur : https://developer.frame.io/)
pip install -r requirements.txt
bash start.sh
# → http://localhost:5057
```

Le `start.sh` lance le worker (`worker.py`) en arrière-plan puis le serveur web (gunicorn).

## Déploiement sur Render (recommandé)

1. Pousser ce dépôt sur GitHub.
2. Sur [render.com](https://render.com) : **New → Blueprint** → sélectionner le dépôt.
   Le fichier `render.yaml` configure tout (service Docker + disque persistant).
3. Dans l'onglet **Environment** du service, renseigner :
   - `FRAMEIO_TOKEN` — token développeur Frame.io (jamais commité !)
   - `ACCESS_CODE` — code d'accès de l'équipe (défaut : `wenov`)
   - `FLASK_SECRET` — généré automatiquement par Render
4. Déployer. L'URL publique `https://factory-qc.onrender.com` est partageable à l'équipe.

> ⚠️ **Note** : sur l'offre gratuite de Render, le service s'endort après inactivité
> (~30 s de réveil au premier accès) et le disque est éphémère. L'offre **Starter**
> (~7 $/mois) donne un service 24/7 + disque persistant de 10 Go.

## Variables d'environnement

| Variable | Défaut | Description |
|---|---|---|
| `ACCESS_CODE` | `wenov` | Code d'accès de la page |
| `FLASK_SECRET` | — | Clé de signature des sessions (**obligatoire en prod**) |
| `FRAMEIO_TOKEN` | — | Token développeur Frame.io (**obligatoire**) |
| `FRAMEIO_ACCOUNT_ID` | `4516c658-…` | Compte Frame.io |
| `WHISPER_MODEL` | `small` | Modèle faster-whisper (`tiny`/`base`/`small`/`medium`) |
| `PORT` | `5057` | Port d'écoute |

## Obtenir un token Frame.io

1. Aller sur https://developer.frame.io/ et se connecter avec le compte Wenov.
2. Créer un **Developer Token** avec les droits sur le compte.
3. Le coller dans `FRAMEIO_TOKEN` (variable d'environnement Render ou `.env` local).

## Sécurité

- Le code d'accès est vérifié **côté serveur** (`/api/code`), session signée `HttpOnly`.
- Les statuts d'approbation Frame.io ne sont **jamais** modifiés — seuls des commentaires sont publiés.
- Ne jamais committer `.env` ni aucun token : utiliser les variables d'environnement de l'hébergeur.

## Structure

```
app.py               Serveur Flask (page + API)
worker.py            Worker : file de jobs + ordonnanceur + traitement
controle_technique.py  Contrôle technique audio/vidéo (ffmpeg + numpy)
templates/index.html Interface (jauge, états animés, terminées)
clients.json         Liste des clients
regles/              Règles de vérification (miroir local)
queue/               Jobs en attente/en cours (runtime)
results/             Résultats + rapports (runtime)
work/                Fichiers temporaires de traitement (runtime)
```
