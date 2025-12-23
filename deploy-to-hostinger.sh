#!/bin/bash

################################################################################
# Hostinger VPS/Cloud Deployment Script for AIlice Platform
################################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  AIlice Platform - Hostinger VPS Deployment             ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

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

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

print_success "Running as root"

# Update system packages
print_status "Updating system packages..."
apt-get update && apt-get upgrade -y
print_success "System updated"

# Install required packages
print_status "Installing required packages..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    build-essential \
    libpq-dev \
    postgresql \
    postgresql-contrib \
    nginx \
    certbot \
    python3-certbot-nginx \
    docker.io \
    docker-compose \
    ufw \
    fail2ban

print_success "Packages installed"

# Start and enable PostgreSQL
print_status "Setting up PostgreSQL..."
systemctl start postgresql
systemctl enable postgresql

# Create database and user
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
su - postgres -c "psql -c \"CREATE DATABASE ailice_db;\""
su - postgres -c "psql -c \"CREATE USER ailice WITH PASSWORD '${DB_PASSWORD}';\""
su - postgres -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE ailice_db TO ailice;\""

print_success "PostgreSQL configured"

# Ask for deployment method
echo ""
echo "Choose deployment method:"
echo "1. Docker Deployment (Recommended)"
echo "2. Native Python Deployment"
read -p "Enter choice (1 or 2): " deploy_method

if [[ $deploy_method == "1" ]]; then
    # Docker deployment
    print_status "Setting up Docker deployment..."
    
    # Start Docker
    systemctl start docker
    systemctl enable docker
    
    # Create app directory
    mkdir -p /opt/ailice
    cd /opt/ailice
    
    # Copy application files (assuming they're in current directory)
    print_status "Copying application files..."
    cp -r $OLDPWD/* /opt/ailice/
    
    # Create .env file
    cat > .env << EOF
DATABASE_URL=postgresql://ailice:${DB_PASSWORD}@postgres:5432/ailice_db
ENVIRONMENT=production
PORT=8080
HOST=0.0.0.0
EOF
    
    # Start with Docker Compose
    print_status "Starting services with Docker Compose..."
    docker-compose up -d
    
    print_success "Docker deployment completed"
    
else
    # Native Python deployment
    print_status "Setting up native Python deployment..."
    
    # Create app directory and user
    useradd -m -s /bin/bash ailice || true
    mkdir -p /opt/ailice
    cd /opt/ailice
    
    # Copy application files
    print_status "Copying application files..."
    cp -r $OLDPWD/* /opt/ailice/
    chown -R ailice:ailice /opt/ailice
    
    # Create virtual environment
    su - ailice -c "cd /opt/ailice && python3 -m venv venv"
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    su - ailice -c "cd /opt/ailice && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"
    
    # Create .env file
    cat > /opt/ailice/.env << EOF
DATABASE_URL=postgresql://ailice:${DB_PASSWORD}@localhost:5432/ailice_db
ENVIRONMENT=production
PORT=8080
HOST=0.0.0.0
EOF
    
    chown ailice:ailice /opt/ailice/.env
    
    # Create systemd service
    cat > /etc/systemd/system/ailice.service << EOF
[Unit]
Description=AIlice Platform Service
After=network.target postgresql.service

[Service]
Type=simple
User=ailice
WorkingDirectory=/opt/ailice
Environment="PATH=/opt/ailice/venv/bin"
EnvironmentFile=/opt/ailice/.env
ExecStart=/opt/ailice/venv/bin/python fastapi_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    # Enable and start service
    systemctl daemon-reload
    systemctl enable ailice
    systemctl start ailice
    
    print_success "Native Python deployment completed"
fi

# Configure Nginx
print_status "Configuring Nginx..."

read -p "Enter your domain name (e.g., ailice.example.com): " DOMAIN_NAME

cat > /etc/nginx/sites-available/ailice << EOF
server {
    listen 80;
    server_name ${DOMAIN_NAME};

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    client_max_body_size 100M;
}
EOF

ln -sf /etc/nginx/sites-available/ailice /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t
systemctl restart nginx

print_success "Nginx configured"

# Configure firewall
print_status "Configuring firewall..."
ufw allow 'Nginx Full'
ufw allow OpenSSH
ufw --force enable

print_success "Firewall configured"

# Setup SSL with Let's Encrypt
echo ""
read -p "Do you want to set up SSL with Let's Encrypt? (y/n): " setup_ssl

if [[ $setup_ssl == "y" || $setup_ssl == "Y" ]]; then
    read -p "Enter your email address for SSL certificate: " EMAIL
    print_status "Setting up SSL certificate..."
    certbot --nginx -d ${DOMAIN_NAME} --non-interactive --agree-tos -m ${EMAIL}
    print_success "SSL certificate installed"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Deployment Successful!                         ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Access your application at:${NC}"
if [[ $setup_ssl == "y" || $setup_ssl == "Y" ]]; then
    echo -e "  https://${DOMAIN_NAME}"
    echo -e "  https://${DOMAIN_NAME}/admin/dashboard"
else
    echo -e "  http://${DOMAIN_NAME}"
    echo -e "  http://${DOMAIN_NAME}/admin/dashboard"
fi
echo ""
echo -e "${BLUE}Database Info:${NC}"
echo -e "  Host: localhost"
echo -e "  Database: ailice_db"
echo -e "  User: ailice"
echo -e "  Password: ${DB_PASSWORD}"
echo -e "  ${YELLOW}⚠ Save this password securely!${NC}"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
if [[ $deploy_method == "1" ]]; then
    echo -e "  View logs: docker-compose logs -f"
    echo -e "  Restart: docker-compose restart"
    echo -e "  Stop: docker-compose down"
else
    echo -e "  View logs: journalctl -u ailice -f"
    echo -e "  Restart: systemctl restart ailice"
    echo -e "  Stop: systemctl stop ailice"
fi
echo ""
print_success "Setup complete!"
