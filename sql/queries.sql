-- 1. List plots with their owners (LEFT JOIN preserves unassigned plots).
SELECT p.id, p.plot_number, p.area_sqm, p.status, o.full_name
FROM plots AS p LEFT JOIN owners AS o ON o.id = p.owner_id
ORDER BY p.plot_number;

-- 2. List recent payments with owner names (JOIN).
SELECT pay.payment_date, pay.amount, pay.description, o.full_name
FROM payments AS pay JOIN owners AS o ON o.id = pay.owner_id
ORDER BY pay.payment_date DESC;

-- 3. Filter by status (parameterized).
SELECT id, plot_number, area_sqm FROM plots WHERE status = ? ORDER BY plot_number;

-- 4. Find plots with debt above a threshold (parameterized).
SELECT id, plot_number, debt FROM plots WHERE debt > ? ORDER BY debt DESC;

-- 5. Search by plot number or owner name (parameterized).
SELECT p.plot_number, o.full_name FROM plots AS p
LEFT JOIN owners AS o ON o.id = p.owner_id
WHERE p.plot_number LIKE ? OR o.full_name LIKE ?;

-- 6. Count all registered plots.
SELECT COUNT(*) AS plot_count FROM plots;

-- 7. Sum recorded payments.
SELECT COALESCE(SUM(amount), 0) AS payments_total FROM payments;

-- 8. Group plots by status.
SELECT status, COUNT(*) AS plot_count FROM plots GROUP BY status ORDER BY status;

-- 9. Group debt by owner and keep only positive balances (HAVING).
SELECT o.full_name, SUM(p.debt) AS total_debt
FROM owners AS o JOIN plots AS p ON p.owner_id = o.id
GROUP BY o.id, o.full_name HAVING SUM(p.debt) > 0 ORDER BY total_debt DESC;

-- 10. Count plots and total debt for each owner (GROUP BY + JOIN).
SELECT o.full_name, COUNT(p.id) AS plot_count, COALESCE(SUM(p.debt), 0) AS total_debt
FROM owners AS o LEFT JOIN plots AS p ON p.owner_id = o.id
GROUP BY o.id, o.full_name ORDER BY o.full_name;

-- 11. Filter payment history by owner and date range.
SELECT payment_date, amount, description FROM payments
WHERE owner_id = ? AND payment_date BETWEEN ? AND ? ORDER BY payment_date DESC;

-- 12. Paginated plot list with deterministic ordering.
SELECT id, plot_number, status FROM plots ORDER BY plot_number LIMIT ? OFFSET ?;
