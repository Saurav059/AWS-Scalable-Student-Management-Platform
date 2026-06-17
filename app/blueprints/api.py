from flask import Blueprint, jsonify, request, send_file, abort
from flask_login import login_required, current_user
import io

from app.models import Student, Course, Attendance, Mark
from app.services.report_service import ReportService
from app.services.attendance_service import AttendanceService
from app.services.marks_service import MarksService
from app.services.course_service import CourseService
from app.services.auth_service import role_required

api_bp = Blueprint('api', __name__)

@api_bp.route('/health', methods=['GET'])
def health():
    """Duplicate health check endpoint registered under /api for convenience."""
    return jsonify({"status": "healthy"}), 200


@api_bp.route('/reports/students', methods=['GET'])
@login_required
@role_required(['admin', 'teacher'])
def export_students():
    fmt = request.args.get('format', 'csv').lower()
    students = Student.query.all()
    
    if fmt == 'pdf':
        pdf_buffer = ReportService.generate_students_pdf(students)
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"student_registry_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
    else:  # csv
        csv_buffer = ReportService.generate_students_csv(students)
        return send_file(
            io.BytesIO(csv_buffer.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f"student_registry_{datetime.now().strftime('%Y%m%d')}.csv"
        )


@api_bp.route('/reports/courses', methods=['GET'])
@login_required
@role_required(['admin', 'teacher'])
def export_courses():
    fmt = request.args.get('format', 'csv').lower()
    courses = Course.query.all()
    
    if fmt == 'pdf':
        pdf_buffer = ReportService.generate_courses_pdf(courses)
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"course_catalog_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
    else:
        csv_buffer = ReportService.generate_courses_csv(courses)
        return send_file(
            io.BytesIO(csv_buffer.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f"course_catalog_{datetime.now().strftime('%Y%m%d')}.csv"
        )


@api_bp.route('/reports/attendance', methods=['GET'])
@login_required
def export_attendance():
    fmt = request.args.get('format', 'csv').lower()
    student_id_str = request.args.get('student_id')
    course_id_str = request.args.get('course_id')
    
    student_id = int(student_id_str) if student_id_str else None
    course_id = int(course_id_str) if course_id_str else None
    
    # Permission checks
    if current_user.role == 'student':
        student = Student.query.filter_by(user_id=current_user.id).first()
        if not student:
            abort(404)
        # Students can only pull their own logs
        student_id = student.id
    
    # If student_id is set, pull a specific student's log
    if student_id:
        student = Student.query.get(student_id)
        if not student:
            abort(404)
            
        records = AttendanceService.get_student_attendance(student.id, course_id=course_id)
        
        if fmt == 'pdf':
            percentage = AttendanceService.calculate_attendance_percentage(student.id, course_id=course_id)
            pdf_buffer = ReportService.generate_attendance_pdf(student, records, percentage)
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"attendance_report_{student.student_id}.pdf"
            )
        else:
            csv_buffer = ReportService.generate_attendance_csv(records)
            return send_file(
                io.BytesIO(csv_buffer.getvalue().encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f"attendance_report_{student.student_id}.csv"
            )
            
    # Registry-wide logs (Admin/Teacher only)
    if current_user.role not in ['admin', 'teacher']:
        abort(403)
        
    query = Attendance.query
    if course_id:
        query = query.filter_by(course_id=course_id)
    records = query.all()
    
    if fmt == 'pdf':
        # Registry list courses pdf is generic courses list, so for batch attendance we offer CSV. 
        # PDF defaults to CSV if registry-wide to keep it simple, or generate standard PDF.
        # Let's generate student PDF with all records.
        # For simplicity, registry-wide attendance report is returned as CSV.
        csv_buffer = ReportService.generate_attendance_csv(records)
        return send_file(
            io.BytesIO(csv_buffer.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name="system_attendance_report.csv"
        )
    else:
        csv_buffer = ReportService.generate_attendance_csv(records)
        return send_file(
            io.BytesIO(csv_buffer.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name="system_attendance_report.csv"
        )


@api_bp.route('/reports/marks', methods=['GET'])
@login_required
def export_marks():
    fmt = request.args.get('format', 'csv').lower()
    student_id_str = request.args.get('student_id')
    course_id_str = request.args.get('course_id')
    
    student_id = int(student_id_str) if student_id_str else None
    course_id = int(course_id_str) if course_id_str else None
    
    # Permission checks
    if current_user.role == 'student':
        student = Student.query.filter_by(user_id=current_user.id).first()
        if not student:
            abort(404)
        student_id = student.id
        
    if student_id:
        student = Student.query.get(student_id)
        if not student:
            abort(404)
            
        marks = MarksService.get_student_marks(student.id)
        if course_id:
            marks = [m for m in marks if m.course_id == course_id]
            
        if fmt == 'pdf':
            gpa = MarksService.calculate_student_gpa(student.id)
            pdf_buffer = ReportService.generate_marks_pdf(student, marks, gpa)
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"transcript_{student.student_id}.pdf"
            )
        else:
            csv_buffer = ReportService.generate_marks_csv(marks)
            return send_file(
                io.BytesIO(csv_buffer.getvalue().encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f"transcript_{student.student_id}.csv"
            )
            
    # System wide marks (Admin/Teacher only)
    if current_user.role not in ['admin', 'teacher']:
        abort(403)
        
    query = Mark.query
    if course_id:
        query = query.filter_by(course_id=course_id)
    marks = query.all()
    
    csv_buffer = ReportService.generate_marks_csv(marks)
    return send_file(
        io.BytesIO(csv_buffer.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name="system_marks_report.csv"
    )

from datetime import datetime
