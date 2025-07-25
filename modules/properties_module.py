# modules/properties_module.py
from flask import Blueprint, render_template, request, url_for, redirect
from app import get_db # Import get_db from main app

properties_bp = Blueprint('properties_bp', __name__)

@properties_bp.route("/saved_properties")
def list_properties():
    """Displays a list of all saved properties with options to load/edit or delete."""
    db = get_db()
    cursor = db.cursor()
    properties = cursor.execute("SELECT id, property_address FROM properties ORDER BY saved_at DESC").fetchall()
    cursor.close() # Close cursor explicitly
    # No need to close db here, it's managed by app.teardown_appcontext

    message = request.args.get('message')
    error = request.args.get('error')
    return render_template('saved_properties.html', properties=properties, message=message, error=error)

@properties_bp.route("/delete_property/<int:property_id>")
def delete_property(property_id):
    """Deletes a property from the database."""
    db = get_db()
    cursor = db.cursor()
    message = None
    error = None
    try:
        cursor.execute("SELECT property_address FROM properties WHERE id = %s", (property_id,))
        prop = cursor.fetchone()
        if prop:
            property_address = prop['property_address']
            cursor.execute("DELETE FROM properties WHERE id = %s", (property_id,))
            db.commit()
            message = f"Property '{property_address}' deleted successfully!"
        else:
            message = "Property not found."
    except Exception as e:
        db.rollback()
        error = f"Database error while deleting: {e}"
    finally:
        cursor.close() # Close cursor explicitly

    return redirect(url_for('properties_bp.list_properties', message=message, error=error))
