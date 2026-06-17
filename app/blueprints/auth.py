from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.database import db
from app.models import User, Student, Teacher
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService
from app.services.student_service import StudentService
from app.services.storage_service import get_storage_service
from flask import current_app

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = AuthService.authenticate_user(email, password)
        if user:
            login_user(user, remember=remember)
            # Log successful login
            AuditService.log_event(
                action="login",
                user_id=user.id,
                email=user.email,
                details="User logged in successfully"
            )
            flash("Welcome back!", "success")
            
            # Redirect to next parameter if present
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            # Log failed login
            AuditService.log_event(
                action="failed_login",
                email=email,
                details="Failed login attempt with incorrect credentials"
            )
            flash("Login failed. Please check your credentials and try again.", "danger")
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    user_id = current_user.id
    email = current_user.email
    logout_user()
    
    # Log successful logout
    AuditService.log_event(
        action="logout",
        user_id=user_id,
        email=email,
        details="User logged out successfully"
    )
    flash("You have been logged out.", "info")
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Allows registration. To make the demo robust, it supports admin, teacher, and student registration."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'student')  # admin, teacher, student
        
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("Email already registered.", "danger")
            return redirect(url_for('auth.register'))
            
        try:
            if role == 'student':
                # Student registration requires student details
                storage = get_storage_service(current_app.config)
                student_service = StudentService(storage)
                student_data = {
                    'email': email,
                    'password': password,
                    'student_id': request.form.get('student_id'),
                    'first_name': request.form.get('first_name'),
                    'last_name': request.form.get('last_name'),
                    'date_of_birth': datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date() if request.form.get('date_of_birth') else datetime.now().date(),
                    'gender': request.form.get('gender'),
                    'phone': request.form.get('phone'),
                    'address': request.form.get('address'),
                    'department': request.form.get('department', 'Computer Science'),
                    'program': request.form.get('program', 'B.Sc. CS')
                }
                student_service.create_student(student_data, current_user_id=None)
            elif role == 'teacher':
                # Teacher registration
                user = AuthService.register_user(email, password, 'teacher')
                teacher = Teacher(
                    user_id=user.id,
                    employee_id=request.form.get('employee_id'),
                    first_name=request.form.get('t_first_name') or request.form.get('first_name'),
                    last_name=request.form.get('t_last_name') or request.form.get('last_name'),
                    phone=request.form.get('t_phone') or request.form.get('phone'),
                    department=request.form.get('t_department') or request.form.get('department'),
                    specialization=request.form.get('specialization')
                )
                db.session.add(teacher)
                db.session.commit()
            else:
                # Admin registration
                AuthService.register_user(email, password, 'admin')
                
            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash(f"Error registering user: {str(e)}", "danger")
            
    return render_template('auth/register.html')

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Simple password reset workflow."""
    if request.method == 'POST':
        email = request.form.get('email')
        new_password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user:
            user.password_hash = AuthService.hash_password(new_password)
            db.session.commit()
            AuditService.log_event(
                action="password_reset",
                user_id=user.id,
                email=user.email,
                details="User successfully reset password"
            )
            flash("Your password has been reset successfully. Please log in.", "success")
            return redirect(url_for('auth.login'))
        else:
            flash("Email not found in database.", "danger")
            
    return render_template('auth/reset_password.html')
from datetime import datetime
