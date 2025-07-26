# modules/brrrr_module.py
from flask import Blueprint, render_template, request, url_for, redirect
from app import get_db  # Import get_db from main app

brrrr_bp = Blueprint('brrrr_bp', __name__)

# --- Helper Function for Mortgage Calculation ---
def calculate_monthly_payment(principal, annual_interest_rate, loan_term_years):
    if principal <= 0 or loan_term_years <= 0:
        return 0

    monthly_interest_rate = (annual_interest_rate / 100) / 12
    number_of_payments = loan_term_years * 12

    if monthly_interest_rate == 0:
        return principal / number_of_payments
    else:
        monthly_payment = principal * (monthly_interest_rate * (1 + monthly_interest_rate)**number_of_payments) / \
                          ((1 + monthly_interest_rate)**number_of_payments - 1)
        return monthly_payment

# --- Core BRRRR Calculation Logic ---
def perform_brrrr_calculations(form_inputs):
    error = None

    calculated_outputs = {
        'total_initial_investment': 0.0, 'hard_money_loan_amount': 0.0, 'monthly_interest_only_hm': 0.0,
        'holding_costs_rehab': 0.0, 'total_out_of_pocket': 0.0, 'refinance_loan_amount': 0.0,
        'money_from_refi_after_payoff': 0.0, 'cash_left_in_deal': 0.0, 'equity_created': 0.0,
        'monthly_mortgage_refi': 0.0, 'monthly_operating_expenses': 0.0, 'monthly_cash_flow': 0.0,
        'annual_cash_flow': 0.0, 'cash_on_cash_return': 0.0, 'results_calculated': False
    }

    try:
        property_address = form_inputs.get("property_address", "").strip()
        if not property_address:
            raise ValueError("Property Address/Name is required to calculate.")

        purchase_price = float(form_inputs.get("purchase_price", 0.0))
        rehab_cost = float(form_inputs.get("rehab_cost", 0.0))
        closing_costs_1 = float(form_inputs.get("closing_costs_1", 0.0))
        arv = float(form_inputs.get("arv", 0.0))

        down_payment_1_pct = float(form_inputs.get("down_payment_1_pct", 0.0))
        interest_rate_1 = float(form_inputs.get("interest_rate_1", 0.0))
        rehab_period_months = int(form_inputs.get("rehab_period_months", 0))

        refinance_pct = float(form_inputs.get("refinance_pct", 0.0))
        interest_rate_2 = float(form_inputs.get("interest_rate_2", 0.0))
        loan_term_years = int(form_inputs.get("loan_term_years", 0))
        closing_costs_2 = float(form_inputs.get("closing_costs_2", 0.0))

        rent_estimate = float(form_inputs.get("rent_estimate", 0.0))
        property_tax = float(form_inputs.get("property_tax", 0.0))
        insurance = float(form_inputs.get("insurance", 0.0))
        property_management_pct = float(form_inputs.get("property_management_pct", 0.0))
        maintenance_pct = float(form_inputs.get("maintenance_pct", 0.0))
        vacancy_pct = float(form_inputs.get("vacancy_pct", 0.0))

        down_payment_1_decimal = down_payment_1_pct / 100
        refinance_decimal = refinance_pct / 100
        prop_management_decimal = property_management_pct / 100
        maintenance_decimal = maintenance_pct / 100
        vacancy_decimal = vacancy_pct / 100

        hard_money_loan_amount = (purchase_price * (1 - down_payment_1_decimal)) + rehab_cost
        monthly_interest_only_hm = (hard_money_loan_amount * (interest_rate_1 / 100)) / 12
        monthly_property_tax_actual = property_tax / 12
        monthly_insurance_actual = insurance / 12
        holding_costs_rehab = (monthly_interest_only_hm * rehab_period_months) + \
                              (monthly_property_tax_actual * rehab_period_months) + \
                              (monthly_insurance_actual * rehab_period_months)

        refinance_loan_amount = arv * refinance_decimal

        total_initial_investment = (purchase_price * down_payment_1_decimal) + closing_costs_1
        total_out_of_pocket = total_initial_investment + holding_costs_rehab
        money_from_refi_after_payoff = refinance_loan_amount - hard_money_loan_amount - closing_costs_2
        cash_left_in_deal = total_out_of_pocket - money_from_refi_after_payoff
        equity_created = arv - refinance_loan_amount

        monthly_mortgage_refi = calculate_monthly_payment(refinance_loan_amount, interest_rate_2, loan_term_years)
        monthly_property_management = rent_estimate * prop_management_decimal
        monthly_maintenance = rent_estimate * maintenance_decimal
        monthly_vacancy = rent_estimate * vacancy_decimal
        monthly_operating_expenses = monthly_property_management + monthly_maintenance + \
                                    monthly_vacancy + monthly_property_tax_actual + monthly_insurance_actual
        monthly_cash_flow = rent_estimate - monthly_operating_expenses - monthly_mortgage_refi
        annual_cash_flow = monthly_cash_flow * 12

        if annual_cash_flow > 0 and (cash_left_in_deal == 0 or (cash_left_in_deal > -0.01 and cash_left_in_deal < 0.01)):
            cash_on_cash_return = float('inf')
        elif cash_left_in_deal != 0:
            cash_on_cash_return = (annual_cash_flow / cash_left_in_deal) * 100
        else:
            cash_on_cash_return = 0.0

        calculated_outputs.update({
            'total_initial_investment': total_initial_investment,
            'hard_money_loan_amount': hard_money_loan_amount,
            'monthly_interest_only_hm': monthly_interest_only_hm,
            'holding_costs_rehab': holding_costs_rehab,
            'total_out_of_pocket': total_out_of_pocket,
            'refinance_loan_amount': refinance_loan_amount,
            'money_from_refi_after_payoff': money_from_refi_after_payoff,
            'cash_left_in_deal': cash_left_in_deal,
            'equity_created': equity_created,
            'monthly_mortgage_refi': monthly_mortgage_refi,
            'monthly_operating_expenses': monthly_operating_expenses,
            'monthly_cash_flow': monthly_cash_flow,
            'annual_cash_flow': annual_cash_flow,
            'cash_on_cash_return': cash_on_cash_return,
            'results_calculated': True
        })

    except ValueError as ve:
        error = f"Please ensure all inputs are valid numbers and all required fields are filled. Error: {ve}"
        calculated_outputs['results_calculated'] = False
    except Exception as e:
        error = f"An unexpected error occurred: {e}"
        calculated_outputs['results_calculated'] = False

    return calculated_outputs, error

