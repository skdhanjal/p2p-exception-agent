-- ERP server: purchase orders, lines, receipts, invoices (read)
GRANT `roles/bigquery.dataViewer`
  ON TABLE `PROJECT_ID.p2p_erp.purchase_orders`
  TO "serviceAccount:ERP_SA_EMAIL";
GRANT `roles/bigquery.dataViewer`
  ON TABLE `PROJECT_ID.p2p_erp.po_lines`
  TO "serviceAccount:ERP_SA_EMAIL";
GRANT `roles/bigquery.dataViewer`
  ON TABLE `PROJECT_ID.p2p_erp.goods_receipts`
  TO "serviceAccount:ERP_SA_EMAIL";
GRANT `roles/bigquery.dataViewer`
  ON TABLE `PROJECT_ID.p2p_erp.invoices`
  TO "serviceAccount:ERP_SA_EMAIL";
 
-- Vendor server: vendors (read)
GRANT `roles/bigquery.dataViewer`
  ON TABLE `PROJECT_ID.p2p_erp.vendors`
  TO "serviceAccount:VENDOR_SA_EMAIL";
 
-- Payments server: read invoices and vendors, write payment_requests
GRANT `roles/bigquery.dataViewer`
  ON TABLE `PROJECT_ID.p2p_erp.invoices`
  TO "serviceAccount:PAY_SA_EMAIL";
GRANT `roles/bigquery.dataViewer`
  ON TABLE `PROJECT_ID.p2p_erp.vendors`
  TO "serviceAccount:PAY_SA_EMAIL";
GRANT `roles/bigquery.dataEditor`
  ON TABLE `PROJECT_ID.p2p_erp.payment_requests`
  TO "serviceAccount:PAY_SA_EMAIL";
