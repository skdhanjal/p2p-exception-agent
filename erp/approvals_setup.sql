CREATE TABLE IF NOT EXISTS `PROJECT_ID.p2p_erp.approvals` (
  approval_id STRING,
  invoice_number STRING,
  vendor_id STRING,
  amount FLOAT64,
  currency STRING,
  decision STRING,
  approver_email STRING,
  comment STRING,
  decided_at TIMESTAMP
)
OPTIONS (kms_key_name = 'KMS_KEY');
 
CREATE TABLE IF NOT EXISTS `PROJECT_ID.p2p_erp.approval_consumptions` (
  approval_id STRING,
  request_id STRING,
  consumed_at TIMESTAMP
);
