"""
University Gown Management System - Authentication Routes
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

from app import db
from app.models import User, AuditLog
from app.forms import LoginForm, UserForm

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    # If user is authenticated and has admin privileges, redirect to dashboard
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('main.dashboard'))
        else:
            # User is logged in but not admin - logout and show login
            logout_user()
            flash('Session expired. Please login again.', 'warning')
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact administrator.', 'danger')
                return render_template('login.html', form=form)
            
            # Check if user has a valid role (all users are created by SuperAdmin)
            if not user.role:
                flash('Your account has no role assigned. Please contact a SuperAdmin.', 'warning')
                return render_template('login.html', form=form)
            
            # Check if admin has department assigned (for non-SuperAdmin)
            if user.role != 'SuperAdmin' and not user.has_department():
                flash('Your account is not assigned to any department. Please contact a SuperAdmin.', 'warning')
                return render_template('login.html', form=form)
            
            login_user(user, remember=form.remember.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Log the login
            log = AuditLog(
                user_id=user.id,
                action='Login',
                details=f'User {user.username} logged in',
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout"""
    # Log the logout
    log = AuditLog(
        user_id=current_user.id,
        action='Logout',
        details=f'User {current_user.username} logged out',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/users')
@login_required
def users():
    """List all users (SuperAdmin only)"""
    if not current_user.is_superadmin():
        flash('Access denied. SuperAdmin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    users_list = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('users.html', users=users_list)


@auth_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
def new_user():
    """Create new user (SuperAdmin only)"""
    if not current_user.is_superadmin():
        flash('Access denied. SuperAdmin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    form = UserForm()
    
    # Remove password requirement for editing
    if request.method == 'GET':
        form.password.validators = []
        form.confirm_password.validators = []
    
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data,
            is_active=form.is_active.data if form.is_active.data else True
        )
        user.set_password(form.password.data)
        
        # Set department based on role
        if form.role.data == 'SuperAdmin':
            user.department_id = None
        else:
            user.department_id = form.department.data if form.department.data != 0 else None
            user.is_approved = True  # Auto-approve users created by SuperAdmin
        
        db.session.add(user)
        db.session.commit()
        
        # Log the action
        log = AuditLog(
            user_id=current_user.id,
            action='Create User',
            entity_type='User',
            entity_id=user.id,
            details=f'Created user {user.username} with role {user.role}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'User {user.username} created successfully!', 'success')
        return redirect(url_for('auth.users'))
    
    return render_template('user_form.html', form=form, title='Create User')


@auth_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Edit user (SuperAdmin only)"""
    if not current_user.is_superadmin():
        flash('Access denied. SuperAdmin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    
    # Remove password validation for editing (optional)
    form.password.description = 'Leave blank to keep current password'
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.is_active = form.is_active.data
        
        # Update department based on role
        if form.role.data == 'SuperAdmin':
            user.department_id = None
        else:
            user.department_id = form.department.data if form.department.data != 0 else None
        
        if form.password.data:
            user.set_password(form.password.data)
        
        db.session.commit()
        
        # Log the action
        log = AuditLog(
            user_id=current_user.id,
            action='Edit User',
            entity_type='User',
            entity_id=user.id,
            details=f'Edited user {user.username}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'User {user.username} updated successfully!', 'success')
        return redirect(url_for('auth.users'))
    
    return render_template('user_form.html', form=form, title=f'Edit User: {user.username}')


@auth_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete user (SuperAdmin only)"""
    if not current_user.is_superadmin():
        flash('Access denied. SuperAdmin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('auth.users'))
    
    username = user.username
    
    # Log before deletion
    log = AuditLog(
        user_id=current_user.id,
        action='Delete User',
        entity_type='User',
        entity_id=user.id,
        details=f'Deleted user {username}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {username} deleted successfully!', 'success')
    return redirect(url_for('auth.users'))


# =====================================================
# Registration - Disabled (Only SuperAdmin can create accounts)
# =====================================================

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration is disabled - only SuperAdmin can create accounts"""
    flash('Registration is disabled. Please contact a SuperAdmin to create your account.', 'info')
    return redirect(url_for('auth.login'))


# =====================================================
# Admin Approval Workflow Routes - REMOVED
# Only SuperAdmin can create staff/admin accounts
# =====================================================
