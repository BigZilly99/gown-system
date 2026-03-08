"""
University Gown Management System - Database Models (Simplified)
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

import bcrypt


class User(UserMixin, db.Model):
    """User model for authentication and authorization"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=True)  # SuperAdmin, Staff
    is_approved = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Department assignment - one admin belongs to only 1 department (except SuperAdmin)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    
    # Relationships - with cascade delete
    transactions = db.relationship('Transaction', backref='issuer', lazy='dynamic', 
                                   foreign_keys='Transaction.issued_by', cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic', 
                                  cascade='all, delete-orphan')
    approver = db.relationship('User', remote_side=[id], foreign_keys=[approved_by])
    department = db.relationship('Department', backref='admins', foreign_keys=[department_id])
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password - supports both werkzeug and legacy bcrypt hashes"""
        # Check if it's a bcrypt hash (starts with $2a$, $2b$, or $2y$)
        if self.password_hash and self.password_hash.startswith('$2'):
            try:
                return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
            except Exception:
                return False
        # Otherwise use werkzeug
        return check_password_hash(self.password_hash, password)
    
    def is_superadmin(self):
        """Check if user is SuperAdmin"""
        return self.role == 'SuperAdmin'
    
    def is_admin(self):
        """Check if user is Admin or SuperAdmin"""
        return self.role in ['Admin', 'SuperAdmin']
    
    def has_department(self):
        """Check if user has a department assigned"""
        return self.department_id is not None
    
    def is_approved_account(self):
        """Check if user account is approved by SuperAdmin"""
        if self.role == 'SuperAdmin':
            return True
        return self.is_approved == True and self.role is not None
    
    def can_access_department(self, department_id):
        """Check if user can access a specific department's data"""
        if self.is_superadmin():
            return True
        if self.department_id == department_id:
            return True
        return False
    
    def __repr__(self):
        return f'<User {self.username}>'


class Department(db.Model):
    """Department model for FACULTY OF COMPUTING AND INFORMATION SYSTEMS (FoCIS)"""
    
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.String(255))
    # Programme keywords that map to this department (comma-separated, case-insensitive)
    programme_keywords = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    students = db.relationship('Student', backref='department', lazy='dynamic')
    
    def get_student_count(self):
        """Get total number of students in this department"""
        return self.students.count()
    
    def matches_programme(self, programme):
        """Check if a programme matches this department based on keywords"""
        if not self.programme_keywords or not programme:
            return False
        keywords = [k.strip().lower() for k in self.programme_keywords.split(',')]
        programme_lower = programme.lower()
        return any(keyword in programme_lower for keyword in keywords)
    
    @staticmethod
    def get_department_by_programme(programme):
        """Find department that matches the given programme - prioritizes longer/more specific matches"""
        if not programme:
            return None
        departments = Department.query.filter_by(is_active=True).all()
        
        best_match = None
        best_match_length = 0
        
        for dept in departments:
            if dept.programme_keywords and programme:
                keywords = [k.strip().lower() for k in dept.programme_keywords.split(',')]
                programme_lower = programme.lower()
                
                for keyword in keywords:
                    if keyword in programme_lower:
                        # Prioritize longer keyword matches
                        if len(keyword) > best_match_length:
                            best_match = dept
                            best_match_length = len(keyword)
        
        return best_match
    
    def __repr__(self):
        return f'<Department {self.name}>'


class Student(db.Model):
    """Student model - simplified to only collect essential fields for gown management"""
    
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    index_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(200), nullable=False, index=True)
    programme = db.Column(db.String(200), nullable=False)
    level = db.Column(db.String(50), nullable=False)  # Level 100, Level 200, Diploma, Bachelor, Master, PhD
    
    # Department is auto-assigned based on programme
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='student', lazy='dynamic')
    
    def has_active_rental(self):
        """Check if student has an active rental"""
        return self.transactions.filter(Transaction.status == 'Issued').first() is not None
    
    def get_active_transaction(self):
        """Get the student's active transaction if any"""
        return self.transactions.filter(Transaction.status == 'Issued').first()
    
    def assign_department(self):
        """Auto-assign department based on programme"""
        if not self.department_id and self.programme:
            dept = Department.get_department_by_programme(self.programme)
            if dept:
                self.department_id = dept.id
        return self.department_id
    
    def __repr__(self):
        return f'<Student {self.index_number}>'


