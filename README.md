# ENS Rennes – Convertisseur de relevés pour l'international
Cet outil a pour but de convertir les relevés de notes des étudiants et élèves normaliens de l'École normale supérieure de Rennes du département informatique en un relevé de notes adapté pour l'international, notamment en utilisant le système de notation GPA.

## Motivation
Afin de répondre aux critères de notation à l'international (e.g., des universités américaines), il est fortement bénéfique d'avoir un système de notation connu des universités étrangères à la France.

La motivation est principalement de proposer des relevés de notes équivalents qui permettraient de ne **pas pénaliser** les étudiants et élèves du département informatique de l'ENS Rennes dans leur candidature à l'international : le système de notation de l'ENS Rennes – et en particulier des grandes écoles françaises – est connu, en France, comme plus sévère mais ce n'est pas forcément le cas des universités étrangères.

De plus, le système de notation français (notes sur 20, passage à 10 et difficulté d'obtenir de hautes notes) n'est en général pas connu des universités étrangères : pour maximiser l'égalité et les chances des étudiants et élèves de l'ENS Rennes dans leur candidature, faciliter la lecture et compréhension avec un système de notation commun et adapté est bénéfique.

Enfin, d'autres écoles comme l'INSA Lyon ou d'autres ENS comme l'ENS Ulm proposent déjà des relevés de notes adaptés à l'international en soulignant la difficulté du cursus avec un barème adapté. Il est alors d'autant plus bénéfique de proposer un système similaire pour mettre sur un pied d'égalité les étudiants et élèves de l'ENS Rennes avec les autres écoles.

## Conversion des notes

Chaque école qui propose un tel système a un barème adapté à la difficulté du cursus de son école ou celui d'un département – notamment, pour les ENS. Cela peut être rendu public dans une grille d'équivalences de notes ou être effectué en interne (où la notation est donnée implicitement).
Par exemple :

À l'INSA Lyon, grille publique : [Tableau de conversion de notes](https://www.insa-lyon.fr/sites/www.insa-lyon.fr/files/tableau_de_conversion_des_notes_0.pdf)

À l'ENS Ulm, exemple de relevés de notes de L3 d'un élève au département informatique : [Relevé de notes](https://www.normalesup.org/~rouvroy/ressources/L3_Grades.pdf)

Voici une proposition de grille d'équivalences de notation pour le département informatique de l'ENS Rennes, ci-dessous. Elle est inspirée des exemples ci-dessus (ENS Ulm et INSA Lyon) :

| Note française (sur 20) | GPA  | Lettre |
|--------------------------|------|--------|
| ≥ 16                    | 4.0  | A+     |
| 14 - 15.99              | 4.0  | A      |
| 13 – 13.99              | 3.7  | A-     |
| 12 – 12.99              | 3.33 | B+     |
| 11 – 11.99              | 3.0  | B      |
| 10 – 10.99              | 2.7  | B-     |
| 9 – 9.99                | 2.33 | C+     |
| 8 – 8.99                | 2.0  | C      |
| 7 – 7.99                | 1.7  | C-     |
| < 7                     | 0.0  | F      |
| N/A                     | N/A  | N/A    |

## Outil

L'outil est encore en développement. Il se compose en deux temps :

1. Lecture d'un relevé de notes en PDF-texte (et non image) qui peut être certifié ou non (par la scolarité) : ceci est géré dans le fichier grades.py avec un paramètre dans la fonction read_grades(). Le programme génère dans le dossier config un fichier grades.json qui contient UEs, ECTS et notes. Si une UE n'a pas été validée, au dépend du fichier certifié ou non, il peut ne pas contenir les ECTS. Il est donc laissé à l'utilisateur le soin de vérifier le fichier config/grades.json avec les bons ECTS.

/!\ Les bulletins n'étant pas standardisés, la lecture des documents PDF-textes (et non images) peut échouer. Dans ce cas, il faut modifier à la main les fichiers config/grades.json et config/info.yaml. Lors d'une proposition de standardisation des bulletins, le fichier grades.py sera entièrement refactorisé.

2. Création d'un relevé de notes équivalent en PDF dans le répertoire local : ceci est géré dans le fichier main.py à exécuter.
Il est possible de spécifier les fichiers que main.py doit utiliser à l'aide des options -g, -i et -o. (voir ``python main.py --help`` pour plus d'information)

## Accord

Afin de compléter l'outil, nous avons besoin de l'accord et la collaboration du directeur du département informatique de l'ENS Rennes. Et ce sur les points suivants :

- [x] Validation de la grille d'équivalences de notation proposée ci-dessus.

- [ ] Validation de l'outil ou de son intégration dans le système déjà existant.

- [x] Approbation du contenu du relevé de notes équivalent en PDF généré et remplissage des éléments manquants : signature, tampon.
