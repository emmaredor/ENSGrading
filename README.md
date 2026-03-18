# Générateur de Relevés de Notes ENS

Un programme Python pour générer des relevés de notes académiques professionnels au format PDF. Prend en charge la génération individuelle d'étudiant à partir de fichiers YAML et la génération par lots à partir de fichiers Excel.

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

## 📁 Structure du Projet

```
ENSGrading/
├── main.py              # Point d'entrée principal
├── data_loader.py           # Utilitaires de chargement de données (YAML, JSON, Excel)
├── text_formatter.py        # Formatage de texte et traitement de modèles
├── grades_processor.py      # Calculs de notes et conversion GPA
├── pdf_generator.py         # Création et stylisation PDF
├── requirements.txt         # Dépendances Python
├── assets/
│   ├── logo.png            # Logo de l'école pour les PDF
│   └── text.json           # Modèles de texte pour les sections du relevé
└── config/
    ├── info_student.yaml   # Informations étudiant (mode individuel)
    ├── info_author.yaml    # Informations auteur
    ├── grades.json         # Données de notes (mode individuel)
    └── students.xlsx       # Données étudiants pour traitement par lots
```

## 🚀 Fonctionnalités

### Mode Individuel
- Génère un PDF à partir de fichiers YAML et JSON individuels 
- Nom de fichier de sortie personnalisé / personnalisable

### Mode Batch
- Génère plusieurs PDF à partir d'un fichier Excel
- Formatage automatique des noms de fichier de sortie (NOM Prénom)

### Fonctionnalités PDF
- Mise en page professionnelle avec logo de l'école
- Tableaux de notes formatés avec conversion GPA
- Formatage de nombres ordinaux (1er, 2ème, 3ème, etc.)
- Système de compensation pour le calcul des crédits et ajout d'une note automatiquement afin d'expliquer le système de compensation
- Stylisation personnalisée pour l'ENS Rennes

## 📋 Prérequis

```bash
pip install -r requirements.txt
```

Packages requis :
- `reportlab` - Génération PDF
- `pandas` - Traitement de fichiers Excel
- `openpyxl` - Lecture de fichiers Excel
- `PyYAML` - Traitement de fichiers YAML

## 🔧 Utilisation

### Mode Étudiant Individuel

#### Avec fichiers séparés :
```bash
python main.py --single --student-info config/info_student.yaml --author-info config/info_author.yaml --year-info config/info_year.yaml --grades config/grades.json -o output/transcript.pdf
```

#### Avec fichier combiné hérité :
```bash
python main.py --single \
    -i config/info.yaml \
    --grades config/grades.json
```

### Mode Batch

```bash
python main.py --batch \
    --students-excel config/students.xlsx \
    --author-yaml config/info_author.yaml \
    -o output_directory
```

## 📄 Formats de Fichiers

### YAML Informations Étudiant (`info_student.yaml`)
```yaml
student:
  gender: Mr
  name: Jean
  firstname: DUPONT
  pronoun: he
  dob: 26th of August 2000
  pob: Rennes (FRANCE)
```

### YAML Informations Auteur (`info_author.yaml`)
```yaml
author:
  gender: Mr
  name: Martin
  firstname: QUINSON
  field: Computer Science
  title: Director of the Computer Sciences teaching department
  schoolyear: 2023-2024
  yearname: First year of Master's degree in Computer Science
```

### JSON Notes (`grades.json`)
```json
{
  "Programming 1": [16.5, 6, 6],
  "Algorithms": [14.2, 6, 6],
  "Mathematics": [12.8, 3, 3]
}
```
Format : `[note_sur_20, ECTS_obtenues, ECTS_max]`

OU

```json
{
  "Programming 1": [16.5, 6],
  "Algorithms": [14.2, 6],
  "Mathematics": [12.8, 3]
}
```
Format : `[note_sur_20, ECTS_max]`

### Structure du Fichier Excel
Le fichier Excel doit avoir des en-têtes en ligne 1 avec des colonnes comme :
- `Etud_Nom` - Nom de famille de l'étudiant
- `Etud_Prénom` - Prénom de l'étudiant
- `Etud_Naissance` - Date de naissance
- `Etud_Ville` - Ville de naissance
- `ObjXX_Libellé` - Noms des cours
- `ObjXX_Note_Ado/20` - Notes (échelle 0-20)
- `ObjXX_Crédits` - Crédits des cours

Si le fichiers contient d'autres colonnes, elles seront ignorées.

## 🏗️ Architecture

Le code source est organisé en modules spécialisés :

### `data_loader.py`
- **DataLoader** : Gère les opérations de fichiers YAML et JSON
- **ExcelStudentLoader** : Traite les fichiers Excel pour le mode batch
- Correspondance flexible de motifs de colonnes
- Validation de données et gestion d'erreur

### `text_formatter.py`
- **TextFormatter** : Traitement de modèles et remplacement de variables
- **DateFormatter** : Formatage de dates avec nombres ordinaux
- **NameFormatter** : Capitalisation des noms (NOM Prénom)

### `grades_processor.py`
- **GradeConverter** : Conversion des notes en notes lettres et GPA
- **CreditCalculator** : Calculs de crédits avec logique de compensation
- **GradeTableGenerator** : Crée des tableaux de notes formatés
- **GradeValidator** : Valide l'intégrité des données de notes

### `pdf_generator.py`
- **TranscriptPDFGenerator** : Orchestrateur principal de création PDF
- **PDFStyleManager** : Gère les polices, styles et formatage
- **PDFHeaderGenerator** : Crée les en-têtes avec logo et titres
- **PDFTableGenerator** : Formate les tableaux de notes
- **PDFFooterGenerator** : Ajoute le pied de page institutionnel

### `main.py`
- **TranscriptGenerator** : Coordinateur de logique métier principal
- **CommandLineInterface** : Analyse et validation d'arguments
- Gestion d'erreur et retour utilisateur

## 🎨 Personnalisation

### Stylisation
Modifiez les styles dans `pdf_generator.py` :
- Tailles et familles de polices
- Couleurs et espacement
- Formatage de tableaux
- Dimensions de mise en page

### Modèles de Texte
Éditez `assets/text.json` pour personnaliser :
- Texte d'introduction
- Informations sur l'école
- Description du système de notation
- Déclarations de certification

### Système de Compensation
- Cours individuel : Crédits attribués seulement si note ≥ 10
- Moyenne générale > 10 : Tous les crédits attribués par compensation
- Cours échoués marqués d'un astérisque (*)

## 🐛 Dépannage

### Problèmes Courants

1. **"Excel file headers not found"**
   - Vérifiez que les en-têtes sont en ligne 1 (pas ligne 0)
   - Vérifiez que les noms de colonnes correspondent aux motifs attendus

2. **"Missing required fields"**
   - Assurez-vous que tous les champs YAML requis sont présents
   - Vérifiez les fautes de frappe dans les noms de champs

3. **"Logo not found"**
   - Placez le logo à `assets/logo.png`
   - Assurez-vous que l'image est au format PNG

4. **macOS hashlib errors**
   - Le script gère automatiquement ce problème courant sur macOS

## 📈 Performance

- Mode individuel : < 1 seconde par relevé
- Mode lot : ~2-3 secondes par relevé
- Utilisation mémoire : ~50MB pour un lot typique de 20 étudiants

## 📝 Licence

Ce projet est développé pour usage académique à l'ENS Rennes (École Normale Supérieure de Rennes).