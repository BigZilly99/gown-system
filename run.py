"""
University Gown Management System - Application Entry Point
"""

import os
from app import create_app, db
from app.models import User, GownType

app = create_app()


@app.cli.command('init-db')
def init_db_command():
    """Initialize the database with default data"""
    db.create_all()
    
    # Create default gown types if none exist
    if GownType.query.count() == 0:
        gown_types = [
            GownType(name='Bachelor', description='Bachelor degree gown', deposit_amount=50.0, rental_fee=25.0),
            GownType(name='Master', description='Master degree gown', deposit_amount=75.0, rental_fee=35.0),
            GownType(name='PhD', description='Doctoral gown', deposit_amount=100.0, rental_fee=50.0),
        ]
        db.session.bulk_save_objects(gown_types)
        db.session.commit()
        print('Created default gown types.')
    
    print('Database initialized successfully.')


if __name__ == '__main__':
    # Create instance folder if it doesn't exist
    instance_path = os.path.join(os.path.dirname(__file__), 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
