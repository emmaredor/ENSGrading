"""
Grades Processing Module for ENS Transcript Generator

This module handles all grade-related calculations and processing:
- Grade to letter grade conversion
- GPA calculations
- Grade table creation
- Credit calculations with compensation logic

Author: ENS Transcript Generator
Date: September 2025
"""

from typing import Dict, List, Tuple, Any
import pandas as pd


class GradeConverter:
    """Handles conversion between different grading systems."""
    
    @staticmethod
    def grade_to_letter_and_gpa(grade_20: float) -> Tuple[str, str]:
        """
        Convert grade out of 20 to letter grade and 4.0 GPA scale.
        
        Args:
            grade_20: Grade on a scale of 0-20
            
        Returns:
            Tuple of (letter_grade, gpa_string)
            
        Example:
            16.5 -> ("A+", "4.33")
            12.0 -> ("B+", "3.33")
        """
        if grade_20 is None:
            return "N/A", "N/A"
        
        elif grade_20 >= 16:
            return "A+", "4.33"
        elif grade_20 >= 14:
            return "A", "4.0"
        elif grade_20 >= 13:
            return "A-", "3.67"
        elif grade_20 >= 12:
            return "B+", "3.33"
        elif grade_20 >= 11:
            return "B", "3.0"
        elif grade_20 >= 10:
            return "B-", "2.67"
        elif grade_20 >= 9:
            return "C+", "2.33"
        elif grade_20 >= 8:
            return "C", "2.0"
        elif grade_20 >= 7:
            return "C-", "1.67"
        else:
            return "F", "0.0"
    
    @staticmethod
    def get_grading_scale_info() -> str:
        """
        Get formatted grading scale information for display.
        
        Returns:
            HTML-formatted string describing the grading scale
        """
        return """
        • 16-20:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Outstanding<br/>
        • 14-15.99:&nbsp;&nbsp;&nbsp;&nbsp;Very Good<br/>
        • 12-13.99:&nbsp;&nbsp;&nbsp;&nbsp;Good<br/>
        • 10-11.99:&nbsp;&nbsp;&nbsp;&nbsp;Fair<br/>
        • < 10:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Fail
        """


class CreditCalculator:
    """Handles credit calculations and compensation logic."""
    
    @staticmethod
    def calculate_individual_credits(grade: float, max_credits: int) -> int:
        """
        Calculate credits earned for an individual course.
        
        Args:
            grade: Grade received (0-20 scale)
            max_credits: Maximum credits available for the course
            
        Returns:
            Credits earned (0 if grade < 10, max_credits if grade >= 10)
        """
        return max_credits if grade >= 10 else 0
    
    @staticmethod
    def calculate_compensation_credits(average_grade: float, total_max_credits: int, 
                                    actual_credits_earned: int) -> int:
        """
        Calculate credits with compensation system.
        
        Args:
            average_grade: Overall average grade
            total_max_credits: Total maximum credits possible
            actual_credits_earned: Credits earned without compensation
            
        Returns:
            Credits to display (with or without compensation)
        """
        if average_grade > 10:
            # If average > 10, grant all credits through compensation
            return total_max_credits
        else:
            # If average ≤ 10, only count actually earned credits
            return actual_credits_earned
    
    @staticmethod
    def should_mark_course_unvalidated(grade: float) -> bool:
        """
        Determine if a course should be marked as unvalidated (with asterisk).
        
        Args:
            grade: Grade received for the course
            
        Returns:
            True if course should be marked with asterisk, False otherwise
        """
        return grade < 10


