# 🎨 ComfyUI_DAO_master

**ComfyUI_DAO_master** est une collection de custom nodes pour **ComfyUI**.
Ces nodes apportent des outils supplémentaires pour la création, la manipulation d’image et l’expérimentation visuelle, avec un focus sur les **workflows vectoriels** (DXF & SVG) et les utilitaires de production.

<p align="center">
<img width="1928" height="1033" alt="image" src="https://github.com/user-attachments/assets/0d425b29-379b-4b0d-b8b6-c168c8d4cee1" />
<img width="1273" height="1075" alt="image" src="https://github.com/user-attachments/assets/a55e99cc-9b3f-4d79-b6cd-e5fa600c6081" />
<img width="1743" height="1094" alt="image" src="https://github.com/user-attachments/assets/dfe6e21a-a0a6-4359-bc90-335bdce485f5" />
<img width="1055" height="1009" alt="image" src="https://github.com/user-attachments/assets/6b7c35ad-9396-4902-ad90-486d0ec05c39" />
<img width="1827" height="1151" alt="image" src="https://github.com/user-attachments/assets/09c76182-d705-49de-bf19-84aa85c23fc2" />
<img width="1380" height="996" alt="image" src="https://github.com/user-attachments/assets/67f70e2a-432d-4372-b683-31b0c6f0c1f3" />
<img width="898" height="1097" alt="image" src="https://github.com/user-attachments/assets/4595c263-a446-4710-a276-5934f1a38fea" />
<img width="625" height="723" alt="image" src="https://github.com/user-attachments/assets/13de492e-721c-4646-961e-84433cfa3932" />
<img width="825" height="957" alt="image" src="https://github.com/user-attachments/assets/0de4a91c-1d96-4deb-a3b6-a267ab5f2707" />
<img width="578" height="678" alt="image" src="https://github.com/user-attachments/assets/e0357bf7-d350-4ba9-af7e-355a28485498" />
<img width="2306" height="1026" alt="image" src="https://github.com/user-attachments/assets/28d4709c-761d-4454-bdb2-0e87891b2d43" />

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
<summary><code>DAO RVB Color Picker</code></summary>

> Un sélecteurs de couleurs interactifs pour choisir des couleurs à partir de listes personnalisables.

*   **Catégorie :** `DAO_master/Color`
*   **💡 Fonctionnement UI :** Créez vos propres listes de couleurs dans le dossier `RGB_List/`. Le node affichera des menus déroulants pour choisir le fichier et la couleur. Un bouton `↻` permet de rafraîchir les listes.
*   **Modes :** `Manual`, `Random`, `Increment`, `Decrement`.

</details>

<details>
<summary><code>folder_file_pro</code></summary>

- **Catégorie** : `DAO_master/IO`
- **Vue** : Grille ou Liste, défilement fiable, double-clic pour ouvrir/preview, bouton **Up** & **Explorer**.
- **Aperçus** : vignettes images, SVG inline ; autres fichiers affichés avec un badge `[File.ext]`. Icône dossier PNG non déformée.
- **Filtres** : `extensions`, `name_regex` (modes `include` / `exclude`, option *ignore case*).
- **Tri** : `sort_by = name | mtime | size` + `descending` (asc/desc).
- **Sélection** :  
  - **Modes** : `manual` (UI), `fixed`, `increment`, `decrement`, `randomize` (piloté par `seed`).  
  - **Raccourcis** : *type-to-select* (taper des lettres pour sauter au prochain item).
- **Sorties** :  
  - `file_path` (chemin complet), `filename`, `dir_used`, `files_json` (liste des fichiers)  
  - `file_info` (JSON) : taille octets, dates ISO (création/modif), et si image/vidéo → `width` / `height`.
- **Compat** : l’icône de dossier est référencée via `new URL("./ico_dossier.png", import.meta.url).href` → fonctionne quel que soit l’emplacement/nom du dossier de l’extension.

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

<details>
<summary><strong>💡 Guides d'Installation (Potrace & Polices)</strong></summary>

<br>