@brrrr_bp.route("/brrrr_calculator", methods=["GET", "POST"], endpoint="brrrr_calculator_full_page")
def brrrr_calculator_page():
    error = None
    message = None
    results_calculated = False

    form_data_for_template = {
        "property_address": "", "purchase_price": "", "rehab_cost": "",
        "closing_costs_1": "", "arv": "", "down_payment_1_pct": "",
        "interest_rate_1": "", "rehab_period_months": "", "refinance_pct": "",
        "interest_rate_2": "", "loan_term_years": "", "closing_costs_2": "",
        "rent_estimate": "", "property_tax": "", "insurance": "",
        "property_management_pct": "", "maintenance_pct": "", "vacancy_pct": ""
    }
    calculated_outputs = {}

    property_id = request.args.get('property_id')
    if request.method == "GET" and property_id:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM properties WHERE id = %s", (property_id,))
        prop_data = cursor.fetchone()
        cursor.close()

        if prop_data:
            message = f"Property '{prop_data['property_address']}' loaded successfully! Click 'Calculate BRRRR' to view results."
            for key in form_data_for_template.keys():
                form_data_for_template[key] = str(prop_data[key]) if prop_data[key] is not None else ""
        else:
            error = "Property not found."

    if request.method == "POST":
        action = request.form.get('action')
        form_inputs = dict(request.form)

        calculated_outputs, calc_error = perform_brrrr_calculations(form_inputs)
        error = calc_error

        form_data_for_template.update(form_inputs)
        results_calculated = calculated_outputs.get('results_calculated', False)

        if not error and action == 'save':
            db = get_db()
            cursor = db.cursor()
            try:
                property_address = form_inputs.get("property_address")
                if not property_address:
                    raise ValueError("Cannot save property: Address/Name is required.")

                cursor.execute("SELECT id FROM properties WHERE property_address = %s", (property_address,))
                existing_property = cursor.fetchone()

                columns = """
                    property_address, purchase_price, rehab_cost, closing_costs_1, arv,
                    down_payment_1_pct, interest_rate_1, rehab_period_months,
                    refinance_pct, interest_rate_2, loan_term_years, closing_costs_2,
                    rent_estimate, property_tax, insurance, property_management_pct,
                    maintenance_pct, vacancy_pct
                """
                values_tuple = (
                    property_address,
                    float(form_inputs.get('purchase_price', 0.0)),
                    float(form_inputs.get('rehab_cost', 0.0)),
                    float(form_inputs.get('closing_costs_1', 0.0)),
                    float(form_inputs.get('arv', 0.0)),
                    float(form_inputs.get('down_payment_1_pct', 0.0)),
                    float(form_inputs.get('interest_rate_1', 0.0)),
                    int(form_inputs.get('rehab_period_months', 0)),
                    float(form_inputs.get('refinance_pct', 0.0)),
                    float(form_inputs.get('interest_rate_2', 0.0)),
                    int(form_inputs.get('loan_term_years', 0)),
                    float(form_inputs.get('closing_costs_2', 0.0)),
                    float(form_inputs.get('rent_estimate', 0.0)),
                    float(form_inputs.get('property_tax', 0.0)),
                    float(form_inputs.get('insurance', 0.0)),
                    float(form_inputs.get('property_management_pct', 0.0)),
                    float(form_inputs.get('maintenance_pct', 0.0)),
                    float(form_inputs.get('vacancy_pct', 0.0))
                )

                if existing_property:
                    set_clause_parts = [f"{col} = %s" for col in columns.split(', ') if col.strip() != 'property_address']
                    set_clause = ", ".join(set_clause_parts)
                    update_values = values_tuple[1:] + (property_address,)
                    cursor.execute(f"""
                       UPDATE properties SET {set_clause}, saved_at = CURRENT_TIMESTAMP
                        WHERE property_address = %s
                    """, update_values)
                    message = f"Property '{property_address}' updated successfully!"
                else:
                    placeholders = ", ".join(["%s"] * len(values_tuple))
                    cursor.execute(f"""
                        INSERT INTO properties ({columns}) VALUES ({placeholders})
                    """, values_tuple)
                    message = f"Property '{property_address}' saved successfully!"
                db.commit()

            except ValueError as ve:
                error = f"Error saving: Invalid numeric input. {ve}"
            except Exception as e:
                db.rollback()
                error = f"Database error while saving: {e}"
            finally:
                cursor.close()

        for key, value in form_data_for_template.items():
            if not isinstance(value, str) and value is not None:
                form_data_for_template[key] = str(value)

        return render_template(
            'brrrr_calculator.html',
            page_title="BRRRR Investment Calculator (Full)",
            error=error,
            message=message,
            hide_default_inputs=False,
            **form_data_for_template,
            **calculated_outputs
        )

    return render_template(
        'brrrr_calculator.html',
        page_title="BRRRR Investment Calculator (Full)",
        error=error,
        message=message,
        hide_default_inputs=False,
        **form_data_for_template,
        **calculated_outputs
    )