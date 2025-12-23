#!/bin/bash

################################################################################
# Docker Compose Quick Start Script for AIlice Platform
################################################################################

set -e

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Starting AIlice Platform with Docker Compose...${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker is not installed. Please install Docker first.${NC}"
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}docker-compose is not installed. Please install it first.${NC}"
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if .env exists, if not create from example
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ .env file created. Please update it with your settings.${NC}"
    else
        echo -e "${YELLOW}Warning: .env.example not found. Creating minimal .env...${NC}"
        cat > .env << EOF
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
DATABASE_URL=postgresql://ailice:\${DB_PASSWORD}@postgres:5432/ailice_db
ENVIRONMENT=production
PORT=8080
HOST=0.0.0.0
CORS_ORIGINS=*
EOF
    fi
fi

# Ask if user wants to include PgAdmin
read -p "Do you want to start PgAdmin for database management? (y/n): " start_pgadmin

if [[ $start_pgadmin == "y" || $start_pgadmin == "Y" ]]; then
    COMPOSE_PROFILES="admin"
    export COMPOSE_PROFILES
    echo -e "${GREEN}Starting with PgAdmin...${NC}"
fi

# Pull latest images
echo -e "${BLUE}Pulling latest images...${NC}"
docker-compose pull

# Build the application
echo -e "${BLUE}Building AIlice application...${NC}"
docker-compose build

# Start services
echo -e "${BLUE}Starting services...${NC}"
docker-compose up -d

# Wait for services to be healthy
echo -e "${BLUE}Waiting for services to be ready...${NC}"
sleep 10

# Check health
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo ""
    echo -e "${GREEN}================================================================${NC}"
    echo -e "${GREEN}  AIlice Platform is now running!${NC}"
    echo -e "${GREEN}================================================================${NC}"
    echo ""
    echo -e "${BLUE}Access your platform at:${NC}"
    echo -e "  • Home: http://localhost:8080"
    echo -e "  • Admin Dashboard: http://localhost:8080/admin/dashboard"
    echo -e "  • API Docs: http://localhost:8080/docs"
    
    if [[ $start_pgadmin == "y" || $start_pgadmin == "Y" ]]; then
        echo -e "  • PgAdmin: http://localhost:5050"
    fi
    
    echo ""
    echo -e "${BLUE}Useful commands:${NC}"
    echo -e "  View logs: docker-compose logs -f"
    echo -e "  Stop services: docker-compose down"
    echo -e "  Restart: docker-compose restart"
    echo ""
else
    echo -e "${YELLOW}Services are starting but not yet ready.${NC}"
    echo -e "${YELLOW}Check logs with: docker-compose logs -f${NC}"
fi
