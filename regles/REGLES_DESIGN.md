# RÈGLES DESIGN — Pipeline 🎨 DESIGN

> **Source de vérité : ce dossier Drive.** Miroirs locaux : ne pas modifier ici.
**Version :** 3.0.0 | **Date :** 2026-10-16 | **Portée :** globale Wenov
**S'applique avec :** `REGLES_COMMUNES.md` (principes, verdicts, commentaires, traçabilité)

**Périmètre :** tous les fichiers image du partage Frame.io (PNG, JPG, etc.).
Chaque visuel est contrôlé intégralement — pas d'échantillonnage sur un lot :
**chaque design déposé est vérifié**.

---

## D-01 — TEXTES ET LANGUE (LANG-001 à LANG-010)

Extraire **tous** les textes visibles : titres, CTA, prix, dates, mentions, coordonnées,
URLs, textes incrustés. Texte illisible : localiser et signaler (bloquant).

| ID | Règle | Gravité |
|----|-------|---------|
| LANG-001 | Extraire tous les textes visibles (voir ci-dessus). | MAJEUR |
| LANG-002 | Identifier langue et variante par bloc. Un texte anglais n'est pas une faute dans un livrable anglais. | MAJEUR |
| LANG-003 | **Orthographe** : accents, apostrophes, lettres manquantes/ajoutées, homophones, traits d'union, pluriels, capitalisation. | MAJEUR |
| LANG-004 | **Grammaire** : genre, nombre, déterminants, pronoms, prépositions, syntaxe, accords sujet-verbe, participes passés. | MAJEUR |
| LANG-005 | **Conjugaison** : temps, infinitif, participe, auxiliaires, concordance. Ne pas reformuler arbitrairement. | MAJEUR |
| LANG-006 | Ponctuation et espaces : signes, guillemets, parenthèses, espaces doubles/absentes selon la langue. | MINEUR |
| LANG-007 | **Anglicismes** : aucun dans les textes français créés par Wenov, sauf nom officiel/marque/terme autorisé. | MAJEUR |
| LANG-008 | Termes techniques : vérifier dans la base client puis sources officielles. Ressemblance phonétique insuffisante. | MAJEUR |
| LANG-009 | Noms propres : vérifier dans les références officielles. Respecter exactement l'écriture confirmée. | MAJEUR |
| LANG-010 | **Forme vs sens** : distinguer correction linguistique et changement de sens. Ne jamais transformer une donnée factuelle sans source. | MAJEUR |

**Standard DG : zéro faute en français ET en anglais.** Une seule faute = RÉVISION.

---

## D-02 — IDENTITÉ VISUELLE

Comparer systématiquement au dossier Drive client (`02_Charte_Graphique`, `03_Logos`, `04_Polices`).

- [ ] **Bon logo, bonne variante** — jamais de logo régénéré, approximatif ou recréé.
  Interdits : déformer, recolorer, incliner, couper, modifier le logo.
- [ ] **Couleurs conformes** — codes hex exacts de la charte (mesure indicative sur proxy
  compressé : en cas de doute, signaler « à mesurer sur source » plutôt que valider).
- [ ] **Typographies conformes** — familles et graisses autorisées uniquement.
- [ ] Zone de protection du logo respectée ; taille minimale respectée.
- [ ] Utilisation correcte des assets officiels (`05_Assets`).

Sans dossier client : identité non validée par défaut — marquer « non applicable »,
jamais supposer qu'un logo ou une couleur « va bien ».

---

## D-03 — COMPOSITION (regard directeur artistique)

- **Alignement** : tous les éléments s'alignent sur une grille cohérente ; aucun décalage
  involontaire de quelques pixels entre éléments censés être alignés.
- **Espacements** : rythme constant (base 8 px : 8/16/24/32/48/64…) ; même type
  d'éléments = mêmes marges internes partout ; pas de zone écrasée ni de vide inexpliqué.
- **Hiérarchie** : un seul message principal, identifiable en 3 secondes (taille, graisse,
  couleur, position) ; les niveaux secondaires sont visuellement en retrait.
- **Équilibre** : poids visuel réparti, marges internes suffisantes autour de chaque bloc ;
  rien ne touche les bords sauf effet voulu et assumé.
- **Proximité** : les éléments liés sont regroupés visuellement ; les groupes distincts
  sont séparés.

---

## D-04 — LISIBILITÉ ET CONTRASTE

- **Contraste WCAG AA** : texte courant ≥ 4,5:1 ; grand texte (≥ 18 px / 14 px gras) ≥ 3:1.
  En cas de doute visuel : signaler « contraste à mesurer ».
- Texte jamais posé sur une zone de photo chargée sans fond de protection
  (bandeau, ombrage, flou).
- Tailles minimales : corps lisible à distance d'usage (mobile : ≥ ~16 px équivalent) ;
  mentions légales lisibles sans loupe abusive.
- Pas de texte coupé, tronqué, chevauché ou sortant de son conteneur.
- Interlignage : corps ~1,4–1,6×, titres ~1,1–1,3× ; longueur de ligne ≤ ~75 caractères.

---

## D-05 — FORMAT ET ZONES SÛRES

- **Dimensions exactes** du format cible (ex. 1080×1080 post, 1080×1920 story/reel) ;
  ratio respecté, pas de déformation.
- **Zones sûres plateformes** : aucun texte ni logo dans les zones masquées par les
  interfaces — repère 1080×1920 : garder ~270 px en haut, ~670 px en bas, ~180 px
  à droite libres d'éléments critiques.
- **Marges de sécurité** : éléments critiques à ≥ ~5 % des bords
  (print : tenir compte des fonds perdus si applicable).

---

## D-06 — QUALITÉ D'IMAGE

- Pas de pixelisation, de flou involontaire, de compression visible sur les aplats.
- Logos et textes nets.
- Poids du fichier cohérent avec l'usage (ni surcompression visible, ni export aberrant).

---

## D-07 — FINITION

- Aucun élément parasite : repères de découpe, filigrane d'outil, « lorem ipsum »,
  calque oublié, bord de photo visible, guide d'alignement resté affiché.
- Cohérence entre les déclinaisons d'une même campagne (même système visuel, mêmes espacements).
- Nommage clair du fichier ; format d'export adapté (PNG/JPG web, PDF print).

---

## D-08 — CTA ET MENTIONS

- CTA présent, formulé correctement et conforme (un seul CTA sauf règle client contraire).
- Mentions légales : présentes si requises (ex. loterie : licence, 18+, juridiction),
  lisibles, placées sans être masquées.
- URL/QR : lisibles, corrects, testés quand c'est possible.

---

## PREUVE (chaque anomalie)

Fichier + zone/localisation + règle (D-xx ou LANG-xxx) + texte concerné +
correction proposée + source (charte, asset, règle client) + confiance
(élevée/moyenne/faible) + gravité.

## LIMITE — choix créatif assumé

Un désalignement volontaire, une composition atypique ou un ton décalé **cohérent dans
tout le livrable** n'est pas une faute : le signaler en « remarque », pas en correction.
En revanche, une incohérence interne (deux traitements différents sans raison) = correction.
