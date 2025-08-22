# ComfyUI_DAO_master

**ComfyUI_DAO_master** est une collection de **custom nodes** pour [ComfyUI](https://github.com/comfyanonymous/ComfyUI).  
Ces nodes apportent des outils supplémentaires pour la création, la manipulation d’image et l’expérimentation visuelle avec un focus pour le vectoriel

---

## 🚀 Installation

1. Télécharger ou cloner ce dépôt dans le dossier `custom_nodes` de votre installation **ComfyUI** :

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/orion4d/ComfyUI_DAO_master.git
```

# Documentation Technique

Ce document fournit une description détaillée de chaque custom node inclus dans le pack **ComfyUI_DAO_master**.

##  primitives DXF

Cette catégorie regroupe les nodes fondamentaux pour la création de formes géométriques simples. Ils constituent la base de tout dessin vectoriel.

**Principe de fonctionnement commun :**
Chaque node de cette catégorie fonctionne de manière non-destructive. Il prend un objet `DXF` en entrée, crée une copie de son contenu, y ajoute la nouvelle forme, et retourne un nouvel objet `DXF` en sortie. Le document d'origine n'est jamais modifié.

---

### DXF Add Circle
Ce node ajoute un cercle à un document DXF.

*   **Description :** Crée un cercle défini par un point central et un rayon.
*   **Catégorie :** `DAO_master/DXF/Primitives`

**Entrées (Inputs)**
*   `dxf` (`DXF`): Le document DXF de base auquel ajouter la forme.
*   `cx` (`FLOAT`, défaut: `0.0`): La coordonnée X du centre du cercle.
*   `cy` (`FLOAT`, défaut: `0.0`): La coordonnée Y du centre du cercle.
*   `radius` (`FLOAT`, défaut: `10.0`): Le rayon du cercle. Doit être une valeur positive.

**Sorties (Outputs)**
*   `dxf` (`DXF`): Le nouveau document DXF contenant le cercle ajouté.

---

### DXF Add Rectangle
Ce node ajoute un rectangle à un document DXF.

*   **Description :** Crée un rectangle défini par un point d'ancrage, une largeur et une hauteur.
*   **Catégorie :** `DAO_master/DXF/Primitives`

**Entrées (Inputs)**
*   `dxf` (`DXF`): Le document DXF de base.
*   `x` (`FLOAT`, défaut: `0.0`): La coordonnée X du point d'ancrage.
*   `y` (`FLOAT`, défaut: `0.0`): La coordonnée Y du point d'ancrage.
*   `width` (`FLOAT`, défaut: `20.0`): La largeur du rectangle.
*   `height` (`FLOAT`, défaut: `10.0`): La hauteur du rectangle.
*   `centered` (`BOOLEAN`, défaut: `False`): Si `True`, le point `(x, y)` est le centre du rectangle. Si `False`, c'est le coin inférieur gauche.

**Sorties (Outputs)**
*   `dxf` (`DXF`): Le nouveau document DXF contenant le rectangle ajouté.

---

### DXF Add Rounded Rectangle
Ce node ajoute un rectangle avec des coins arrondis.

*   **Description :** Similaire au rectangle standard, mais permet de spécifier un rayon pour adoucir les angles.
*   **Catégorie :** `DAO_master/DXF/Primitives`

**Entrées (Inputs)**
*   `dxf` (`DXF`): Le document DXF de base.
*   `x` (`FLOAT`, défaut: `0.0`): La coordonnée X du point d'ancrage.
*   `y` (`FLOAT`, défaut: `0.0`): La coordonnée Y du point d'ancrage.
*   `width` (`FLOAT`, défaut: `20.0`): La largeur totale du rectangle.
*   `height` (`FLOAT`, défaut: `10.0`): La hauteur totale du rectangle.
*   `radius` (`FLOAT`, défaut: `2.0`): Le rayon des quatre coins arrondis. Si le rayon est `0`, un rectangle standard est dessiné.
*   `centered` (`BOOLEAN`, défaut: `False`): Si `True`, le point `(x, y)` est le centre. Si `False`, c'est le coin inférieur gauche.

**Sorties (Outputs)**
*   `dxf` (`DXF`): Le nouveau document DXF contenant le rectangle arrondi.

---

### DXF Add Line
Ce node ajoute un segment de ligne simple.

*   **Description :** Dessine une ligne droite entre deux points définis par leurs coordonnées.
*   **Catégorie :** `DAO_master/DXF/Primitives`

**Entrées (Inputs)**
*   `dxf` (`DXF`): Le document DXF de base.
*   `x1` (`FLOAT`, défaut: `0.0`): Coordonnée X du point de départ.
*   `y1` (`FLOAT`, défaut: `0.0`): Coordonnée Y du point de départ.
*   `x2` (`FLOAT`, défaut: `20.0`): Coordonnée X du point d'arrivée.
*   `y2` (`FLOAT`, défaut: `0.0`): Coordonnée Y du point d'arrivée.

**Sorties (Outputs)**
*   `dxf` (`DXF`): Le nouveau document DXF contenant la ligne ajoutée.

---

### DXF Add Polygon
Ce node ajoute un polygone régulier.

*   **Description :** Crée un polygone régulier (tous les côtés et angles sont égaux) inscrit dans un cercle.
*   **Catégorie :** `DAO_master/DXF/Primitives`

**Entrées (Inputs)**
*   `dxf` (`DXF`): Le document DXF de base.
*   `cx` (`FLOAT`, défaut: `0.0`): La coordonnée X du centre du polygone.
*   `cy` (`FLOAT`, défaut: `0.0`): La coordonnée Y du centre du polygone.
*   `radius` (`FLOAT`, défaut: `10.0`): Le rayon du cercle circonscrit au polygone (la distance du centre à chaque sommet).
*   `num_sides` (`INT`, défaut: `6`): Le nombre de côtés du polygone (ex: 3 pour un triangle, 5 pour un pentagone, 6 pour un hexagone).

**Sorties (Outputs)**
*   `dxf` (`DXF`): Le nouveau document DXF contenant le polygone ajouté.

---

### DXF Add Ellipse
Ce node ajoute une ellipse.

*   **Description :** Crée une ellipse définie par son centre, son axe majeur et le ratio de son axe mineur.
*   **Catégorie :** `DAO_master/DXF/Primitives`

**Entrées (Inputs)**
*   `dxf` (`DXF`): Le document DXF de base.
*   `cx` (`FLOAT`, défaut: `0.0`): La coordonnée X du centre de l'ellipse.
*   `cy` (`FLOAT`, défaut: `0.0`): La coordonnée Y du centre de l'ellipse.
*   `major_axis_x` (`FLOAT`, défaut: `20.0`): Composante X du vecteur de l'axe majeur. Ce vecteur définit la longueur et l'orientation de l'ellipse.
*   `major_axis_y` (`FLOAT`, défaut: `0.0`): Composante Y du vecteur de l'axe majeur.
*   `ratio` (`FLOAT`, défaut: `0.5`): Le rapport entre la longueur de l'axe mineur et celle de l'axe majeur (valeur entre 0 et 1).

**Sorties (Outputs)**
*   `dxf` (`DXF`): Le nouveau document DXF contenant l'ellipse ajoutée.

*   ### DXF Add Star
Ce node ajoute une étoile à un document DXF.

*   **Description :** Crée une étoile définie par un centre, deux rayons (externe et interne) et un nombre de pointes.
*   **Catégorie :** `DAO_master/DXF/Primitives`

**Entrées (Inputs)**
*   `dxf` (`DXF`): Le document DXF de base.
*   `cx` (`FLOAT`, défaut: `0.0`): La coordonnée X du centre de l'étoile.
*   `cy` (`FLOAT`, défaut: `0.0`): La coordonnée Y du centre de l'étoile.
*   `outer_radius` (`FLOAT`, défaut: `20.0`): Le rayon externe (distance du centre aux pointes de l'étoile).
*   `inner_radius` (`FLOAT`, défaut: `10.0`): Le rayon interne (distance du centre aux creux de l'étoile).
*   `num_points` (`INT`, défaut: `5`): Le nombre de branches/pointes que possède l'étoile.

**Sorties (Outputs)**
*   `dxf` (`DXF`): Le nouveau document DXF contenant l'étoile ajoutée.

---

### DXF Add Triangle
Ce node ajoute un triangle.

*   **Description :** Crée un triangle en reliant trois points spécifiés par leurs coordonnées.
*   **Catégorie :** `DAO_master/DXF/Primitives`

**Entrées (Inputs)**
*   `dxf` (`DXF`): Le document DXF de base.
*   `x1` (`FLOAT`, défaut: `0.0`): Coordonnée X du premier sommet du triangle.
*   `y1` (`FLOAT`, défaut: `0.0`): Coordonnée Y du premier sommet du triangle.
*   `x2` (`FLOAT`, défaut: `20.0`): Coordonnée X du deuxième sommet du triangle.
*   `y2` (`FLOAT`, défaut: `0.0`): Coordonnée Y du deuxième sommet du triangle.
*   `x3` (`FLOAT`, défaut: `10.0`): Coordonnée X du troisième sommet du triangle.
*   `y3` (`FLOAT`, défaut: `15.0`): Coordonnée Y du troisième sommet du triangle.

**Sorties (Outputs)**
*   `dxf` (`DXF`): Le nouveau document DXF contenant le triangle ajouté.

## Création et I/O (Input/Output)

Ces nodes permettent de créer de nouveaux documents DXF, de les charger depuis un fichier ou de les sauvegarder sur le disque.

---

### DXF New
Ce node est le point de départ pour la plupart des workflows. Il crée un document DXF vierge.

*   **Description :** Initialise un nouvel environnement de dessin vectoriel.
*   **Catégorie :** `DAO_master/DXF`

**Entrées (Inputs)**
*   `units` (`LISTE`, défaut: `mm`): Définit l'unité de mesure principale pour le document (millimètres, centimètres, pouces, etc.). Cette information est stockée dans l'en-tête du fichier DXF.

**Sorties (Outputs)**
*   `dxf` (`DXF`): Un nouvel objet DXF vide, prêt à recevoir des formes.

---

### DXF Import
Ce node permet de charger un fichier DXF existant depuis votre ordinateur.

*   **Description :** Lit un fichier `.dxf` et le convertit en un objet `DXF` utilisable dans ComfyUI.
*   **Catégorie :** `DAO_master/DXF/IO`

**Entrées (Inputs)**
*   `file_path` (`STRING`): Le chemin d'accès complet vers le fichier DXF à importer.

**Sorties (Outputs)**
*   `dxf` (`DXF`): L'objet DXF contenant la géométrie du fichier chargé.

---

### DXF Save
Ce node sauvegarde l'objet DXF en cours dans un fichier `.dxf`.

*   **Description :** Écrit le contenu de l'objet DXF sur le disque.
*   **Catégorie :** `DAO_master/DXF/Utils`

**Entrées (Inputs)**
*   `dxf` (`DXF`): Le document DXF à sauvegarder.
*   `directory` (`STRING`, défaut: `output/dxf`): Le dossier de destination pour le fichier.
*   `filename` (`STRING`, défaut: `shape.dxf`): Le nom du fichier de sortie.
*   `timestamp_suffix` (`BOOLEAN`, défaut: `True`): Si `True`, ajoute un horodatage (date et heure) au nom du fichier pour éviter d'écraser les versions précédentes.
*   `save_file` (`BOOLEAN`, défaut: `True`): Un interrupteur pour activer ou désactiver la sauvegarde. Utile pour contrôler l'exécution dans des workflows complexes.

**Sorties (Outputs)**
*   `dxf` (`DXF`): Le même objet DXF passé en entrée (pass-through).
*   `path` (`STRING`): Le chemin d'accès complet du fichier qui a été sauvegardé.

---

## Modification

Cette catégorie contient les nodes qui altèrent la géométrie existante.

---

### DXF Transform
Ce node applique des transformations géométriques (translation, rotation, échelle) à l'ensemble du dessin.

*   **Description :** Modifie la position, la taille et l'orientation de toutes les entités d'un document DXF.
*   **Catégorie :** `DAO_master/DXF/Modify`

**Entrées (Inputs)**
*   `dxf` (`DXF`): Le document DXF à transformer.
*   `translate_x` (`FLOAT`, défaut: `0.0`): Déplacement horizontal (gauche/droite).
*   `translate_y` (`FLOAT`, défaut: `0.0`): Déplacement vertical (haut/bas).
*   `scale` (`FLOAT`, défaut: `1.0`): Facteur d'échelle. `1.0` = taille originale, `<1.0` = réduction, `>1.0` = agrandissement.
*   `rotation_degrees` (`FLOAT`, défaut: `0.0`): Angle de rotation en degrés.
*   `rotation_center` (`LISTE`, défaut: `object_center`): Le point pivot pour la rotation.
    *   `object_center`: Le centre géométrique de l'ensemble des formes.
    *   `origin`: Le point d'origine du document (0,0).

**Sorties (Outputs)**
*   `dxf` (`DXF`): Un nouveau document DXF contenant la géométrie transformée.

---

## Utilitaires (Utils)

Ces nodes fournissent des outils pour visualiser ou analyser les données DXF.

---

### DXF Preview
Ce node génère un aperçu visuel (une image) du contenu d'un objet DXF.

*   **Description :** Effectue un rendu rastérisé du dessin vectoriel pour l'afficher dans ComfyUI.
*   **Catégorie :** `DAO_master/DXF/Utils`

**Entrées (Inputs)**
*   `dxf` (`DXF`): Le document à prévisualiser.
*   `size` (`INT`, défaut: `512`): La résolution de l'image de sortie (en pixels, `size` x `size`).
*   `line_width` (`INT`, défaut: `3`): L'épaisseur des traits en pixels.
*   `stroke_hex` (`STRING`, défaut: `#000000`): La couleur des traits (format hexadécimal).
*   `fill_enabled` (`BOOLEAN`, défaut: `False`): Active ou désactive le remplissage des formes fermées.
*   `fill_hex` (`STRING`, défaut: `#00A2FF`): La couleur de remplissage.
*   `bg_enabled` (`BOOLEAN`, défaut: `True`): Active ou désactive le fond de l'image.
*   `bg_hex` (`STRING`, défaut: `#F5F5F5`): La couleur du fond.
*   `show_grid` (`BOOLEAN`, défaut: `True`): Affiche une grille en arrière-plan.
*   `transparent_bg` (`BOOLEAN`, défaut: `False`): Si `True`, le fond est transparent (l'image de sortie aura un canal alpha).
*   `emit_mask` (`BOOLEAN`, défaut: `False`): Si `True`, génère un masque en niveaux de gris où les formes sont blanches et le fond noir.

**Sorties (Outputs)**
*   `image` (`IMAGE`): L'image de l'aperçu.
*   `mask` (`MASK`): Le masque de la géométrie.

---

### DXF Stats
Ce node analyse un document DXF et en extrait des statistiques simples.

*   **Description :** Fournit des informations sur les dimensions et le contenu du dessin.
*   **Catégorie :** `DAO_master/DXF/Utils`

**Entrées (Inputs)**
*   `dxf` (`DXF`): Le document à analyser.

**Sorties (Outputs)**
*   `bbox` (`STRING`): La "bounding box" (boîte englobante), qui représente le plus petit rectangle contenant toutes les formes. Format: `(min_x, min_y, max_x, max_y)`.
*   `count` (`INT`): Le nombre total d'entités (lignes, cercles, etc.) dans le document.

---

## Conversion

Ces nodes permettent de passer d'un format de données à un autre.

---

### DXF to SVG
Ce node convertit un document DXF en code SVG (Scalable Vector Graphics).

*   **Description :** Transforme la géométrie DXF en un format SVG textuel, en tentant d'assembler les segments de lignes pour créer des chemins propres.
*   **Catégorie :** `DAO_master/SVG/Convert`

**Entrées (Inputs)**
*   `dxf` (`DXF`): Le document DXF à convertir.
*   `curve_quality` (`INT`, défaut: `50`): Précision de la conversion des courbes en segments de ligne (plus la valeur est haute, plus c'est précis).
*   `scale` (`FLOAT`, défaut: `1.0`): Facteur de zoom appliqué à la `viewBox` du SVG.
*   `padding_percent` (`FLOAT`, défaut: `5.0`): Marge ajoutée autour du dessin (en pourcentage de sa taille).
*   `close_tolerance_percent` (`FLOAT`, défaut: `0.0`): Tolérance pour joindre des segments de lignes proches et former des polygones fermés. `0.0` pour une détection automatique.
*   `fill_rule` (`LISTE`, défaut: `evenodd`): Règle de remplissage SVG. `evenodd` permet de gérer correctement les "trous" dans les formes.
*   ... (paramètres de sauvegarde de fichier identiques à `DXF Save`)

**Sorties (Outputs)**
*   `svg_text` (`SVG_TEXT`): Le contenu complet du fichier SVG sous forme de chaîne de caractères.
*   `path` (`STRING`): Le chemin d'accès complet du fichier `.svg` sauvegardé (si l'option est activée).
