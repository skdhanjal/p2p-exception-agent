export BILLING_ACCOUNT_ID="017DDD-922AD9-BDAA1B"
export ORG_ID="347408772710"
export PROJECT_ID="p2p-exception-agent-lab"
export REGION="us-central1"                 # deploy region
export GOOGLE_CLOUD_PROJECT="$PROJECT_ID"
export GOOGLE_CLOUD_LOCATION="global"       # model location
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export AGENT_SA="p2p-agent-local@$PROJECT_ID.iam.gserviceaccount.com"
export ERP_SA="p2p-erp-mcp-sa@$PROJECT_ID.iam.gserviceaccount.com"
export VENDOR_SA="p2p-vendor-mcp-sa@$PROJECT_ID.iam.gserviceaccount.com"
export PAY_SA="p2p-payments-mcp-sa@$PROJECT_ID.iam.gserviceaccount.com"
export REPO="$REGION-docker.pkg.dev/$PROJECT_ID/mcp-servers"
# from Phase 1, for example serviceAccount:service-123@gcp-sa-...:
export RUNTIME_PRINCIPAL="serviceAccount:service-701958438048@gcp-sa-aiplatform-re.iam.gserviceaccount.com"

export ERP_URL="https://p2p-erp-mcp-hf65ncko5q-uc.a.run.app"
export VENDOR_URL="https://p2p-vendor-mcp-hf65ncko5q-uc.a.run.app"
export PAYMENTS_URL="https://p2p-payments-mcp-hf65ncko5q-uc.a.run.app"

export PAYAGENT_SA="p2p-payments-agent-sa@$PROJECT_ID.iam.gserviceaccount.com"
export AGENT_REPO="$REGION-docker.pkg.dev/$PROJECT_ID/agents"
export PAYAGENT_URL="https://p2p-payments-agent-hf65ncko5q-uc.a.run.app"

export ERP_SERVER_ID="agentregistry-00000000-0000-0000-643c-d1a9c4ce4cff"
export VENDOR_SERVER_ID="agentregistry-00000000-0000-0000-2d3e-7f091be42c0f"
export A2A_PAYMENTS_AGENT_URL="$PAYAGENT_URL"

export DEV_AGENT_RESOURCE="projects/$PROJECT_ID/locations/$REGION/reasoningEngines/7430561153161363456"
export PROD_AGENT_RESOURCE="projects/$PROJECT_ID/locations/$REGION/reasoningEngines/412827033811288064"
export GITHUB_REPO="skdhanjal/p2p-exception-agent"

