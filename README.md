# 🎨 ComfyUI_DAO_master

**ComfyUI_DAO_master** est une collection de custom nodes pour **ComfyUI**.
Ces nodes apportent des outils supplémentaires pour la création, la manipulation d’image et l’expérimentation visuelle, avec un focus sur les **workflows vectoriels** (DXF & SVG) et les utilitaires de production.

<p align="center">
<img width="1242" height="635" alt="image" src="https://github.com/user-attachments/assets/b2097f01-370e-4dd0-b3d8-0dbacbe8bc24" />
</p>

### ✨ Aperçu des fonctionnalités

*   **Création Vectorielle DXF :** Générez des formes primitives (cercles, rectangles, polygones...) et assemblez-les.
*   **Manipulation SVG :** Effectuez des opérations booléennes (union, différence...), stylisez vos SVG et convertissez-les.
*   **Conversion Robuste :** Passez facilement d'une image à un SVG (vectorisation) et d'un SVG à une image (rastérisation).
*   **Utilitaires Puissants :** Un sélecteur de fichiers avancé, des sélecteurs de couleurs dynamiques, un générateur de texte complet et des filtres d'image pratiques.
*   **Interface Améliorée :** De nombreux nodes disposent d'une interface utilisateur interactive avec des menus déroulants dynamiques pour une utilisation plus intuitive.

---

### 🚀 Installation

1.  Naviguez vers le dossier `custom_nodes` de votre installation ComfyUI.
2.  Clonez ce dépôt :
    ```sh
    cd ComfyUI/custom_nodes
    git clone https://github.com/orion4d/ComfyUI_DAO_master.git
    ```
3.  **Installez les dépendances :** Certains nodes nécessitent des bibliothèques supplémentaires. Installez-les via pip :
    ```sh
    pip install cairosvg potrace ezdxf svgpathtools lxml pyclipper shapely
    ```
    *   **Note :** Le node `Convert IMG to SVG` fonctionne mieux si l'exécutable `potrace` est installé et accessible dans le PATH de votre système.

---

### 📚 Documentation des Nodes

<details>
<summary><strong>📐 DXF : Primitives</strong></summary>

> Cette catégorie regroupe les nodes fondamentaux pour la création de formes géométriques simples. Ils constituent la base de tout dessin vectoriel.
> **Principe de fonctionnement commun :** Chaque node de cette catégorie fonctionne de manière non-destructive. Il prend un objet `DXF` en entrée, crée une copie de son contenu, y ajoute la nouvelle forme, et retourne un nouvel objet `DXF` en sortie.

<details>
<summary><code>DXF Add Circle</code></summary>

> Ajoute un cercle à un document DXF.

*   **Catégorie :** `DAO_master/DXF/Primitives`
*   **Entrées :**
    *   `dxf` (`DXF`): Le document de base.
    *   `cx`, `cy` (`FLOAT`): Coordonnées du centre.
    *   `radius` (`FLOAT`): Rayon du cercle.
*   **Sorties :**
    *   `dxf` (`DXF`): Le nouveau document DXF avec le cercle.

</details>

<details>
<summary><code>DXF Add Rectangle</code> / <code>DXF Add Rounded Rectangle</code></summary>

> Ajoute un rectangle (standard ou aux coins arrondis) à un document DXF.

*   **Catégorie :** `DAO_master/DXF/Primitives`
*   **Entrées :**
    *   `dxf` (`DXF`): Le document de base.
    *   `x`, `y` (`FLOAT`): Point d'ancrage.
    *   `width`, `height` (`FLOAT`): Dimensions.
    *   `radius` (`FLOAT`): Rayon des coins (pour la version arrondie).
    *   `centered` (`BOOLEAN`): Si `True`, `(x, y)` est le centre ; sinon, c'est le coin inférieur gauche.
*   **Sorties :**
    *   `dxf` (`DXF`): Le nouveau document DXF avec le rectangle.

</details>

<details>
<summary><code>DXF Add Polygon</code> / <code>DXF Add Star</code> / <code>DXF Add Triangle</code></summary>

> Ajoute une forme polygonale (polygone régulier, étoile ou triangle) à un document DXF.

*   **Catégorie :** `DAO_master/DXF/Primitives`
*   **Entrées (Polygone/Étoile) :**
    *   `dxf` (`DXF`): Le document de base.
    *   `cx`, `cy` (`FLOAT`): Centre de la forme.
    *   `outer_radius`, `inner_radius` (`FLOAT`): Rayons pour définir les sommets.
    *   `num_sides` / `num_points` (`INT`): Nombre de côtés ou de pointes.
