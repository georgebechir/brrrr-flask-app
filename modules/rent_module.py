# modules/rent_module.py
from flask import Blueprint, render_template, request
import os
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from app import get_db # Import get_db from main app

rent_bp = Blueprint('rent_bp', __name__)

# --- Load Rent Data (happens once when the app starts) ---
# Ensure the Excel file is in the same directory as app.py (or accessible path)
# On Render, files are in /opt/render/project/src/
# The path here is relative to this file's location (modules/)
# os.path.dirname(__file__) is 'your-github-repo/modules'
# os.path.dirname(os.path.dirname(__file__)) goes up two levels to 'your-github-repo'
file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fairmarketrent.xlsx")
try:
    df = pd.read_excel(file_path, sheet_name="can you organize this in a tabl")
    print(f"Rent module initialized. Excel columns loaded: {df.columns.tolist()}")
except FileNotFoundError:
    print(f"Error: fairmarketrent.xlsx not found at {file_path}. Rent lookup will not work.")
    df = pd.DataFrame() # Create an empty DataFrame to prevent errors later
except Exception as e:
    print(f"Error loading fairmarketrent.xlsx: {e}")
    df = pd.DataFrame() # Create an empty DataFrame

@rent_bp.route("/rent_estimate", methods=["GET", "POST"])
def rent_estimate_page():
    rent = None
    error = None
    if request.method == "POST":
        input_string = request.form.get("address_or_zip", "").strip()
        bedrooms = request.form.get("bedrooms", "")

        zip_code_for_lookup = None

        try:
            if input_string.isdigit() and len(input_string) == 5:
                zip_code_for_lookup = input_string
            else:
                geolocator = Nominatim(user_agent="fair_market_rent_app")
                try:
                    location = geolocator.geocode(input_string, country_codes=['US'], addressdetails=True, timeout=5)
                    if location and location.raw and 'address' in location.raw and 'postcode' in location.raw['address']:
                        zip_code_for_lookup = location.raw['address']['postcode']
                        if '-' in zip_code_for_lookup:
                            zip_code_for_lookup = zip_code_for_lookup.split('-')[0]
                        if not (zip_code_for_lookup.isdigit() and len(zip_code_for_lookup) == 5):
                            zip_code_for_lookup = None
                    else:
                        error = "Could not find a ZIP code for the provided address."
                except (GeocoderTimedOut, GeocoderServiceError) as e:
                    error = f"Geocoding service error: {e}. Please try again or enter a ZIP code directly."
                except Exception as e:
                    error = f"An unexpected error occurred during geocoding: {e}"

            if zip_code_for_lookup:
                if not df.empty: # Check if DataFrame was loaded successfully
                    zip_row = df[df['ZIP'] == int(zip_code_for_lookup)]
                    if zip_row.empty:
                        error = f"No data found for ZIP code {zip_code_for_lookup}. Please try a different ZIP or address."
                    else:
                        col_map = {
                            '0': 'Efficiency',
                            '1': 'One-Bedroom',
                            '2': 'Two-Bedroom',
                            '3': 'Three-Bedroom',
                            '4': 'Four-Bedroom'
                        }
                        col_name = col_map.get(bedrooms)
                        if col_name and col_name in zip_row.columns:
                            rent = zip_row.iloc[0][col_name]
                        else:
                            error = "Invalid bedroom selection. Please try again."
                else:
                    error = "Rent data not loaded. Please ensure 'fairmarketrent.xlsx' is correctly placed."
            elif not error:
                error = "Please enter a valid 5-digit ZIP code or a complete address."
        except ValueError:
            error = "Invalid input. Please enter a 5-digit ZIP code or a complete address."
        except Exception as e:
            error = f"An unexpected server error occurred: {e}"

    return render_template('rent_lookup.html', rent=rent, error=error, request=request)
