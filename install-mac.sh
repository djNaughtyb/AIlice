#!/bin/bash

################################################################################
# AIlice Platform - macOS Installer
# Automated installation script for Mac
################################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        AIlice Platform - macOS Installer                  ║${NC}"
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

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script is for macOS only"
    exit 1
fi

print_success "macOS detected"

# Check for Homebrew
print_status "Checking for Homebrew..."
if ! command -v brew &> /dev/null; then
    print_warning "Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for Apple Silicon
    if [[ $(uname -m) == 'arm64' ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
    
    print_success "Homebrew installed"
else
    print_success "Homebrew found"
fi

# Update Homebrew
print_status "Updating Homebrew..."
brew update

# Install Python 3.10 or higher
print_status "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_warning "Python not found. Installing Python 3.11..."
    brew install python@3.11
    print_success "Python installed"
else
    PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2 | cut -d '.' -f 1,2)
    print_success "Python $PYTHON_VERSION found"
fi

# Install PostgreSQL
print_status "Checking PostgreSQL installation..."
if ! command -v psql &> /dev/null; then
    print_warning "PostgreSQL not found. Installing..."
    brew install postgresql@15
    brew services start postgresql@15
    print_success "PostgreSQL installed and started"
else
    print_success "PostgreSQL found"
    # Ensure PostgreSQL is running
    brew services start postgresql@15 || brew services restart postgresql@15
fi

# Install Git (usually pre-installed on macOS)
print_status "Checking Git installation..."
if ! command -v git &> /dev/null; then
    print_warning "Git not found. Installing..."
    brew install git
    print_success "Git installed"
else
    print_success "Git found"
fi

# Create installation directory
INSTALL_DIR="$HOME/AIlice"
print_status "Creating installation directory at $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Copy application files
print_status "Copying application files..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/" 2>/dev/null || true

# Create virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

print_success "Virtual environment created"

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
print_status "Installing Python dependencies..."
print_warning "This may take several minutes..."

if [ -f requirements.txt ]; then
    pip install -r requirements.txt
    print_success "Dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi

# Setup PostgreSQL database
print_status "Setting up PostgreSQL database..."

# Generate random password
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# Create database and user
psql postgres << EOF
CREATE DATABASE ailice_db;
CREATE USER ailice WITH PASSWORD '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON DATABASE ailice_db TO ailice;
\q
EOF

print_success "Database configured"

# Create .env file
print_status "Creating configuration file..."
cat > .env << EOF
DATABASE_URL=postgresql://ailice:${DB_PASSWORD}@localhost:5432/ailice_db
ENVIRONMENT=development
PORT=8080
HOST=127.0.0.1
EOF

print_success "Configuration file created"

# Create launch script
print_status "Creating launch script..."
cat > start_ailice.sh << 'EOF'
#!/bin/bash
cd "$( dirname "${BASH_SOURCE[0]}" )"
source venv/bin/activate
python fastapi_app.py
EOF

chmod +x start_ailice.sh

# Create stop script
cat > stop_ailice.sh << 'EOF'
#!/bin/bash
pkill -f "fastapi_app.py"
echo "AIlice stopped"
EOF

chmod +x stop_ailice.sh

print_success "Launch scripts created"

# Create LaunchAgent for auto-start (optional)
print_status "Setting up auto-start (optional)..."
read -p "Do you want AIlice to start automatically on login? (y/n): " auto_start

if [[ $auto_start == "y" || $auto_start == "Y" ]]; then
    PLIST_PATH="$HOME/Library/LaunchAgents/com.ailice.platform.plist"
    mkdir -p "$HOME/Library/LaunchAgents"
    
    cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ailice.platform</string>
    <key>ProgramArguments</key>
    <array>
        <string>${INSTALL_DIR}/start_ailice.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${INSTALL_DIR}/logs/ailice.log</string>
    <key>StandardErrorPath</key>
    <string>${INSTALL_DIR}/logs/ailice.error.log</string>
</dict>
</plist>
EOF
    
    mkdir -p "$INSTALL_DIR/logs"
    launchctl load "$PLIST_PATH"
    print_success "Auto-start configured"
fi

# Start the service
print_status "Starting AIlice Platform..."
source venv/bin/activate
nohup python fastapi_app.py > logs/ailice.log 2>&1 &
AILICE_PID=$!
echo $AILICE_PID > ailice.pid

print_success "AIlice is starting..."

# Wait for service to be ready
print_status "Waiting for service to be ready..."
sleep 5

# Test if service is running
if curl -s http://localhost:8080/health > /dev/null; then
    print_success "AIlice is running!"
else
    print_warning "Service may still be starting. Check logs/ailice.log for details."
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         Installation Successful!                       ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Access your AIlice platform at:${NC}"
echo -e "  • Home: http://localhost:8080"
echo -e "  • Admin Dashboard: http://localhost:8080/admin/dashboard"
echo -e "  • API Docs: http://localhost:8080/docs"
echo ""
echo -e "${BLUE}Installation Directory:${NC} $INSTALL_DIR"
echo ""
echo -e "${BLUE}Database Info:${NC}"
echo -e "  Host: localhost"
echo -e "  Database: ailice_db"
echo -e "  User: ailice"
echo -e "  Password: ${DB_PASSWORD}"
echo -e "  ${YELLOW}⚠ Save this password securely!${NC}"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo -e "  Start AIlice: cd $INSTALL_DIR && ./start_ailice.sh"
echo -e "  Stop AIlice: cd $INSTALL_DIR && ./stop_ailice.sh"
echo -e "  View logs: tail -f $INSTALL_DIR/logs/ailice.log"
echo ""

# Open browser
read -p "Open admin dashboard in browser now? (y/n): " open_browser
if [[ $open_browser == "y" || $open_browser == "Y" ]]; then
    sleep 2
    open http://localhost:8080/admin/dashboard
fi

print_success "Setup complete! Enjoy using AIlice."
echo ""