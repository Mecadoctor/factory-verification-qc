# RÈGLES FINALES — Factory de Contrôle Qualité Wenov

> **MIROIR LOCAL** — source de vérité : Drive (dossier Règles QC). Ne pas modifier ici ; modifier dans le Drive puis resynchroniser.
**Version :** 2.2.2 | **Date :** 2026-10-07 | **Portée :** globale Wenov

Ce document est la **référence unique** des règles appliquées par l'agent de contrôle qualité.
Il consolide : les règles linguistiques (LANG), les règles vidéo/sous-titres (SUB),
le contrôle technique, le branding, le workflow WenovTime et les règles de décision.

**Maintenance :** pour modifier une règle, éditez la section correspondante ci-dessous,
incrémentez la version, et faites valider par le responsable Wenov avant activation.
Ne modifiez jamais les règles sans validation humaine (veto absolu du DG).

---

## 1. PRINCIPE FONDAMENTAL

**BRIEF + RÈGLES CLIENT + DRIVE + FRAME.IO + CONTRÔLE COMPLET = DÉCISION QUALITÉ.**

Workflow permanent :
**DÉTECTER → COMPRENDRE → VÉRIFIER → COMMENTER → REVÉRIFIER → DÉCIDER → RÉVISION OU VALIDATION → SURVEILLER → RECOMMENCER JUSQU'À VALIDATION.**

Standard de validation : **prêt à être livré au client.** Pas de "suffisamment bon".

---

## 2. PRIORITÉ DES SOURCES (ordre de référence)

1. Instruction spécifique et récente dans le brief actuel
2. Demandes explicites liées à la tâche actuelle
3. Règles et documentation officielles du client dans Drive
4. Assets officiels du client
5. Standards professionnels Wenov (ce document)

**En cas de contradiction :** ne pas inventer, ne pas choisir arbitrairement.
Signaler : *"Contradiction détectée entre les références client — vérification humaine nécessaire."*

**Note mode sans brief :** en entrée « page HTML » (mode B, §8bis), la priorité n°1 est absente
(pas de brief) et la n°3 ne s'applique que si un client est identifié (sélection sur la page).
Les dimensions sans source disponible sont marquées « non applicable » — jamais supposées.

---

## 3. RÈGLES LINGUISTIQUES (LANG-001 à LANG-010)

| ID | Règle | Gravité | Bloquant |
|----|-------|---------|----------|
| LANG-001 | Extraire TOUS les textes visibles (titres, CTA, sous-titres, prix, dates, mentions, coordonnées, URLs, textes incrustés). Texte illisible : localiser et signaler. | MAJEUR | Oui |
| LANG-002 | Identifier langue et variante par bloc. Un texte anglais n'est pas une faute dans un livrable anglais. | MAJEUR | Oui |
| LANG-003 | **Orthographe** : accents, apostrophes, lettres manquantes/ajoutées, homophones, traits d'union, pluriels, capitalisation. | MAJEUR | Oui |
| LANG-004 | **Grammaire** : genre, nombre, déterminants, pronoms, prépositions, syntaxe, accords sujet-verbe, participes passés. | MAJEUR | Oui |
| LANG-005 | **Conjugaison** : temps, infinitif, participe, auxiliaires, concordance. Ne pas reformuler arbitrairement. | MAJEUR | Oui |
| LANG-006 | Ponctuation et espaces : signes, guillemets, parenthèses, espaces doubles/absentes selon la langue. | MINEUR | Non |
| LANG-007 | **Anglicismes** : aucun dans les textes français créés par Wenov, sauf nom officiel/marque/terme autorisé. En sous-titrage aussi : corriger l'anglicisme en français propre. | MAJEUR | Oui |
| LANG-008 | Termes techniques : vérifier dans la base client puis sources officielles. Ressemblance phonétique insuffisante. | MAJEUR | Oui |
| LANG-009 | Noms propres : vérifier dans références officielles. Respecter exactement l'écriture confirmée. | MAJEUR | Oui |
| LANG-010 | **Forme vs sens** : distinguer correction linguistique et changement de sens. Ne jamais transformer une donnée factuelle sans source. | MAJEUR | Oui |

**Règle DG (permanente) :** zéro faute en français ET en anglais sur tout livrable client. Vérification obligatoire avant livraison. Ne jamais présenter un livrable comme produit par l'IA.

---

## 4. RÈGLES VIDÉO ET SOUS-TITRES (SUB-001 à SUB-012)

