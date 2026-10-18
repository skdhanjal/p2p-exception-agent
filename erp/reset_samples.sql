DELETE FROM `PROJECT_ID.p2p_erp.invoices`
WHERE invoice_number IN
  ('INV-2001', 'INV-2002', 'INV-2003', 'INV-2005', 'INV-2006');
DELETE FROM `PROJECT_ID.p2p_erp.payment_requests`
WHERE invoice_number IN
  ('INV-2001', 'INV-2002', 'INV-2003', 'INV-2005', 'INV-2006');
