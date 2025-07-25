
# app.py
from flask import Flask, render_template, g
import os
import psycopg2 # For PostgreSQL
from psycopg2 import extras # For dictionary-like rows

app = Flask(__name__)

# --- Database Configuration for PostgreSQL ---
# DATABASE_URL will be set as an environment variable on Render
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    """
    Establishes a PostgreSQL database connection or returns the existing one.
    """
    db = getattr(g, '_database', None)
    if db is None:
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is not set.")
        db = g._database = psycopg2.connect(DATABASE_URL)
        # Use RealDictCursor to get dictionary-like rows for easy column access
        db.cursor_factory = psycopg2.extras.RealDictCursor
    return db

@app.teardown_appcontext
def close_connection(exception):
    """
    Closes the database connection at the end of the application context.
    """
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """
    Initializes the database by executing the schema.sql script.
    This function will be called manually once after database creation (e.g., from Render shell).
    """
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            # For PostgreSQL, execute() is typically used for a single statement or script
            # executescript() is SQLite specific. For complex SQL, it's better to
            # execute line by line or ensure schema.sql is one valid command.
            # Assuming schema.sql is simple DDL for now.
            cursor = db.cursor()
            cursor.execute(f.read())
            db.commit()
            cursor.close()
    print("Database initialized/updated successfully.")

# --- Register Blueprints (Modularized App Sections) ---
# Import blueprints from their respective modules
from modules.rent_module import rent_bp
from modules.brrrr_module import brrrr_bp
from modules.properties_module import properties_bp

app.register_blueprint(rent_bp)
app.register_blueprint(brrrr_bp)
app.register_blueprint(properties_bp)

# --- Main Route ---
@app.route("/")
def index():
    """Renders the main landing page."""
    return render_template('main_menu.html')

if __name__ == "__main__":
    # This block runs only when you execute app.py directly (e.g., python app.py)
    # On Render, your web app is run by gunicorn, not this block.
    # For local testing, you can uncomment app.run(debug=True).
    # init_db() # You might run this once locally to create the db schema if not using a cloud DB directly
    app.run(debug=True)
