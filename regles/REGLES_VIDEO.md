# RÈGLES VIDÉO — Pipeline 🎬 VIDÉO

> **Source de vérité : ce dossier Drive.** Miroirs locaux : ne pas modifier ici.
**Version :** 3.0.0 | **Date :** 2026-10-16 | **Portée :** globale Wenov
**S'applique avec :** `REGLES_COMMUNES.md` (principes, verdicts, commentaires, traçabilité)

**Périmètre :** tous les fichiers vidéo du partage Frame.io.
Chaque vidéo est contrôlée **intégralement** (transcription complète + 1 capture/seconde).

---

## V-01 — TRANSCRIPTION INTÉGRALE (SUB-004)

Transcription intégrale de l'audio avec repères temporels (faster-whisper, langue FR
sauf livrable anglais). La transcription sert à identifier les mots ; elle est conservée
avec le rapport.

## V-02 — CADENCE OCR ET LIMITE DE COUVERTURE (SUB-001, SUB-002)

- **Une capture par seconde** (0, 1, 2… < durée), timecodes conservés.
- **Limite déclarée dans le rapport** : une capture/seconde peut manquer un élément
  affiché entre deux captures. Ne jamais prétendre avoir tout vérifié.
- OCR en haute qualité (1080p) ; filtrer les fragments de logo/URL.

## V-03 — TEXTES À L'ÉCRAN (SUB-003)

Sur chaque capture : analyser textes, sous-titres, logo, couleurs, polices, placement,
CTA, faits, mentions. Appliquer **D-01 (LANG-001 à 010)** à tous les textes incrustés
et **D-02 à D-08** aux frames clés (ouverture, frames de titre, frame de fin/CTA).

## V-04 — ÉCRIT IMPECCABLE (SUB-005) — décision DG permanente

Les titres, sous-titres et textes incrustés doivent être un français (ou un anglais)
**écrit impeccable** : orthographe, grammaire, accords, typographie — **même si l'audio
contient une faute**. Corriger les fautes de l'oral à l'écrit. Rester aligné sur le sens
et le découpage temporel de l'audio ; seule la forme écrite est normalisée.
**Anglicismes** : corrigés aussi à l'écrit (LANG-007), sauf marque/terme autorisé.

## V-05 — COHÉRENCE AUDIO ↔ TEXTE (SUB-006, SUB-007, SUB-009)

- Comparer la transcription et les textes incrustés ; reconstruire le texte sur
  plusieurs sous-titres successifs avant comparaison (retours à la ligne ignorés).
- Mot ambigu : utiliser le contexte pour l'identifier, jamais pour accepter une
  reformulation différente.
- Mot incertain : réécouter, consulter les références. Si incertain : marquer
  **À VÉRIFIER** avec segment audio + timecode. **Ne rien inventer.**
- Hésitations (euh, répétitions) : appliquer la règle client ; sans règle, signaler
  sans classer critique.

## V-06 — CONTRÔLE TECHNIQUE (automatique via `controle_technique.py`)

- **Vidéo** : codec H.264 (`yuv420p`), `faststart` activé pour le web ; résolution =
  celle promise (ex. 1080×1920 pour un reel) ; fps constant (pas de 29,97/30 mélangés) ;
  durée conforme (±1 s) et au format plateforme.
- **Audio** : codec AAC, 48 kHz, stéréo (ou mono si voulu) ; présence d'une piste.
- **Niveaux** : crête > −1 dB → **ALERTE** (écrêtage) ; niveau moyen < −30 dB → **ALERTE**
  (niveau très faible) ; pas de saturation.
- **Silences** : plage silencieuse > 3 secondes → **ALERTE** ; silence > 0,5 s en
  ouverture/fermeture → point à signaler ; pas de coupure brutale du son.
- **Fichier** : poids cohérent avec durée et résolution ; le fichier se lit normalement
  du début à la fin (pas de frame noire figée, pas de freeze).
- Les alertes sont publiées comme commentaires Frame.io horodatés + fiche dans le rapport.

## V-07 — CONTRÔLES VISUELS

Coupures, frames noires, glitchs, détourage, overlays, synchronisation A/V,
sous-titres décalés, texte coupé, bandes noires parasites, filigrane d'outil,
timecode incrusté oublié, transitions propres (pas de saut de cut non voulu).

## V-08 — FIN SUR CTA

La vidéo **se termine par un visuel CTA** quand la grille client l'exige :
URL/QR lisibles, affichés assez longtemps (TV : ≥ 8 s).
Appliquer D-05 (zones sûres) et D-08 (CTA et mentions) à la frame de fin.

## V-09 — MENTIONS LÉGALES

Présentes si requises, lisibles, affichées assez longtemps pour être lues,
jamais dans une zone masquée.

## V-10 — PREUVE (chaque anomalie, SUB-012)

Timecode observé + capture + transcription + texte à l'écran + mot problématique +
type d'écart + correction proposée + source (règle, charte, référence) +
confiance (élevée/moyenne/faible) + gravité.

## LIMITES (à déclarer, jamais masquer)

- L'échantillonnage à 1 image/seconde ne remplace pas un visionnage intégral :
  un défaut bref entre deux captures peut passer — le signaler dans le rapport.
- La synchronisation labiale et la fluidité du mouvement ne sont pas évaluées de
  façon fiable : réservées à l'œil humain (validation finale).
- Sur proxy basse résolution, les mesures de netteté et de hex sont indicatives.