*   **Entrées (Triangle) :**
    *   `x1, y1, x2, y2, x3, y3` (`FLOAT`): Coordonnées des trois sommets.
*   **Sorties :**
    *   `dxf` (`DXF`): Le nouveau document DXF avec la forme.

</details>

<details>
<summary><code>DXF Add Line</code> / <code>DXF Add Ellipse</code></summary>

> Ajoute une ligne ou une ellipse à un document DXF.

*   **Catégorie :** `DAO_master/DXF/Primitives`
*   **Entrées (Ligne) :**
    *   `x1, y1, x2, y2` (`FLOAT`): Coordonnées des points de départ et d'arrivée.
*   **Entrées (Ellipse) :**
    *   `cx, cy` (`FLOAT`): Centre de l'ellipse.
    *   `major_axis_x, major_axis_y` (`FLOAT`): Vecteur de l'axe principal (définit la longueur et l'orientation).
    *   `ratio` (`FLOAT`): Rapport entre l'axe mineur et l'axe majeur.
*   **Sorties :**
    *   `dxf` (`DXF`): Le nouveau document DXF avec la forme.

</details>

</details>

<details>
<summary><strong>📂 DXF : I/O, Modification et Utilitaires</strong></summary>

<details>
<summary><code>DXF New</code> / <code>DXF Import</code> / <code>DXF Save</code></summary>

> Crée, charge ou sauvegarde des documents DXF.

*   **Catégorie :** `DAO_master/DXF`, `DAO_master/DXF/IO`
*   **Fonctionnalités :**
    *   **New :** Crée un document DXF vierge en spécifiant les unités.
    *   **Import :** Charge un fichier `.dxf` depuis le disque.
    *   **Save :** Sauvegarde un objet DXF en fichier `.dxf`, avec des options d'horodatage.

</details>

<details>
<summary><code>DXF Transform</code></summary>

> Applique des transformations géométriques (translation, rotation, échelle) à l'ensemble du dessin.

*   **Catégorie :** `DAO_master/DXF/Modify`
*   **Entrées :**
    *   `translate_x`, `translate_y` (`FLOAT`): Déplacement.
    *   `scale` (`FLOAT`): Facteur d'échelle.
    *   `rotation_degrees` (`FLOAT`): Angle de rotation.
    *   `rotation_center` (`LISTE`): Point pivot (`object_center` ou `origin`).
*   **Sorties :**
    *   `dxf` (`DXF`): Un nouveau document avec la géométrie transformée.

</details>

<details>
<summary><code>DXF Preview</code></summary>

> Génère un aperçu visuel (une image) du contenu d'un objet DXF.

*   **Catégorie :** `DAO_master/DXF/Utils`
*   **Fonctionnalités :** Contrôle total sur la taille, l'épaisseur des traits, les couleurs de remplissage/contour, le fond et la grille. Peut également générer un masque.

</details>

<details>
<summary><code>DXF Stats</code></summary>

> Analyse un document DXF et en extrait des statistiques.

*   **Catégorie :** `DAO_master/DXF/Utils`
*   **Sorties :**
    *   `bbox` (`STRING`): La boîte englobante du dessin `(min_x, min_y, max_x, max_y)`.
    *   `count` (`INT`): Le nombre total d'entités dans le document.

</details>

</details>

<details>
<summary><strong>🎨 SVG : Manipulation et Conversion</strong></summary>

<details>
<summary><code>SVG Boolean</code></summary>

> Effectue des opérations booléennes (Pathfinder) entre deux formes SVG.

*   **Catégorie :** `DAO_master/SVG`
*   **Entrées :** `svg_a`, `svg_b`
*   **Opérations :**
    *   `union`: Fusionne les deux formes.
    *   `difference`: Soustrait la forme B de la forme A.
    *   `intersection`: Ne conserve que la zone commune.
    *   `xor`: Ne conserve que les zones non communes.

</details>

<details>
<summary><code>SVG Style</code> / <code>SVG Preview</code></summary>

> Applique des styles ou génère un aperçu d'un SVG.

*   **Catégorie :** `DAO_master/SVG`
*   **Fonctionnalités :**
    *   **Style :** Permet de définir la couleur de remplissage, la couleur et l'épaisseur du contour.
    *   **Preview :** Utilise `CairoSVG` pour un rendu de haute qualité avec gestion du ratio d'aspect.

