CREATE TABLE IF NOT EXISTS `PROJECT_ID.p2p_erp.payment_requests` (
  request_id STRING,
  idempotency_key STRING,
  invoice_number STRING,
  vendor_id STRING,
  amount FLOAT64,
  currency STRING,
  approval_id STRING,
  status STRING,
  created_at TIMESTAMP
);
