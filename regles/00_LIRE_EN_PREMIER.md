# Factory de vérification — LIRE EN PREMIER

> **Source de vérité : ce dossier Drive.** Les copies locales (`~/workspace/qc-subs/regles/`) sont des miroirs de repli — ne pas les modifier ; modifier ici puis resynchroniser.
**Version :** 3.0.0 | **Date :** 2026-10-16 | **Portée :** globale Wenov

## La factory v3 (depuis le 2026-10-16)

**Une seule page HTML, deux pipelines.** La personne qui dépose un contrôle choisit d'abord
**🎨 DESIGN** ou **🎬 VIDÉO**, puis colle le lien Frame.io. Chaque pipeline applique son propre
paquet de règles — parce qu'un visuel statique et une vidéo n'ont pas les mêmes spécificités.

| Fichier | Contenu | Pipeline |
|---|---|---|
| `REGLES_COMMUNES.md` | Principes, priorité des sources, verdicts, commentaires Frame.io, traçabilité, dossiers clients, maintenance | DESIGN + VIDÉO |
| `REGLES_DESIGN.md` | Textes et langue (LANG-001 à 010), identité visuelle, composition, lisibilité, format et zones sûres, qualité d'image, CTA | DESIGN |
| `REGLES_VIDEO.md` | Transcription, sous-titres (SUB-001 à 012), textes à l'écran, contrôle technique audio/vidéo, fin sur CTA | VIDÉO |
| `09_Modele_rapport.md` | Modèle du rapport de contrôle | DESIGN + VIDÉO |

## Dossiers clients (Drive)

Chaque client a son dossier Drive (renseigné dans `clients.json` de la page) :
`01_Regles_Client` (règles spécifiques), `02_Charte_Graphique`, `03_Logos`, `04_Polices`,
`05_Assets`, `06_Contenus_Approuves`, `07_Campagnes`.
Dès qu'un client est sélectionné sur la page, ses règles, sa charte et ses visuels sont
contrôlés **au même niveau d'exigence** que les règles globales. Sans client : ces dimensions
sont marquées « non applicable », jamais supposées.

## Ce qui a changé en v3

- **Fin de WenovTime** : la surveillance WenovTime est désactivée et son code archivé
  (`archives/wenovtime_qc-20261016`). La page HTML est la seule entrée de la factory.
- **Fin du mode « motion »** : deux choix uniquement, DESIGN ou VIDÉO
  (un ancien dépôt « motion » est traité comme VIDÉO).
- **Règles séparées par pipeline** : `REGLES_DESIGN.md` et `REGLES_VIDEO.md` remplacent
  l'ancien fichier unique. Les anciens fichiers (v1/v2, dont `REGLES_FINALES.md`,
  `02_Textes_et_langues.md`, `03_Videos_et_sous_titres.md`) sont conservés dans
  `ARCHIVES_v2/` — ils ne sont plus actifs.
- **Pas de brief sur la page** : la conformité au brief est toujours « non applicable ».
  Tout le reste s'applique.

## Standard de validation

**Prêt à être livré au client. Zéro faute en français ET en anglais. Aucune erreur ne passe.**

## Avant chaque analyse (rappel moteur)

1. Confirmer pipeline (DESIGN ou VIDÉO), client, langue, média, destination, version du fichier.
2. Charger `REGLES_COMMUNES.md` + le fichier du pipeline + les règles du dossier Drive client
   (si client identifié). Charger les familles applicables en entier.
3. En cas de contradiction entre sources : signaler et demander une validation humaine.
   Ne jamais inventer, ne jamais choisir arbitrairement.
4. Une analyse incomplète ou une incertitude essentielle bloque — elle ne peut recevoir VALIDÉ.

## Maintenance

1. Modifier la règle dans le Drive (jamais la copie locale).
2. Incrémenter la version en tête du fichier.
3. Faire valider par le responsable Wenov — **veto absolu du DG**, aucune règle ne change sans lui.
4. Tester sur un cas réel avant activation générale.
5. Resynchroniser les miroirs locaux.
