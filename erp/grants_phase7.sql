-- The approvals service writes approvals. Nobody else can.
GRANT `roles/bigquery.dataEditor`
  ON TABLE `PROJECT_ID.p2p_erp.approvals`
  TO "serviceAccount:APPROVALS_SA_EMAIL";
-- The payments server reads approvals and records consumption.
GRANT `roles/bigquery.dataViewer`
  ON TABLE `PROJECT_ID.p2p_erp.approvals`
  TO "serviceAccount:PAY_SA_EMAIL";
GRANT `roles/bigquery.dataEditor`
  ON TABLE `PROJECT_ID.p2p_erp.approval_consumptions`
  TO "serviceAccount:PAY_SA_EMAIL";
