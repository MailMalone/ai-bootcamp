# Day 3 vendor-payment insights

The synthetic CSV contains 123 records and 10 columns. Invoice dates run from August 1 to November 14, 2026. The pandas audit found seven blank categories and 28 blank payment dates. PostgreSQL loaded all 123 records and preserved these blanks as `NULL`. Amounts are in currency units because the CSV gives no currency code.

1. Malnad Industrial Tools was paid more than any other vendor. Its payments added up to 1,059,341.33. (Q1)
2. Three invoices appeared twice for the same vendor. Those six records need checking to see whether any invoice was actually paid twice. (Q2)
3. September 2026 had the most money paid out. The 25 payments that month added up to 1,581,246.34. (Q3)
4. Of the 95 payments, 66 were made after the due date. The longest delay was 14 days. (Q4, Q9)
5. The 28 unpaid records added up to 1,437,550.35. Of that amount, 630,207.48 was marked overdue across 13 records. (Q5)

## Index comparison

The invoice-date filter used a sequential scan both times. With just 123 rows, PostgreSQL estimated that scanning the table was cheaper than using the index.

Both runs returned the same plan.

```text
Seq Scan on vendor_payments  (cost=0.00..3.54 rows=2 width=73)
  Filter: (invoice_date = '2026-08-15'::date)
```
