export BILLING_ACCOUNT_ID="01D6C8-3B6B7B-19CD26"
export PROJECT_ID="p2p-agent-ab42"
export REGION="asia-south1"                 # deploy region
export GOOGLE_CLOUD_PROJECT="$PROJECT_ID"
export GOOGLE_CLOUD_LOCATION="$REGION"       # model location
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export AGENT_SA="p2p-agent-local@$PROJECT_ID.iam.gserviceaccount.com"
export ERP_SA="p2p-erp-mcp-sa@$PROJECT_ID.iam.gserviceaccount.com"
export VENDOR_SA="p2p-vendor-mcp-sa@$PROJECT_ID.iam.gserviceaccount.com"
export PAY_SA="p2p-payments-mcp-sa@$PROJECT_ID.iam.gserviceaccount.com"
export REPO="$REGION-docker.pkg.dev/$PROJECT_ID/mcp-servers"
# from Phase 1, for example serviceAccount:service-123@gcp-sa-...:
export RUNTIME_PRINCIPAL="serviceAccount:service-673103961300@gcp-sa-aiplatform-re.iam.gserviceaccount.com"

export ERP_URL="https://p2p-erp-mcp-d2mdcgbgwa-el.a.run.app"
export VENDOR_URL="https://p2p-vendor-mcp-d2mdcgbgwa-el.a.run.app"
export PAYMENTS_URL="https://p2p-payments-mcp-d2mdcgbgwa-el.a.run.app"
