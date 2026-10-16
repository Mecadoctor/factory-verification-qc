# Factorie — Videos et sous titres

> **MIROIR LOCAL** — source de vérité : Drive (dossier Règles QC). Ne pas modifier ici ; modifier dans le Drive puis resynchroniser.
Version : 1.0.0 | Date : 2026-10-01 | Portée : globale Wenov

Source : consignes Wenov de cette conversation. Les dispositions opérationnelles sur les limites, conflits et analyses incomplètes explicitent le fonctionnement.

## SUB-001 — Cadence imposée

**Gravité par défaut :** MAJEUR | **Bloquant par défaut :** oui

Produire exactement une capture par seconde, aux temps 0, 1, 2… strictement inférieurs à la durée. Pour D secondes : ceil(D) captures ; 30 secondes = 30 captures. Conserver les timecodes et définir l’arrondi utilisé pour les durées non entières.

## SUB-002 — Limite de couverture

**Gravité par défaut :** MAJEUR | **Bloquant par défaut :** oui

Une capture par seconde peut manquer un élément affiché entre deux captures. Déclarer cette limite dans le rapport et ne pas prétendre avoir vérifié toutes les images. Si une vérification supplémentaire est nécessaire, demander une dérogation à la cadence imposée.

## SUB-003 — Analyse des captures

**Gravité par défaut :** MAJEUR | **Bloquant par défaut :** oui

Sur chaque capture analyser textes, sous-titres, logo, couleurs, polices, placement, CTA, faits et mentions selon les familles applicables.

## SUB-004 — Transcription intégrale

**Gravité par défaut :** MAJEUR | **Bloquant par défaut :** oui

Transcrire les paroles avec repères temporels. L’audio sert ici à identifier les mots ; qualité, mixage, musique et niveau sonore sont hors périmètre de cette famille.

## SUB-005 — Écrit impeccable (FR/EN)

**Gravité par défaut :** MAJEUR | **Bloquant par défaut :** oui

Le sous-titre doit être un français (ou un anglais) écrit impeccable : orthographe, grammaire, accords, typographie — **même si l'audio contient une faute**. Corriger les fautes de l'oral à l'écrit. Rester aligné sur le sens et le découpage temporel de l'audio ; seule la forme écrite est normalisée.

## SUB-006 — Contexte limité

**Gravité par défaut :** MAJEUR | **Bloquant par défaut :** oui

Utiliser contexte, phrases voisines, secteur et base client pour identifier un mot ambigu, jamais pour accepter une reformulation différente.

## SUB-007 — Mot incertain

**Gravité par défaut :** MAJEUR | **Bloquant par défaut :** oui

Réécouter, consulter les références et rechercher au besoin. Si le mot reste incertain : À VÉRIFIER avec segment audio et timecode, aucune correction inventée.

## SUB-008 — Hésitations

**Gravité par défaut :** MINEUR | **Bloquant par défaut :** non

Appliquer la règle client sur euh, répétitions et faux départs. Sans règle, identifier la différence sans automatiquement classer leur omission comme critique.

## SUB-009 — Retours à la ligne

**Gravité par défaut :** MAJEUR | **Bloquant par défaut :** oui

Reconstruire le texte sur plusieurs lignes et les sous-titres successifs. Comparer les mots indépendamment des retours à la ligne.

## SUB-010 — Relecture du sous-titre comme texte écrit

**Gravité par défaut :** MINEUR | **Bloquant par défaut :** non

Relire le sous-titre comme un texte écrit autonome : accents, traits d'union, apostrophes typographiques, espaces insécables, ponctuation.

## SUB-011 — Évolution et doublons

**Gravité par défaut :** MINEUR | **Bloquant par défaut :** non

Suivre texte identique, modifié, nouveau et disparu. Fusionner une même anomalie continue ; conserver des occurrences séparées si elle réapparaît. Ne pas inventer un début/une fin exacts entre captures.

## SUB-012 — Preuve vidéo

**Gravité par défaut :** MAJEUR | **Bloquant par défaut :** oui

Chaque anomalie doit fournir timecode observé, capture, transcription, sous-titre, mot problématique, type d’écart, correction, source et confiance.