</details>

<details>
<summary><code>SVG Load</code> / <code>SVG Save</code> / <code>SVG Passthrough</code></summary>

> Charge, sauvegarde ou convertit le type de données SVG.

*   **Catégorie :** `DAO_master/SVG/IO`, `DAO_master/SVG/Utils`
*   **Fonctionnalités :**
    *   **Load :** Charge un `.svg` et permet de le redimensionner à la volée.
    *   **Save :** Sauvegarde du texte SVG dans un fichier `.svg`.
    *   **Passthrough :** Convertit le type `SVG_TEXT` en `STRING` pour la compatibilité.

</details>

<details>
<summary><code>DXF to SVG</code></summary>

> Convertit un document DXF en code SVG.

*   **Catégorie :** `DAO_master/SVG/Convert`
*   **Description :** Transforme la géométrie DXF en un format SVG textuel, en tentant d'assembler intelligemment les segments pour créer des chemins propres. Offre des contrôles sur la qualité des courbes et la mise en page.

</details>

<details>
<summary><code>Convert SVG → IMG (+colors)</code></summary>

> Convertit un SVG en une image rastérisée et extrait les couleurs utilisées.

*   **Catégorie :** `DAO_master/SVG/Convert`
*   **Description :** Un node de conversion avancé avec deux moteurs de rendu (`natif` ou `cairosvg`) pour une compatibilité maximale.
*   **Sorties :** `image`, `mask`, et `colors_json` (un rapport détaillé des couleurs et formes détectées).

</details>

<details>
<summary><code>Convert IMG → SVG (1-bit)</code></summary>

> Vectorise une image en un SVG monochrome en utilisant Potrace.

*   **Catégorie :** `DAO_master/SVG/Convert`
*   **Description :** Binarise une image (la transforme en noir et blanc pur) puis utilise l'algorithme de Potrace pour tracer les contours des formes, générant ainsi un SVG.

</details>

</details>

<details>
<summary><strong>🛠️ Utilitaires, Filtres et Générateurs</strong></summary>

<details>
<summary><code>DAO Hex/RVB Color Picker</code></summary>

> Des sélecteurs de couleurs interactifs pour choisir des couleurs à partir de listes personnalisables.

*   **Catégorie :** `DAO_master/Color`
*   **💡 Fonctionnement UI :** Créez vos propres listes de couleurs dans les dossiers `hexadecimal_List/` ou `RGB_List/`. Le node affichera des menus déroulants pour choisir le fichier et la couleur. Un bouton `↻` permet de rafraîchir les listes.
*   **Modes :** `Manual`, `Random`, `Increment`, `Decrement`.

</details>

<details>
<summary><code>Folder File Picker</code></summary>

> Un explorateur de fichiers avancé pour sélectionner dynamiquement un fichier dans un dossier.

