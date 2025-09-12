import pdfplumber
import json
import re
import argparse

def read_grades(file, certified=True):
    """
        Given the grades in a PDF file (certified or not),
        this function returns
            - the name, surname, birthdate and location of the student,
            - the academic year,
            - and the courses with associated grades and credits.
    """
    grades = {} # dict: UE -> (grade, credits) if certified, otherwise, UE -> (grade, gained_credits, credits)

    # 1. Read raw data
    data = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                data.extend(text.splitlines())

    if len(data) == 0:
        print("[Error] Image based")

        return None
    
    # 2. Process data
    if certified:
        academic_year = int(data[0].split(" ")[-1].split("/")[0]) # Year n/n+1, retrieves n
        surname, name = data[4].split(" ")
        birth_date, birth_location = data[9].split(":")[1:]
        birth_date = birth_date[:len(birth_date)-4].strip()
        birth_location = birth_location.strip()

        n_data = data[5:]
        for line in n_data:
            if line.startswith("UE"):
                line = line[5:]
                idx_end = line.index("/20")
                idx_beg = line.rfind(" ", 0, idx_end-1) # remove the space before /
                grade = float(line[idx_beg: idx_end].strip().replace(",", "."))
                course = line[:idx_beg]
                # Si l'UE n'est pas validée, alors les ECTS ne sont pas affichés et donc il n'y a pas d'espace avant le dernier slash.
                if line[-2] == " ":
                    credits = int(line[-1])
                else:
                    credits = 0
                print(f"{course} — {grade}/20 ({credits}ECTS)")
                grades[course] = (grade, credits)
    else:
        name, surname = data[2].split(" ")
        academic_year = int(data[4].split("/")[0].split(":")[-1].strip()) # Year n/n+1, retrieves n
        birth_date, birth_location = None, None

        n_data = data[5:]
        for line in n_data:
            if (line.endswith("AJ") or line.endswith("ADM")) and not ("Semestre" in line or "L3" in line or "Moyenne" in line or "Séminaire" in line or "Stage" in line or "Master" in line):
                line = line[line.index(" ")+1:]
                # Le bulletin étant parfois mal réalisé, il peut contenir un nombre imaginaire d'ECTS, e.g., 2I.
                # Le fix ici est simpliste et volontairement simpliste.
                line = line.replace("I/", "/").replace("UE - ", "").replace("EU - ", "")
                idx_slash = line.rfind("/")
                print("line", line)
                if idx_slash != -1: # Les ECTS ne sont pas affichés en cas de non-validation.
                    # Le bulletin était parfois (très) mal réalisé, il peut contenir une note imaginaire, e.g. 16F.
                    # On utilise ici quelque chose de plus raffiné, i.e., une regex.
                    grade = float(re.sub(r"[A-Za-z]", "", line[idx_slash+3: line.rfind(" ")].strip().replace(",", ".")))
                    course = line[:idx_slash - 2]
                    gained_credits = int(line[idx_slash-1: idx_slash])
                    credits = int(line[idx_slash+1: idx_slash+2])
                    #print(f"{course} — {grade}/20 ({gained_credits}/{credits}ECTS)")
                else:
                    idx_end = line.rfind(" ")
                    idx_beg = line.rfind(" ", 0, idx_end)
                    grade = float(re.sub(r"[A-Za-z]", "", line[idx_beg+1: idx_end].strip().replace(",", ".")))
                    course = line[:idx_beg]
                    credits = 0
                grades[course] = (grade, gained_credits, credits)
    return name, surname, academic_year, birth_date, birth_location, grades

parser = argparse.ArgumentParser()
parser.add_argument('--file', type=str)
parser.add_argument('-c', action='store_true') 
args = parser.parse_args()

file = args.file
certified = args.c
name, surname, academic_year, birth_date, birth_location, grades = read_grades(file, certified)

#print(name, surname, academic_year, birth_date, birth_location)
with open('config/grades.json', 'w', encoding='utf8') as json_file:
    json.dump(grades, json_file, indent=4, ensure_ascii=False)
print(f"Grades saved to grades.json")