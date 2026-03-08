"""
University Gown Management System - Access Control Decorators
"""

from functools import wraps
from flask import flash, redirect, url_for, request
from flask_login import current_user


def superadmin_required(f):
    """Decorator to require SuperAdmin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_superadmin():
            flash('Access denied. SuperAdmin privileges required.', 'danger')
            return redirect(url_for('main.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require Admin or SuperAdmin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin():
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function


def department_required(f):
    """Decorator to require department assignment (non-SuperAdmin)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('auth.login'))
        
        # SuperAdmin can access all departments
        if current_user.is_superadmin():
            return f(*args, **kwargs)
        
        # Check if admin has a department assigned
        if not current_user.has_department():
            flash('You are not assigned to any department. Please contact a SuperAdmin.', 'warning')
            return redirect(url_for('main.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


def get_user_permissions():
    """Get current user's permissions based on role"""
    if not current_user.is_authenticated:
        return {
            'can_view_dashboard': False,
            'can_view_students': False,
            'can_manage_students': False,
            'can_manage_inventory': False,
            'can_issue_gowns': False,
            'can_return_gowns': False,
            'can_view_transactions': False,
            'can_verify_documents': False,
            'can_manage_users': False,
            'can_view_audit_logs': False,
            'can_export_data': False,
            'is_superadmin': False,
            'is_admin': False,
            'department_id': None,
            'department_name': None,
        }
    
    is_super = current_user.is_superadmin()
    is_admin = current_user.is_admin()
    
    return {
        'can_view_dashboard': True,
        'can_view_students': is_super or is_admin,  # Both can view
        'can_manage_students': is_super,  # SuperAdmin only - add/edit/delete/import
        'can_manage_inventory': is_super,  # SuperAdmin only - manage inventory
        'can_issue_gowns': is_super or is_admin,  # Both can issue
        'can_return_gowns': is_super or is_admin,  # Both can return
        'can_view_transactions': is_super or is_admin,  # Both can view
        'can_verify_documents': is_super or is_admin,  # Both can verify
        'can_manage_users': is_super,  # SuperAdmin only
        'can_view_audit_logs': is_super,  # SuperAdmin only
        'can_export_data': is_super,  # SuperAdmin only
        'is_superadmin': is_super,
        'is_admin': is_admin,
        'department_id': current_user.department_id,
        'department_name': current_user.department.name if current_user.department else None,
    }


def get_accessible_department_id():
    """Get the department_id that the current user can access data for"""
    if not current_user.is_authenticated:
        return None
    
    # SuperAdmin can access all departments
    if current_user.is_superadmin():
        return None  # None means all departments
    
    # Regular admin can only access their department
    return current_user.department_id