*   **Catégorie :** `DAO_master/IO`
*   **💡 Fonctionnement UI :** Une interface très réactive où tous les paramètres de filtrage (extensions, RegEx) et de tri mettent à jour un menu déroulant listant les fichiers trouvés en temps réel.
*   **Modes de sélection :** `manual` (via l'UI), `fixed`, `increment`, `decrement`, `randomize` (piloté par la `seed`).

</details>

<details>
<summary><code>DAO Text Maker</code></summary>

> Crée une image, un SVG et un masque à partir d'un texte.

*   **Catégorie :** `DAO_master/Text`
*   **💡 Fonctionnement UI :** Le champ `font_file` devient un menu déroulant listant les polices `.ttf`/`.otf` que vous placez dans le dossier `Fonts/`.
*   **Fonctionnalités :** Contrôle total sur la police, la taille, l'alignement, les couleurs de remplissage/contour, le fond, et la sortie (SVG textuel ou vectorisé).

</details>

<details>
<summary><code>DAO Move</code></summary>

> Applique des transformations (déplacement, échelle, rotation) et des symétries à une image.

*   **Catégorie :** `DAO_master/Utils`
*   **Description :** Permet de manipuler la position, la taille et l'orientation d'une image et de son masque associé, avec un contrôle précis sur le point de pivot.

</details>

<details>
<summary><code>DAO Blur</code></summary>

> Applique un flou gaussien et peut générer une ombre portée.

*   **Catégorie :** `DAO_master/Filter`
*   **Description :** Floute une image et/ou un masque, et peut générer une image séparée contenant une ombre portée personnalisable (couleur, opacité, décalage).

</details>

</details>

# 🚀 Guide d'Installation : Potrace sur Windows

Pour utiliser le node `Convert IMG to SVG` de la manière la plus performante, il est fortement recommandé d'installer l'utilitaire **Potrace** et de l'ajouter au **PATH** de votre système.

Ce guide vous montrera comment faire, étape par étape.

### Étape 1 : Télécharger Potrace

1.  Rendez-vous sur la page officielle de Potrace : [http://potrace.sourceforge.net/#downloading](http://potrace.sourceforge.net/#downloading)
2.  Cherchez la section "Windows" et téléchargez la dernière version 64-bit. Le fichier sera une archive `.zip`, par exemple `potrace-1.16.win64-x64.zip`.

    > **Note :** Prenez bien la version 64-bit (win64) si votre système Windows est 64-bit, ce qui est le cas pour la grande majorité des ordinateurs modernes.

### Étape 2 : Créer un Dossier et Extraire les Fichiers

Pour garder les choses simples et propres, nous allons créer un dossier permanent pour Potrace.

1.  Ouvrez l'Explorateur de Fichiers.
2.  Allez à la racine de votre disque principal, généralement `C:`.
3.  Créez un nouveau dossier et nommez-le `Potrace`. Le chemin sera donc `C:\Potrace`.
4.  Ouvrez le fichier `.zip` que vous avez téléchargé et extrayez **tous les fichiers** qu'il contient directement dans le dossier `C:\Potrace`.

    📁 Votre dossier `C:\Potrace` devrait maintenant contenir des fichiers comme `potrace.exe`, `mkbitmap.exe` et plusieurs fichiers `.dll`.

### Étape 3 : Ajouter Potrace au PATH Système

C'est l'étape la plus importante. Elle permet à Windows (et donc à ComfyUI) de trouver `potrace.exe` depuis n'importe quel emplacement.

1.  Cliquez sur le bouton **Démarrer** de Windows et tapez `variables d'environnement`.
2.  Cliquez sur **"Modifier les variables d'environnement système"**.

    

3.  Dans la fenêtre "Propriétés système" qui s'ouvre, cliquez sur le bouton **"Variables d'environnement..."**.

    

4.  Une nouvelle fenêtre s'ouvre avec deux sections. Nous allons modifier les variables de votre utilisateur (plus sûr et ne nécessite pas de droits administrateur).
    Dans la section du haut ("Variables utilisateur pour [votre_nom]"), trouvez et sélectionnez la variable `Path`, puis cliquez sur **"Modifier..."**.

    

5.  Dans la fenêtre "Modifier la variable d'environnement", cliquez sur **"Nouveau"**.
6.  Un nouveau champ vide apparaît. Tapez ou collez-y le chemin exact du dossier que vous avez créé à l'étape 2 :

    ```
    C:\Potrace
    ```

    

7.  Cliquez sur **OK** pour fermer chaque fenêtre que vous avez ouverte. C'est essentiel pour sauvegarder les changements.

### Étape 4 : Vérifier l'Installation

Pour vous assurer que tout fonctionne correctement :

1.  **Ouvrez un NOUVEAU terminal.** (Important : les terminaux déjà ouverts ne connaîtront pas le nouveau PATH).
    *   Appuyez sur `Win + R`, tapez `cmd` et appuyez sur Entrée.

2.  Dans la fenêtre de commande, tapez la commande suivante et appuyez sur Entrée :

    ```sh
    potrace --version
    ```

3.  Si l'installation a réussi, vous devriez voir s'afficher la version de Potrace, comme ceci :
    ```
    potrace 1.16 (C) 2001-2019 Peter Selinger
    ```

✅ **Félicitations !** Potrace est maintenant correctement installé et configuré sur votre système.

### Dépannage

*   **La commande `potrace` n'est pas reconnue...**
    *   Assurez-vous d'avoir ouvert un **nouveau** terminal après avoir modifié le PATH.
    *   Vérifiez que le chemin `C:\Potrace` dans vos variables d'environnement est correct et ne contient pas de fautes de frappe.
    *   Vérifiez que le fichier `potrace.exe` se trouve bien directement dans `C:\Potrace` (et non dans un sous-dossier).

*   **ComfyUI ne trouve toujours pas Potrace...**
    *   Redémarrez complètement ComfyUI (fermez la console et relancez `run_nvidia_gpu.bat` ou équivalent). Dans certains cas, un redémarrage complet de l'ordinateur peut être nécessaire pour que tous les programmes prennent en compte le nouveau PATH.
