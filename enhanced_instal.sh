

# Check and install required tools
echo "🔧 Checking and installing required tools..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "Google Cloud SDK not found!"
    echo "Please install Google Cloud SDK first:"
    echo "https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Update gcloud components
print_status "Updating Google Cloud SDK..."
gcloud components update --quiet

# Check if Docker is available (for local testing)
if ! command -v docker &> /dev/null; then
    print_warning "Docker not found (optional for local testing)"
fi

# Install Python dependencies if needed
print_status "Checking Python dependencies..."
python3 --version || (print_error "Python 3 not found" && exit 1)

pip3 install --user --quiet fastapi uvicorn requests 2>/dev/null || print_warning "pip install failed (will use Docker instead)"

# Check if we're in the right project
echo ""
echo "📋 Project Configuration"
echo "======================="

PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    print_error "No project selected!"
    echo "Please run: gcloud config set project YOUR_PROJECT_ID"
    echo "Or create a new project at: https://console.cloud.google.com/"
    exit 1
fi

if [ "$PROJECT_ID" != "viralspark-app" ]; then
    print_warning "Current project: $PROJECT_ID"
    read -p "Do you want to use this project? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Please set the correct project:"
        echo "gcloud config set project viralspark-app"
        exit 1
    fi
fi

print_status "Using project: $PROJECT_ID"

# Enable required APIs
echo ""
echo "🔧 Enabling Google Cloud APIs"
echo "==========================="

apis=(
    "run.googleapis.com"
    "storage.googleapis.com" 
    "secretmanager.googleapis.com"
    "cloudbuild.googleapis.com"
    "containerregistry.googleapis.com"
)

for api in "${apis[@]}"; do
    echo "Enabling $api..."
    gcloud services enable $api --quiet || print_error "Failed to enable $api"
done

print_status "All APIs enabled successfully"

# Create the application
echo ""
echo "📦 Creating Ailice Application"
echo "============================="

mkdir -p ailice-app
cd ailice-app

# Create enhanced main application
cat > main.py << 'PYEOF'
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import json
import uvicorn
import os
from datetime import datetime

app = FastAPI(
    title="Ailice - Your AI Assistant",
    description="Central AI engine for all your applications",
    version="1.0.0"
)

