"""
ENS Transcript Generator - Main Script

This is the main entry point for the ENS transcript generation system.
It supports two modes:
1. Single mode: Generate one PDF from YAML files
2. Batch mode: Generate multiple PDFs from an Excel file

Usage Examples:
    # Single mode with separate files
    python main.py --single --student-info config/info_student.yaml --author-info config/info_author.yaml --grades config/grades.json

    # Legacy single mode with combined file
    python main.py --single -i config/info.yaml --grades config/grades.json

    # Batch mode
    python main.py --batch --students-excel config/students.xlsx --author-yaml config/info_author.yaml -g config/grades.json

Author: ENS Transcript Generator
Date: September 2025
"""

import argparse
import os
import sys
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional

# Import our custom modules
from data_loader import DataLoader, ExcelStudentLoader
from text_formatter import TextFormatter
from pdf_generator import TranscriptPDFGenerator
from grades_processor import GradeValidator


class TranscriptGenerator:
    """Main class for transcript generation operations."""
    
    def __init__(self):
        self.data_loader = DataLoader()
        self.excel_loader = ExcelStudentLoader()
        self.text_formatter = TextFormatter()
        self.pdf_generator = TranscriptPDFGenerator()
        self.grade_validator = GradeValidator()
    
    def generate_single_transcript(self, student_info_path: Optional[str], 
                                 author_info_path: Optional[str],
                                 combined_info_path: Optional[str],
                                 grades_path: str,
                                 output_path: Optional[str] = None) -> str:
        """
        Generate a single student transcript.
        
        Args:
            student_info_path: Path to student YAML file (None for legacy mode)
            author_info_path: Path to author YAML file (None for legacy mode)
            combined_info_path: Path to combined YAML file (legacy mode)
            grades_path: Path to grades JSON file
            output_path: Output PDF filename (auto-generated if None)
            
        Returns:
            Path to the generated PDF file
            
        Raises:
            FileNotFoundError: If required files are not found
            Exception: If there's an error during generation
        """
        print("=== SINGLE TRANSCRIPT GENERATION ===")
        
        # Load student and author data
        if combined_info_path:
            # Legacy mode: combined info file
            print(f"Loading combined info from: {combined_info_path}")
            student_data = self.data_loader.load_combined_info(combined_info_path)
        else:
            # New mode: separate student and author files
            print(f"Loading student info from: {student_info_path}")
            print(f"Loading author info from: {author_info_path}")
            
            student_info = self.data_loader.load_student_info(student_info_path)
            author_info = self.data_loader.load_author_info(author_info_path)
            
            # Combine the data properly
            student_data = self.text_formatter.combine_student_author_data(student_info, author_info)
        
        # Validate student data
        if not self.text_formatter.validate_required_fields(student_data):
            raise ValueError("Missing required fields in student data")
        
        # Load text templates and grades
        print(f"Loading text templates from: assets/text.json")
        text_templates = self.data_loader.load_text_templates('assets/text.json')
        
        print(f"Loading grades from: {grades_path}")
        grades_data = self.data_loader.load_grades_data(grades_path)
        
        # Validate grades data
        is_valid, errors = self.grade_validator.validate_grades_data(grades_data)
        if not is_valid:
            raise ValueError(f"Invalid grades data: {'; '.join(errors)}")
        
        # Format text templates
        print("Formatting text templates...")
        formatted_texts = self.text_formatter.format_all_templates(student_data, text_templates)
        
        # Generate output filename if not provided
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{student_data['student']['firstname']}_{student_data['student']['name']}_transcript_{timestamp}.pdf"
            output_path = filename
        elif not output_path.lower().endswith('.pdf'):
            output_path += '.pdf'
        
        # Generate PDF
        print(f"Generating PDF: {output_path}")
        created_pdf = self.pdf_generator.generate_transcript(
            formatted_texts, student_data, grades_data, output_path
        )
        
        print(f"\n✅ PDF GENERATED SUCCESSFULLY")
        print(f"📄 File: {created_pdf}")
        print(f"📍 Location: {os.path.abspath(created_pdf)}")
        
        return created_pdf
    
    def generate_batch_transcripts(self, excel_path: str, author_yaml_path: str, 
                                 grades_template_path: Optional[str] = None,
                                 output_dir: str = 'output') -> List[str]:
        """
        Generate multiple transcripts from an Excel file.
        
        Args:
            excel_path: Path to Excel file containing student data
            author_yaml_path: Path to author YAML file
            grades_template_path: Path to grades template (optional)
            output_dir: Output directory for generated PDFs
            
        Returns:
            List of paths to generated PDF files
            
        Raises:
            FileNotFoundError: If required files are not found
            Exception: If there's an error during generation
        """
        print("=== BATCH TRANSCRIPT GENERATION ===")
        print(f"📊 Excel file: {excel_path}")
        print(f"👤 Author info: {author_yaml_path}")
        print(f"📁 Output directory: {output_dir}")
        
        # Load author info and text templates
        author_data = self.data_loader.load_author_info(author_yaml_path)
        text_templates = self.data_loader.load_text_templates('assets/text.json')
        
        print("✅ Author data and templates loaded")
        
        # Load students from Excel
        students = self.excel_loader.load_students_from_excel(excel_path)
        print(f"✅ Loaded {len(students)} students from Excel")
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"📁 Created output directory: {output_dir}")
        
        generated_pdfs = []
        successful_count = 0
        
        for i, student_excel_data in enumerate(students):
            try:
                print(f"\n--- Processing student {i+1}/{len(students)} ---")
                
                # Skip students with no grades
                if not student_excel_data['grades']:
                    print(f"⚠️  Skipping student {i+1}: No grades found")
                    continue
                
                # Combine student data with author data
                student_data = self.text_formatter.combine_student_author_data(
                    {'student': student_excel_data['student']}, author_data
                )
                
                print(f"👤 Student: {student_data['student']['firstname']} {student_data['student']['name']}")
                print(f"📚 Courses: {len(student_excel_data['grades'])}")
                
                # Validate grades data
                is_valid, errors = self.grade_validator.validate_grades_data(student_excel_data['grades'])
                if not is_valid:
                    print(f"❌ Invalid grades data for student {i+1}: {'; '.join(errors)}")
                    continue
                
                # Format text templates
                formatted_texts = self.text_formatter.format_all_templates(student_data, text_templates)
                
                # Generate PDF filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                pdf_filename = f"{student_data['student']['firstname']}_{student_data['student']['name']}_transcript_{timestamp}_{i+1:03d}.pdf"
                pdf_path = os.path.join(output_dir, pdf_filename)
                
                # Create temporary grades file for this student
                temp_grades_file = os.path.join(output_dir, f"temp_grades_{i+1:03d}.json")
                self.data_loader.save_json_file(student_excel_data['grades'], temp_grades_file)
                
                # Generate PDF
                created_pdf = self.pdf_generator.generate_transcript(
                    formatted_texts, student_data, student_excel_data['grades'], pdf_path
                )
                
                # Clean up temporary grades file
                os.remove(temp_grades_file)
                
                generated_pdfs.append(created_pdf)
                successful_count += 1
                print(f"✅ Generated: {os.path.basename(created_pdf)}")
                
            except Exception as e:
                print(f"❌ Error generating PDF for student {i+1}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\n🎉 BATCH GENERATION COMPLETE")
        print(f"✅ Successfully generated: {successful_count}/{len(students)} PDFs")
        print(f"📁 Output directory: {os.path.abspath(output_dir)}")
        
        return generated_pdfs


