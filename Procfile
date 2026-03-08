web: python -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database created!')" && gunicorn run:app --timeout 120
