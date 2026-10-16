# RÈGLES COMMUNES — Factory de vérification Wenov

> **Source de vérité : ce dossier Drive.** Miroirs locaux : ne pas modifier ici.
**Version :** 3.0.0 | **Date :** 2026-10-16 | **Portée :** globale Wenov
**S'applique aux deux pipelines :** 🎨 DESIGN et 🎬 VIDÉO

---

## 1. PRINCIPE FONDAMENTAL

**RÈGLES CLIENT + DRIVE + FRAME.IO + CONTRÔLE COMPLET = DÉCISION QUALITÉ.**

Workflow permanent :
**DÉTECTER → COMPRENDRE → VÉRIFIER → COMMENTER → REVÉRIFIER → DÉCIDER → RÉVISION OU VALIDATION.**

Standard de validation : **prêt à être livré au client. Zéro faute en français ET en anglais.
Aucune erreur ne passe.** Pas de « suffisamment bon ».

Ne jamais présenter un livrable client comme produit par l'IA.

---

## 2. PRIORITÉ DES SOURCES (ordre de référence)

1. Demandes explicites liées à la tâche actuelle
2. Règles et documentation officielles du client dans son dossier Drive
3. Assets officiels du client
4. Standards professionnels Wenov (ce dossier : `REGLES_COMMUNES.md` + fichier du pipeline)

**En cas de contradiction :** ne pas inventer, ne pas choisir arbitrairement.
Signaler : *« Contradiction détectée entre les références — vérification humaine nécessaire. »*

**Note — pas de brief sur la page :** l'entrée unique de la factory est la page HTML,
où aucun brief n'est fourni. La conformité au brief est donc **toujours « non applicable »**.
C'est la seule dimension qui disparaît ; tout le reste s'applique.

---

## 3. PÉRIMÈTRE SELON LE CLIENT

- **Client identifié** (sélectionné sur la page, dossier Drive trouvé) :
  règles Drive client, charte, logos, polices, assets et visuels **vérifiés au même niveau
  d'exigence** que les règles globales.
- **Client identifié mais dossier introuvable** : marquer « non applicable — dossier
  client introuvable », jamais supposé.
- **Aucun client** (dépôt rapide) : règles client et branding marqués « non applicable —
  aucun client ». Standards professionnels génériques uniquement — un logo ou une couleur
  ne sont jamais « validés » par défaut.
- **Anti faux positifs renforcé** : sans brief ni règle client, un choix créatif non
  documenté (ton, mise en page, formulation) n'est jamais signalé comme une erreur.

---

## 4. COMMENTAIRES FRAME.IO (directive permanente du DG)

Les commentaires Frame.io **sont l'output du contrôle** — ils sont publiés
**automatiquement, sans demander de feu vert**.

- **Vidéo** : commentaire au timecode précis. **Image** : commentaire sans timestamp.
- Clairs, précis, exploitables, professionnels, concis, sans ambiguïté.
- Format : `00:08 — Corriger 'X' en 'Y'.` Ne jamais dire simplement « À corriger ».
- Si tout est valide : **un seul commentaire `PARFAIT !`**.
- **Ne jamais modifier les statuts d'approbation Frame.io.**
- Identité d'affichage : **Soufiane** (`soufiane@wenov.ca`).
- Commentaires automatiques autorisés UNIQUEMENT pour les fichiers soumis via la factory.

---

## 5. RÈGLES DE DÉCISION

### VALIDÉ (périmètre restreint) — tous les critères
- [ ] Règles client respectées *(si client identifié, sinon « non applicable »)*
- [ ] Charte graphique respectée *(si dossier client, sinon standards génériques uniquement)*
- [ ] Assets corrects
- [ ] Orthographe et grammaire parfaites (FR et EN)
- [ ] Contraintes techniques OK
- [ ] Aucune information erronée
- [ ] Conformité au brief : toujours « non applicable — aucun brief fourni » (signalé)

« VALIDÉ (périmètre restreint) » signifie : rien d'anormal détecté sur les dimensions
vérifiables — la conformité au brief reste à confirmer par un humain.

