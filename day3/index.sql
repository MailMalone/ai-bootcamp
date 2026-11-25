\set ON_ERROR_STOP on

ANALYZE vendor_payments;

\echo Before the index
EXPLAIN SELECT * FROM vendor_payments WHERE invoice_date = DATE '2026-08-15';

CREATE INDEX vendor_payments_invoice_date_idx ON vendor_payments (invoice_date);

\echo After the index
EXPLAIN SELECT * FROM vendor_payments WHERE invoice_date = DATE '2026-08-15';
