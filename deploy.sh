#!/bin/bash
# Deployment script for GA4 KPI Reporter Cloud Function

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="${GCP_REGION:-us-central1}"
FUNCTION_NAME="${FUNCTION_NAME:-ga4-kpi-report}"
RUNTIME="python311"
MEMORY="512MB"
TIMEOUT="540s"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== GA4 KPI Reporter Deployment ===${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    exit 1
fi

# Check if project is set
if [ "$PROJECT_ID" == "your-project-id" ]; then
    echo -e "${YELLOW}Warning: GCP_PROJECT_ID not set, using current gcloud project${NC}"
    PROJECT_ID=$(gcloud config get-value project)
fi

echo -e "${GREEN}Project: ${PROJECT_ID}${NC}"
echo -e "${GREEN}Region: ${REGION}${NC}"
echo -e "${GREEN}Function: ${FUNCTION_NAME}${NC}"

# Deploy HTTP function
echo -e "\n${GREEN}Deploying HTTP Cloud Function...${NC}"
gcloud functions deploy ${FUNCTION_NAME} \
    --gen2 \
    --runtime=${RUNTIME} \
    --region=${REGION} \
    --source=. \
    --entry-point=marketing_kpi_report \
    --trigger-http \
    --allow-unauthenticated \
    --memory=${MEMORY} \
    --timeout=${TIMEOUT} \
    --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID}"

echo -e "\n${GREEN}Deployment completed!${NC}"

# Get function URL
FUNCTION_URL=$(gcloud functions describe ${FUNCTION_NAME} --region=${REGION} --gen2 --format='value(serviceConfig.uri)')
echo -e "${GREEN}Function URL: ${FUNCTION_URL}${NC}"

echo -e "\n${YELLOW}Note: Remember to set the following environment variables in Cloud Console:${NC}"
echo "  - GA4_DATASET"
echo "  - AI_PROVIDER (openai or vertexai)"
echo "  - OPENAI_API_KEY (if using OpenAI)"
echo "  - SLACK_WEBHOOK_URL or SLACK_BOT_TOKEN"
echo "  - SLACK_CHANNEL"
echo "  - REPORT_LANGUAGE (ja or en)"
