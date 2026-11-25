\set ON_ERROR_STOP on

BEGIN;

CREATE TABLE vendor_payments (
    payment_id text PRIMARY KEY,
    vendor_id text NOT NULL,
    vendor_name text NOT NULL,
    category text,
    invoice_number text NOT NULL,
    invoice_date date NOT NULL,
    due_date date NOT NULL,
    paid_date date,
    amount numeric(12, 2) NOT NULL CHECK (amount > 0),
    status text NOT NULL CHECK (status IN ('Paid', 'Pending', 'Overdue'))
);

\copy vendor_payments FROM 'vendor_payments.csv' WITH (FORMAT csv, HEADER MATCH)

COMMIT;

SELECT COUNT(*) AS loaded_rows FROM vendor_payments;
