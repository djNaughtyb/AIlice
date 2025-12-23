#!/bin/bash

################################################################################
# Google Cloud Run Deployment Script for AIlice Platform
# Project: eighth-beacon-479707-c3
# Service: viralspark-ailice
################################################################################

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="eighth-beacon-479707-c3"
SERVICE_NAME="viralspark-ailice"
REGION="us-central1"  # Change this to your preferred region
DB_INSTANCE_NAME="ailice-postgres"
DB_NAME="ailice_db"
DB_USER="ailice"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  AIlice Platform - Google Cloud Run Deployment          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to print status messages
print_status() {
    echo -e "${BLUE}▶${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed. Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

print_success "gcloud CLI found"

# Check if user is logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "."; then
    print_warning "Not logged in to gcloud. Please authenticate..."
    gcloud auth login
fi

print_success "Authenticated with gcloud"

# Set the project
print_status "Setting project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}
print_success "Project set to ${PROJECT_ID}"

# Enable required APIs
print_status "Enabling required Google Cloud APIs..."
APIS=(
    "cloudbuild.googleapis.com"
    "run.googleapis.com"
    "sqladmin.googleapis.com"
    "compute.googleapis.com"
    "containerregistry.googleapis.com"
    "secretmanager.googleapis.com"
    "vpcaccess.googleapis.com"
)

for api in "${APIS[@]}"; do
    print_status "Enabling ${api}..."
    gcloud services enable ${api} --project=${PROJECT_ID}
done
print_success "All required APIs enabled"

# Build the Docker image
print_status "Building Docker image..."
print_warning "This may take several minutes..."
gcloud builds submit --tag ${IMAGE_NAME} --timeout=30m
print_success "Docker image built successfully: ${IMAGE_NAME}"

# Ask user if they want to create a Cloud SQL instance
echo ""
read -p "Do you want to create a Cloud SQL PostgreSQL instance? (y/n): " create_db

if [[ $create_db == "y" || $create_db == "Y" ]]; then
    print_status "Creating Cloud SQL PostgreSQL instance..."
    print_warning "This may take several minutes..."
    
    # Generate a random password for the database
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    
    # Create the Cloud SQL instance
    if gcloud sql instances describe ${DB_INSTANCE_NAME} --project=${PROJECT_ID} &> /dev/null; then
        print_warning "Cloud SQL instance ${DB_INSTANCE_NAME} already exists"
    else
        gcloud sql instances create ${DB_INSTANCE_NAME} \
            --database-version=POSTGRES_15 \
            --tier=db-f1-micro \
            --region=${REGION} \
            --project=${PROJECT_ID}
        print_success "Cloud SQL instance created: ${DB_INSTANCE_NAME}"
    fi
    
    # Set the root password
    print_status "Setting database password..."
    gcloud sql users set-password postgres \
        --instance=${DB_INSTANCE_NAME} \
        --password=${DB_PASSWORD} \
        --project=${PROJECT_ID}
    
    # Create the database
    print_status "Creating database: ${DB_NAME}..."
    gcloud sql databases create ${DB_NAME} \
        --instance=${DB_INSTANCE_NAME} \
        --project=${PROJECT_ID} || true
    
    # Create a dedicated user
    print_status "Creating database user: ${DB_USER}..."
    gcloud sql users create ${DB_USER} \
        --instance=${DB_INSTANCE_NAME} \
        --password=${DB_PASSWORD} \
        --project=${PROJECT_ID} || true
    
    # Store the database password in Secret Manager
    print_status "Storing database password in Secret Manager..."
    echo -n ${DB_PASSWORD} | gcloud secrets create ailice-db-password \
        --data-file=- \
        --replication-policy="automatic" \
        --project=${PROJECT_ID} || \
    echo -n ${DB_PASSWORD} | gcloud secrets versions add ailice-db-password \
        --data-file=- \
        --project=${PROJECT_ID}
    
    print_success "Database configuration completed"
    
    # Get the connection name
    CONNECTION_NAME=$(gcloud sql instances describe ${DB_INSTANCE_NAME} \
        --project=${PROJECT_ID} \
        --format="value(connectionName)")
    
    DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${CONNECTION_NAME}"
    
    # Deploy with Cloud SQL
    print_status "Deploying to Cloud Run with Cloud SQL..."
    gcloud run deploy ${SERVICE_NAME} \
        --image ${IMAGE_NAME} \
        --platform managed \
        --region ${REGION} \
        --allow-unauthenticated \
        --memory 2Gi \
        --cpu 2 \
        --timeout 300 \
        --max-instances 10 \
        --set-env-vars "DATABASE_URL=${DATABASE_URL},ENVIRONMENT=production" \
        --add-cloudsql-instances ${CONNECTION_NAME} \
        --project=${PROJECT_ID}
else
    print_status "Deploying to Cloud Run without database..."
    gcloud run deploy ${SERVICE_NAME} \
        --image ${IMAGE_NAME} \
        --platform managed \
        --region ${REGION} \
        --allow-unauthenticated \
        --memory 2Gi \
        --cpu 2 \
        --timeout 300 \
        --max-instances 10 \
        --set-env-vars "ENVIRONMENT=production" \
        --project=${PROJECT_ID}
fi

print_success "Deployment completed!"

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --platform managed \
    --region ${REGION} \
    --project=${PROJECT_ID} \
    --format="value(status.url)")

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Deployment Successful!                         ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Service URL:${NC} ${SERVICE_URL}"
echo -e "${BLUE}Admin Dashboard:${NC} ${SERVICE_URL}/admin/dashboard"
echo -e "${BLUE}API Docs:${NC} ${SERVICE_URL}/docs"
echo ""

if [[ $create_db == "y" || $create_db == "Y" ]]; then
    echo -e "${BLUE}Database Info:${NC}"
    echo -e "  Instance: ${DB_INSTANCE_NAME}"
    echo -e "  Database: ${DB_NAME}"
    echo -e "  User: ${DB_USER}"
    echo -e "  Password: ${DB_PASSWORD}"
    echo -e "  ${YELLOW}⚠ Save this password securely!${NC}"
    echo ""
fi

echo -e "${BLUE}Useful commands:${NC}"
echo -e "  View logs: gcloud run services logs read ${SERVICE_NAME} --region ${REGION} --project ${PROJECT_ID}"
echo -e "  Update service: gcloud run services update ${SERVICE_NAME} --region ${REGION} --project ${PROJECT_ID}"
echo -e "  Delete service: gcloud run services delete ${SERVICE_NAME} --region ${REGION} --project ${PROJECT_ID}"
echo ""

print_success "Setup complete! Your AIlice platform is now live."
echo ""