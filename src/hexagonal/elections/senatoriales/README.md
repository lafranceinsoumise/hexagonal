# Sénatoriales

Les sénateurs sont élus au suffrage indirect. Leur mandat dure 6 ans, mais le Sénat est renouvelé par moitié et des
élections sénatoriales sont donc organisées tous les 3 ans : à cette fin, les départements sont répartis en deux séries
dont [la composition est prévue dans le code électoral (tableau III).](https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006070239/LEGISCTA000006115479/?anchor=LEGIARTI000023260785#LEGIARTI000023260785)

## Calendrier

Les prochaines élections sénatoriales auront lieu le 27 septembre 2026 et concernent la série n°2.

Voici le calendrier applicable pour cette élection :

- désignation des délégués municipaux : 5 juin
- dépôt des candidatures : du 7 au 11 septembre
- élections : 27 septembre
- début du mandat : 1er octobre

La série n°2 est composée :

- des départements numérotés de 01 (Ain) à 36 (Indre), y compris les deux départements de Corse (2A et 2B)
- des départements numérotés de 67 (Bas-Rhin) à 89 (Yonne)
- de la Guyane
- de la Polynésie française,de Saint-Barthélemy, de Saint-Martin et des îles Wallis-et-Futuna
- de 6 des sénateurs des français de l'étranger

## Composition du collège électoral

Le collège des grands électeurs est constitué de :

- les députés et sénateurs élus dans le département ;
- les conseillers régionaux, votants dans le département correspondant à leur section départementale d'élection ;
- les conseillers de l'assemblée de Corse ;
- les conseillers à l'assemblée de Guyane, à l'assemblée de Martinique, et à l'assemblée de Mayotte ;
- les conseillers départementaux ;
- les conseillers de la métropole de Lyon ;
- les délégués des conseils municipaux.

Cette dernière catégorie représente près de 95 % des grands électeurs.

### Cas particuliers

#### Corse

Dans le mois qui suit son élection, l'Assemblée de Corse procède à la répartition de ses membres entre les collèges
de Corse-du-Sud et de Haute Corse (respectivement 29 et 34 membres)

#### Collectivité européenne d'Alsace

Dans le mois qui suit son élection, le conseil régional du Grand Est procède à la répartition de ses membres élus dans
la section départementale de la Collectivité européenne d'Alsace entre les départements du Bas-Rhin, Haut-Rhin en les
répartissant proportionnellement à la population de ces départements, en suivant la règle de la plus forte moyenne.

En 2026, 61 élus figurent dans la section départementale de la collectivité européenne d'Alsace. Leur répartition entre
les départements s'est faite sur la base des populations de référence en 2021 (donc la population de 2018). Cela donne
donc 37 élus pour le Bas-Rhin et 24 pour le Haut-Rhin.

Les conseillers départementaux d'Alsace votent dans le département où se trouve le canton dans lequel ils ont été élus.

#### Français de l'étranger

12 sénateurs représentent les français de l'étranger et sont renouvelés par moitié.

Le collège des grands électeurs est constitué :

- les sénateurs et députés représentant les français de l'étranger
- les conseillers des Français de l'étranger
- des délégués consulaires, élus simultanément aux conseillers, à raison d'un délégué pour 10 000 inscrits au registre
  des français de l'étranger.

### Les délégués des conseils municipaux

Le
fichier [data/03_main/elections/nombre_conseillers_municipaux.parquet](/productions.md#data/03_main/elections/nombre_conseillers_municipaux.parquet)
indique pour chaque commune le nombre de conseillers municipaux et le nombre total de délégués municipaux attribués à
cette commune (attention à ne garder que les valeurs correspondant à l'année 2026).

Voir aussi [le script qui génère ce fichier](/src/hexagonal/elections/nombre_conseillers_municipaux.py).

#### Communes de moins de 9 000 habitants

Dans les communes de moins de 9 000 habitants, les conseils municipaux élisent parmi leurs membres un certain nombre de
délégués, en fonction de la taille de leur conseil municipal. Le nombre de délégués élu est de :

- 1 pour les conseils de 7 et 11 membres (jusqu'à 500 habitants)
- 3 pour les conseils de 15 membres (de 500 à 1 500 habitants)
- 5 pour les conseils de 19 membres (de 1 500 à 2 500 habitants)
- 7 pour les conseils de 23 membres (de 2 500 à 3 500 habitants)
- 15 pour les conseils de 27 et 29 membres (de 3 500 à 9 000 habitants)

À noter que les communes de 9 000 à 10 000 habitants ont elles aussi un conseil de 29 membres mais se trouvent dans la
catégorie suivante.

Dans les communes de moins de 1 000 habitants, l'élection des 1 à 3 délégués se fait au scrutin secret majoritaire à
deux tours.

Dans les communes de plus de 1 000 habitants, l'élection se fait à la proportionnelle selon la règle de la plus forte
moyenne.

#### Communes de 9 000 habitants et plus

Dans les communes de plus de 9000 habitants, tous les conseillers municipaux sont délégués de droit.

#### Communes de plus de 30 000 habitants

Dans celles-ci, en plus des membres du conseil municipal, celui-ci élit des délégués supplémentaires à raison de 1 pour
800 habitants en sus de 30 000.

L'élection de ces délégués supplémentaires se fait à la proportionnelle selon la règle de la plus forte moyenne.

## Mode de scrutin

Le nombre de sénateurs à élire par département
est [fixé par le code électoral](https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006070239/LEGISCTA000006134805/?anchor=LEGIARTI000006354327#LEGIARTI000006354327)
et déjà compilé dans le tableau
[data/01_raw/lafranceinsoumise/2003-senateurs-par-departement.csv](/sources.md#data/01_raw/lafranceinsoumise/2003-senateurs-par-departements.csv).

### Scrutin majoritaire

Pour les départements où le nombre de sénateurs à élire est de 1 ou 2, l'élection sénatoriale prend la forme
d'un scrutin majoritaire à deux tours. Dans le cas des départements où sont élus deux sénateurs, chaque suffrage exprimé
se porte sur deux noms.

Pour être élu au 1er tour, il faut avoir réuni au moins la majorité absolue des suffrages exprimés et un nombre égal au
quart des électeurs incrits.

Si un deuxième tour doit être organisé, il a lieu le même jour.

### Scrutin proportionnel

Pour les départements où le nombre de sénateurs à élire est de 3 ou plus, l'élection sénatoriale prend la forme d'un
scrutin proportionnel à un tour suivant la règle de la plus forte moyenne. Chaque suffrage exprimé se porte donc vers
une des listes candidates.

L'élection des 6 sénateurs représentant les français de l'étranger par série se fait aussi selon ce mode de scrutin.