| ID | Règle | Gravité | Bloquant |
|----|-------|---------|----------|
| SUB-001 | **Cadence** : une capture par seconde (0, 1, 2… < durée). Conserver timecodes. | MAJEUR | Oui |
| SUB-002 | **Limite de couverture** : déclarer qu'une capture/seconde peut manquer des éléments inter-captures. Ne pas prétendre avoir tout vérifié. | MAJEUR | Oui |
| SUB-003 | Sur chaque capture : analyser textes, sous-titres, logo, couleurs, polices, placement, CTA, faits, mentions. | MAJEUR | Oui |
| SUB-004 | **Transcription intégrale** de l'audio avec repères temporels (faster-whisper). | MAJEUR | Oui |
| SUB-005 | **Écrit impeccable (FR/EN)** : le sous-titre doit être clean et sans faute (orthographe, grammaire, accords, typographie), **même si l'audio contient une faute** — corriger les fautes de l'oral à l'écrit. Rester aligné sur le sens et le découpage de l'audio ; seule la forme écrite est normalisée. | MAJEUR | Oui |
| SUB-006 | Utiliser le contexte pour identifier un mot ambigu, jamais pour accepter une reformulation. | MAJEUR | Oui |
| SUB-007 | Mot incertain : réécouter, consulter références. Si incertain : marquer À VÉRIFIER, ne rien inventer. | MAJEUR | Oui |
| SUB-008 | Hésitations (euh, répétitions) : appliquer règle client ; sans règle, signaler sans classer critique. | MINEUR | Non |
| SUB-009 | Reconstruire le texte sur plusieurs lignes/sous-titres successifs avant comparaison. | MAJEUR | Oui |
| SUB-010 | Relire le sous-titre comme un texte écrit autonome : accents, traits d'union, apostrophes typographiques, espaces insécables, ponctuation. | MINEUR | Non |
| SUB-011 | Suivre l'évolution du texte (identique/modifié/nouveau/disparu). Fusionner les anomalies continues. | MINEUR | Non |
| SUB-012 | **Preuve** : chaque anomalie = timecode + capture + transcription + sous-titre + mot + type d'écart + correction + source + confiance. | MAJEUR | Oui |

**OCR** : utiliser la haute qualité (1080p). L'OCR 180p est inexploitable. Filtrer les fragments de logo/URL.

---

## 5. CONTRÔLE TECHNIQUE VIDÉO

Vérifié automatiquement par `controle_technique.py` :

- **Vidéo** : codec, résolution, cadence (fps), débit, durée
- **Audio** : codec, canaux (mono/stéréo), fréquence d'échantillonnage
- **Niveaux** : crête dB, RMS dB
  - Écrêtage si crête > -1 dB → ALERTE
  - Niveau très faible si < -30 dB → ALERTE
- **Silences** : plage silencieuse > 3 secondes → ALERTE
- Les alertes sont publiées comme commentaires Frame.io horodatés + fiche dans le rapport

**Contrôles visuels** (manuel/Muse) : coupures, frames noires, glitchs, détourage,
overlays, synchronisation A/V, sous-titres décalés, texte coupé, safe zone,
résolution, pixellisation, qualité des assets.

---

## 6. CONTRÔLE BRANDING

Comparer systématiquement avec le dossier Drive client :

- [ ] Bon logo, bonne variante (jamais de logo régénéré/approximatif)
- [ ] Couleurs conformes (codes hex exacts)
- [ ] Typographies conformes (familles et graisses autorisées)
- [ ] Tailles, marges, alignements, proportions, positionnement
- [ ] Lisibilité, zones de sécurité respectées
- [ ] Cohérence graphique globale, style animations/transitions
- [ ] Utilisation correcte des assets officiels

**Sources branding** : dossier Drive client (source de vérité).

Détecter aussi les écarts subtils, pas seulement les erreurs flagrantes.

---

## 7. CONTRÔLE DU BRIEF

- Est-ce exactement ce qui a été demandé ?
- Tous les éléments demandés sont-ils présents ?
- Un élément important manque-t-il ?
- Un élément non demandé a-t-il été ajouté ?
- Message principal correctement communiqué ?
- CTA correct et conforme ?
- Format et plateforme de destination corrects ?
- Bon produit/service présenté ?

**Une production visuellement réussie mais non conforme au brief → RÉVISION.**

---

## 8. WORKFLOW WENOVTIME (déclencheur et boucle)

### Déclencheur
Surveiller en permanence les nouvelles tâches WenovTime nécessitant validation.
Chaque nouveau lien de production déposé = nouvelle version à contrôler.
**Chaque nouvelle version doit être vérifiée à nouveau** (jamais réutiliser une ancienne vérification).

### Identification
Récupérer : client, projet, tâche, responsable, brief, deadline, format,
plateforme, lien Frame.io, instructions particulières.

