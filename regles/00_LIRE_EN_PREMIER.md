# Factorie — Installation dans Google Drive

Créer un dossier FACTORIE, puis y placer ces fichiers selon le tableau.

| Dossier Drive | Fichiers à déposer |
|---|---|
| FACTORIE/00_GOUVERNANCE | 00_LIRE_EN_PREMIER.md ; 01_Gouvernance_et_sources.md ; 10_Contrat_moteur.md |
| FACTORIE/01_REGLES_GLOBALES | 02_Textes_et_langues.md ; 03_Videos_et_sous_titres.md ; 04_Identite_visuelle.md ; 05_Faits_et_coherence.md ; 06_Rapports_et_verdicts.md |
| FACTORIE/02_MODELES | 07_Modele_regles_client.md ; 08_Modele_regles_campagne.md ; 09_Modele_rapport.md |
| FACTORIE/03_EXPORT_MACHINE | 11_Regles_structurees.json ; 12_Manifest.json |
| FACTORIE/CLIENTS/[CLIENT] | Copies complétées des modèles client et campagne ; charte ; logos ; polices ; sources ; assets ; exemples approuvés |
| FACTORIE/ARCHIVES | Anciennes versions datées, non actives |

## Organisation de chaque client
Créer : 01_Regles_Client, 02_Charte_Graphique, 03_Logos, 04_Polices, 05_Assets, 06_Contenus_Approuves, 07_Campagnes. Renseigner l’identifiant du dossier client dans Factorie. Les modèles vierges ne sont jamais des règles actives.

## Quelle version modifier ?
Pour la V1, les fichiers Markdown (.md) sont les documents éditables de référence. Ils sont du texte simple lisible par un humain et un agent. Le JSON est leur export initial structuré, pas une deuxième base indépendante. Après modification : incrémenter la version, faire approuver par le responsable Wenov, régénérer JSON et manifest puis activer l’ensemble cohérent. En attendant cette régénération, le moteur doit lire les Markdown à jour ou bloquer un export obsolète. Ne jamais modifier séparément les deux versions.

## Avant chaque analyse
1. Confirmer client, campagne, langue, média, destination et version du fichier.
2. Vérifier les versions actuelles des règles et références Drive. Un cache est permis uniquement si sa version reste actuelle.
3. Charger toutes les règles applicables et les seuls assets pertinents ; ne pas parcourir les dossiers des autres clients.
4. Enregistrer un paquet figé avec sources, versions et empreintes.
5. Faire analyser le livrable par le moteur choisi.
6. Valider le rapport, les preuves et la couverture. Retourner le verdict ; conserver le paquet et le rapport.

## V1 simple / évolution
Au départ, un agent ayant réellement accès à Drive peut lire ces fichiers avant l’analyse. Le moteur doit charger les familles applicables en entier, pas quelques passages trouvés par similarité. Ensuite, Factorie peut synchroniser Drive vers une base structurée et assembler automatiquement les paquets. Ce téléchargement ne crée ni la connexion Drive ni cette synchronisation.

## Responsabilités
Wenov approuve les règles, exceptions et sources. Factorie sélectionne et historise. Le moteur analyse. L’équipe corrige et prend la décision de livraison. Aucun fichier ici ne contient une charte réelle BBL, FSO ou Jets : elles doivent être ajoutées depuis leurs dossiers officiels.

## Points à retenir
La cadence d’une capture par seconde demandée est conservée. Elle ne garantit pas la détection des éléments plus brefs qu’une seconde. Les contrôles exacts de police/couleur peuvent nécessiter les sources. Une analyse incomplète ou une incertitude essentielle bloque ; elle ne peut recevoir PASS.
