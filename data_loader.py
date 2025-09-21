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
    def find_column_by_patterns(df: pd.DataFrame, patterns: List[str]) -> Optional[str]:
        """
        Find a column in the DataFrame that matches any of the given patterns.
        
        Args:
            df: Pandas DataFrame to search
            patterns: List of patterns to search for in column names
            
        Returns:
            Column name if found, None otherwise
        """
        for pattern in patterns:
            for col in df.columns:
                if pattern.lower() in str(col).lower():
                    return col
        return None
    
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
            # Read with header=1 because actual headers are in row 1
            df = pd.read_excel(file_path, header=1)
            print(f"Excel file loaded. Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            
            # Find student info columns using pattern matching
            name_col = cls.find_column_by_patterns(df, ['Etud_Nom', 'nom', 'lastname', 'name'])
            firstname_col = cls.find_column_by_patterns(df, ['Etud_Prénom', 'prénom', 'prenom', 'firstname', 'first_name'])
            birth_col = cls.find_column_by_patterns(df, ['Etud_Naissance', 'naissance', 'birth', 'date_naissance'])
            city_col = cls.find_column_by_patterns(df, ['Etud_Ville', 'ville', 'city', 'lieu_naissance'])
            
            print(f"Found columns:")
            print(f"  Name: {name_col}")
            print(f"  Firstname: {firstname_col}")
            print(f"  Birth: {birth_col}")
            print(f"  City: {city_col}")
            
            students = []
            
            for index, row in df.iterrows():

                
                # Extract and format student info
                student_info = cls._extract_student_info(row, name_col, firstname_col, birth_col, city_col)
                
                # Extract grades from course columns
                grades = cls._extract_grades_from_row(row, df.columns)
                
                
                students.append({
                    'student': student_info,
                    'grades': grades
                })
            
            return students
            
        except Exception as e:
            print(f"Error loading Excel file: {e}")
            import traceback
            traceback.print_exc()
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
        # Get raw values
        name_value = row.get(name_col, '') if name_col else ''
        firstname_value = row.get(firstname_col, '') if firstname_col else ''
        
        # Format names: lastname in ALL CAPS, firstname with title case
        formatted_name = ''
        if name_value and pd.notna(name_value):
            formatted_name = str(name_value).upper()  # ALL CAPS for lastname
        
        formatted_firstname = ''
        if firstname_value and pd.notna(firstname_value):
            formatted_firstname = str(firstname_value).title()  # Title case for firstname
        
        return {
            'gender': '',  # Empty as requested
            'name': formatted_name,
            'firstname': formatted_firstname,
            'pronoun': 'they',
            'dob': cls.format_date_from_excel(row.get(birth_col, '')) if birth_col else '',
            'pob': row.get(city_col, '') if city_col else ''
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
            found_cols = [col for col in all_columns if 'Obj' in col and pattern in col]
            obj_columns.extend(found_cols)
        
        # Remove duplicates
        obj_columns = list(set(obj_columns))
        print(f"  Found {len(obj_columns)} course columns: {obj_columns}")
        
        for obj_col in obj_columns:
            # Extract the prefix (everything before the pattern)
            obj_prefix = obj_col
            for pattern in course_patterns:
                if pattern in obj_col:
                    obj_prefix = obj_col.replace(pattern, '')
                    break
            
            course_name = row.get(obj_col, '')
            
            if pd.notna(course_name) and str(course_name).strip():
                # Find corresponding grade and credits columns
                grade_col = cls._find_grade_column(obj_prefix, all_columns)
                credits_col = cls._find_credits_column(obj_prefix, all_columns)
                
                grade = row.get(grade_col, None) if grade_col else None
                credits = row.get(credits_col, 0) if credits_col else 0
                
                print(f"    Course: {course_name}")
                print(f"    Grade column: {grade_col}, Value: {grade}")
                print(f"    Credits column: {credits_col}, Value: {credits}")
                
                if pd.notna(grade):
                    try:
                        # Format: [grade, credits_obtained, max_credits]
                        credits_int = int(credits) if pd.notna(credits) else 6
                        grades[str(course_name)] = [float(grade), credits_int, credits_int]
                        print(f"    Added grade: {grades[str(course_name)]}")
                    except (ValueError, TypeError) as e:
                        print(f"    Error converting grade/credits: {e}")
        
        return grades
    
    @staticmethod
    def _find_grade_column(obj_prefix: str, all_columns: List[str]) -> Optional[str]:
        """Find the grade column for a given course prefix."""
        grade_patterns = ['_Note_Ado/20', '_note_ado/20', '_Note', '_note', '_Grade', '_grade']
        
        for pattern in grade_patterns:
            potential_col = f"{obj_prefix}{pattern}"
            if potential_col in all_columns:
                return potential_col
        return None
    
    @staticmethod
    def _find_credits_column(obj_prefix: str, all_columns: List[str]) -> Optional[str]:
        """Find the credits column for a given course prefix."""
        credits_patterns = ['_Crédits', '_credits', '_Credits', '_CREDITS', '_ECTS', '_ects']
        
        for pattern in credits_patterns:
            potential_col = f"{obj_prefix}{pattern}"
            if potential_col in all_columns:
                return potential_col
        return None