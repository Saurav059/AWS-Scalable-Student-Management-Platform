from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from datetime import datetime, date

from app.services.attendance_service import AttendanceService
from app.services.course_service import CourseService
from app.services.auth_service import role_required
from app.models import Course, Student, Teacher, Attendance

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/')
@login_required
def index():
    if current_user.role == 'student':
        student = Student.query.filter_by(user_id=current_user.id).first()
        if not student:
            flash("Student profile not found.", "danger")
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('attendance.student_report', student_id=student.id))
        
    # For Admin/Teacher, list courses
    courses = []
    if current_user.role == 'admin':
        courses = CourseService.get_all_courses()
    elif current_user.role == 'teacher':
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        if teacher:
            courses = CourseService.get_teacher_courses(teacher.id)
            
    return render_template('attendance/index.html', courses=courses)

@attendance_bp.route('/course/<int:course_id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'teacher'])
def record(course_id):
    course = CourseService.get_course_by_id(course_id)
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for('attendance.index'))
        
    # Check authorization for Teacher
    if current_user.role == 'teacher':
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        if not teacher or course.teacher_id != teacher.id:
            abort(403)
            
    # Selected date
    date_str = request.args.get('date') or request.form.get('date')
    if date_str:
        try:
            date_val = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            date_val = date.today()
    else:
        date_val = date.today()
        
    enrolled_students = CourseService.get_enrolled_students(course.id)
    
    if request.method == 'POST':
        # Batch save attendance records
        attendance_data = []
        for s in enrolled_students:
            status_val = request.form.get(f"status_{s.id}")
            if status_val:
                attendance_data.append({
                    'student_id': s.id,
                    'status': status_val
                })
                
        try:
            AttendanceService.batch_mark_attendance(course.id, date_val, attendance_data)
            flash(f"Attendance recorded successfully for {date_val.strftime('%Y-%m-%d')}!", "success")
            return redirect(url_for('attendance.record', course_id=course.id, date=date_val.strftime('%Y-%m-%d')))
        except Exception as e:
            flash(f"Error saving attendance: {str(e)}", "danger")
            
    # Retrieve existing records for this date
    existing_records = AttendanceService.get_course_attendance_on_date(course.id, date_val)
    status_map = {r.student_id: r.status for r in existing_records}
    
    # Calculate summary stats for page header
    summary = AttendanceService.get_course_attendance_summary(course.id)
    
    return render_template(
        'attendance/record.html',
        course=course,
        date=date_val,
        students=enrolled_students,
        status_map=status_map,
        summary=summary
    )

@attendance_bp.route('/student/<int:student_id>')
@login_required
def student_report(student_id):
    student = Student.query.get(student_id)
    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for('attendance.index'))
        
    # Check permissions
    if current_user.role == 'student':
        logged_in_student = Student.query.filter_by(user_id=current_user.id).first()
        if not logged_in_student or logged_in_student.id != student.id:
            abort(403)
            
    # Course filter
    course_id_str = request.args.get('course_id')
    course_id = int(course_id_str) if course_id_str else None
    
    records = AttendanceService.get_student_attendance(student.id, course_id=course_id)
    percentage = AttendanceService.calculate_attendance_percentage(student.id, course_id=course_id)
    
    # List of enrolled courses for filter dropdown
    enrolled_courses = [e.course for e in student.enrollments]
    
    return render_template(
        'attendance/student_report.html',
        student=student,
        records=records,
        percentage=percentage,
        courses=enrolled_courses,
        selected_course_id=course_id
    )
