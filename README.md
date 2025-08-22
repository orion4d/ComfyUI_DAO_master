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

