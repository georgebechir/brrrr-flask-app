-- schema.sql
-- PostgreSQL schema for brrrr_real_estate_app

CREATE TABLE IF NOT EXISTS properties (
    id SERIAL PRIMARY KEY,
    property_address TEXT NOT NULL UNIQUE,
    purchase_price NUMERIC(15, 2) NOT NULL,
    rehab_cost NUMERIC(15, 2) NOT NULL,
    closing_costs_1 NUMERIC(15, 2) NOT NULL,
    arv NUMERIC(15, 2) NOT NULL,
    down_payment_1_pct NUMERIC(5, 2) NOT NULL,
    interest_rate_1 NUMERIC(5, 3) NOT NULL,
    rehab_period_months INTEGER NOT NULL,
    refinance_pct NUMERIC(5, 2) NOT NULL,
    interest_rate_2 NUMERIC(5, 3) NOT NULL,
    loan_term_years INTEGER NOT NULL,
    closing_costs_2 NUMERIC(15, 2) NOT NULL,
    rent_estimate NUMERIC(15, 2) NOT NULL,
    property_tax NUMERIC(15, 2) NOT NULL,
    insurance NUMERIC(15, 2) NOT NULL,
    property_management_pct NUMERIC(5, 2) NOT NULL,
    maintenance_pct NUMERIC(5, 2) NOT NULL,
    vacancy_pct NUMERIC(5, 2) NOT NULL,
    saved_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
