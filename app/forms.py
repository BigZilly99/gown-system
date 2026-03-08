"""
University Gown Management System - Forms (Simplified)
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SelectField, 
    FloatField, DateField, TextAreaField,
    BooleanField, IntegerField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, 
    NumberRange, Optional
)
from wtforms import ValidationError

from app.models import User, Student, Inventory, Department


class LoginForm(FlaskForm):
    """Login form"""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=80, message='Username must be between 3 and 80 characters')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required')
    ])
    remember = BooleanField('Remember Me')


class UserForm(FlaskForm):
    """User creation/editing form"""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=80, message='Username must be between 3 and 80 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Invalid email address')
    ])
    role = SelectField('Role', choices=[
        ('Admin', 'Admin'),
        ('Staff', 'Staff'),
        ('SuperAdmin', 'SuperAdmin')
    ], validators=[DataRequired(message='Role is required')])
    department = SelectField('Department', coerce=int, validators=[Optional()])
    password = PasswordField('Password', validators=[
        Length(min=6, message='Password must be at least 6 characters')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        EqualTo('password', message='Passwords must match')
    ])
    is_active = BooleanField('Active')
    
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        departments = Department.query.filter_by(is_active=True).all()
        self.department.choices = [(0, 'No Department (SuperAdmin)')] + [(d.id, d.name) for d in departments]
        self._user_id = None
        if 'obj' in kwargs and kwargs['obj']:
            self._user_id = kwargs['obj'].id
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user and user.id != self._user_id:
            raise ValidationError('Username already exists')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user and user.id != self._user_id:
            raise ValidationError('Email already exists')


class StudentForm(FlaskForm):
    """Student creation/editing form - simplified to only collect essential fields"""
    index_number = StringField('Index Number', validators=[
        DataRequired(message='Index number is required'),
        Length(min=3, max=50, message='Index number must be between 3 and 50 characters')
    ])
    full_name = StringField('Full Name', validators=[
        DataRequired(message='Full name is required'),
        Length(min=2, max=200, message='Full name must be between 2 and 200 characters')
    ])
    programme = StringField('Programme', validators=[
        DataRequired(message='Programme is required'),
        Length(max=200)
    ])
    level = SelectField('Level', choices=[
        ('Level 100', 'Level 100'),
        ('Level 200', 'Level 200'),
        ('Level 300', 'Level 300'),
        ('Level 400', 'Level 400'),
        ('Diploma', 'Diploma'),
        ('Bachelor', 'Bachelor'),
        ('Master', 'Master'),
        ('PhD', 'PhD')
    ], validators=[DataRequired(message='Level is required')])
    
    def validate_index_number(self, index_number):
        student = Student.query.filter_by(index_number=index_number.data).first()
        if student:
            raise ValidationError('Index number already exists')


class InventoryForm(FlaskForm):
    """Form for updating inventory counts (SuperAdmin only)"""
    gown_type = SelectField('Gown Type', choices=[
        ('GCTU Gowns', 'GCTU Gowns'),
        ('Gowns Rented from Out of Campus', 'Gowns Rented from Out of Campus')
    ], validators=[DataRequired(message='Gown type is required')])
    total_count = IntegerField('Total Count', validators=[
        DataRequired(message='Total count is required'),
        NumberRange(min=1, message='Total count must be at least 1')
    ])


class IssueGownForm(FlaskForm):
    """Form for issuing a gown to a student"""
    student_id = StringField('Student ID', validators=[
        DataRequired(message='Please select a student')
    ])
    gown_type = SelectField('Select Gown Type', choices=[
        ('GCTU Gowns', 'GCTU Gowns'),
        ('Gowns Rented from Out of Campus', 'Gowns Rented from Out of Campus')
    ], validators=[DataRequired(message='Please select a gown type')])
    expected_return_date = DateField('Expected Return Date', validators=[
        DataRequired(message='Expected return date is required')
    ])
    notes = TextAreaField('Notes', validators=[Optional()])


class ReturnGownForm(FlaskForm):
    """Form for returning a gown"""
    student_id = StringField('Student ID', validators=[
        DataRequired(message='Please select a student')
    ])
    notes = TextAreaField('Notes', validators=[Optional()])


class SearchForm(FlaskForm):
    """General search form"""
    search = StringField('Search', validators=[Optional()])
    search_type = SelectField('Search By', choices=[
        ('index', 'Index Number'),
        ('name', 'Name')
    ], default='index')


class GownTypeForm(FlaskForm):
    """Form for creating/editing gown types"""
    name = StringField('Gown Type Name', validators=[
        DataRequired(message='Name is required'),
        Length(max=50)
    ])
    description = StringField('Description', validators=[
        Optional(),
        Length(max=255)
    ])
    deposit_amount = FloatField('Deposit Amount', validators=[
        Optional(),
        NumberRange(min=0)
    ])
    rental_fee = FloatField('Rental Fee', validators=[
        Optional(),
        NumberRange(min=0)
    ])


class GownForm(FlaskForm):
    """Form for creating/editing individual gowns"""
    gown_type = SelectField('Gown Type', coerce=int, validators=[
        DataRequired(message='Gown type is required')
    ])
    size = SelectField('Size', choices=[
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
        ('XXL', 'Double XL')
    ], validators=[Optional()])
    status = SelectField('Status', choices=[
        ('Available', 'Available'),
        ('Issued', 'Issued'),
        ('Maintenance', 'Under Maintenance')
    ], validators=[DataRequired(message='Status is required')])
    condition = SelectField('Condition', choices=[
        ('Excellent', 'Excellent'),
        ('Good', 'Good'),
        ('Fair', 'Fair'),
        ('Poor', 'Poor')
    ], validators=[DataRequired(message='Condition is required')])
    notes = TextAreaField('Notes', validators=[Optional()])
    purchase_date = DateField('Purchase Date', validators=[Optional()])
