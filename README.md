# Hexagonal

Ce dépôt agrège l'information électorale, administrative et géographique française 
nécessaire pour faciliter l'analyse électorale.

- [Liste des fichiers mis à disposition](productions.md)
- [Liste des sources utilisées](sources.md)

## Organisation du projet

Les données sont stockées dans le dossier `data` avec les sous-dossiers suivants:

- `01_raw/`: Données brutes (téléchargées)
- `02_clean/`: Données nettoyées (formatées, filtrées)
- `03_main/`: Données prêtes à l'emploi par étude (_feature engineering_, jointures,
  aggrégats, etc.)

## Mise en place

### Installation des dépendances

L'installation du projet se fait avec le gestionnaire de paquets
uv ([voir instructions d'installation](https://docs.astral.sh/uv/getting-started/installation/)).

Pour créer l'environnement virtuel et installer les dépendances, utilisez la commande
suivante.

```bash
uv sync
```

Pour pouvoir utiliser `just`, il est conseillé de l'installer globalement avec `uv` s'il
n'est pas déjà disponible :

```bash
uv tool install rust-just
```

Définir les alias suivants permettent de simplifier l'utilisation de dvc et de just
```bash
alias dvc="uv run dvc"
alias just="uv run just"
```

### Récupération initiale des données

Une version initiale des données (et notamment des sources, dont certaines peuvent ne
plus être disponibles en ligne) peut être récupérée depuis le cache en ligne.

```bash
uv run just pull
```

Une fois cette opération terminée, tous les fichiers devraient avoir été créés dans le dossier
`data`.

## Gestion des données sources

L'ensemble des données sources sont présentes dans le dossier `data/01_raw`. Les 
fichiers sont organisés dans des dossiers correspondant aux éditeurs des données.

L'ensemble des fichiers sources est versionné avec dvc et non directement avec git. En 
effet, git ne gère pas correctement les fichiers volumineux. En pratique, cela signifie
que les jeux de données ne sont jamais ajoutés directement dans le dépôt git (et le
fichier `.gitignore` exclut d'ailleurs la plupart des extensions correspondant à des 
jeux de données). À chaque jeu de donnée correspond un fichier `.dvc` généré par DVC.
C'est ce dernier qui doit être ajouté dans git.

### Ajouter un jeu de données source

La démarche est différente selon qu'il s'agisse d'un jeu de données disponible sur 
internet, ou non (par exemple s'il s'agit d'un jeu de données produit par la France
insoumise).

Dans les deux cas, la commande à utiliser crée un fichier `.dvc` qu'il faut 
impérativement versionner avec git. Le fichier lui-même ne doit pas être versionné

#### Depuis une URL externe

La commande `import-url` de DVC permet d'importer une source externe depuis une URL :

```bash
uv run dvc import-url <url> data/01_raw/<editeur>/<nom du fichier>
```

#### Sans URL externe

Le fichier doit être enregistré dans le dossier `data/01_raw/<editeur>/<nom fichier>`.
La commande `uv run dvc add data/01_raw/<editeur>/<nom fichier>` permet ensuite de
générer le fichier `.dvc`.

### Mettre à jour une source existante

Les sources ne sont pas mises à jour automatiquement. Pour les mises à jour, il y a
trois  cas de figure.

#### Il n'y a pas d'URL externe

Il faut alors éditer le fichier directement, ou le remplacer par la nouvelle version.
Une fois que c'est fait, la commande `uv run dvc add` permet de mettre à jour le fichier 
`.dvc` correspondant pour prendre en compte les modifications correspondantes.

#### L'URL de la source ne change pas

Pour certains fichiers, l'URL de téléchargement renvoit un état actuel de la source de
données qui peut donc changer à n'importe quel moment. C'est par exemple le cas pour les
données de l'Assemblée nationale. Il suffit alors de faire tourner la commande :

```bash
uv run dvc update <chemin du fichier dans data/01_raw> 
```

Cette commande interroge le serveur d'origine, télécharge la nouvelle version le cas
échéant, et met à jour le fichier .dvc.

#### L'URL de la source change

Pour d'autres fichiers, l'URL correspond à une édition particulière du fichier, et il
faut donc la changer pour mettre à jour le fichier. C'est par exemple le cas du COG.

Dans ce cas, il faut utiliser la commande :

```bash
uv run dvc import-url <nouvelle url> <chemin complet du fichier à mettre à jour>
```

### Documenter les sources

Chaque source ajoutée doit être documentée, voir ci-dessous
## Traitements des données

Les traitements de données sont définis dans le fichier `dvc.yaml`
([voir la documentation de DVC](https://dvc.org/doc/user-guide/pipelines/defining-pipelines)).

### Reproduire les traitements de données

La commande `uv run dvc repro` fait tourner tous les traitements de données qui ne sont
plus à jour.

S'il y en avait, le fichier `dvc.lock` est mis à jour en conséquence. Si c'est le cas,
il est impératif :

1. de versionner `dvc.lock`
2. de pousser les nouvelles versions des fichiers.


### Conventions à suivre pour ajouter de nouveaux traitements de données

De préférence, les traitements de données doivent être écrits en Python. Si nécessaire,
il est toutefois possible d'ajouter des traitements sous la forme de scripts bash.

#### Écrire un traitement de données en Python

Les traitements de données en Python doivent respecter les conventions suivantes :

1. Chaque traitement doit être un module Python exécutable dans le paquet `hexagonal` ;
   le fichier source doit donc se trouver dans le dossier `src/hexagonal`.
2. Sauf execption, le module exécutable doit prendre en argument les chemins vers les fichiers sources
   et les fichiers destination plutôt que d'accéder aux fichiers avec un chemin en dur.
   Il est possible d'utiliser la bibliothèque `click` pour faciliter le traitement des
   arguments.


#### Écrire un traitement de données en bash

Les traitements de données en Bash doivent respecter les conventions suivantes :

1. Les scripts de traitements doivent se trouver dans le dossier `src/scripts`.
2. Sauf exception, le script doit prendre en argument les chemins vers les fichiers sources
   et les fichiers destination plutôt que d'accéder aux fichiers avec un chemin en dur, dans la mesure du possible.
3. Les scripts ne peuvent utiliser de dépendances externes qu'en cas de nécessité.

#### Ajouter le traitement dans `dvc.yaml`

Une fois le traitement écrit, il faut l'ajouter dans le fichier `dvc.yaml` selon les
conventions suivantes :

1. Donner un nom explicite au nom du traitement, en s'assurant qu'il soit bien unique
2. La liste des dépendances doit inclure aussi bien la source du traitement que les jeux de données utilisés
3. Les variables `${src}`, `${raw}`, `${clean}` et `${main}` doivent être utilisés plutôt que les chemins complets.
4. Pour un traitement en python, le script doit être invoqué avec la syntaxe `${python} <nom.du.module>`


### Pousser les modifications

Lorsque des fichiers ont été modifiés, il faut les pousser vers le cache distant de DVC
pour les rendre accessibles. Pour cela, il est nécessaire de me contacter pour obtenir
des droits en écriture sur le bucket S3 `hexagonal-data`.

```shell
just push
```

## Documentation

L'ensemble des sources, et l'ensemble des données produites sont documentés. Cette
documentation se trouve dans un fichier portant le même nom que le fichier documenté,
suivi de l'extension `.toml`.

### Créer la documentation pour un nouveau fichier

La commande suivante permet de créer une version initiale de ces fichiers pour les
nouvelles sources et productions :

```shell
just scaffold
```

Elle met par ailleurs à jour la liste des dépendances des différents fichiers (à partir
des pipelines définis dans DVC).

### Documenter les sources

Un fichier `.toml` est créé dans le même dossier que les sources ajoutées par la commande ci-dessus.
Pour une source, les propriétés suivantes peuvent être renseignées :

| Propriété | Description                                 |
|-----------|---------------------------------------------|
| `nom` | Une désignation complète du jeu de données  |
| `description` | Une description aussi complète que possible |
| `editeur` | L'éditeur du jeu de données                 |
| `date` | La date du jeu de données, si pertinent     |
| `info_url` | Une URL vers une documentation externe      |

### Documenter les productions

Un fichier `.toml` est créé dans le même dossier que les fichiers produits. Pour un fichier produit,
les propriétés suivantes peuvent être renseignées :

| Propriété     | Description                                         |
|---------------|-----------------------------------------------------|
| `nom`         | Une désignation complète du jeu de données          |
| `description` | Une description aussi complète que possible         |
| `section`     | La catégorie à laquelle appartient cette production |

Par ailleurs, pour les fichiers de type tabulaire (CSV ou parquet), il faut documenter les différentes 
colonnes avec les propriétés suivantes :

| Propriété     | Description                                              |
|---------------|----------------------------------------------------------|
| `type`        | Le type de données de la colonne                         |
| `description` | Une description plus précise, lorsqu'elle est nécessaire |
| `nullable`    | Si la colonne admet des valeurs nulles.                  |

### Générer la documentation

La commande suivante permet de créer ou mettre à jour les deux fichiers <sources.md>
et <productions.md> :

```shell
just build_doc
```

### Ajouter les bons headers aux fichiers dans S3

Pour permettre le téléchargement correct des fichiers depuis les fichiers <sources.md>
et <productions.md>, il faut réécrire les headers HTTP `Content-Type` et
`Content-Disposition` pour y mettre les bons types et noms de fichiers.

```shell
just push
```