class CommandLineInterface:
    """Handles command-line argument parsing and validation."""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create and configure the argument parser."""
        parser = argparse.ArgumentParser(
            description='Generate student transcript PDFs',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Single mode with separate files
  python main.py --single --student-info config/info_student.yaml --author-info config/info_author.yaml --grades config/grades.json

  # Legacy single mode
  python main.py --single -i config/info.yaml --grades config/grades.json

  # Batch mode
  python main.py --batch --students-excel config/students.xlsx --author-yaml config/info_author.yaml -g config/grades.json
            """
        )
        
        # Mode selection
        mode_group = parser.add_mutually_exclusive_group(required=True)
        mode_group.add_argument('--single', action='store_true',
                               help='Generate single PDF from YAML files (OPTION 1)')
        mode_group.add_argument('--batch', action='store_true',
                               help='Generate multiple PDFs from Excel file (OPTION 2)')
        
        # Single student mode arguments
        parser.add_argument('--student-info',
                           help='Path to student info YAML file (single mode)')
        parser.add_argument('--author-info',
                           help='Path to author info YAML file (single mode)')
        parser.add_argument('-g', '--grades',
                           help='Path to grades JSON file (single mode)')
        
        # Batch mode arguments
        parser.add_argument('--students-excel',
                           help='Path to students Excel file (batch mode)')
        parser.add_argument('--author-yaml',
                           help='Path to author YAML file (batch mode)')
        
        # Common arguments
        parser.add_argument('-o', '--output',
                           help='Output PDF filename (single mode) or output directory (batch mode)')
        
        # Legacy support
        parser.add_argument('-i', '--info',
                           help='Path to combined info YAML file (legacy single mode)')
        
        return parser
    
    def parse_args(self) -> argparse.Namespace:
        """Parse and validate command-line arguments."""
        args = self.parser.parse_args()
        
        # Validate arguments based on mode
        if args.single:
            self._validate_single_mode_args(args)
        elif args.batch:
            self._validate_batch_mode_args(args)
        
        return args
    
    def _validate_single_mode_args(self, args: argparse.Namespace) -> None:
        """Validate arguments for single mode."""
        if not args.student_info and not args.info:
            self.parser.error("Single mode requires --student-info (or legacy -i/--info)")
        if not args.author_info and not args.info:
            self.parser.error("Single mode requires --author-info (or legacy -i/--info)")
        if not args.grades:
            self.parser.error("Single mode requires --grades")
    
    def _validate_batch_mode_args(self, args: argparse.Namespace) -> None:
        """Validate arguments for batch mode."""
        if not args.students_excel:
            self.parser.error("Batch mode requires --students-excel")
        if not args.author_yaml:
            self.parser.error("Batch mode requires --author-yaml")


