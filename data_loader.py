"""
Data Loading Module for ENS Transcript Generator

This module handles loading data from various file formats:
- YAML files (student info, author info)
- JSON files (text templates, grades)
- Excel files (batch student data)

Author: ENS Transcript Generator
Date: September 2025
"""

import json
import yaml
import pandas as pd
from typing import Dict, List, Any, Optional
import os


class DataLoader:
    """Handles loading data from various file formats for transcript generation."""
    
    @staticmethod
    def load_yaml_file(file_path: str) -> Dict[str, Any]:
        """
        Load data from a YAML file.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Dictionary containing the YAML data
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            yaml.YAMLError: If the file is not valid YAML
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"YAML file not found: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    
    @staticmethod
    def load_json_file(file_path: str) -> Dict[str, Any]:
        """
        Load data from a JSON file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Dictionary containing the JSON data
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file is not valid JSON
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"JSON file not found: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    
    @staticmethod
    def save_json_file(data: Dict[str, Any], file_path: str) -> None:
        """
        Save data to a JSON file.
        
        Args:
            data: Dictionary to save
            file_path: Path where to save the JSON file
        """
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_student_info(cls, file_path: str) -> Dict[str, Any]:
        """
        Load student information from a YAML file.
        
        Args:
            file_path: Path to the student info YAML file
            
        Returns:
            Dictionary with student data, ensuring 'student' key exists
        """
        data = cls.load_yaml_file(file_path)
        return {'student': data['student']} if 'student' in data else data
    
    @classmethod
    def load_author_info(cls, file_path: str) -> Dict[str, Any]:
        """
        Load author information from a YAML file.
        
        Args:
            file_path: Path to the author info YAML file
            
        Returns:
            Dictionary with author data, ensuring 'author' key exists
        """
        data = cls.load_yaml_file(file_path)
        return {'author': data['author']} if 'author' in data else data
    
    @classmethod
    def load_combined_info(cls, file_path: str) -> Dict[str, Any]:
        """
        Load combined student and author information from a single YAML file.
        This is for legacy support.
        
        Args:
            file_path: Path to the combined info YAML file
            
        Returns:
            Dictionary containing both student and author data
        """
        return cls.load_yaml_file(file_path)
    
    @classmethod
    def load_text_templates(cls, file_path: str) -> Dict[str, str]:
        """
        Load text templates from a JSON file.
        
        Args:
            file_path: Path to the text templates JSON file
            
        Returns:
            Dictionary mapping template names to template strings
        """
        return cls.load_json_file(file_path)
    
    @classmethod
    def load_grades_data(cls, file_path: str) -> Dict[str, List[float]]:
        """
        Load grades data from a JSON file.
        
        Args:
            file_path: Path to the grades JSON file
            
        Returns:
            Dictionary mapping course names to either:
            - [grade, max_credits] (2-element format)
            - [grade, credits_obtained, max_credits] (3-element format)
        """
        return cls.load_json_file(file_path)