### Boucle de contrôle obligatoire
```
Nouvelle soumission
→ identifier client → lire brief → consulter Drive → ouvrir Frame.io
→ vérifier (global + frame par frame) → commenter erreurs
→ vérification finale complète → DÉCISION
    → VALIDÉ : commentaire "PARFAIT !" sur Frame.io + valider dans WenovTime
    → RÉVISION : commentaires Frame.io + fiche WenovTime (corrections + temps estimé + lien)
                + email compte rendu + surveiller nouvelle version → RECOMMENCER
```

### Champs révision WenovTime (obligatoires)
1. **Corrections** : liste organisée avec timecodes (ex. "00:08 — Corriger '...' en '...'")
   + terminer par : *"Voir le lien Frame.io pour les commentaires détaillés et les timecodes."*
2. **Temps estimé** : estimation réaliste (15 min, 30 min, 1h, 2h…)
3. **Liens** : lien Frame.io de la production contrôlée (vérifié)

### Email de compte rendu (après chaque révision)
**À** : ads@wenov.ca, imane@wenov.ca, soufiane@wenov.ca
**Objet** : *Contrôle qualité — [Client] — [Tâche] — Révision demandée*
**Contenu** : client, tâche, responsable, statut, corrections principales,
temps estimé, lien Frame.io, confirmation du statut WenovTime.

### Nouvelle version
Revérifier ENTIÈREMENT (pas seulement les points corrigés) :
anciennes corrections appliquées ? nouvelles erreurs introduites ?
vérification globale complète.

---

## 8bis. DEUX MODES D'ENTRÉE (même traitement, périmètre différent)

La factory accepte **deux entrées** qui déclenchent le **même pipeline technique**
(téléchargement → transcription/OCR → contrôle technique → analyse → commentaires
Frame.io horodatés). Seul le **périmètre vérifiable** change, selon la présence d'un brief.

### Mode A — WenovTime (AVEC brief) : contrôle COMPLET

- Sources : brief + règles client Drive + assets client + le présent document.
- Toutes les dimensions sont vérifiées : langue (§3), vidéo/sous-titres (§4),
  technique (§5), branding client (§6), conformité au brief (§7).
- Verdicts §10 applicables intégralement.

### Mode B — Page HTML (SANS brief) : contrôle sans brief, pas sans client

Quelqu'un colle un lien Frame.io sur la page. Il n'y a jamais de brief sur cette
entrée — mais **tout le reste s'applique** dès qu'un client est identifié.