class GradeTableGenerator:
    """Generates grade tables for transcript display."""
    
    def __init__(self):
        self.converter = GradeConverter()
        self.calculator = CreditCalculator()
    
    def create_grades_table(self, grades_data: Dict[str, List[float]]) -> Tuple[List[List[str]], bool]:
        """
        Create a formatted grades table from grades data.
        
        Args:
            grades_data: Dictionary mapping course names to [grade, credits_obtained, max_credits]
            
        Returns:
            Tuple of (table_data, passed_all_courses)
            - table_data: List of lists representing table rows
            - passed_all_courses: Boolean indicating if all courses were passed individually
        """
        # Table headers
        table_data = [
            ['Course Title', 'Credits\nAwarded', 'Grade out\nof 20', 'Letter\nGrade', 'GPA']
        ]
        
        # Track overall statistics
        passed_all = True
        total_grade_points = 0
        actual_credits_earned = 0
        total_grade_sum = 0
        total_courses = 0
        total_max_credits = 0
        
        # Process each course
        for course_title, course_info in grades_data.items():
            grade = course_info[0]
            
            # Support both formats: [grade, max_credits] and [grade, credits_obtained, max_credits]
            if len(course_info) == 2:
                # Format: [grade, max_credits] - calculate credits_obtained based on grade
                max_credits = course_info[1]
                credits_obtained = self.calculator.calculate_individual_credits(grade, max_credits)
            elif len(course_info) == 3:
                # Format: [grade, credits_obtained, max_credits] - use provided credits_obtained
                credits_obtained = course_info[1]
                max_credits = course_info[2]
            else:
                # Invalid format, skip this course
                continue
            
            # Check if course was failed
            if self.calculator.should_mark_course_unvalidated(grade):
                passed_all = False
            
            # Format credits display
            credits_display = f"{credits_obtained}/{max_credits}"
            if self.calculator.should_mark_course_unvalidated(grade):
                credits_display = f"{credits_display} *"
            
            # Convert to letter grade and GPA
            letter_grade, gpa = self.converter.grade_to_letter_and_gpa(grade)
            grade_display = str(grade) if grade is not None else "N/A"
            
            # Accumulate statistics for GPA calculation
            if grade is not None and credits_obtained > 0:
                if gpa != "N/A":
                    total_grade_points += float(gpa) * credits_obtained
                    actual_credits_earned += credits_obtained
            
            # Track totals for average calculation
            if grade is not None:
                total_grade_sum += grade
                total_courses += 1
                total_max_credits += max_credits
            
            # Add course row to table
            table_data.append([
                course_title,
                credits_display,
                grade_display,
                letter_grade,
                gpa
            ])
        
        # Calculate summary statistics
        average_grade = total_grade_sum / total_courses if total_courses > 0 else 0
        
        # Determine credits for TOTALS row (with compensation logic)
        credits_for_totals = self.calculator.calculate_compensation_credits(
            average_grade, total_max_credits, actual_credits_earned
        )
        
        # Calculate cumulative GPA
        cumulative_gpa = self._calculate_cumulative_gpa(
            grades_data, average_grade, total_max_credits, actual_credits_earned
        )
        
        # Add summary row
        summary_row = self._create_summary_row(
            credits_for_totals, average_grade, cumulative_gpa
        )
        table_data.append(summary_row)
        
        return table_data, passed_all
    
    def _calculate_cumulative_gpa(self, grades_data: Dict[str, List[float]], 
                                average_grade: float, total_max_credits: int, 
                                actual_credits_earned: int) -> float:
        """Calculate cumulative GPA based on compensation logic."""
        if average_grade > 10:
            # Use all max credits for compensation GPA calculation
            total_grade_points_compensation = 0
            for course_title, course_info in grades_data.items():
                grade = course_info[0]
                
                # Support both formats for max_credits
                if len(course_info) == 2:
                    max_credits = course_info[1]
                elif len(course_info) == 3:
                    max_credits = course_info[2]
                else:
                    continue
                    
                if grade is not None:
                    _, gpa = self.converter.grade_to_letter_and_gpa(grade)
                    if gpa != "N/A":
                        total_grade_points_compensation += float(gpa) * max_credits
            return total_grade_points_compensation / total_max_credits if total_max_credits > 0 else 0
        else:
            # Use only actually earned credits
            total_grade_points = 0
            for course_title, course_info in grades_data.items():
                grade = course_info[0]
                
                # Support both formats for credits calculation
                if len(course_info) == 2:
                    max_credits = course_info[1]
                    credits_obtained = self.calculator.calculate_individual_credits(grade, max_credits)
                elif len(course_info) == 3:
                    credits_obtained = course_info[1]
                else:
                    continue
                    
                if grade is not None and credits_obtained > 0:
                    _, gpa = self.converter.grade_to_letter_and_gpa(grade)
                    if gpa != "N/A":
                        total_grade_points += float(gpa) * credits_obtained
            return total_grade_points / actual_credits_earned if actual_credits_earned > 0 else 0
    
    def _create_summary_row(self, credits_for_totals: int, average_grade: float, 
                          cumulative_gpa: float) -> List[str]:
        """Create the summary row for the grades table."""
        avg_letter_grade, _ = self.converter.grade_to_letter_and_gpa(average_grade)
        
        return [
            'TOTALS',
            f'{credits_for_totals}',
            f'{average_grade:.2f}',
            avg_letter_grade,
            f'{cumulative_gpa:.2f}'
        ]


