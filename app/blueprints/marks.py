from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.services.marks_service import MarksService
from app.services.course_service import CourseService
from app.services.auth_service import role_required
from app.models import Course, Student, Teacher, Mark

marks_bp = Blueprint('marks', __name__)

@marks_bp.route('/')
@login_required
def index():
    if current_user.role == 'student':
        student = Student.query.filter_by(user_id=current_user.id).first()
        if not student:
            flash("Student profile not found.", "danger")
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('marks.student_report', student_id=student.id))
        
    # For Admin/Teacher, list courses
    courses = []
    if current_user.role == 'admin':
        courses = CourseService.get_all_courses()
    elif current_user.role == 'teacher':
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        if teacher:
            courses = CourseService.get_teacher_courses(teacher.id)
            
    return render_template('marks/index.html', courses=courses)

@marks_bp.route('/course/<int:course_id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'teacher'])
def record(course_id):
    course = CourseService.get_course_by_id(course_id)
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for('marks.index'))
        
    # Check authorization for Teacher
    if current_user.role == 'teacher':
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        if not teacher or course.teacher_id != teacher.id:
            abort(403)
            
    enrolled_students = CourseService.get_enrolled_students(course.id)
    
    if request.method == 'POST':
        # Process bulk grades input
        success_count = 0
        error_messages = []
        
        for s in enrolled_students:
            assignment_str = request.form.get(f"assignment_{s.id}")
            midterm_str = request.form.get(f"midterm_{s.id}")
            final_str = request.form.get(f"final_{s.id}")
            
            # If any are empty, we skip or assume 0 (or require all filled)
            if assignment_str is not None and midterm_str is not None and final_str is not None:
                try:
                    assignment = float(assignment_str) if assignment_str != '' else 0.0
                    midterm = float(midterm_str) if midterm_str != '' else 0.0
                    final = float(final_str) if final_str != '' else 0.0
                    
                    MarksService.save_marks(
                        student_id=s.id,
                        course_id=course.id,
                        assignment=assignment,
                        midterm=midterm,
                        final=final,
                        current_user_id=current_user.id
                    )
                    success_count += 1
                except Exception as e:
                    error_messages.append(f"Student {s.student_id}: {str(e)}")
                    
        if error_messages:
            flash(f"Updated grades with some errors: {', '.join(error_messages)}", "warning")
        else:
            flash(f"Successfully recorded grades for {success_count} students!", "success")
            
        return redirect(url_for('marks.record', course_id=course.id))
        
    # Get existing grade records
    existing_marks = MarksService.get_course_marks(course.id)
    marks_map = {m.student_id: m for m in existing_marks}
    
    return render_template(
        'marks/record.html',
        course=course,
        students=enrolled_students,
        marks_map=marks_map
    )

@marks_bp.route('/student/<int:student_id>')
@login_required
def student_report(student_id):
    student = Student.query.get(student_id)
    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for('marks.index'))
        
    # Check permissions
    if current_user.role == 'student':
        logged_in_student = Student.query.filter_by(user_id=current_user.id).first()
        if not logged_in_student or logged_in_student.id != student.id:
            abort(403)
            
    marks = MarksService.get_student_marks(student.id)
    cumulative_gpa = MarksService.calculate_student_gpa(student.id)
    
    return render_template(
        'marks/student_report.html',
        student=student,
        marks=marks,
        cumulative_gpa=cumulative_gpa
    )
