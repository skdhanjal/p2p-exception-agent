#!/usr/bin/env bash
# Usage: scripts/deploy_env.sh dev|prod [update-only]
set -euo pipefail
 
ENV="${1:?usage: deploy_env.sh dev|prod [update-only]}"
case "$ENV" in dev|prod) ;; *) echo "env must be dev or prod"; exit 2;; esac
SHA="$(git rev-parse --short=8 HEAD)"
SA="p2p-agent-$ENV-sa@$PROJECT_ID.iam.gserviceaccount.com"
 
VARS="APP_ENV=$ENV,GIT_SHA=$SHA,PAYMENTS_DRY_RUN=true"
VARS="$VARS,ERP_SERVER_ID=$ERP_SERVER_ID"
VARS="$VARS,VENDOR_SERVER_ID=$VENDOR_SERVER_ID"
VARS="$VARS,A2A_PAYMENTS_AGENT_URL=$A2A_PAYMENTS_AGENT_URL"
 
EXTRA=()
if [ "${2:-}" = "update-only" ]; then EXTRA+=(--update-only); fi
 
agents-cli deploy \
  --project "$PROJECT_ID" --region "$REGION" \
  --service-name "p2p-agent-$ENV" \
  --service-account "$SA" \
  --min-instances "${MIN_INSTANCES:-0}" --max-instances 5 \
  --labels "env=$ENV,git_sha=$SHA" \
  --update-env-vars "$VARS" \
  --no-confirm-project \
  ${EXTRA[@]+"${EXTRA[@]}"}
echo "deployed $ENV at $SHA"
