#!/bin/bash
set -e

# AIlice Google Cloud Run Deployment Script
# This script builds and deploys AIlice to Google Cloud Run

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-eighth-beacon-479707-c3}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-viralspark-ailice}"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Database configuration (set these as needed)
INSTANCE_CONNECTION_NAME="${CLOUD_SQL_INSTANCE:-}"
DATABASE_URL="${DATABASE_URL:-}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}AIlice Cloud Run Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service Name: $SERVICE_NAME"
echo "Image: $IMAGE_NAME"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed.${NC}"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project
echo -e "${YELLOW}Setting GCP project...${NC}"
gcloud config set project $PROJECT_ID

# Build Docker image
echo ""
echo -e "${YELLOW}Building Docker image...${NC}"
gcloud builds submit --tag $IMAGE_NAME

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Docker build failed.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker image built successfully${NC}"

# Prepare deployment command
DEPLOY_CMD="gcloud run deploy $SERVICE_NAME \
    --image=$IMAGE_NAME \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --memory=4Gi \
    --cpu=2 \
    --timeout=3600 \
    --max-instances=100 \
    --min-instances=1 \
    --concurrency=80 \
    --port=8080"

# Add Cloud SQL connection if provided
if [ -n "$INSTANCE_CONNECTION_NAME" ]; then
    echo -e "${YELLOW}Adding Cloud SQL connection: $INSTANCE_CONNECTION_NAME${NC}"
    DEPLOY_CMD="$DEPLOY_CMD --add-cloudsql-instances=$INSTANCE_CONNECTION_NAME"
fi

# Add database URL if provided
if [ -n "$DATABASE_URL" ]; then
    echo -e "${YELLOW}Setting DATABASE_URL environment variable${NC}"
    DEPLOY_CMD="$DEPLOY_CMD --set-env-vars=\"DATABASE_URL=$DATABASE_URL\""
fi

# Deploy to Cloud Run
echo ""
echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
eval $DEPLOY_CMD

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Deployment failed.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✓ Deployment complete!${NC}"

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --format='value(status.url)')

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Service Name: ${GREEN}$SERVICE_NAME${NC}"
echo -e "Service URL: ${GREEN}$SERVICE_URL${NC}"
echo -e "Region: ${GREEN}$REGION${NC}"
echo ""
echo -e "${YELLOW}To view logs:${NC}"
echo "  gcloud run services logs tail $SERVICE_NAME --region=$REGION"
echo ""
echo -e "${YELLOW}To view service details:${NC}"
echo "  gcloud run services describe $SERVICE_NAME --region=$REGION"
echo ""
echo -e "${YELLOW}To update environment variables:${NC}"
echo "  gcloud run services update $SERVICE_NAME --set-env-vars=\"KEY=VALUE\" --region=$REGION"
echo ""
echo -e "${GREEN}Testing the service...${NC}"
curl -I $SERVICE_URL

echo ""
echo -e "${GREEN}Deployment successful! 🚀${NC}"