class Inventory(db.Model):
    """Inventory model - tracks total gown counts by type (SuperAdmin only)"""
    
    __tablename__ = 'inventory'
    
    id = db.Column(db.Integer, primary_key=True)
    gown_type = db.Column(db.String(50), unique=True, nullable=False)  # 'GCTU Gowns' or 'Gowns Rented from Out of Campus'
    total_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_available_count(self):
        """Get available gowns = total - issued"""
        issued = Transaction.query.filter_by(
            gown_type=self.gown_type,
            status='Issued'
        ).count()
        return self.total_count - issued
    
    def get_issued_count(self):
        """Get currently issued count"""
        return Transaction.query.filter_by(
            gown_type=self.gown_type,
            status='Issued'
        ).count()
    
    def __repr__(self):
        return f'<Inventory {self.gown_type}: {self.total_count}>'


class Transaction(db.Model):
    """Transaction model for gown rentals"""
    
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    gown_type = db.Column(db.String(50), nullable=False)  # 'GCTU Gowns' or 'Gowns Rented from Out of Campus'
    issued_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    issue_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expected_return_date = db.Column(db.Date, nullable=False)
    actual_return_date = db.Column(db.DateTime)
    
    status = db.Column(db.String(20), nullable=False, default='Issued', index=True)  # Issued, Returned
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def is_overdue(self):
        """Check if transaction is overdue"""
        from datetime import date
        if self.status == 'Issued' and date.today() > self.expected_return_date:
            return True
        return False
    
    def get_days_overdue(self):
        """Get number of days overdue"""
        if self.is_overdue():
            from datetime import date
            return (date.today() - self.expected_return_date).days
        return 0
    
    def __repr__(self):
        return f'<Transaction {self.id} - Student {self.student_id}>'


class AuditLog(db.Model):
    """Audit log for tracking all actions"""
    
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    entity_type = db.Column(db.String(50))
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<AuditLog {self.action} by User {self.user_id}>'


class GownType(db.Model):
    """Gown type model for different categories of gowns"""
    
    __tablename__ = 'gown_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # Bachelor, Master, PhD
    description = db.Column(db.String(255))
    deposit_amount = db.Column(db.Float, default=0.0)
    rental_fee = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    gowns = db.relationship('Gown', backref='gown_type', lazy='dynamic')
    
    def get_total_count(self):
        """Get total number of gowns of this type"""
        return self.gowns.count()
    
    def get_available_count(self):
        """Get available gowns of this type"""
        return self.gowns.filter_by(status='Available').count()
    
    def get_issued_count(self):
        """Get issued gowns of this type"""
        return self.gowns.filter_by(status='Issued').count()
    
    def __repr__(self):
        return f'<GownType {self.name}>'


class Gown(db.Model):
    """Individual gown model"""
    
    __tablename__ = 'gowns'
    
    id = db.Column(db.Integer, primary_key=True)
    gown_type_id = db.Column(db.Integer, db.ForeignKey('gown_types.id'), nullable=False)
    size = db.Column(db.String(20))  # S, M, L, XL, XXL
    status = db.Column(db.String(20), default='Available', index=True)  # Available, Issued, Maintenance
    condition = db.Column(db.String(20), default='Good')  # Excellent, Good, Fair, Poor
    notes = db.Column(db.Text)
    purchase_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Note: Transaction.gown_type is a string field, not a foreign key to Gown
    # So there's no direct relationship between Gown and Transaction
    
    def is_available(self):
        """Check if gown is available"""
        return self.status == 'Available'
    
    def __repr__(self):
        return f'<Gown {self.id} - {self.gown_type.name if self.gown_type else "Unknown"}>'


# Helper function to log audit
def log_audit(user_id, action, entity_type=None, entity_id=None, details=None, ip_address=None):
    """Log an audit entry"""
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip_address
    )
    db.session.add(log)
    db.session.commit()