### RÉVISION (si au moins un)
- Faute d'orthographe ou de grammaire (même une seule)
- Information erronée
- Mauvais logo / couleur non conforme / CTA incorrect
- Élément non conforme aux règles client
- Défaut technique visible
- Incohérence dégradant la qualité

### BLOQUÉ
- Information ou accès manquant (Frame.io, Drive)
- Contradiction entre sources sans résolution possible
- Lien Frame.io illisible ou partage vide
- **Ne jamais valider par défaut en cas de blocage**

### Anti faux positifs
Une correction doit être justifiée par : règles client, charte, asset de référence,
langue/grammaire, problème technique, incohérence objective, ou qualité manifestement
insuffisante. **Jamais une préférence personnelle.**

### Ne pas inventer
Si la solution dépend d'une décision créative/commerciale non documentée : expliquer le
problème et demander confirmation. Ne pas créer de nouvelle règle.

### Nouvelle version
Chaque nouvelle version = **contrôle intégral** (anciennes corrections appliquées ?
nouvelles erreurs introduites ?), jamais seulement les points corrigés.

---

## 6. DOSSIERS CLIENTS — STRUCTURE ATTENDUE

Dans le dossier Drive de chaque client :
- `01_Regles_Client` — règles spécifiques (interdits, mentions obligatoires, formulations)
- `02_Charte_Graphique` — guide officiel (couleurs hex, typographies, usages)
- `03_Logos` — fichiers sources officiels (jamais de logo régénéré/approximatif)
- `04_Polices` — fichiers de polices autorisées
- `05_Assets` — visuels, photos, éléments officiels
- `06_Contenus_Approuves` — exemples validés (référence de ton et de style)
- `07_Campagnes` — règles par campagne

Un document modèle vide n'est jamais une règle active.

---

## 7. TRAÇABILITÉ (par contrôle)

Conserver : pipeline (DESIGN/VIDÉO), client, version, lien Frame.io, date/heure,
fichiers de règles appliqués (+ versions), anomalies détectées, décision,
temps estimé, statut final, historique des révisions.

**Sauvegarde :** chaque rapport est copié automatiquement dans le dossier Drive
« Factory QC — Rapports » à la fin du contrôle (le Drive survit aux redémarrages).

Format de décision interne :
```
PIPELINE : DESIGN | VIDÉO
CLIENT : [nom] | VERSION : [n]
FRAME.IO : [lien]
RÈGLES : REGLES_COMMUNES vX + REGLES_DESIGN|VIDEO vY (+ règles client)
RÉSULTAT : VALIDÉ (périmètre restreint) / RÉVISION / BLOQUÉ
CORRECTIONS : [nombre + principales]
TEMPS ESTIMÉ : [durée]
PROCHAINE ACTION : [Surveillance / Terminé / Intervention humaine]
```

---

## 8. LIMITES CONNUES (ne pas masquer)

- Comparaison audio ↔ OCR ↔ textes : automatisée pour la détection, vérification fine par Muse
- Détection des éléments visuels parasites : partielle
- Synchronisation A/V fine et défauts visuels subtils : contrôle manuel
- OAuth Adobe requis pour Frame.io v4 (autorisation unique)
- Ne pas prétendre à une vérification exhaustive si ces points ne sont pas couverts

---

## 9. MAINTENANCE

1. Éditer la section correspondante dans le Drive
2. Incrémenter la version en tête du document
3. Faire valider par le responsable Wenov (**veto absolu du DG**)
4. Tester sur un cas réel avant activation générale
5. Resynchroniser les miroirs locaux

### Historique des versions
- v1.0.0 (2026-10-01) : règles initiales LANG + SUB (ancien fichier unique)
- v2.1.0 (2026-10-07) : SUB-005 inversée (écrit impeccable même si l'audio est fautif) ; anglicismes corrigés en sous-titrage ; Drive client = seule source branding
- v2.2.x (2026-10-07) : deux modes d'entrée (WenovTime / page HTML) ; sauvegarde auto des rapports dans Drive
- **v3.0.0 (2026-10-16) : fin de WenovTime (page HTML = seule entrée) ; règles séparées par pipeline (`REGLES_DESIGN.md` / `REGLES_VIDEO.md`) ; ce fichier devient le socle commun ; fin du mode « motion »**