<details>
<summary><strong>🚀 Installer Potrace sur Windows (pour la vectorisation d'images)</strong></summary>

> Pour utiliser le node `Convert IMG to SVG` de la manière la plus performante, il est fortement recommandé d'installer l'utilitaire **Potrace** et de l'ajouter au **PATH** de votre système. Ce guide vous montrera comment faire, étape par étape.

#### Étape 1 : Télécharger Potrace
1.  Rendez-vous sur la page officielle : [http://potrace.sourceforge.net/#downloading](http://potrace.sourceforge.net/#downloading)
2.  Cherchez la section "Windows" et téléchargez la dernière version 64-bit (ex: `potrace-1.16.win64-x64.zip`).
    > **Note :** Prenez bien la version 64-bit (win64), adaptée à la majorité des ordinateurs modernes.

#### Étape 2 : Créer un Dossier et Extraire les Fichiers
1.  Dans l'Explorateur de Fichiers, allez à la racine de votre disque `C:`.
2.  Créez un nouveau dossier nommé `Potrace`.
3.  Extrayez **tous les fichiers** de l'archive `.zip` téléchargée directement dans ce dossier `C:\Potrace`.
    > 📁 Votre dossier `C:\Potrace` doit maintenant contenir `potrace.exe` et d'autres fichiers.

#### Étape 3 : Ajouter Potrace au PATH Système
> C'est l'étape la plus importante. Elle permet à Windows de trouver `potrace.exe` depuis n'importe où.

1.  Dans le menu Démarrer, cherchez et ouvrez **"Modifier les variables d'environnement système"**.
2.  Cliquez sur le bouton **"Variables d'environnement..."**.
3.  Dans la section du haut ("Variables utilisateur"), sélectionnez la ligne `Path` et cliquez sur **"Modifier..."**.
4.  Cliquez sur **"Nouveau"** et collez le chemin de votre dossier : `C:\Potrace`.
5.  Cliquez sur **OK** sur toutes les fenêtres pour sauvegarder.

#### Étape 4 : Vérifier l'Installation
1.  **Ouvrez un NOUVEAU terminal** (via `cmd` dans le menu Démarrer).
2.  Tapez `potrace --version` et appuyez sur Entrée.
3.  Si tout est correct, la version de Potrace s'affichera.
    > ✅ **Félicitations !** Potrace est prêt. Si ComfyUI ne le trouve pas, redémarrez-le.

</details>

<details>
<summary><strong>✍️ Installer des Polices Personnalisées (pour DAO Text Maker)</strong></summary>

> Le node `DAO Text Maker` vous permet d'utiliser n'importe quelle police au format `.ttf` ou `.otf`. L'installation est très simple.

#### Étape 1 : Trouver et Télécharger une Police
> Choisissez une police sur un des sites recommandés. Cherchez le bouton "Download" pour obtenir un fichier `.zip`.
> *   [**Google Fonts**](https://fonts.google.com/) (le plus sûr)
> *   [**Fontshare**](https://www.fontshare.com/)
> *   [**Velvetyne**](https://velvetyne.fr/)
> *   [**DaFont**](https://www.dafont.com/fr/) (**Attention : vérifiez la licence de chaque police !**)

#### Étape 2 : Localiser et Copier la Police
1.  Naviguez jusqu'au dossier : `ComfyUI/custom_nodes/ComfyUI_DAO_master/Fonts/`.
2.  Ouvrez le `.zip` que vous avez téléchargé.
3.  Copiez le ou les fichiers **`.ttf`** ou **`.otf`** directement dans ce dossier `Fonts`.

#### Étape 3 : Rafraîchir dans ComfyUI
1.  Retournez dans ComfyUI.
2.  Sur votre node `DAO Text Maker`, cliquez sur le bouton de rafraîchissement **`↻`**.
3.  Votre nouvelle police apparaîtra dans le menu déroulant `font_file`.

#### ⚠️ Note sur les Licences
> Respectez le travail des créateurs. Les polices de **Google Fonts, Fontshare et Velvetyne** sont généralement open-source et sûres pour tout usage. Sur **DaFont**, beaucoup de polices sont "gratuites pour un usage personnel" uniquement. Vérifiez toujours la licence avant utilisation.

</details>

</details>

---
<div align="center">

<h3>🌟 <strong>Show Your Support</strong></h3>
<p>If this project helped you, please consider giving it a ⭐ on GitHub!</p>
<p><strong>Made with ❤️ for the ComfyUI community</strong></p>
<p><strong>by Orion4D</strong></p>
<a href="https://ko-fi.com/orion4d">
<img src="https://ko-fi.com/img/githubbutton_sm.svg" alt="Buy Me A Coffee" height="41" width="174">
</a>

</div>
