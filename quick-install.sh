#!/bin/bash

################################################################################
# AIlice Platform - Universal Quick Installer
# One-command installation for Unix-based systems
################################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${MAGENTA}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║                                                            ║${NC}"
echo -e "${MAGENTA}║         🤖 AIlice Platform Quick Installer 🚀              ║${NC}"
echo -e "${MAGENTA}║                                                            ║${NC}"
echo -e "${MAGENTA}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

print_status() {
    echo -e "${CYAN}▶${NC} $1"
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

print_header() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Detect OS
print_status "Detecting operating system..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    print_success "Linux detected"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
    print_success "macOS detected"
else
    print_error "Unsupported operating system: $OSTYPE"
    echo "Please use install-mac.sh or install-windows.ps1 directly."
    exit 1
fi

# Display installation options
print_header "Choose Installation Method"
echo "1. 🐳 Docker Compose (Recommended - Easiest)"
echo "2. 💻 Native Installation (Full control)"
echo "3. 📦 Manual Setup (Advanced users)"
echo ""
read -p "Enter your choice (1-3): " install_choice

case $install_choice in
    1)
        print_header "Docker Compose Installation"
        
        # Check for Docker
        if ! command -v docker &> /dev/null; then
            print_warning "Docker not found. Would you like to install it?"
            read -p "Install Docker? (y/n): " install_docker
            
            if [[ $install_docker == "y" || $install_docker == "Y" ]]; then
                print_status "Installing Docker..."
                if [[ $OS == "mac" ]]; then
                    print_warning "Please download Docker Desktop from: https://www.docker.com/products/docker-desktop"
                    read -p "Press Enter after installing Docker Desktop..."
                else
                    curl -fsSL https://get.docker.com -o get-docker.sh
                    sudo sh get-docker.sh
                    sudo usermod -aG docker $USER
                    rm get-docker.sh
                    print_success "Docker installed"
                    print_warning "Please log out and log back in for group changes to take effect."
                    read -p "Press Enter to continue or Ctrl+C to exit..."
                fi
            else
                print_error "Docker is required for this installation method."
                exit 1
            fi
        fi
        
        # Check for docker-compose
        if ! command -v docker-compose &> /dev/null; then
            print_status "Installing docker-compose..."
            if [[ $OS == "mac" ]]; then
                brew install docker-compose
            else
                sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
                sudo chmod +x /usr/local/bin/docker-compose
            fi
            print_success "docker-compose installed"
        fi
        
        # Run Docker Compose setup
        print_status "Starting Docker Compose setup..."
        bash docker-compose-start.sh
        ;;
        
    2)
        print_header "Native Installation"
        
        if [[ $OS == "mac" ]]; then
            print_status "Running macOS installer..."
            bash install-mac.sh
        else
            print_status "Running Linux installer..."
            
            # Detect Linux distribution
            if [ -f /etc/debian_version ]; then
                print_success "Debian/Ubuntu-based system detected"
                
                # Check if running as root
                if [[ $EUID -ne 0 ]]; then
                    print_warning "This installation requires sudo privileges."
                    sudo bash install-mac.sh  # The Mac script works for Linux too with minor adjustments
                else
                    bash install-mac.sh
                fi
            elif [ -f /etc/redhat-release ]; then
                print_success "RedHat/CentOS-based system detected"
                print_warning "Please install manually or use Docker installation."
                exit 1
            else
                print_warning "Unknown Linux distribution. Attempting generic installation..."
                bash install-mac.sh
            fi
        fi
        ;;
        
    3)
        print_header "Manual Setup Instructions"
        echo ""
        echo -e "${CYAN}To manually set up AIlice:${NC}"
        echo ""
        echo "1. Install dependencies:"
        echo "   - Python 3.10 or higher"
        echo "   - PostgreSQL 15 or higher"
        echo "   - Git"
        echo ""
        echo "2. Create a virtual environment:"
        echo "   python3 -m venv venv"
        echo "   source venv/bin/activate  # On Windows: venv\\Scripts\\activate"
        echo ""
        echo "3. Install Python packages:"
        echo "   pip install -r requirements.txt"
        echo ""
        echo "4. Set up PostgreSQL:"
        echo "   createdb ailice_db"
        echo "   createuser ailice -P"
        echo ""
        echo "5. Create .env file with:"
        echo "   DATABASE_URL=postgresql://ailice:password@localhost:5432/ailice_db"
        echo "   ENVIRONMENT=development"
        echo "   PORT=8080"
        echo "   HOST=127.0.0.1"
        echo ""
        echo "6. Start the application:"
        echo "   python fastapi_app.py"
        echo ""
        echo -e "${CYAN}For detailed instructions, see DEPLOYMENT_OPTIONS.md${NC}"
        echo ""
        ;;
        
    *)
        print_error "Invalid choice. Please run the script again."
        exit 1
        ;;
esac

print_header "Installation Complete!"
print_success "Thank you for installing AIlice Platform!"
echo ""
echo -e "${CYAN}Need help?${NC}"
echo "  • Documentation: README.md"
echo "  • Deployment options: DEPLOYMENT_OPTIONS.md"
echo "  • Issues: Create an issue on GitHub"
echo ""
