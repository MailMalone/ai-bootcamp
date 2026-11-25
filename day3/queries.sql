-- 1. Which five vendors received the most in recorded payments?
SELECT vendor_id, MIN(vendor_name) AS vendor_name, SUM(amount) AS paid_amount
FROM vendor_payments
WHERE paid_date IS NOT NULL
GROUP BY vendor_id
ORDER BY paid_amount DESC, vendor_id
LIMIT 5;

-- 2. Which records repeat an invoice number for the same vendor?
WITH invoice_records AS (
    SELECT vendor_id, invoice_number, payment_id, amount, status,
           COUNT(*) OVER (PARTITION BY vendor_id, invoice_number) AS record_count
    FROM vendor_payments
)
SELECT vendor_id, invoice_number, payment_id, amount, status, record_count
FROM invoice_records
WHERE record_count > 1
ORDER BY vendor_id, invoice_number, payment_id;

-- 3. How much was paid each calendar month, based on the payment date?
SELECT DATE_TRUNC('month', paid_date)::date AS payment_month,
       COUNT(*) AS records, SUM(amount) AS paid_amount
FROM vendor_payments
WHERE paid_date IS NOT NULL
GROUP BY payment_month
ORDER BY payment_month;

-- 4. How many records were paid late per vendor, and what was the longest delay?
SELECT vendor_id, COUNT(*) AS late_payments, MAX(paid_date - due_date) AS max_days_late
FROM vendor_payments
WHERE paid_date > due_date
GROUP BY vendor_id
ORDER BY late_payments DESC, vendor_id;

-- 5. How much remains unpaid by recorded status?
SELECT status, COUNT(*) AS records, SUM(amount) AS outstanding_amount
FROM vendor_payments
WHERE paid_date IS NULL
GROUP BY status
ORDER BY outstanding_amount DESC, status;

-- 6. Which categories account for the most recorded spend?
SELECT category, SUM(amount) AS paid_amount
FROM vendor_payments
WHERE paid_date IS NOT NULL
GROUP BY category
ORDER BY paid_amount DESC, category;

-- 7. Which five recorded payments above the overall paid average were largest?
SELECT payment_id, vendor_id, invoice_number, amount
FROM vendor_payments
WHERE paid_date IS NOT NULL
  AND amount > (SELECT AVG(amount) FROM vendor_payments WHERE paid_date IS NOT NULL)
ORDER BY amount DESC, payment_id
LIMIT 5;

-- 8. On average, how many days elapsed between invoice and payment by vendor?
SELECT vendor_id, ROUND(AVG(paid_date - invoice_date), 1) AS average_days_to_pay
FROM vendor_payments
WHERE paid_date IS NOT NULL
GROUP BY vendor_id
ORDER BY average_days_to_pay DESC, vendor_id;

-- 9. What share of paid records met their due date?
SELECT COUNT(*) AS paid_records,
       COUNT(*) FILTER (WHERE paid_date <= due_date) AS on_time_records,
       ROUND(100.0 * COUNT(*) FILTER (WHERE paid_date <= due_date) / NULLIF(COUNT(*), 0), 1)
           AS on_time_percent
FROM vendor_payments
WHERE paid_date IS NOT NULL;

-- 10. Which vendors have at least two outstanding records?
SELECT vendor_id, COUNT(*) AS open_records, SUM(amount) AS outstanding_amount
FROM vendor_payments
WHERE paid_date IS NULL
GROUP BY vendor_id
HAVING COUNT(*) >= 2
ORDER BY outstanding_amount DESC, vendor_id;
