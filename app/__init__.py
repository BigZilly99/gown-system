"""
University Gown Management System - Application Factory
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_caching import Cache
from apscheduler.schedulers.background import BackgroundScheduler

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()
cache = Cache()
scheduler = BackgroundScheduler()

# Import models for registration
from app.models import User, Student, Inventory, Transaction, AuditLog, Department


def init_db_optimizations(app):
    """Initialize database optimizations for SQLite"""
    
    if 'sqlite' in app.config.get('SQLALCHEMY_DATABASE_URI', ''):
        from sqlalchemy import event
        from sqlalchemy.engine import Engine
        
        @event.listens_for(Engine, "connect")
        def set_pragma(dbapi_conn, connection_record):
            """Set SQLite optimizations for better performance"""
            cursor = dbapi_conn.cursor()
            
            # Enable WAL mode for better concurrency
            cursor.execute('PRAGMA journal_mode=WAL')
            
            # Enable foreign keys
            cursor.execute('PRAGMA foreign_keys=ON')
            
            # Synchronous mode - NORMAL is safe with WAL and faster
            cursor.execute('PRAGMA synchronous=NORMAL')
            
            # Cache size - negative value = KB, 2000 = 2MB cache
            cursor.execute('PRAGMA cache_size=-2000')
            
            # Temp store in memory
            cursor.execute('PRAGMA temp_store=MEMORY')
            
            # Memory map size (512MB)
            cursor.execute('PRAGMA mmap_size=536870912')
            
            # Read uncommitted for better read performance
            cursor.execute('PRAGMA read_uncommitted=1')
            
            cursor.close()


def create_app(config_name=None):
    """Application factory"""
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    
    # Load configuration
    from config import config
    app.config.from_object(config.get(config_name, config['default']))
    
    # Initialize database optimizations
    db.init_app(app)
    init_db_optimizations(app)
    
    # Initialize other extensions
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    cache.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.students import students_bp
    from app.routes.inventory import inventory_bp
    from app.routes.transactions import transactions_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(transactions_bp)
    
    # Register context processor for permissions
    from app.access_control import get_user_permissions
    @app.context_processor
    def inject_permissions():
        permissions = get_user_permissions()
        return dict(user_permissions=permissions)
    
    # Create instance folder if it doesn't exist
    instance_path = os.path.join(os.path.dirname(__file__), 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    
    # Create upload folder
    upload_folder = os.path.join(app.root_path, 'uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    # Register CLI commands
    register_cli_commands(app)
    
    return app


def register_cli_commands(app):
    """Register CLI commands"""
    
    @app.cli.command('create-superadmin')
    def create_superadmin_command():
        """Create a superadmin user"""
        from app.models import User
        from app import db
        
        username = input('Enter superadmin username: ')
        
        # Check if user exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f'User {username} already exists!')
            return
        
        password = input('Enter password: ')
        email = input('Enter email: ')
        
        # Create superadmin
        user = User(
            username=username,
            email=email,
            role='SuperAdmin',
            is_active=True
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        print(f'Superadmin {username} created successfully!')
    
    @app.cli.command('create-admin')
    def create_admin_command():
        """Create an admin user"""
        from app.models import User
        from app import db
        
        username = input('Enter admin username: ')
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f'User {username} already exists!')
            return
        
        password = input('Enter password: ')
        email = input('Enter email: ')
        
        user = User(
            username=username,
            email=email,
            role='Admin',
            is_active=True
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        print(f'Admin {username} created successfully!')
    
    @app.cli.command('init-db')
    def init_db_command():
        """Initialize database with optimizations"""
        from app import db
        
        with app.app_context():
            # Create all tables
            db.create_all()
            
            # Run optimizations
            if 'sqlite' in app.config.get('SQLALCHEMY_DATABASE_URI', ''):
                from sqlalchemy import text
                # Create indexes for better query performance
                db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_students_index ON students(index_number)'))
                db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_students_name ON students(full_name)'))
                db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_inventory_gown_type ON inventory(gown_type)'))
                db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_transactions_student ON transactions(student_id)'))
                db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_transactions_gown_type ON transactions(gown_type)'))
                db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status)'))
                db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id)'))
                db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp)'))
                db.session.commit()
                print('Database initialized with performance optimizations!')
            else:
                print('Database initialized!')