def fix_macos_hashlib():
    """Fix for macOS hashlib issue."""
    if sys.platform == "darwin":
        if not hasattr(hashlib.md5, "__patched__"):
            _orig_md5 = hashlib.md5
            def _patched_md5(*args, **kwargs):
                kwargs.pop("usedforsecurity", None)  # Ignore unsupported kwarg
                return _orig_md5(*args, **kwargs)
            _patched_md5.__patched__ = True
            hashlib.md5 = _patched_md5


def main():
    """Main entry point for the transcript generator."""
    # Fix macOS issue
    fix_macos_hashlib()
    
    # Parse command-line arguments
    cli = CommandLineInterface()
    args = cli.parse_args()
    
    # Create transcript generator
    generator = TranscriptGenerator()
    
    try:
        if args.single:
            # Single mode
            generator.generate_single_transcript(
                student_info_path=args.student_info,
                author_info_path=args.author_info,
                combined_info_path=args.info,
                grades_path=args.grades,
                output_path=args.output
            )
        elif args.batch:
            # Batch mode
            output_dir = args.output if args.output else 'output'
            generator.generate_batch_transcripts(
                excel_path=args.students_excel,
                author_yaml_path=args.author_yaml,
                grades_template_path=args.grades,
                output_dir=output_dir
            )
    except FileNotFoundError as e:
        print(f"❌ Error: File not found - {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()