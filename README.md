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

*   ## Manipulation SVG

Ces nodes permettent de modifier, combiner et prévisualiser des données au format SVG.

---

### SVG Boolean
Ce node effectue des opérations booléennes (union, différence, etc.) entre deux formes SVG.

*   **Description :** Combine deux géométries SVG pour en créer une nouvelle. C'est l'équivalent des fonctions "Pathfinder" dans les logiciels de dessin vectoriel.
*   **Catégorie :** `DAO_master/SVG`

**Entrées (Inputs)**
*   `svg_a` (`SVG_TEXT`): Le premier SVG (sujet).
*   `svg_b` (`SVG_TEXT`): Le deuxième SVG (opérateur).
*   `operation` (`LISTE`): L'opération à effectuer :
    *   `union`: Fusionne les deux formes.
    *   `difference`: Soustrait la forme B de la forme A.
    *   `intersection`: Ne conserve que la zone où les deux formes se superposent.
    *   `xor`: Ne conserve que les zones où les formes ne se superposent pas.
*   `curve_quality` (`INT`, défaut: `60`): Précision utilisée pour convertir les courbes en segments de lignes avant l'opération. Une valeur plus élevée donne un résultat plus précis mais peut être plus lente.

**Sorties (Outputs)**
*   `svg_text` (`SVG_TEXT`): Le SVG résultant de l'opération booléenne.

---

### SVG Style
Ce node applique des styles de remplissage et de contour à un SVG.

*   **Description :** Permet de définir ou de remplacer les attributs de style (`fill`, `stroke`, `stroke-width`) de tous les chemins (`<path>`) à l'intérieur d'un SVG.
*   **Catégorie :** `DAO_master/SVG`

**Entrées (Inputs)**
*   `svg_text` (`SVG_TEXT`): Le SVG à styliser.
*   `fill_enabled` (`BOOLEAN`, défaut: `True`): Active ou désactive le remplissage.
*   `fill_color` (`STRING`, défaut: `#00A2FF`): La couleur de remplissage (format hexadécimal).
*   `stroke_color` (`STRING`, défaut: `#000000`): La couleur du contour.
*   `stroke_width` (`FLOAT`, défaut: `1.0`): L'épaisseur du contour. Une valeur de `0` désactive le contour.

**Sorties (Outputs)**
*   `svg_text` (`SVG_TEXT`): Le SVG avec les nouveaux styles appliqués.

---

### SVG Preview
Génère une prévisualisation d'un SVG sous forme d'image. Nécessite l'installation de `cairosvg`.

*   **Description :** Utilise la bibliothèque CairoSVG pour effectuer un rendu de haute qualité d'un SVG.
*   **Catégorie :** `DAO_master/SVG`

**Entrées (Inputs)**
*   `svg_text` (`SVG_TEXT`): Le SVG à prévisualiser.
*   `width` (`INT`, défaut: `512`): Largeur de l'image de sortie.
*   `height` (`INT`, défaut: `512`): Hauteur de l'image de sortie.
*   `fit_mode` (`LISTE`): Gère le redimensionnement du SVG pour l'adapter à la sortie :
    *   `stretch`: Étire le SVG pour remplir les dimensions `width` x `height`.
    *   `fit_width`: Ajuste la hauteur pour conserver le ratio d'aspect en fonction de la largeur.
    *   `fit_height`: Ajuste la largeur pour conserver le ratio d'aspect en fonction de la hauteur.
    *   `contain`: Redimensionne pour que le SVG soit entièrement visible sans déformation, centré dans la zone.
*   `bg_enabled` (`BOOLEAN`, défaut: `False`): Active un fond de couleur unie.
*   `bg_color_hex` (`STRING`, défaut: `#FFFFFF`): Couleur du fond. Si désactivé, le fond est transparent.

**Sorties (Outputs)**
*   `image` (`IMAGE`): L'image de l'aperçu.

---

## I/O SVG (Input/Output)

---

### SVG Load
Charge un fichier SVG depuis le disque et permet de le redimensionner.

*   **Description :** Lit un fichier `.svg`, le parse et permet d'appliquer une transformation d'échelle à son contenu ou à sa zone de dessin (`canvas`).
*   **Catégorie :** `DAO_master/SVG/IO`

**Entrées (Inputs)**
*   `file_path` (`STRING`): Chemin d'accès au fichier SVG.
*   `scale` (`FLOAT`, défaut: `1.0`): Facteur d'échelle appliqué au contenu du SVG.
*   `center_on_viewbox` (`BOOLEAN`, défaut: `True`): Si `True`, la mise à l'échelle se fait par rapport au centre de la `viewBox` du SVG.
*   `scale_canvas` (`BOOLEAN`, défaut: `False`): Si `True`, met également à l'échelle les attributs `width` et `height` de la balise `<svg>`.
*   `ensure_viewbox` (`BOOLEAN`, défaut: `True`): Si le SVG n'a pas de `viewBox` mais a `width` et `height`, en crée une automatiquement.

**Sorties (Outputs)**
*   `svg_text` (`SVG_TEXT`): Le contenu du fichier SVG (potentiellement modifié).
*   `path` (`STRING`): Le chemin absolu du fichier chargé.

---