- **Toujours VÉRIFIÉS** : contrôle technique (§5), langue (§3 LANG + §4 SUB —
  dont SUB-005 : écrit impeccable même si l'audio est fautif), règles globales Wenov.
- **Si un client est identifié** (sélectionné sur la page) :
  - **Règles Drive client : vérifiées** (dossier client consulté, comme en mode A) ;
  - **Branding et visuels client : vérifiés** contre la charte et les assets du dossier client ;
  - si le dossier client est introuvable : marquer « non applicable — dossier client
    introuvable », jamais supposé.
- **Si aucun client n'est identifié** : règles client et branding marqués
  « non applicable — aucun client » (standards professionnels génériques uniquement —
  un logo ou une couleur ne sont jamais « validés » par défaut).
- **Conformité au brief (§7 entier) : TOUJOURS « non applicable — aucun brief fourni »**,
  même avec client identifié. C'est la seule dimension qui disparaît en mode B.
- Le rapport et la page affichent le **mode d'entrée** et la **liste des dimensions
  non couvertes**.
- Verdict : **VALIDÉ (périmètre restreint)** / RÉVISION / BLOQUÉ.
  « VALIDÉ (périmètre restreint) » signifie : rien d'anormal détecté sur les
  dimensions vérifiables — la conformité au brief reste à confirmer par un humain.
- **Anti faux positifs renforcé** : sans brief, un choix créatif non documenté
  (ton, mise en page, formulation) n'est jamais signalé comme une erreur.

### Règles communes aux deux modes

- Même pipeline, mêmes commentaires Frame.io horodatés, même exigence zéro faute.
- Commentaires automatiques autorisés UNIQUEMENT pour les fichiers soumis via la factory (§9).
- Chaque nouvelle version = contrôle intégral, quel que soit le mode.
- Traçabilité §11 avec le **mode d'entrée indiqué** (A ou B).

---

## 9. COMMENTAIRES FRAME.IO

- Positionnés au timecode/frame le plus précis possible
- Clairs, précis, exploitables, professionnels, concis, sans ambiguïté
- Format : `"00:08 — Corriger 'X' en 'Y'."`
- Ne jamais dire simplement "À corriger" — expliquer exactement quoi faire
- Si VALIDÉ : un seul commentaire `"PARFAIT !"`
- **Ne jamais modifier les statuts d'approbation Frame.io**
- Les commentaires automatiques sont autorisés UNIQUEMENT pour les fichiers soumis via la factory

---

## 10. RÈGLES DE DÉCISION

### VALIDÉ (tous les critères)
- [ ] Brief respecté intégralement *(mode A ; en mode B : toujours « non applicable — signalé »)*
- [ ] Règles client respectées *(mode A : oui ; mode B : oui si client identifié, sinon « non applicable »)*
- [ ] Charte graphique respectée *(mode A : oui ; mode B : oui si dossier client, sinon standards génériques uniquement)*
- [ ] Assets corrects
- [ ] Orthographe et grammaire parfaites
- [ ] Contraintes techniques OK
- [ ] Aucune information erronée

### RÉVISION (si au moins un)
- Faute d'orthographe ou grammaire (même une seule)
- Information erronée
- Mauvais logo / couleur non conforme / CTA incorrect
- Élément demandé absent ou non conforme
- Défaut technique visible
- Incohérence dégradant la qualité

### BLOQUÉ
- Information ou accès manquant (WenovTime, Frame.io, Drive, brief)
- Contradiction entre sources sans résolution possible
- Lien Frame.io illisible
- **Ne jamais valider par défaut en cas de blocage**

### Anti faux positifs
Une correction doit être justifiée par : brief, règles client, charte,
asset de référence, langue/grammaire, problème technique, incohérence objective,
ou qualité manifestement insuffisante. **Jamais une préférence personnelle.**

### Ne pas inventer
Si la solution dépend d'une décision créative/commerciale non documentée :
expliquer le problème et demander confirmation. Ne pas créer de nouvelle règle.

---

## 11. TRAÇABILITÉ (par contrôle)

Conserver : tâche, client, version, lien Frame.io, date/heure,
anomalies détectées, décision, temps estimé, statut final, historique des révisions.

**Sauvegarde :** chaque rapport est copié automatiquement dans le dossier Drive
« Factory QC — Rapports » à la fin du contrôle (le Drive survit aux redémarrages
de la page). Le lien Drive du rapport est consigné dans le résultat.

Format de décision interne :
```
CLIENT : [nom] | TÂCHE : [nom] | VERSION : [n]
FRAME.IO : [lien]
RÉSULTAT : VALIDÉ / RÉVISION / BLOQUÉ
CORRECTIONS : [nombre + principales]
TEMPS ESTIMÉ : [durée]
ACTION WENOVTIME : [Validée / Révision / Bloquée]
EMAIL : [Envoyé / Non nécessaire]
PROCHAINE ACTION : [Surveillance / Terminé / Intervention humaine]
```

---

## 12. LIMITES CONNUES (ne pas masquer)

- Comparaison audio ↔ OCR ↔ sous-titres : automatisée pour la détection, vérification fine par Muse
- Détection des éléments visuels parasites : partielle
- Synchronisation A/V fine et défauts visuels subtils : contrôle manuel
- API WenovTime en lecture seule : les mises à jour de statut (Révision/Validé) passent par l'interface web
- OAuth Adobe requis pour Frame.io v4 (autorisation unique de l'utilisateur)
- Ne pas prétendre à une vérification exhaustive si ces points ne sont pas couverts

---

## 13. GUIDE DE MAINTENANCE

### Modifier une règle
1. Éditer la section correspondante dans ce fichier
2. Incrémenter la version en tête de document
3. Faire valider par le responsable Wenov (veto DG obligatoire)
4. Tester sur un cas réel avant activation générale

### Ajouter une règle client
1. Créer une section dans le dossier Drive du client (pas ici)
2. Ce document reste les règles GLOBALES ; les règles client les complètent
3. En cas de conflit : la règle client spécifique prime (priorité #3 > #5)

### Historique des versions
- v1.0.0 (2026-10-01) : règles initiales LANG + SUB
- v2.1.0 (2026-10-07) : SUB-005/SUB-010 — sous-titres en français/anglais impeccable même si l'audio a une faute (décision DG) ; LANG-007 — anglicismes corrigés aussi en sous-titrage ; priorité des sources sans « branding WenovTime » (Drive client = seule source branding)
- v2.2.0 (2026-10-07) : §8bis — deux modes d'entrée (A : WenovTime avec brief = contrôle complet ; B : page HTML sans brief = contrôle restreint, dimensions non vérifiables marquées « non applicable ») ; verdicts §10 adaptés au mode
- v2.2.1 (2026-10-07) : §8bis précisé — en mode B, les règles Drive client et le branding/visuels client s'appliquent dès qu'un client est identifié ; seul le brief reste toujours non applicable
- v2.2.2 (2026-10-07) : §11 — chaque rapport est sauvegardé automatiquement dans le dossier Drive « Factory QC — Rapports » (le Drive survit aux redémarrages de la page)