class ExcelStudentLoader:
    """Handles loading student data from Excel files for batch processing."""
    
    @staticmethod
    def format_date_from_excel(date_value: Any) -> str:
        """
        Convert date from Excel format to readable text format.
        
        Args:
            date_value: Date value from Excel (string like "26/09/2001" or pandas datetime)
            
        Returns:
            Formatted date string like "26th of September 2001"
        """
        try:
            if isinstance(date_value, str):
                # Handle string format like "26/09/2001"
                day, month, year = date_value.split('/')
            else:
                # Handle pandas datetime
                day = str(date_value.day)
                month = str(date_value.month)
                year = str(date_value.year)
            
            # Convert to ordinal
            day_int = int(day)
            if day_int in [11, 12, 13]:
                suffix = 'th'
            elif day_int % 10 == 1:
                suffix = 'st'
            elif day_int % 10 == 2:
                suffix = 'nd'
            elif day_int % 10 == 3:
                suffix = 'rd'
            else:
                suffix = 'th'
            
            # Month names
            months = [
                '', 'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ]
            
            month_name = months[int(month)]
            return f"{day_int}{suffix} of {month_name} {year}"
        except Exception:
            return str(date_value)  # Fallback to original if parsing fails
    
    @staticmethod
    def find_column_by_patterns(columns, patterns: List[str]) -> Optional[str]:
        """
        Find a column in a list of column names that matches any of the given patterns.
        
        Args:
            columns: List of column names to search
            patterns: List of patterns to search for in column names
            
        Returns:
            Column name if found, None otherwise
        """
        for pattern in patterns:
            for col in columns:
                # Handle both direct column name and DataFrame column access
                col_str = str(col)
                if pattern.lower() in col_str.lower():
                    return col
        return None
    
    @staticmethod
    def extract_program_info(df: pd.DataFrame) -> Dict[str, str]:
        """
        Extract program name and school year information from the Excel file.
        
        Args:
            df: Raw DataFrame read from Excel file without header parameter
            
        Returns:
            Dictionary with program_name and school_year
        """
        program_info = {
            'program_name': 'ENS Computer Science Program',
            'school_year': 'Current Academic Year'
        }
        
        try:
            # Look for program name in row 5 (matches the target Excel format)
            for i in range(5, 10):  # Look in rows 5-9
                if i < len(df):
                    row = df.iloc[i]
                    for col in df.columns:
                        val = row.get(col)
                        if pd.notna(val) and isinstance(val, str) and 'Informatique' in val:
                            program_info['program_name'] = str(val)
                            print(f"Found program name in row {i}, col {col}: {val}")
                            break
            
            # Look for school year in row 1 (matches the target Excel format)
            for i in range(0, 5):  # Look in rows 0-4
                if i < len(df):
                    row = df.iloc[i]
                    
                    # First check for "ANNEE UNIVERSITAIRE" pattern
                    for j, val in enumerate(row):
                        if pd.notna(val) and isinstance(val, str) and "UNIVERSITAIRE" in val.upper():
                            print(f"Found 'UNIVERSITAIRE' in row {i}, column {j}")
                            
                            # Check next columns for years - specifically for pattern like "2023" followed by "/"
                            # followed by "2024" which may be in separate columns
                            year1 = None
                            year2 = None
                            
                            # Check for year1 in next column
                            if j + 1 < len(row) and pd.notna(row.iloc[j + 1]):
                                try:
                                    if isinstance(row.iloc[j + 1], (int, float)):
                                        year1 = int(row.iloc[j + 1])
                                        print(f"Found year1: {year1}")
                                except (ValueError, TypeError):
                                    pass
                                    
                            # Check for year2, which might be 2 columns over due to a "/" separator
                            if j + 2 < len(row) and pd.notna(row.iloc[j + 2]) and isinstance(row.iloc[j + 2], str) and "/" in row.iloc[j + 2]:
                                # If next column is "/", check the one after
                                if j + 3 < len(row) and pd.notna(row.iloc[j + 3]):
                                    try:
                                        if isinstance(row.iloc[j + 3], (int, float)):
                                            year2 = int(row.iloc[j + 3])
                                            print(f"Found year2: {year2}")
                                    except (ValueError, TypeError):
                                        pass
                            elif j + 2 < len(row) and pd.notna(row.iloc[j + 2]):
                                # Direct check for year2
                                try:
                                    if isinstance(row.iloc[j + 2], (int, float)):
                                        year2 = int(row.iloc[j + 2])
                                        print(f"Found year2: {year2}")
                                except (ValueError, TypeError):
                                    pass
                                    
                            # If we found both years, format the school year
                            if year1 and year2 and abs(year2 - year1) == 1 and 2000 <= year1 <= 2100:
                                program_info['school_year'] = f"{year1} / {year2}"
                                print(f"Found school year in row {i}: {program_info['school_year']}")
                                break
                                
                    # General check for consecutive years in any column
                    if program_info['school_year'] == 'Current Academic Year':  # If we haven't found it yet
                        for j in range(len(row) - 1):
                            if j < len(row) - 1:
                                val1 = row.iloc[j]
                                val2 = row.iloc[j + 1]
                                
                                if pd.notna(val1) and pd.notna(val2):
                                    try:
                                        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                                            year1 = int(val1)
                                            year2 = int(val2)
                                            if abs(year2 - year1) == 1 and 2000 <= year1 <= 2100 and 2000 <= year2 <= 2100:
                                                program_info['school_year'] = f"{year1} / {year2}"
                                                print(f"Found consecutive years in row {i}: {program_info['school_year']}")
                                    except (ValueError, TypeError):
                                        pass
        except Exception as e:
            print(f"Warning: Could not extract program info: {e}")
        
        return program_info
    
    @classmethod
    def load_students_from_excel(cls, file_path: str) -> List[Dict[str, Any]]:
        """
        Load student data from an Excel file for batch processing.
        
        Args:
            file_path: Path to the Excel file containing student data
            
        Returns:
            List of dictionaries, each containing student info and grades
            
        Raises:
            FileNotFoundError: If the Excel file doesn't exist
            Exception: If there's an error reading the Excel file
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Excel file not found: {file_path}")
        
        print(f"Loading Excel file: {file_path}")
        
        try:
            # First read without specifying header to extract program info
            raw_df = pd.read_excel(file_path)
            program_info = cls.extract_program_info(raw_df)
            print(f"Detected program: {program_info['program_name']}")
            print(f"Detected school year: {program_info['school_year']}")
            
            # In the new format, the header is in row 9, but we need to read row 11 onwards for actual data
            
            # Find the actual header row by looking for "Etud_Numér"
            header_row = None
            for i in range(len(raw_df)):
                row = raw_df.iloc[i]
                for col, val in row.items():
                    if pd.notna(val) and isinstance(val, str) and 'Etud_Numér' in val:
                        header_row = i
                        print(f"Found header row at index {i}")
                        break
                if header_row is not None:
                    break
            
            if header_row is None:
                print("Warning: Couldn't find header row with 'Etud_Numér', defaulting to row 9")
                # Default based on observed structure in L3SIF_PV_23_24.xlsx
                header_row = 9
            
            # Create header mapping directly from the values in the header row
            headers = {}
            header_values = raw_df.iloc[header_row].tolist()
            for i, val in enumerate(header_values):
                if pd.notna(val) and isinstance(val, str):
                    headers[i] = str(val)
                else:
                    headers[i] = f"Column_{i}"
            
            # Create column mapping for easier access later
            # We'll create fixed column names for the student info columns we know we need
            id_col = "student_id"
            name_col = "student_name"
            firstname_col = "student_firstname"
            birth_col = "student_birthdate"
            city_col = "student_birthplace"
            
            # Read the data from row 11 onwards (skipping the header row and any empty rows)
            students = []
            
            for i in range(header_row + 1, len(raw_df)):
                row = raw_df.iloc[i]
                
                # Check if this row contains a student record
                # Student records have a numeric ID in the first column
                if not pd.notna(row.iloc[0]) or not isinstance(row.iloc[0], (int, float)):
                    continue
                
                # Extract student info
                student_info = {
                    'gender': '',  # Empty as requested
                    'name': str(row.iloc[1]).upper() if pd.notna(row.iloc[1]) else '',
                    'firstname': str(row.iloc[2]).title() if pd.notna(row.iloc[2]) else '',
                    'pronoun': 'they',
                    'dob': cls.format_date_from_excel(row.iloc[3]) if pd.notna(row.iloc[3]) else '',
                    'pob': str(row.iloc[4]) if pd.notna(row.iloc[4]) else '',
                    'program': program_info['program_name'],
                    'school_year': program_info['school_year']
                }
                
                # Extract grades
                grades = {}
                
                # Look for course columns (Obj*_Libellé)
                for j in range(len(header_values)):
                    if j >= len(row):
                        continue
                        
                    header_val = header_values[j] if j < len(header_values) else None
                    
                    if not header_val or not isinstance(header_val, str) or "_Libellé" not in header_val:
                        continue
                    
                    obj_prefix = header_val.split("_")[0]  # Extract Obj1, Obj2, etc.
                    
                    # Find corresponding grade column
                    grade_col = None
                    for k in range(len(header_values)):
                        if k < len(header_values) and isinstance(header_values[k], str) and header_values[k].startswith(f"{obj_prefix}_Note_Ado/20"):
                            grade_col = k
                            break
                    
                    # Find corresponding credits column
                    credits_col = None
                    for k in range(len(header_values)):
                        if k < len(header_values) and isinstance(header_values[k], str) and header_values[k].startswith(f"{obj_prefix}_Crédits"):
                            credits_col = k
                            break
                    
                    # Find corresponding type column
                    type_col = None
                    for k in range(len(header_values)):
                        if k < len(header_values) and isinstance(header_values[k], str) and header_values[k].startswith(f"{obj_prefix}_Type"):
                            type_col = k
                            break
                    
                    # Get course name
                    course_name = row.iloc[j] if j < len(row) and pd.notna(row.iloc[j]) else None
                    
                    # Skip empty course names or non-ELP course types
                    if not course_name or not isinstance(course_name, str) or not course_name.strip():
                        continue
                    
                    # Skip courses with 'Bloc' or 'Semestre' in the title
                    course_name_str = str(course_name).strip()
                    if 'Bloc' in course_name_str or 'Semestre' in course_name_str:
                        print(f"    Skipping block/semester course: {course_name_str}")
                        continue
                        
                    # Check if course type is ELP
                    if type_col and type_col < len(row):
                        course_type = row.iloc[type_col]
                        if pd.notna(course_type) and str(course_type).upper() != 'ELP':
                            continue
                    
                    # Get grade and credits
                    grade = None
                    credits = 6  # Default
                    
                    if grade_col and grade_col < len(row):
                        grade_val = row.iloc[grade_col]
                        if pd.notna(grade_val):
                            try:
                                # Handle string grades like "U 15.5"
                                if isinstance(grade_val, str):
                                    grade_val = grade_val.replace('U ', '').strip()
                                grade = float(str(grade_val).replace(',', '.'))
                            except (ValueError, TypeError):
                                continue
                    
                    if credits_col and credits_col < len(row):
                        credits_val = row.iloc[credits_col]
                        if pd.notna(credits_val):
                            try:
                                if isinstance(credits_val, str):
                                    credits_val = credits_val.strip()
                                credits = int(float(str(credits_val).replace(',', '.')))
                            except (ValueError, TypeError):
                                pass
                    
                    if grade is not None:
                        grades[course_name] = [grade, credits, credits]
                
                if len(grades) > 0:  # Only include students with grades
                    students.append({
                        'student': student_info,
                        'grades': grades
                    })
                    print(f"Added student: {student_info['firstname']} {student_info['name']} with {len(grades)} grades")
            
            # Return the collected student data
            return students
            
        except Exception as e:
            print(f"Error loading Excel file: {e}")
            print(f"File path: {file_path}")
            import traceback
            traceback.print_exc()
            print("Attempting to debug Excel structure...")
            try:
                # Try basic reading to see if we can at least get some information
                basic_df = pd.read_excel(file_path)
                print(f"Excel file shape: {basic_df.shape}")
                print(f"First 5 rows summary:")
                for i in range(min(5, len(basic_df))):
                    non_empty = basic_df.iloc[i].dropna()
                    if len(non_empty) > 0:
                        print(f"Row {i} has {len(non_empty)} non-empty values")
            except Exception as debug_e:
                print(f"Debug attempt also failed: {debug_e}")
            raise
    
    @classmethod
    def _extract_student_info(cls, row: pd.Series, name_col: str, firstname_col: str, 
                             birth_col: str, city_col: str) -> Dict[str, str]:
        """
        Extract student information from a row in the Excel file.
        
        Args:
            row: Pandas Series representing a row from the Excel file
            name_col, firstname_col, birth_col, city_col: Column names for student data
            
        Returns:
            Dictionary containing formatted student information
        """
        # Get raw values safely with checks
        name_value = ''
        if name_col and name_col in row.index and pd.notna(row[name_col]):
            name_value = row[name_col]
        
        firstname_value = ''
        if firstname_col and firstname_col in row.index and pd.notna(row[firstname_col]):
            firstname_value = row[firstname_col]
        
        birth_value = ''
        if birth_col and birth_col in row.index and pd.notna(row[birth_col]):
            birth_value = row[birth_col]
        
        city_value = ''
        if city_col and city_col in row.index and pd.notna(row[city_col]):
            city_value = row[city_col]
        
        # Format names: lastname in ALL CAPS, firstname with title case
        formatted_name = str(name_value).upper() if name_value else ''
        formatted_firstname = str(firstname_value).title() if firstname_value else ''
        
        return {
            'gender': '',  # Empty as requested
            'name': formatted_name,
            'firstname': formatted_firstname,
            'pronoun': 'they',
            'dob': cls.format_date_from_excel(birth_value) if birth_value else '',
            'pob': str(city_value) if city_value else '',
            'program': '',  # Will be filled by the calling method
            'school_year': ''  # Will be filled by the calling method
        }
    
    @classmethod
    def _extract_grades_from_row(cls, row: pd.Series, all_columns: List[str]) -> Dict[str, List[float]]:
        """
        Extract grades from course-related columns in a row.
        
        Args:
            row: Pandas Series representing a row from the Excel file
            all_columns: List of all column names in the DataFrame
            
        Returns:
            Dictionary mapping course names to [grade, credits_obtained, max_credits]
        """
        grades = {}
        
        # Look for course name columns
        course_patterns = ['_Libellé', '_libelle', '_libellé', '_name', '_Name', '_LIBELLE']
        obj_columns = []
        
        for pattern in course_patterns:
            found_cols = [col for col in all_columns if 'Obj' in str(col) and pattern in str(col)]
            obj_columns.extend(found_cols)
        
        # Remove duplicates
        obj_columns = list(set(obj_columns))
        
        for obj_col in obj_columns:
            # Extract the prefix (everything before the pattern)
            obj_prefix = obj_col
            for pattern in course_patterns:
                if pattern in str(obj_col):
                    obj_prefix = str(obj_col).replace(pattern, '')
                    break
            
            # Get course name safely
            course_name = None
            if obj_col in row.index:
                course_name = row[obj_col]
            
            if course_name and pd.notna(course_name) and str(course_name).strip():
                # Skip courses with 'Bloc' or 'Semestre' in the title
                course_name_str = str(course_name).strip()
                if 'Bloc' in course_name_str or 'Semestre' in course_name_str:
                    print(f"    Skipping block/semester course: {course_name_str}")
                    continue
                    
                # Check if course type is 'ELP' or if no type column exists
                type_col = cls._find_type_column(obj_prefix, all_columns)
                
                course_type = None
                if type_col and type_col in row.index:
                    course_type = row[type_col]
                
                # Only include course if type is 'ELP' or if no type column is found
                if not type_col or (pd.notna(course_type) and str(course_type).strip().upper() == 'ELP'):
                    # Find corresponding grade and credits columns
                    grade_col = cls._find_grade_column(obj_prefix, all_columns)
                    credits_col = cls._find_credits_column(obj_prefix, all_columns)
                    
                    grade = None
                    if grade_col and grade_col in row.index:
                        grade = row[grade_col]
                    
                    credits = 0
                    if credits_col and credits_col in row.index:
                        credits = row[credits_col]

                    if pd.notna(grade):
                        try:
                            # Convert to proper numeric values
                            grade_float = float(str(grade).replace(',', '.').strip()) if isinstance(grade, str) else float(grade)
                            
                            # Handle credits
                            credits_int = 0
                            if pd.notna(credits):
                                if isinstance(credits, str):
                                    # Handle string values like "U 15.5"
                                    credits_str = str(credits).strip()
                                    if credits_str.startswith('U '):
                                        credits_str = credits_str[2:].strip()
                                    credits_int = int(float(credits_str.replace(',', '.')))
                                else:
                                    credits_int = int(credits) if credits else 6
                            else:
                                credits_int = 6  # Default credits
                            
                            # Format: [grade, credits_obtained, max_credits]
                            grades[str(course_name)] = [grade_float, credits_int, credits_int]
                            
                        except (ValueError, TypeError) as e:
                            print(f"    Error converting grade/credits for {course_name}: {e}, grade={grade}, credits={credits}")
        
        return grades
    
    @staticmethod
    def _find_type_column(obj_prefix: str, all_columns: List[str]) -> Optional[str]:
        """Find the type column for a given course prefix."""
        type_patterns = ['_Type', '_type', '_TYPE']
        
        for pattern in type_patterns:
            potential_col = f"{obj_prefix}{pattern}"
            for col in all_columns:
                if str(col) == potential_col:
                    return col
        return None
    
    @staticmethod
    def _find_grade_column(obj_prefix: str, all_columns: List[str]) -> Optional[str]:
        """Find the grade column for a given course prefix."""
        grade_patterns = ['_Note_Ado/20', '_note_ado/20', '_Note', '_note', '_Grade', '_grade']
        
        for pattern in grade_patterns:
            potential_col = f"{obj_prefix}{pattern}"
            for col in all_columns:
                if str(col) == potential_col:
                    return col
        return None
    
    @staticmethod
    def _find_credits_column(obj_prefix: str, all_columns: List[str]) -> Optional[str]:
        """Find the credits column for a given course prefix."""
        credits_patterns = ['_Crédits', '_credits', '_Credits', '_CREDITS', '_ECTS', '_ects']
        
        for pattern in credits_patterns:
            potential_col = f"{obj_prefix}{pattern}"
            for col in all_columns:
                if str(col) == potential_col:
                    return col
        return None