### SVG Save
Sauvegarde une chaîne de texte SVG dans un fichier `.svg`.

*   **Description :** Écrit le contenu `SVG_TEXT` sur le disque.
*   **Catégorie :** `DAO_master/SVG/IO`

**Entrées (Inputs)**
*   `svg_text` (`SVG_TEXT`): Le contenu SVG à sauvegarder.
*   ... (paramètres `directory`, `filename`, `timestamp_suffix` identiques à `DXF Save`)

**Sorties (Outputs)**
*   `path` (`STRING`): Le chemin absolu du fichier sauvegardé.

---

### SVG Passthrough
Convertit un type `SVG_TEXT` en `STRING` standard.

*   **Description :** Node utilitaire simple servant de convertisseur de type pour connecter une sortie `SVG_TEXT` à une entrée qui attend une `STRING` générique.
*   **Catégorie :** `DAO_master/SVG/Utils`

**Entrées (Inputs)**
*   `svg_text` (`SVG_TEXT`): Le SVG en entrée.

**Sorties (Outputs)**
*   `string` (`STRING`): Le même contenu, mais de type `STRING`.

---

## Conversion SVG ↔ Image

---

### Convert SVG → IMG (+colors)
Convertit un SVG en une image rastérisée et extrait les couleurs utilisées.

*   **Description :** Un node de conversion avancé qui parse la structure d'un SVG, identifie les formes et leurs couleurs, puis les rend sous forme d'image. Il propose deux moteurs de rendu : un "natif" basé sur PIL et un basé sur "CairoSVG" pour une meilleure compatibilité.
*   **Catégorie :** `DAO_master/SVG/Convert`

**Entrées (Inputs)**
*   `svg_text` (`SVG_TEXT`): Le contenu SVG à convertir.
*   `svg_path` (`STRING`, optionnel): Chemin vers un fichier SVG, utilisé si `svg_text` est vide.
*   `width` (`INT`, défaut: `512`): Largeur de l'image de sortie (la hauteur est calculée pour garder le ratio).
*   `scale_in_canvas` (`FLOAT`, défaut: `1.0`): Applique un zoom "dans" le SVG en modifiant sa `viewBox` avant le rendu.
*   `transparent_bg` (`BOOLEAN`, défaut: `False`): Rend l'image avec un fond transparent.
*   `background_hex` (`STRING`, défaut: `#000000`): Couleur de fond si la transparence est désactivée.
*   `pad_px` (`INT`, défaut: `0`): Ajoute une marge (padding) en pixels autour de l'image.
*   `keep_alpha_as_mask` (`BOOLEAN`, défaut: `True`): Si `True`, génère un masque basé sur les zones non transparentes de l'image.
*   `stroke_only` (`BOOLEAN`, défaut: `False`): Ne rend que les contours (`stroke`), ignore les remplissages (`fill`).
*   `open_subpaths_px` (`INT`, défaut: `0`): Si supérieur à 0, les chemins ouverts (non fermés) seront rendus avec cette épaisseur.
*   `renderer` (`LISTE`, défaut: `auto`): Choix du moteur de rendu. `auto` essaie le `native` d'abord, et si le résultat semble vide, bascule sur `cairosvg`.

**Sorties (Outputs)**
*   `image` (`IMAGE`): L'image rastérisée du SVG.
*   `mask` (`MASK`): Le masque de l'image.
*   `colors_json` (`STRING`): Une chaîne JSON listant toutes les formes détectées avec leur type (`fill`/`stroke`) et leur couleur.

---

### Convert IMG → SVG (1-bit)
Convertit une image en un SVG monochrome en utilisant Potrace.

*   **Description :** Ce node binarise une image (la transforme en noir et blanc pur) puis utilise l'algorithme de Potrace pour tracer les contours des formes, générant ainsi un SVG.
*   **Catégorie :** `DAO_master/SVG/Convert`

**Entrées (Inputs)**
*   `image` (`IMAGE`): L'image source.
*   `threshold` (`INT`, défaut: `128`): Seuil de luminosité (0-255) pour la binarisation.
*   `auto_otsu` (`BOOLEAN`, défaut: `True`): Si `True`, calcule automatiquement le meilleur seuil (méthode d'Otsu) et ignore la valeur `threshold`.
*   `invert` (`BOOLEAN`, défaut: `False`): Inverse le noir et le blanc avant le traçage.
*   ... (paramètres `turdsize`, `alphamax`, etc.) : Paramètres avancés de l'algorithme Potrace pour contrôler la finesse et la simplification du tracé.
*   `fill_rule` (`LISTE`, défaut: `nonzero`): Règle de remplissage pour le SVG généré.
*   `backend` (`LISTE`, défaut: `auto`): Permet de choisir entre l'exécutable `potrace` (si installé) ou la bibliothèque Python.
*   ... (paramètres de sauvegarde `save_svg`, `out_dir`, etc.)

**Sorties (Outputs)**
*   `svg_path` (`STRING`): Le chemin du fichier `.svg` sauvegardé (si l'option est activée).
*   `svg_text` (`SVG_TEXT`): Le contenu du SVG généré sous forme de texte.
*   `preview` (`IMAGE`): Un aperçu de l'image binarisée qui a été utilisée pour le traçage.
