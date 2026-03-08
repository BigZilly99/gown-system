web: python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('Database initialized!')" && gunicorn 'run:app' --bind 0.0.0.0:$PORT --timeout 120
