"""
Text Formatting Module for ENS Transcript Generator

This module handles all text formatting operations:
- Ordinal number formatting (1st, 2nd, 3rd, etc.)
- Template placeholder replacement
- Dynamic content highlighting
- Text processing utilities

Author: ENS Transcript Generator
Date: September 2025
"""

import re
from typing import Dict, Any


class TextFormatter:
    """Handles text formatting operations for transcript generation."""
    
    @staticmethod
    def format_ordinal_numbers(text: str) -> str:
        """
        Format ordinal numbers (1st, 2nd, 3rd, 11th, etc.) with superscript suffixes.
        
        Args:
            text: Input text containing ordinal numbers
            
        Returns:
            Text with ordinal suffixes formatted as superscript
            
        Example:
            "26th of September" -> "26<sup>th</sup> of September"
        """
        def replace_ordinal(match):
            number = match.group(1)
            suffix = match.group(2)
            return f'{number}<sup>{suffix}</sup>'
        
        # Pattern to match ordinal numbers: digits followed by st, nd, rd, or th
        formatted_text = re.sub(r'(\d+)(st|nd|rd|th)\b', replace_ordinal, text)
        return formatted_text
    
    @staticmethod
    def format_text_with_data(text: str, data: Dict[str, Any], highlight_color: str = "#2259af") -> str:
        """
        Format text by replacing placeholders with actual data and highlighting dynamic content.
        
        Args:
            text: Template text with placeholders in format <section.field>
            data: Dictionary containing the data to replace placeholders
            highlight_color: Hex color code for highlighting dynamic content
            
        Returns:
            Formatted text with placeholders replaced and dynamic content highlighted
            
        Example:
            Input: "Student <student.name> was born on <student.dob>"
            Data: {"student": {"name": "John Doe", "dob": "1st of January 2000"}}
            Output: "Student <font color=#2259af>John Doe</font> was born on <font color=#2259af>1<sup>st</sup> of January 2000</font>"
        """
        def replace_placeholder(match):
            placeholder = match.group(1)  # Get the content between < and >
            keys = placeholder.split('.')
            
            # Navigate through nested dictionary
            value = data
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return match.group(0)  # Return original placeholder if not found
            
            # Format ordinal numbers and wrap in highlight color
            formatted_value = TextFormatter.format_ordinal_numbers(str(value))
            return f'<font color={highlight_color}>{formatted_value}</font>'
        
        # Find all placeholders in format <section.field>
        formatted_text = re.sub(r'<([^>]+)>', replace_placeholder, text)
        return formatted_text
    
    @classmethod
    def format_all_templates(cls, student_data: Dict[str, Any], 
                           text_templates: Dict[str, str]) -> Dict[str, str]:
        """
        Format all text templates with student data.
        
        Args:
            student_data: Dictionary containing student and author information
            text_templates: Dictionary mapping template names to template strings
            
        Returns:
            Dictionary mapping template names to formatted text strings
        """
        formatted_texts = {}
        
        for template_name, template_text in text_templates.items():
            formatted_texts[template_name] = cls.format_text_with_data(template_text, student_data)
        
        return formatted_texts
    
    @staticmethod
    def combine_student_author_data(student_info: Dict[str, Any], 
                                  author_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine student and author information into a single data structure.
        
        Args:
            student_info: Dictionary containing student information
            author_info: Dictionary containing author information
            
        Returns:
            Combined dictionary with proper structure for template processing
        """
        # Ensure we have the proper nested structure
        student_data = student_info.get('student', student_info)
        author_data = author_info.get('author', author_info)
        
        # Add author's yearname and schoolyear to student data if missing
        if 'yearname' not in student_data and 'yearname' in author_data:
            student_data['yearname'] = author_data['yearname']
        if 'schoolyear' not in student_data and 'schoolyear' in author_data:
            student_data['schoolyear'] = author_data['schoolyear']
        
        return {
            'student': student_data,
            'author': author_data
        }
    
    @staticmethod
    def validate_required_fields(student_data: Dict[str, Any]) -> bool:
        """
        Validate that required fields are present in student data.
        
        Args:
            student_data: Dictionary containing student information
            
        Returns:
            True if all required fields are present, False otherwise
        """
        required_student_fields = ['name', 'firstname']
        required_author_fields = ['name', 'firstname']
        
        student_info = student_data.get('student', {})
        author_info = student_data.get('author', {})
        
        # Check required student fields
        for field in required_student_fields:
            if field not in student_info or not student_info[field]:
                print(f"Missing required student field: {field}")
                return False
        
        # Check required author fields
        for field in required_author_fields:
            if field not in author_info or not author_info[field]:
                print(f"Missing required author field: {field}")
                return False
        
        return True


class DateFormatter:
    """Handles date formatting operations."""
    
    @staticmethod
    def add_ordinal_suffix(day: int) -> str:
        """
        Add ordinal suffix to a day number.
        
        Args:
            day: Day number (1-31)
            
        Returns:
            Day with ordinal suffix (e.g., "1st", "2nd", "3rd", "11th")
        """
        if day in [11, 12, 13]:
            return f"{day}th"
        elif day % 10 == 1:
            return f"{day}st"
        elif day % 10 == 2:
            return f"{day}nd"
        elif day % 10 == 3:
            return f"{day}rd"
        else:
            return f"{day}th"
    
    @classmethod
    def format_excel_date(cls, date_value: Any) -> str:
        """
        Convert date from Excel format to readable text format.
        
        Args:
            date_value: Date value from Excel (string or pandas datetime)
            
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
            
            # Month names
            months = [
                '', 'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ]
            
            day_int = int(day)
            month_name = months[int(month)]
            day_with_suffix = cls.add_ordinal_suffix(day_int)
            
            return f"{day_with_suffix} of {month_name} {year}"
        except Exception:
            return str(date_value)  # Fallback to original if parsing fails


class NameFormatter:
    """Handles name formatting operations."""
    
    @staticmethod
    def format_lastname_uppercase(name: str) -> str:
        """
        Format lastname in uppercase.
        
        Args:
            name: Raw name string
            
        Returns:
            Name in uppercase
        """
        return name.upper() if name else ''
    
    @staticmethod
    def format_firstname_titlecase(name: str) -> str:
        """
        Format firstname in title case (first letter capitalized).
        
        Args:
            name: Raw name string
            
        Returns:
            Name in title case
        """
        return name.title() if name else ''
    
    @classmethod
    def format_student_names(cls, lastname: str, firstname: str) -> tuple:
        """
        Format student names according to transcript requirements.
        
        Args:
            lastname: Student's last name
            firstname: Student's first name
            
        Returns:
            Tuple of (formatted_lastname, formatted_firstname)
        """
        formatted_lastname = cls.format_lastname_uppercase(lastname)
        formatted_firstname = cls.format_firstname_titlecase(firstname)
        return formatted_lastname, formatted_firstname