# app.py
from flask import Flask, render_template, g, current_app
import os
import psycopg2 # For PostgreSQL
from psycopg2 import extras # For dictionary-like rows
import logging # For better logging of errors

# Configure logging
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# --- Database Configuration for PostgreSQL ---
# DATABASE_URL will be set as an environment variable on Render
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    """
    Establishes a PostgreSQL database connection or returns the existing one.
    Uses Flask's g object to store the connection for the duration of the request.
    """
    db = getattr(g, '_database', None)
    if db is None:
        if not DATABASE_URL:
            current_app.logger.error("DATABASE_URL environment variable is not set.")
            raise ValueError("DATABASE_URL environment variable is not set.")
        try:
            # Attempt to connect to the database
            conn = psycopg2.connect(DATABASE_URL)
            # Set cursor factory for dictionary-like rows
            conn.cursor_factory = psycopg2.extras.RealDictCursor
            db = g._database = conn
            current_app.logger.info("Successfully connected to the database.")
        except Exception as e:
            current_app.logger.error(f"Failed to connect to database: {e}")
            # Re-raise the exception to make the error visible in the application
            raise
    return db

@app.teardown_appcontext
def close_connection(exception):
    """
    Closes the database connection at the end of the application context.
    """
    db = getattr(g, '_database', None)
    if db is not None:
        # Check if the connection is actually open before trying to close it
        if not db.closed:
            db.close()
            current_app.logger.info("Database connection closed.")


def init_db():
    """
    Initializes the database by executing the schema.sql script.
    This function will be called manually once after database creation (e.g., from Render shell).
    """
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            cursor = db.cursor()
            cursor.execute(f.read())
            db.commit()
            cursor.close()
    app.logger.info("Database initialized/updated successfully.")

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