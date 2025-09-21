"""
PDF Generation Module for ENS Transcript Generator

This module handles all PDF creation and formatting:
- Document structure and layout
- Header creation with logo and titles
- Table styling and formatting
- Footer generation
- PDF assembly and output

Author: ENS Transcript Generator
Date: September 2025
"""

import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

from text_formatter import TextFormatter
from grades_processor import GradeTableGenerator, GradeConverter


class PDFStyleManager:
    """Manages PDF styles and formatting."""
    
    def __init__(self):
        self.base_styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom paragraph styles for the transcript."""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.base_styles['Heading1'],
            fontSize=16,
            spaceAfter=10,
            alignment=1,  # Center alignment
            fontName='Helvetica-Bold'
        )

        self.subtitle_style = ParagraphStyle(
            'CustomSubTitle',
            parent=self.base_styles['Heading2'],
            fontSize=12,
            spaceAfter=12,
            alignment=1,  # Center alignment
            fontName='Helvetica-Bold'
        )

        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.base_styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=4,  # Justify
            fontName='Helvetica'
        )
        
        self.note_style = ParagraphStyle(
            'CustomNote',
            parent=self.base_styles['Normal'],
            fontSize=8,
            spaceAfter=6,
            alignment=4,  # Justify
            fontName='Helvetica'
        )
    
    def get_style(self, style_name: str) -> ParagraphStyle:
        """Get a style by name."""
        style_map = {
            'title': self.title_style,
            'subtitle': self.subtitle_style,
            'body': self.body_style,
            'note': self.note_style
        }
        return style_map.get(style_name, self.body_style)


class PDFHeaderGenerator:
    """Generates PDF headers with logo and title information."""
    
    def __init__(self, style_manager: PDFStyleManager):
        self.style_manager = style_manager
        self.text_formatter = TextFormatter()
    
    def create_header(self, student_data: Dict[str, Any], logo_path: str = 'assets/logo.png') -> Any:
        """
        Create the PDF header with logo and title/subtitle.
        
        Args:
            student_data: Dictionary containing student information
            logo_path: Path to the logo image file
            
        Returns:
            ReportLab table object for the header, or title/subtitle paragraphs if no logo
        """
        try:
            if os.path.exists(logo_path):
                return self._create_header_with_logo(student_data, logo_path)
            else:
                print(f"Warning: Logo not found at {logo_path}, creating header without logo")
                return self._create_header_without_logo(student_data)
        except Exception as e:
            print(f"Warning: Could not create header with logo: {e}")
            return self._create_header_without_logo(student_data)
    
    def _create_header_with_logo(self, student_data: Dict[str, Any], logo_path: str) -> Table:
        """Create header with logo on left and title/subtitle on right."""
        # Create logo image
        logo = Image(logo_path, width=2.2*inch, height=0.75*inch)
        
        # Create title and subtitle
        title_text = "Transcript of academic record"
        title_para = Paragraph(title_text, self.style_manager.get_style('title'))
        
        subtitle_text = self.text_formatter.format_ordinal_numbers(
            student_data['student']['yearname']
        )
        subtitle_para = Paragraph(subtitle_text, self.style_manager.get_style('subtitle'))
        
        # Create nested table for title and subtitle
        title_subtitle_data = [[title_para], [subtitle_para]]
        title_subtitle_table = Table(title_subtitle_data, colWidths=[4*inch])
        title_subtitle_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        # Create main header table
        header_data = [[logo, title_subtitle_table]]
        header_table = Table(header_data, colWidths=[2.5*inch, 4*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),     # Logo left aligned
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),   # Title/subtitle centered
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        return header_table
    
    def _create_header_without_logo(self, student_data: Dict[str, Any]) -> List[Any]:
        """Create header without logo (fallback)."""
        title_text = "Transcript of academic record"
        title_para = Paragraph(title_text, self.style_manager.get_style('title'))
        
        subtitle_text = self.text_formatter.format_ordinal_numbers(
            student_data['student']['yearname']
        )
        subtitle_para = Paragraph(subtitle_text, self.style_manager.get_style('subtitle'))
        
        return [title_para, subtitle_para]


class PDFTableGenerator:
    """Generates formatted tables for PDF documents."""
    
    def __init__(self):
        self.grade_table_generator = GradeTableGenerator()
    
    def create_grades_table(self, grades_data: Dict[str, List[float]], 
                          available_width: float) -> Tuple[Table, bool]:
        """
        Create a formatted grades table.
        
        Args:
            grades_data: Dictionary containing grades information
            available_width: Available width for the table
            
        Returns:
            Tuple of (table_object, passed_all_courses)
        """
        # Get table data from grades processor
        table_data, passed_all = self.grade_table_generator.create_grades_table(grades_data)
        
        # Create table with appropriate column widths
        grades_table = Table(
            table_data,
            colWidths=[
                available_width * 0.40,  # Course Title
                available_width * 0.14,  # Credits Awarded
                available_width * 0.14,  # Grade out of 20
                available_width * 0.14,  # Letter Grade
                available_width * 0.18   # GPA
            ]
        )
        
        # Apply table styling
        grades_table.setStyle(self._get_grades_table_style())
        
        return grades_table, passed_all
    
    def _get_grades_table_style(self) -> TableStyle:
        """Get the table style for grades tables."""
        return TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            
            # Data rows styling (excluding summary row)
            ('BACKGROUND', (0, 1), (-1, -2), colors.white),
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Summary row styling (last row)
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 10),
            
            # Grid styling
            ('BOX', (0, 0), (-1, -1), 0.8, colors.black),  # Thick outer border
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),  # Thin inner lines
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),  # Double line above summary
            
            # Text alignment
            ('ALIGN', (0, 1), (0, -2), 'LEFT'),  # Left align course titles
            ('ALIGN', (0, -1), (0, -1), 'LEFT'),  # Left align summary row label
        ])


class PDFFooterGenerator:
    """Generates PDF footers."""
    
    @staticmethod
    def add_footer(canvas, doc):
        """Add footer to each page."""
        canvas.saveState()
        
        # Footer text
        footer_text = [
            "École normale supérieure de Rennes",
            "Campus de Ker lann, 11 Av. Robert Schuman, 35170 Bruz",
            "+33  (0)2 99 05 93 00"
        ]
        
        # Set font and color for footer
        canvas.setFont('Helvetica', 6)
        canvas.setFillColor(colors.grey)
        
        # Position footer at bottom left with proper margins
        x = 40  # Left margin (matching document margin)
        y = 30  # Bottom margin
        
        for i, line in enumerate(footer_text):
            canvas.drawString(x, y - (i * 12), line)
        
        canvas.restoreState()


class TranscriptPDFGenerator:
    """Main PDF generator for student transcripts."""
    
    def __init__(self):
        self.style_manager = PDFStyleManager()
        self.header_generator = PDFHeaderGenerator(self.style_manager)
        self.table_generator = PDFTableGenerator()
        self.footer_generator = PDFFooterGenerator()
        self.grade_converter = GradeConverter()
    
    def generate_transcript(self, formatted_texts: Dict[str, str], 
                          student_data: Dict[str, Any], 
                          grades_data: Dict[str, List[float]], 
                          output_filename: str) -> str:
        """
        Generate a complete student transcript PDF.
        
        Args:
            formatted_texts: Dictionary of formatted text templates
            student_data: Student and author information
            grades_data: Grades information
            output_filename: Output PDF filename
            
        Returns:
            Path to the generated PDF file
        """
        # Create document
        doc = SimpleDocTemplate(
            output_filename, 
            pagesize=A4,
            rightMargin=36, 
            leftMargin=36,
            topMargin=26, 
            bottomMargin=36
        )
        
        # Build document content
        story = []
        
        # Add header
        header = self.header_generator.create_header(student_data)
        if isinstance(header, list):
            story.extend(header)
        else:
            story.append(header)
        story.append(Spacer(1, 12))
        
        # Add introduction
        if 'intro' in formatted_texts:
            story.append(Paragraph(formatted_texts['intro'], self.style_manager.get_style('body')))
        
        # Add grades table
        try:
            available_width = A4[0] - doc.leftMargin - doc.rightMargin - 8
            grades_table, passed_all = self.table_generator.create_grades_table(grades_data, available_width)
            story.append(grades_table)
            
            # Add note for failed courses if needed
            if not passed_all:
                story.append(Spacer(1, 6))
                note = "* <i>This course unit is not validated (ECTS credits not awarded). The academic year is validated by compensation, on the basis of the overall average grade.</i>"
                story.append(Paragraph(note, self.style_manager.get_style('body')))
                
        except Exception as e:
            print(f"Warning: Could not create grades table: {e}")
        
        # Add ENS information
        if 'ENS' in formatted_texts:
            story.append(Paragraph(formatted_texts['ENS'], self.style_manager.get_style('body')))
        
        # Add grading system information
        if 'grading' in formatted_texts:
            story.append(Paragraph(formatted_texts['grading'], self.style_manager.get_style('body')))
            grading_scale = self.grade_converter.get_grading_scale_info()
            story.append(Paragraph(grading_scale, self.style_manager.get_style('body')))
        
        # Add average information
        if 'average' in formatted_texts:
            story.append(Paragraph(formatted_texts['average'], self.style_manager.get_style('body')))
            story.append(Spacer(1, 10))
        
        # Add certification/outro
        if 'outro' in formatted_texts:
            story.append(Paragraph(formatted_texts['outro'], self.style_manager.get_style('body')))
        
        # Add signature area
        signature_text = f"{datetime.now().strftime('%B %d, %Y')}"
        story.append(Paragraph(signature_text, self.style_manager.get_style('body')))
        
        # Build PDF with footer
        doc.build(story, 
                 onFirstPage=self.footer_generator.add_footer, 
                 onLaterPages=self.footer_generator.add_footer)
        
        return output_filename
    
    def validate_inputs(self, formatted_texts: Dict[str, str], 
                       student_data: Dict[str, Any], 
                       grades_data: Dict[str, List[float]]) -> Tuple[bool, List[str]]:
        """
        Validate inputs before PDF generation.
        
        Args:
            formatted_texts: Formatted text templates
            student_data: Student and author data
            grades_data: Grades data
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check required text templates
        required_templates = ['intro', 'ENS', 'grading', 'average', 'outro']
        for template in required_templates:
            if template not in formatted_texts:
                errors.append(f"Missing required text template: {template}")
        
        # Check student data structure
        if 'student' not in student_data:
            errors.append("Missing 'student' section in student data")
        else:
            student_info = student_data['student']
            required_student_fields = ['name', 'firstname', 'yearname']
            for field in required_student_fields:
                if field not in student_info or not student_info[field]:
                    errors.append(f"Missing required student field: {field}")
        
        # Check grades data
        if not grades_data:
            errors.append("No grades data provided")
        
        return len(errors) == 0, errors