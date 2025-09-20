import json
import yaml
import re
import argparse
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, PageTemplate, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
import os
import sys
import hashlib

"""python main.py --help
usage: main.py [-h] [-g GRADES] [-i INFO]
               [-o OUTPUT]

Generate student transcript PDF

options:
  -h, --help           show this help message and     
                       exit
  -g, --grades GRADES  Path to grades JSON file       
                       (default: config/grades.json)  
  -i, --info INFO      Path to student info YAML      
                       file (default:
                       config/info.yaml)
  -o, --output OUTPUT  Output PDF filename (default:  
                       auto-generated from student    
                       name and timestamp)"""


def load_student_data(yaml_file_path):
    """Load student and author data from YAML file."""
    with open(yaml_file_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)


def load_text_templates(json_file_path):
    """Load text templates from JSON file."""
    with open(json_file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def format_ordinal_numbers(text):
    """
    Format ordinal numbers (1st, 2nd, 3rd, 11th, etc.) with superscript suffixes.
    """
    def replace_ordinal(match):
        number = match.group(1)
        suffix = match.group(2)
        return f'{number}<sup>{suffix}</sup>'
    
    # Pattern to match ordinal numbers: digits followed by st, nd, rd, or th
    # This pattern captures both the number part and the suffix
    formatted_text = re.sub(r'(\d+)(st|nd|rd|th)\b', replace_ordinal, text)
    return formatted_text


def format_text_with_data(text, data):
    """
    Format text by replacing placeholders with actual data.
    Placeholders should be in format <section.field> (e.g., <student.name>)
    Dynamic content will be highlighted in light blue.
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
        
        # Wrap the dynamic content in light blue color tags and format ordinal numbers
        formatted_value = format_ordinal_numbers(str(value))
        return f'<font color=#2259af>{formatted_value}</font>'
    
    # Find all placeholders in format <section.field>
    formatted_text = re.sub(r'<([^>]+)>', replace_placeholder, text)
    return formatted_text


def format_all_texts(student_data, text_templates):
    """Format all text templates with student data."""
    formatted_texts = {}
    
    for key, template in text_templates.items():
        formatted_texts[key] = format_text_with_data(template, student_data)
    
    return formatted_texts


def generate_pdf_report(formatted_texts, output_path):
    """Generate a PDF report with the formatted texts."""
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    for section, text in formatted_texts.items():
        story.append(Paragraph(f"{section.upper()}", styles['Title']))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(text, styles['BodyText']))
        story.append(PageBreak())
    
    doc.build(story)

def create_pdf_from_formatted_texts(formatted_texts, student_data, grades_file_path="config/grades.json", output_filename="student_transcript.pdf"):
    """Create a PDF document from the formatted texts."""
    
    def add_footer(canvas, doc):
        """Add footer to each page"""
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
    
    # Create document with custom page template
    doc = SimpleDocTemplate(output_filename, pagesize=A4,
                           rightMargin=36, leftMargin=36,
                           topMargin=26, bottomMargin=36)
    
    # Set the page template with footer
    doc.build_on_page_template = True
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=10,
        alignment=1,  # Center alignment
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'CustomSubTitle',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=12,
        alignment=1,  # Center alignment
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        alignment=4,  # Justify
        fontName='Helvetica'
    )
    
    note_style = ParagraphStyle(
        'CustomNote',
        parent=styles['Normal'],
        fontSize=8,
        spaceAfter=6,
        alignment=4,  # Justify
        fontName='Helvetica'
    )
    # Build story
    story = []

    # Create header with logo on left and title/subtitle on right
    try:
        logo_path = 'assets/logo.png'
        if os.path.exists(logo_path):
            # Create logo image
            logo = Image(logo_path, width=2.2*inch, height=0.75*inch)
            
            # Create title and subtitle as separate paragraphs
            title_text = "Transcript of academic record"
            title_para = Paragraph(title_text, title_style)
            
            subtitle_text = format_ordinal_numbers(student_data['student']['yearname'])
            subtitle_para = Paragraph(subtitle_text, subtitle_style)
            
            # Create a nested table for title and subtitle
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
            
            # Create main header table with logo and title/subtitle
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
            
            story.append(header_table)
            story.append(Spacer(1, 12))  # Add space after header
        else:
            # Fallback if logo doesn't exist - just add title and subtitle
            title_text = "Transcript of academic record"
            story.append(Paragraph(title_text, title_style))
            subtitle_text = format_ordinal_numbers(student_data['student']['yearname'])
            story.append(Paragraph(subtitle_text, subtitle_style))
            
    except Exception as e:
        print(f"Warning: Could not load logo: {e}")
        # Fallback - just add title and subtitle
        title_text = "Transcript of academic record"
        story.append(Paragraph(title_text, title_style))
        subtitle_text = format_ordinal_numbers(student_data['student']['yearname'])
        story.append(Paragraph(subtitle_text, subtitle_style))

    # Introduction
    if 'intro' in formatted_texts:
        story.append(Paragraph(formatted_texts['intro'], body_style))
    
    # Add grades table
    try:
        grades_data = load_grades_data(grades_file_path)
        
        table_data, passed_all = create_grades_table(grades_data)
        
        # Adjust column widths so the table fits within the document margins (A4 width - left/right margins)
        # Account for grid lines (1pt per column, 4 grid lines for 5 columns = 4pt) and some padding
        available_width = A4[0] - doc.leftMargin - doc.rightMargin - 8  # Subtract extra for grid/padding
        # Assign reasonable proportions for each column
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
        grades_table.setStyle(TableStyle([
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
            
            # Grid styling - outer border thick, inner lines thin
            ('BOX', (0, 0), (-1, -1), 0.8, colors.black),  # Thick outer border
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),  # Thin inner lines for all rows including summary
            
            # Double line before summary row
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),  # Double line above summary row
            
            # Align course titles to left
            ('ALIGN', (0, 1), (0, -2), 'LEFT'),  # Left align course titles (excluding summary)
            ('ALIGN', (0, -1), (0, -1), 'LEFT'),  # Left align summary row label
        ]))
        
        story.append(grades_table)
        
        if not passed_all:
            story.append(Spacer(1, 6))
            note = "* <i>This course unit is not validated (ECTS credits not awarded). The academic year is validated by compensation, on the basis of the overall average grade.</i>"
            story.append(Paragraph(note, body_style))
        
    except Exception as e:
        print(f"Warning: Could not load grades data: {e}")
    
    # ENS Information
    if 'ENS' in formatted_texts:
        story.append(Paragraph(formatted_texts['ENS'], body_style))
    
    # Grading system
    if 'grading' in formatted_texts:
        story.append(Paragraph(formatted_texts['grading'], body_style))
        
        # Create grading scale table with two columns
        grading_data = """
        • 16-20:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Outstanding<br/>
        • 14-15.99:&nbsp;&nbsp;&nbsp;&nbsp;Very Good<br/>
        • 12-13.99:&nbsp;&nbsp;&nbsp;&nbsp;Good<br/>
        • 10-11.99:&nbsp;&nbsp;&nbsp;&nbsp;Fair<br/>
        • < 10:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Fail
        """
        story.append(Paragraph(grading_data, body_style))

    
    # Average information
    if 'average' in formatted_texts:
        story.append(Paragraph(formatted_texts['average'], body_style))
        story.append(Spacer(1, 10))
    
    # Certification
    if 'outro' in formatted_texts:
        story.append(Paragraph(formatted_texts['outro'], body_style))
    
    # Signature area
    signature_text = f"""
    {datetime.now().strftime("%B %d, %Y")}"""

    """
    <br/><br/>
    <br/><br/>
    President of ENS Rennes<br/>
    <b>Pascal Mognol</b>
    """
    story.append(Paragraph(signature_text, body_style))
    
    # Build PDF with footer function
    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    return output_filename


def load_grades_data(grades_file_path):
    """Load grades data from JSON file."""
    with open(grades_file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def load_course_names(names_file_path):
    """Load course names mapping from JSON file."""
    with open(names_file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def load_course_credits(credits_file_path):
    """Load course credits mapping from JSON file."""
    with open(credits_file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def convert_grade_to_letter_and_gpa(grade_20):
    """Convert grade out of 20 to letter grade and 4.0 GPA scale."""
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


def create_grades_table(grades_data):
    """Create grades table data from the loaded JSON files.
    
    Args:
        grades_data: Dict with course titles as keys and [grade, credits_obtained, max_credits] as values
    """
    table_data = [
        ['Course Title', 'Credits\nAwarded', 'Grade out\nof 20', 'Letter\nGrade', 'GPA']
    ]
    passed_all = True
    
    # Variables for calculations
    total_grade_points = 0
    actual_credits_earned = 0  # Credits based on individual course performance
    total_grade_sum = 0
    total_courses = 0
    total_max_credits = 0
    
    # Calculate totals and process each course
    for course_title, course_info in grades_data.items():
        grade = course_info[0]
        max_credits = course_info[2]
        
        # Individual course credit logic (always 0 if grade < 10)
        if grade < 10:
            credits_obtained = 0
            passed_all = False
        else:
            credits_obtained = max_credits

        # Format credits as "obtained/maximum"
        credits_display = f"{credits_obtained}/{max_credits}"
        if grade < 10:
            credits_display = f"{credits_display} *"
        
        # Convert grade
        letter_grade, gpa = convert_grade_to_letter_and_gpa(grade)
        grade_display = str(grade) if grade is not None else "N/A"
        
        # Calculate for cumulative GPA using actual earned credits
        if grade is not None and credits_obtained > 0:
            if gpa != "N/A":
                total_grade_points += float(gpa) * credits_obtained
                actual_credits_earned += credits_obtained
        
        # Track totals for average calculation
        if grade is not None:
            total_grade_sum += grade
            total_courses += 1
            total_max_credits += max_credits
        
        table_data.append([
            course_title,
            credits_display,
            grade_display,
            letter_grade,
            gpa
        ])
    
    # Calculate average grade out of 20
    average_grade = total_grade_sum / total_courses if total_courses > 0 else 0
    
    # Determine credits to display in TOTALS row
    if average_grade > 10:
        # If average > 10, show max possible credits in TOTALS (compensation system)
        credits_for_totals = total_max_credits
        # Recalculate GPA using all max credits for compensation
        total_grade_points_compensation = 0
        for course_title, course_info in grades_data.items():
            grade = course_info[0]
            max_credits = course_info[2]
            if grade is not None:
                _, gpa = convert_grade_to_letter_and_gpa(grade)
                if gpa != "N/A":
                    total_grade_points_compensation += float(gpa) * max_credits
        cumulative_gpa_value = total_grade_points_compensation / total_max_credits if total_max_credits > 0 else 0
    else:
        # If average ≤ 10, show only actually earned credits
        credits_for_totals = actual_credits_earned
        cumulative_gpa_value = total_grade_points / actual_credits_earned if actual_credits_earned > 0 else 0
    
    # Add summary row
    summary_row = [
        'TOTALS',
        f'{credits_for_totals}',
        f'{average_grade:.2f}',
        f'{convert_grade_to_letter_and_gpa(average_grade)[0]}',
        f'{cumulative_gpa_value:.2f}'
    ]
    table_data.append(summary_row)
    
    return table_data, passed_all


def generate_student_transcript_pdf(yaml_path=None, json_path=None, grades_path=None, output_path=None):
    """
    Convenience function to generate a student transcript PDF.
    
    Args:
        yaml_path (str): Path to student YAML file (default: 'config/info.yaml')
        json_path (str): Path to text templates JSON file (default: 'assets/text.json')
        grades_path (str): Path to grades JSON file (default: 'config/grades.json')
        output_path (str): Output PDF path (default: auto-generated from student name)
    
    Returns:
        str: Path to the generated PDF file
    """
    # Default paths
    yaml_path = yaml_path or 'config/info.yaml'
    json_path = json_path or 'assets/text.json'
    grades_path = grades_path or 'config/grades.json'
    
    # Load data
    student_data = load_student_data(yaml_path)
    text_templates = load_text_templates(json_path)
    
    # Format texts
    formatted_texts = format_all_texts(student_data, text_templates)
    
    # Generate default output path if not provided
    if not output_path:
        output_path = f"{student_data['student']['firstname']}_{student_data['student']['name']}_transcript.pdf"
    
    # Create PDF
    pdf_path = create_pdf_from_formatted_texts(formatted_texts, student_data, grades_path, output_path)
    
    return pdf_path


def main():
    # Fix for macOS
    if sys.platform == "darwin":
        if not hasattr(hashlib.md5, "__patched__"):
            _orig_md5 = hashlib.md5
            def _patched_md5(*args, **kwargs):
                kwargs.pop("usedforsecurity", None)  # Ignore unsupported kwarg
                return _orig_md5(*args, **kwargs)
            _patched_md5.__patched__ = True
            hashlib.md5 = _patched_md5
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description='Generate student transcript PDF')
    parser.add_argument('-g', '--grades', 
                       default='config/grades.json',
                       help='Path to grades JSON file (default: config/grades.json)')
    parser.add_argument('-i', '--info', 
                       default='config/info.yaml',
                       help='Path to student info YAML file (default: config/info.yaml)')
    parser.add_argument('-o', '--output',
                       help='Output PDF filename (default: auto-generated from student name and timestamp)')
    
    args = parser.parse_args()
    
    # File paths
    student_yaml_path = args.info
    text_json_path = 'assets/text.json'
    grades_file_path = args.grades
    
    try:
        # Load data
        student_data = load_student_data(student_yaml_path)
        text_templates = load_text_templates(text_json_path)
        
        # Format texts
        formatted_texts = format_all_texts(student_data, text_templates)
        
        # Generate PDF filename - use custom name if provided, otherwise auto-generate
        if args.output:
            pdf_filename = args.output
            # Add .pdf extension if not provided
            if not pdf_filename.lower().endswith('.pdf'):
                pdf_filename += '.pdf'
        else:
            # Generate PDF with timestamp to avoid conflicts
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"{student_data['student']['firstname']}_{student_data['student']['name']}_transcript_{timestamp}.pdf"
        
        created_pdf = create_pdf_from_formatted_texts(formatted_texts, student_data, grades_file_path, pdf_filename)
        
        print(f"\n=== PDF GENERATED ===")
        print(f"PDF created successfully: {created_pdf}")
        print(f"Location: {os.path.abspath(created_pdf)}")
        print(f"Using grades file: {grades_file_path}")
        print(f"Using info file: {student_yaml_path}")
        
        return formatted_texts
        
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()

