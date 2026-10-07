CREATE OR REPLACE TABLE `PROJECT_ID.p2p_erp.vendors` (
  vendor_id STRING, name STRING, status STRING,
  bank_account_last4 STRING, payment_terms STRING
);
INSERT INTO `PROJECT_ID.p2p_erp.vendors` VALUES
  ('V-1001', 'Acme Supplies', 'active', '4821', 'NET30'),
  ('V-1002', 'Globex Logistics', 'active', '1190', 'NET45'),
  ('V-1003', 'Initech Office Goods', 'active', '7733', 'NET30'),
  ('V-1004', 'Umbrella Industrial', 'on_hold', '5502', 'NET60');
 
CREATE OR REPLACE TABLE `PROJECT_ID.p2p_erp.purchase_orders` (
  po_number STRING, vendor_id STRING, currency STRING,
  total_amount FLOAT64, status STRING
);
INSERT INTO `PROJECT_ID.p2p_erp.purchase_orders` VALUES
  ('PO-7701', 'V-1001', 'USD', 420.00, 'open'),
  ('PO-7781', 'V-1002', 'USD', 16250.00, 'open'),
  ('PO-7790', 'V-1003', 'USD', 3600.00, 'open');
 
CREATE OR REPLACE TABLE `PROJECT_ID.p2p_erp.po_lines` (
  po_number STRING, line_no INT64, description STRING,
  quantity FLOAT64, unit_price FLOAT64
);
INSERT INTO `PROJECT_ID.p2p_erp.po_lines` VALUES
  ('PO-7701', 1, 'A4 paper ream', 100, 4.20),
  ('PO-7781', 1, 'Pallet freight Mumbai-Delhi', 10, 1600.00),
  ('PO-7781', 2, 'Handling fee', 10, 25.00),
  ('PO-7790', 1, 'Ergonomic chair', 20, 180.00);
 
CREATE OR REPLACE TABLE `PROJECT_ID.p2p_erp.goods_receipts` (
  po_number STRING, line_no INT64, received_qty FLOAT64
);
INSERT INTO `PROJECT_ID.p2p_erp.goods_receipts` VALUES
  ('PO-7701', 1, 100),
  ('PO-7781', 1, 10),
  ('PO-7781', 2, 10),
  ('PO-7790', 1, 15);
CREATE OR REPLACE TABLE `PROJECT_ID.p2p_erp.invoices` (
  invoice_number STRING, vendor_id STRING, po_number STRING,
  total_amount FLOAT64, status STRING, hold_reason STRING
);
INSERT INTO `PROJECT_ID.p2p_erp.invoices` VALUES
  ('INV-1001', 'V-1001', 'PO-7650', 420.00, 'approved', NULL),
  ('INV-1002', 'V-1002', 'PO-7600', 18250.00, 'on_hold',
   'Price mismatch with PO-7600'),
  ('INV-1003', 'V-1004', 'PO-7702', 9800.00, 'on_hold',
   'Vendor under review'),
  ('INV-5521', 'V-1003', 'PO-7688', 1250.00, 'paid', NULL);