# Configuration
CONFIG = {
    "service": "ailice",
    "version": "1.0.0",
    "backend": "viralspark.app",
    "ui": "ailice.viralspark.app",
    "status": "active",
    "deployed_at": datetime.now().isoformat(),
    "agents": [
        "content-creator",
        "coder", 
        "researcher",
        "seo-content-writer",
        "frontend-developer",
        "legal-advisor",
        "software-architect"
    ],
    "capabilities": [
        "web-automation",
        "content-generation",
        "code-development",
        "api-integration"
    ]
}

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head>
            <title>Ailice - Your AI Assistant</title>
            <style>
                body { 
                    font-family: 'Segoe UI', Arial, sans-serif; 
                    margin: 0; 
                    padding: 0; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: #333;
                }
                .container { 
                    max-width: 1000px; 
                    margin: 0 auto; 
                    padding: 40px 20px;
                }
                .header { 
                    background: rgba(255,255,255,0.95);
                    padding: 40px; 
                    border-radius: 15px; 
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    text-align: center;
                    margin-bottom: 30px;
                }
                .feature-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }
                .feature { 
                    background: rgba(255,255,255,0.95);
                    padding: 25px; 
                    border-radius: 10px; 
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                }
                .endpoint { 
                    font-family: 'Courier New', monospace; 
                    background: #e8f0fe; 
                    padding: 8px 12px;
                    border-radius: 5px;
                    display: inline-block;
                    margin: 5px 0;
                }
                .status {
                    background: #4CAF50;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 20px;
                    display: inline-block;
                    font-weight: bold;
                }
                h1 { color: #4285f4; margin-bottom: 10px; }
                h2 { color: #333; border-bottom: 2px solid #4285f4; padding-bottom: 10px; }
                h3 { color: #555; }
                .emoji { font-size: 1.5em; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1><span class="emoji">🧠</span> Ailice is Running!</h1>
                    <p class="status">✅ ACTIVE</p>
                    <p>Your AI assistant is active and ready to serve your applications.</p>
                </div>
                
                <div class="feature-grid">
                    <div class="feature">
                        <h2><span class="emoji">🌐</span> Web Interface</h2>
                        <p>Access Ailice through your web browser with a beautiful, responsive interface.</p>
                    </div>
                    
                    <div class="feature">
                        <h2><span class="emoji">🔌</span> API Endpoints</h2>
                        <p>Connect your applications to Ailice:</p>
                        <div class="endpoint">/api/health</div>
                        <div class="endpoint">/api/config</div>
                        <div class="endpoint">/api/agents</div>
                    </div>
                    
                    <div class="feature">
                        <h2><span class="emoji">🚀</span> Ready for Your Apps</h2>
                        <p>Neuroflow and other applications can connect via the API endpoints above.</p>
                    </div>
                </div>
                
                <div class="feature">
                    <h2><span class="emoji">🛠️</span> Available Agents</h2>
                    <p>Ailice includes specialized AI agents for various tasks:</p>
                    <ul>
                        <li><strong>Content Creator</strong> - Generate engaging content</li>
                        <li><strong>Coder</strong> - Software development</li>
                        <li><strong>Researcher</strong> - Information gathering</li>
                        <li><strong>SEO Writer</strong> - Optimized content</li>
                        <li><strong>Frontend Developer</strong> - Web development</li>
                    </ul>
                </div>
            </div>
        </body>
    </html>
    """

@app.get("/api/health")
async def health():
    return {
        "status": "healthy", 
        "service": "ailice", 
        "message": "Ailice is running and ready to serve!",
        "timestamp": datetime.now().isoformat(),
        "uptime": "Just deployed"
    }

@app.get("/api/config")
async def get_config():
    return CONFIG

@app.get("/api/agents")
async def list_agents():
    return {
        "agents": CONFIG["agents"],
        "total": len(CONFIG["agents"]),
        "message": "All agents are ready to use"
    }

@app.get("/api/capabilities")
async def get_capabilities():
    return {
        "capabilities": CONFIG["capabilities"],
        "description": "Real-world capabilities available through Ailice"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
PYEOF

# Create requirements.txt
ubunto 
cat > requirements.txt << 'REQEOF'
fastapi==0.104.1
uvicorn==0.24.0
requests==2.31.0
python-multipart==0.0.6
REQEOF

# Create Dockerfile
cat > Dockerfile << 'DOCKEREOF'
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# Run the application
CMD ["python", "main.py"]
DOCKEREOF

# Create .dockerignore
cat > .dockerignore << 'DOCKEREOF'
__pycache__
*.pyc
*.pyo
*.pyd
.git
.pytest_cache
.coverage
.tox
.env
*.log
DOCKEREOF

print_status "Ailice application created successfully!"

# Deploy to Cloud Run
echo ""
echo "🚀 Deploying to Google Cloud Run"
echo "==============================="

# Get project ID for image naming
PROJECT_ID=$(gcloud config get-value project)
IMAGE_NAME="gcr.io/${PROJECT_ID}/ailice"
SERVICE_NAME="ailice"
REGION="us-central1"

print_status "Building Docker image..."
gcloud builds submit --tag ${IMAGE_NAME} --quiet

if [ $? -ne 0 ]; then
    print_error "Docker image build failed!"
    exit 1
fi

print_status "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --max-instances 10 \
  --min-instances 0 \
  --quiet

if [ $? -ne 0 ]; then
    print_error "Cloud Run deployment failed!"
    exit 1
fi

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --platform managed \
  --region ${REGION} \
  --format 'value(status.url)')

echo ""
echo "🎉 Installation Complete!"
echo "======================="
print_status "Ailice is now running!"
echo ""
echo "🌐 Web Interface: ${GREEN}${SERVICE_URL}${NC}"
echo "🔌 API Health: ${GREEN}${SERVICE_URL}/api/health${NC}"
echo "🔌 API Config: ${GREEN}${SERVICE_URL}/api/config${NC}"
echo "🔌 API Agents: ${GREEN}${SERVICE_URL}/api/agents${NC}"
echo ""
echo "📋 Next Steps:"
echo "1. Set up your custom domains: viralspark.app and ailice.viralspark.app"
echo "2. Connect your applications to the API endpoints above"
echo "3. Enjoy your Ailice assistant!"
echo ""
echo "📧 For support, check the logs:"
echo "   gcloud logging read 'resource.type=cloud_run_revision'"
echo ""

# Open the service URL in browser (if possible)
if command -v xdg-open &> /dev/null; then
    xdg-open ${SERVICE_URL} 2>/dev/null || print_status "Service URL: ${SERVICE_URL}"
elif command -v open &> /dev/null; then
    open ${SERVICE_URL} 2>/dev/null || print_status "Service URL: ${SERVICE_URL}"
else
    print_status "Service URL: ${SERVICE_URL}"
fi
                  
