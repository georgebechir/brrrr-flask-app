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
    else:
        # Check if the existing connection is still usable
        try:
            # A simple query to check connection health (PostgreSQL specific)
            # If the connection is broken, this will raise an exception
            db.cursor().execute("SELECT 1")
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            current_app.logger.warning(f"Existing DB connection stale or broken: {e}. Reconnecting...")
            # If connection is broken, close it and try to reconnect
            if not db.closed:
                db.close()
            try:
                conn = psycopg2.connect(DATABASE_URL)
                conn.cursor_factory = psycopg2.extras.RealDictCursor
                db = g._database = conn
                current_app.logger.info("Successfully reconnected to the database.")
            except Exception as reconnect_e:
                current_app.logger.error(f"Failed to reconnect to database: {reconnect_e}")
                raise reconnect_e # Re-raise the reconnection error
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
    """
    with app.app_context():
        db = get_db() # Use get_db to ensure a connection
        with app.open_resource('schema.sql', mode='r') as f:
            cursor = db.cursor()
            cursor.execute(f.read())
            db.commit()
            cursor.close()
    app.logger.info("Database initialized/updated successfully.")

# --- Register Blueprints (Modularized App Sections) ---
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
    app.run(debug=True)