class GradeValidator:
    """Validates grade data and performs consistency checks."""
    
    @staticmethod
    def validate_grades_data(grades_data: Dict[str, List[float]]) -> Tuple[bool, List[str]]:
        """
        Validate grades data structure and values.
        
        Args:
            grades_data: Dictionary containing grades data
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if not grades_data:
            errors.append("No grades data provided")
            return False, errors
        
        for course_name, course_info in grades_data.items():
            # Check data structure - support both [grade, max_credits] and [grade, credits_obtained, max_credits]
            if not isinstance(course_info, list) or len(course_info) not in [2, 3]:
                errors.append(f"Course '{course_name}': Invalid data format (expected [grade, max_credits] or [grade, credits_obtained, max_credits])")
                continue
            
            grade = course_info[0]
            
            # Validate grade
            if grade is not None and (not isinstance(grade, (int, float)) or grade < 0 or grade > 20):
                errors.append(f"Course '{course_name}': Invalid grade value {grade} (must be 0-20)")
            
            if len(course_info) == 2:
                # Format: [grade, max_credits]
                max_credits = course_info[1]
                
                # Validate max_credits
                if not isinstance(max_credits, (int, float)) or max_credits < 0:
                    errors.append(f"Course '{course_name}': Invalid max_credits value {max_credits}")
                    
            elif len(course_info) == 3:
                # Format: [grade, credits_obtained, max_credits]
                credits_obtained, max_credits = course_info[1], course_info[2]
                
                # Validate credits
                if not isinstance(max_credits, (int, float)) or max_credits < 0:
                    errors.append(f"Course '{course_name}': Invalid max_credits value {max_credits}")
                
                if not isinstance(credits_obtained, (int, float)) or credits_obtained < 0:
                    errors.append(f"Course '{course_name}': Invalid credits_obtained value {credits_obtained}")
                
                if credits_obtained > max_credits:
                    errors.append(f"Course '{course_name}': Credits obtained ({credits_obtained}) cannot exceed max credits ({max_credits})")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def get_grades_summary(grades_data: Dict[str, List[float]]) -> Dict[str, Any]:
        """
        Get a summary of grades data for logging/debugging.
        
        Args:
            grades_data: Dictionary containing grades data
            
        Returns:
            Dictionary with summary statistics
        """
        if not grades_data:
            return {"total_courses": 0, "average_grade": 0, "total_credits": 0}
        
        grades = [course_info[0] for course_info in grades_data.values() if course_info[0] is not None]
        
        # Calculate total credits - support both formats
        total_credits = 0
        for course_info in grades_data.values():
            if len(course_info) == 2:
                # Format: [grade, max_credits]
                total_credits += course_info[1]
            elif len(course_info) == 3:
                # Format: [grade, credits_obtained, max_credits]
                total_credits += course_info[2]
        
        return {
            "total_courses": len(grades_data),
            "courses_with_grades": len(grades),
            "average_grade": sum(grades) / len(grades) if grades else 0,
            "total_credits": total_credits,
            "course_names": list(grades_data.keys())
        }