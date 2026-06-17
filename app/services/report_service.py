import csv
from io import BytesIO, StringIO
from datetime import datetime
from typing import List

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.models import Student, Course, Attendance, Mark

class ReportService:
    @staticmethod
    def _create_pdf_styles():
        styles = getSampleStyleSheet()
        
        # Add custom styles if they don't exist
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#1a252f'),
            spaceAfter=15
        )
        
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#7f8c8d'),
            spaceAfter=25
        )
        
        cell_style = ParagraphStyle(
            'ReportCell',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#2c3e50')
        )
        
        header_style = ParagraphStyle(
            'ReportHeaderCell',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=colors.white,
            fontName='Helvetica-Bold'
        )
        
        return title_style, subtitle_style, cell_style, header_style

    @classmethod
    def generate_students_pdf(cls, students: List[Student]) -> BytesIO:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
        story = []
        
        title_style, subtitle_style, cell_style, header_style = cls._create_pdf_styles()
        
        story.append(Paragraph("Student Registry Report", title_style))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total Students: {len(students)}", subtitle_style))
        story.append(Spacer(1, 10))
        
        # Table Headers
        headers = ["Student ID", "Full Name", "Email", "Department", "Program", "Enroll Date"]
        data = [[Paragraph(h, header_style) for h in headers]]
        
        # Table Content
        for s in students:
            row = [
                Paragraph(s.student_id, cell_style),
                Paragraph(s.full_name, cell_style),
                Paragraph(s.user.email, cell_style),
                Paragraph(s.department, cell_style),
                Paragraph(s.program, cell_style),
                Paragraph(s.enrollment_date.strftime('%Y-%m-%d') if s.enrollment_date else 'N/A', cell_style)
            ]
            data.append(row)
            
        col_widths = [65, 100, 130, 95, 95, 55]
        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2c3e50')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('TOPPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#bdc3c7')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('TOPPADDING', (0,1), (-1,-1), 6),
            ('BOTTOMPADDING', (0,1), (-1,-1), 6),
        ]))
        
        story.append(t)
        doc.build(story)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_students_csv(students: List[Student]) -> StringIO:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Student ID", "First Name", "Last Name", "Email", "Phone", "Date of Birth", "Gender", "Address", "Department", "Program", "Enrollment Date"])
        
        for s in students:
            writer.writerow([
                s.student_id,
                s.first_name,
                s.last_name,
                s.user.email,
                s.phone or '',
                s.date_of_birth.strftime('%Y-%m-%d') if s.date_of_birth else '',
                s.gender or '',
                s.address or '',
                s.department,
                s.program,
                s.enrollment_date.strftime('%Y-%m-%d') if s.enrollment_date else ''
            ])
        output.seek(0)
        return output

    @classmethod
    def generate_attendance_pdf(cls, student: Student, attendance: List[Attendance], percentage: float) -> BytesIO:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
        story = []
        
        title_style, subtitle_style, cell_style, header_style = cls._create_pdf_styles()
        
        story.append(Paragraph(f"Attendance Report: {student.full_name}", title_style))
        story.append(Paragraph(
            f"Student ID: {student.student_id} | Program: {student.program}<br/>"
            f"Attendance Rate: <b>{percentage}%</b> | Total Logs: {len(attendance)} | Report Generated: {datetime.now().strftime('%Y-%m-%d')}",
            subtitle_style
        ))
        story.append(Spacer(1, 15))
        
        # Headers
        headers = ["Date", "Course Code", "Course Name", "Status"]
        data = [[Paragraph(h, header_style) for h in headers]]
        
        for record in attendance:
            row = [
                Paragraph(record.date.strftime('%Y-%m-%d'), cell_style),
                Paragraph(record.course.course_code, cell_style),
                Paragraph(record.course.course_name, cell_style),
                Paragraph(
                    f"<font color='green'><b>{record.status}</b></font>" if record.status == 'Present'
                    else f"<font color='orange'><b>{record.status}</b></font>" if record.status == 'Late'
                    else f"<font color='red'><b>{record.status}</b></font>",
                    cell_style
                )
            ]
            data.append(row)
            
        col_widths = [80, 80, 240, 100]
        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2c3e50')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#bdc3c7')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        
        story.append(t)
        doc.build(story)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_attendance_csv(attendance: List[Attendance]) -> StringIO:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date", "Student ID", "Student Name", "Course Code", "Course Name", "Status"])
        
        for r in attendance:
            writer.writerow([
                r.date.strftime('%Y-%m-%d'),
                r.student.student_id,
                r.student.full_name,
                r.course.course_code,
                r.course.course_name,
                r.status
            ])
        output.seek(0)
        return output

    @classmethod
    def generate_marks_pdf(cls, student: Student, marks: List[Mark], cumulative_gpa: float) -> BytesIO:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
        story = []
        
        title_style, subtitle_style, cell_style, header_style = cls._create_pdf_styles()
        
        story.append(Paragraph(f"Academic Transcript: {student.full_name}", title_style))
        story.append(Paragraph(
            f"Student ID: {student.student_id} | Program: {student.program}<br/>"
            f"Cumulative GPA: <b>{cumulative_gpa}</b> | Generated on: {datetime.now().strftime('%Y-%m-%d')}",
            subtitle_style
        ))
        story.append(Spacer(1, 15))
        
        # Headers
        headers = ["Course Code", "Course Name", "Credits", "Assignment (20)", "Midterm (30)", "Final (50)", "Total (100)", "Grade", "GPA"]
        data = [[Paragraph(h, header_style) for h in headers]]
        
        for m in marks:
            row = [
                Paragraph(m.course.course_code, cell_style),
                Paragraph(m.course.course_name, cell_style),
                Paragraph(str(m.course.credit_hours), cell_style),
                Paragraph(f"{m.assignment_marks:.1f}", cell_style),
                Paragraph(f"{m.midterm_marks:.1f}", cell_style),
                Paragraph(f"{m.final_marks:.1f}", cell_style),
                Paragraph(f"{m.total_marks:.1f}", cell_style),
                Paragraph(f"<b>{m.grade}</b>", cell_style),
                Paragraph(f"{m.gpa:.1f}", cell_style)
            ]
            data.append(row)
            
        col_widths = [65, 125, 45, 60, 50, 50, 50, 35, 30]
        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2c3e50')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#bdc3c7')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        
        story.append(t)
        doc.build(story)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_marks_csv(marks: List[Mark]) -> StringIO:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Student ID", "Student Name", "Course Code", "Course Name", "Assignment Marks", "Midterm Marks", "Final Exam Marks", "Total Marks", "Grade", "GPA"])
        
        for m in marks:
            writer.writerow([
                m.student.student_id,
                m.student.full_name,
                m.course.course_code,
                m.course.course_name,
                m.assignment_marks,
                m.midterm_marks,
                m.final_marks,
                m.total_marks,
                m.grade,
                m.gpa
            ])
        output.seek(0)
        return output

    @classmethod
    def generate_courses_pdf(cls, courses: List[Course]) -> BytesIO:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=45, rightMargin=45, topMargin=45, bottomMargin=45)
        story = []
        
        title_style, subtitle_style, cell_style, header_style = cls._create_pdf_styles()
        
        story.append(Paragraph("Course Structure & Syllabus Report", title_style))
        story.append(Paragraph(f"Total Configured Courses: {len(courses)} | Report Date: {datetime.now().strftime('%Y-%m-%d')}", subtitle_style))
        story.append(Spacer(1, 10))
        
        # Headers
        headers = ["Course Code", "Course Name", "Credits", "Department", "Semester", "Instructor"]
        data = [[Paragraph(h, header_style) for h in headers]]
        
        for c in courses:
            row = [
                Paragraph(c.course_code, cell_style),
                Paragraph(c.course_name, cell_style),
                Paragraph(str(c.credit_hours), cell_style),
                Paragraph(c.department, cell_style),
                Paragraph(c.semester, cell_style),
                Paragraph(c.teacher.full_name if c.teacher else 'Unassigned', cell_style)
            ]
            data.append(row)
            
        col_widths = [75, 165, 45, 95, 65, 95]
        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2c3e50')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#bdc3c7')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        
        story.append(t)
        doc.build(story)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_courses_csv(courses: List[Course]) -> StringIO:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Course Code", "Course Name", "Credit Hours", "Department", "Semester", "Instructor ID", "Instructor Name"])
        
        for c in courses:
            writer.writerow([
                c.course_code,
                c.course_name,
                c.credit_hours,
                c.department,
                c.semester,
                c.teacher.employee_id if c.teacher else '',
                c.teacher.full_name if c.teacher else 'Unassigned'
            ])
        output.seek(0)
        return output
