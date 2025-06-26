from src.main import create_app, create_default_data
from src.extensions import db
import os

app = create_app()

with app.app_context():
    # Drop all tables
    db.drop_all()
    print("All existing database tables dropped.")
    
    # Create all tables
    db.create_all()
    print("New database tables created.")
    
    # Add default data
    create_default_data()
    print("Default data added.")

print("Database reinitialization complete.")

